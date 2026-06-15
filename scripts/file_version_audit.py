#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - File Version Audit & Cleanup Marking
标记无版本文件，确定可删除/保留/需审查
"""

import sys, os, ast, re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'D:\openclaw-workspace\football_quant_os')
OUTPUT = BASE / 'references' / 'FILE_VERSION_AUDIT_2026-06-14.md'

def has_version_marker(content):
    """检查文件是否有版本标记"""
    markers = [
        r'v[0-9]\.[0-9]',  # v1.0, v2.1, v4.2.1
        r'Version\s*[:=]',  # Version: 1.0
        r'__version__',  # Python version variable
        r'@version',  # Javadoc style
        r'v[0-9]+\.[0-9]+\.[0-9]+',  # semver
        r'2026-\d{2}-\d{2}',  # date marker
        r'Naga Core',  # Naga branding
        r'Football Quant OS',  # System branding
    ]
    for pattern in markers:
        if re.search(pattern, content, re.I):
            return True
    return False

def has_docstring(content):
    """检查是否有模块级文档字符串"""
    try:
        tree = ast.parse(content)
        if tree.body and isinstance(tree.body[0], ast.Expr):
            if isinstance(tree.body[0].value, (ast.Constant, ast.Str)):
                return True
    except:
        pass
    return False

def analyze_file_imports(filepath):
    """分析文件被谁导入"""
    basename = filepath.name
    modname = basename.replace('.py', '')
    importers = []
    for pyf in BASE.rglob('*.py'):
        if pyf == filepath:
            continue
        try:
            with open(pyf, 'r', encoding='utf-8') as f:
                content = f.read()
            if modname in content:
                importers.append(str(pyf.relative_to(BASE)))
        except:
            pass
    return importers

def determine_action(filepath, content, imports, importers, has_version, has_doc):
    """
    确定文件操作：KEEP / DELETE / REVIEW / ARCHIVE
    
    规则：
    - KEEP: 被其他文件导入、有版本标记、是核心模块
    - DELETE: 临时脚本、test文件、无导入、无版本、无功能
    - REVIEW: 可能有价值但不确定
    - ARCHIVE: 保留但标记为历史/备份
    """
    rel = str(filepath.relative_to(BASE))
    
    # 核心文件 - 必须保留
    core_files = ['app/tasks.py', 'app/main.py', 'app/api.py', 'app/auth.py',
                  'core/config.py', 'core/scheduler.py', 'core/redis_cache.py',
                  'core/agent_pool.py', 'core/event_bus.py', 'core/logger.py',
                  'models/kelly.py', 'models/matrix_108.py', 'models/historical_odds.py',
                  'agents/multi_market_predictor.py', 'agents/coach_factor.py',
                  'agents/odds_pricing.py', 'agents/treasury.py', 'agents/intelligence.py',
                  'agents/trading.py', 'agents/risk_guardian.py', 'agents/upset_detector.py',
                  'agents/worldcup_analyst.py', 'agents/worldcup_data_engineer.py',
                  'agents/coach_data_sync.py', 'agents/coach_factor_bridge.py',
                  'agents/coach_types.py', 'agents/worldcup_2026_full_coaches.py',
                  'reports/generate_pdf_report.py', 'reports/gen_pdf.py',
                  'tests/test_core.py', 'tests/__init__.py']
    
    if rel in core_files:
        return 'KEEP', 'Core module - required by system'
    
    # 被导入的文件 - 保留
    if importers:
        return 'KEEP', f'Imported by {len(importers)} file(s): {", ".join(importers[:3])}' + ('...' if len(importers) > 3 else '')
    
    # 临时/测试脚本 - 可删除
    basename = os.path.basename(rel)
    temp_patterns = [
        'test_', 'fix_', 'demo_', 'debug_', 'check_', 'verify_',
        'fetch_', 'scrape_', 'search_', 'analyze_', 'predict_',
        'generate_', 'extract_', 'get_'
    ]
    for pattern in temp_patterns:
        if basename.startswith(pattern) or f'/{pattern}' in rel:
            # 但如果是核心功能，保留
            if 'core' in rel or 'main' in basename or 'api' in basename:
                break
            return 'DELETE', 'Temporary script - no imports, no version, likely one-time use'
    
    # 无文档、无版本、无导入 - 可疑
    if not has_version and not has_doc and not importers:
        # 检查文件内容是否有实际功能
        if len(content.strip()) < 50:
            return 'DELETE', 'Empty or near-empty file'
        if 'def ' not in content and 'class ' not in content:
            return 'DELETE', 'No functions or classes - likely data/config file'
        return 'REVIEW', 'No version, no docstring, no imports - needs manual review'
    
    # 默认保留
    return 'KEEP', 'Default keep - review recommended'

# ============================================================
# MAIN
# ============================================================
print('[1/3] Scanning all Python files...')
all_py = list(BASE.rglob('*.py'))
all_py = [f for f in all_py if '__pycache__' not in str(f) and '.git' not in str(f)]

print(f'  Total Python files: {len(all_py)}')

# Categorize
versioned = []
unversioned = []

for fp in all_py:
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        continue
    
    has_v = has_version_marker(content)
    has_d = has_docstring(content)
    rel = str(fp.relative_to(BASE))
    
    if has_v or has_d:
        versioned.append((rel, has_v, has_d))
    else:
        unversioned.append((rel, has_v, has_d))

print(f'  Versioned: {len(versioned)}')
print(f'  Unversioned: {len(unversioned)}')

# Analyze unversioned files
print('[2/3] Analyzing unversioned files...')
results = []

for rel, has_v, has_d in unversioned:
    fp = BASE / rel
    try:
        with open(fp, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        continue
    
    # Count imports
    try:
        tree = ast.parse(content)
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    except:
        imports = []
    
    # Find importers
    importers = analyze_file_imports(fp)
    
    # Determine action
    action, reason = determine_action(fp, content, imports, importers, has_v, has_d)
    
    # Count functions and classes
    funcs = len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)])
    classes = len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
    lines = len(content.split('\n'))
    
    results.append({
        'file': rel,
        'action': action,
        'reason': reason,
        'lines': lines,
        'funcs': funcs,
        'classes': classes,
        'imports': len(imports),
        'importers': len(importers),
        'importer_list': importers[:3],
    })

# Sort by action
results.sort(key=lambda x: {'DELETE': 0, 'REVIEW': 1, 'ARCHIVE': 2, 'KEEP': 3}.get(x['action'], 4))

print('[3/3] Generating report...')

# Generate report
report = f"""# Football Quant OS - File Version Audit & Cleanup Plan
## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
## Auditor: Naga Core v5.0

---

## Executive Summary

| Category | Count | Action |
|----------|-------|--------|
| Versioned Files | {len(versioned)} | KEEP |
| Unversioned Files | {len(unversioned)} | REVIEW |
| **→ Marked DELETE** | {sum(1 for r in results if r['action'] == 'DELETE')} | Delete |
| **→ Marked REVIEW** | {sum(1 for r in results if r['action'] == 'REVIEW')} | Manual review |
| **→ Marked KEEP** | {sum(1 for r in results if r['action'] == 'KEEP')} | Keep |
| **→ Marked ARCHIVE** | {sum(1 for r in results if r['action'] == 'ARCHIVE')} | Archive |

---

## 1. Files Marked DELETE (Safe to Remove)

> These files are temporary scripts, test files, or empty files with no imports and no version history.

| File | Lines | Functions | Classes | Reason |
|------|-------|-----------|---------|--------|
"""

for r in results:
    if r['action'] == 'DELETE':
        report += f"| `{r['file']}` | {r['lines']} | {r['funcs']} | {r['classes']} | {r['reason']} |\n"

report += """
### DELETE Commands (Copy-Paste Ready)

```powershell
# Run from football_quant_os directory
"""

for r in results:
    if r['action'] == 'DELETE':
        report += f"Remove-Item '{r['file']}' -Force\n"

report += """```

---

## 2. Files Marked REVIEW (Needs Manual Decision)

> These files have no version, no docstring, and are not imported by other files. They may be valuable one-off scripts or dead code.

| File | Lines | Functions | Classes | Importers | Reason |
|------|-------|-----------|---------|-----------|--------|
"""

for r in results:
    if r['action'] == 'REVIEW':
        imp = ', '.join(r['importer_list']) if r['importer_list'] else 'None'
        report += f"| `{r['file']}` | {r['lines']} | {r['funcs']} | {r['classes']} | {r['importers']} | {r['reason']} |\n"

report += """
### Review Checklist

For each REVIEW file, check:
- [ ] Is this script still used by any workflow?
- [ ] Does it contain valuable logic that should be moved to a core module?
- [ ] Is it a duplicate of another script?
- [ ] Can it be merged into an existing module?

---

## 3. Files Marked KEEP (Required by System)

> These files are either imported by other modules, core infrastructure, or have clear purpose.

| File | Lines | Functions | Classes | Importers | Reason |
|------|-------|-----------|---------|-----------|--------|
"""

for r in results:
    if r['action'] == 'KEEP':
        imp = ', '.join(r['importer_list']) if r['importer_list'] else 'None'
        report += f"| `{r['file']}` | {r['lines']} | {r['funcs']} | {r['classes']} | {r['importers']} | {r['reason']} |\n"

report += """
---

## 4. Versioned Files (Reference)

> These files have explicit version markers and are considered maintained.

| File | Version Marker | Docstring |
|------|---------------|-----------|
"""

for rel, has_v, has_d in sorted(versioned):
    v = 'Yes' if has_v else 'No'
    d = 'Yes' if has_d else 'No'
    report += f"| `{rel}` | {v} | {d} |\n"

report += f"""
---

## 5. Cleanup Script

```powershell
# Safe delete (moves to _archive_20260614 instead of deleting)
$archive = '_archive_20260614'
New-Item -ItemType Directory -Force -Path $archive

"""

for r in results:
    if r['action'] == 'DELETE':
        report += f"Copy-Item '{r['file']}' $archive/ 2>$null; Remove-Item '{r['file']}' -Force\n"

report += """```

---

## 6. After Cleanup Stats

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Python Files | REPLACE_TOTAL | REPLACE_AFTER | -REPLACE_DELETED |
| Lines of Code | REPLACE_LOC_BEFORE | REPLACE_LOC_AFTER | -REPLACE_LOC_DELETED |
| Unversioned Files | REPLACE_UNV_BEFORE | REPLACE_UNV_AFTER | -REPLACE_UNV_DELETED |

---

## 7. Recommendations

### Immediate (This Week)
1. **Delete all DELETE-marked files** - Safe, no dependencies
2. **Review all REVIEW-marked files** - Decide keep/archive/delete
3. **Add version markers to all KEEP files** - Prevent future ambiguity

### Short Term (This Month)
4. **Consolidate duplicate scripts** - Many analyze_*.py may be similar
5. **Move reusable logic to core modules** - Scripts should be thin wrappers
6. **Add module-level docstrings** - All files should have documentation

### Long Term (Next Quarter)
7. **Implement semantic versioning** - All modules should have __version__
8. **Add deprecation warnings** - For transitional scripts
9. **Create script inventory** - Document what each script does

---

*File Version Audit | Football Quant OS v4.2.1-naga | {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

# Calculate stats - for unversioned files only
total_loc = sum(r['lines'] for r in results)
delete_loc = sum(r['lines'] for r in results if r['action'] == 'DELETE')
keep_loc = sum(r['lines'] for r in results if r['action'] == 'KEEP')
review_loc = sum(r['lines'] for r in results if r['action'] == 'REVIEW')

total_files = len(results)
delete_files = sum(1 for r in results if r['action'] == 'DELETE')
keep_files = sum(1 for r in results if r['action'] == 'KEEP')
review_files = sum(1 for r in results if r['action'] == 'REVIEW')

report = report.replace('REPLACE_TOTAL', str(len(all_py)))
report = report.replace('REPLACE_AFTER', str(len(all_py) - delete_files))
report = report.replace('REPLACE_DELETED', str(delete_files))
report = report.replace('REPLACE_LOC_BEFORE', str(total_loc))
report = report.replace('REPLACE_LOC_AFTER', str(total_loc - delete_loc))
report = report.replace('REPLACE_LOC_DELETED', str(delete_loc))
report = report.replace('REPLACE_UNV_BEFORE', str(len(unversioned)))
report = report.replace('REPLACE_UNV_AFTER', str(len(unversioned) - delete_files))
report = report.replace('REPLACE_UNV_DELETED', str(delete_files))

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(report)

print(f'\nReport saved: {OUTPUT}')
print(f'\nBreakdown:')
print(f'  DELETE: {delete_files} files ({delete_loc} lines)')
print(f'  REVIEW: {review_files} files ({review_loc} lines)')
print(f'  KEEP: {keep_files} files ({keep_loc} lines)')

print(f'\nTop 10 DELETE candidates:')
for r in results:
    if r['action'] == 'DELETE':
        print(f'  - {r["file"]} ({r["lines"]} lines)')

print(f'\nTop 10 REVIEW candidates:')
for r in results:
    if r['action'] == 'REVIEW':
        print(f'  - {r["file"]} ({r["lines"]} lines) - {r["reason"][:60]}')
