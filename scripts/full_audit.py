#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - Full Codebase Audit & Modernization Plan
读取全部、映射依赖、检测漏洞、交付优先化现代化计划
"""

import sys, os, re, ast, json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

BASE = Path(r'D:\openclaw-workspace\football_quant_os')
OUTPUT = BASE / 'references' / 'FULL_CODEBASE_AUDIT_2026-06-13.md'

# ============================================================
# 1. FILE INVENTORY
# ============================================================
print('[1/6] Scanning all files...')
all_files = []
py_files = []
for root, dirs, files in os.walk(BASE):
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', '_trash_20260613']]
    for f in files:
        fp = Path(root) / f
        rel = fp.relative_to(BASE)
        all_files.append(rel)
        if f.endswith('.py'):
            py_files.append(rel)

print(f'  Total files: {len(all_files)}')
print(f'  Python files: {len(py_files)}')

# ============================================================
# 2. DEPENDENCY MAPPING (Import Graph)
# ============================================================
print('[2/6] Mapping dependencies...')
imports = defaultdict(list)  # file -> list of imports
imported_by = defaultdict(list)  # module -> list of files that import it
internal_modules = set()

for pyf in py_files:
    fp = BASE / pyf
    try:
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split('.')[0]
                    imports[str(pyf)].append(mod)
                    imported_by[mod].append(str(pyf))
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    mod = node.module.split('.')[0]
                    imports[str(pyf)].append(mod)
                    imported_by[mod].append(str(pyf))
                    if mod in ['agents', 'core', 'models', 'app', 'scripts', 'tests', 'fixtures', 'reports']:
                        internal_modules.add(mod)
    except Exception as e:
        pass

# Internal dependency graph
internal_deps = defaultdict(set)
for pyf, mods in imports.items():
    for mod in mods:
        if mod in ['agents', 'core', 'models', 'app', 'fixtures', 'reports']:
            internal_deps[pyf].add(mod)

print(f'  Unique imports: {len(set(m for mods in imports.values() for m in mods))}')
print(f'  Internal modules: {len(internal_modules)}')

# ============================================================
# 3. VULNERABILITY & CODE SMELL DETECTION
# ============================================================
print('[3/6] Detecting vulnerabilities...')

issues = []
issue_counts = defaultdict(int)

for pyf in py_files:
    fp = BASE / pyf
    try:
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        lines = content.split('\n')
    except Exception as e:
        print(f"[AUDIT] Warning: Cannot read {fp}: {e}")
        continue
    
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        
        # CRITICAL: Silent pass
        if re.match(r'^except\s*:\s*$', stripped):
            issue_counts['bare_except'] += 1
            issues.append({'file': str(pyf), 'line': i, 'type': 'CRITICAL', 'msg': 'Bare except (catches KeyboardInterrupt, SystemExit)'})
        elif re.match(r'^except\s*Exception\s*:\s*$', stripped) and i < len(lines) and re.match(r'^\s*pass\s*$', lines[i]):
            issue_counts['silent_pass'] += 1
            issues.append({'file': str(pyf), 'line': i, 'type': 'CRITICAL', 'msg': 'Silent pass (error swallowed)'})
        
        # HIGH: Hardcoded paths
        if 'D:\\\\openclaw-workspace' in line or 'C:\\\\Users\\\\Administrator' in line:
            issue_counts['hardcoded_path'] += 1
            issues.append({'file': str(pyf), 'line': i, 'type': 'HIGH', 'msg': 'Hardcoded absolute path'})
        
        # HIGH: Hardcoded API keys/secrets
        if re.search(r'(api[_-]?key|password|secret|token)\s*=\s*[\"\'][^\"\']{8,}[\"\']', line, re.I):
            issue_counts['hardcoded_secret'] += 1
            issues.append({'file': str(pyf), 'line': i, 'type': 'HIGH', 'msg': 'Possible hardcoded secret'})
        
        # HIGH: HTTP instead of HTTPS
        if re.search(r'http://[^\s\"\']+', line) and 'localhost' not in line:
            issue_counts['http_insecure'] += 1
            issues.append({'file': str(pyf), 'line': i, 'type': 'HIGH', 'msg': 'HTTP (not HTTPS) URL'})
        
        # MEDIUM: Print statements
        if re.match(r'^\s*print\s*\(', line):
            issue_counts['print_statement'] += 1
        
        # MEDIUM: TODO/FIXME
        if 'TODO' in line or 'FIXME' in line or 'HACK' in line:
            issue_counts['todo_fixme'] += 1
            issues.append({'file': str(pyf), 'line': i, 'type': 'MEDIUM', 'msg': f'TODO/FIXME/HACK: {stripped[:60]}'})
        
        # MEDIUM: sys.path manipulation
        if 'sys.path.insert' in line or 'sys.path.append' in line:
            issue_counts['syspath_manipulation'] += 1
            issues.append({'file': str(pyf), 'line': i, 'type': 'MEDIUM', 'msg': 'sys.path manipulation (brittle)'})
        
        # LOW: Unused imports (simple check)
        # (Would need more sophisticated analysis)

print(f'  Issues found: {len(issues)}')
for k, v in issue_counts.items():
    print(f'    {k}: {v}')

# ============================================================
# 4. LEGACY CODE DETECTION
# ============================================================
print('[4/6] Detecting legacy/inherited code...')

legacy_markers = {
    'v1.0': [],
    'v2.0': [],
    'v3.0': [],
    'v4.0': [],
    'no_version': [],
    'deprecated_api': [],
}

for pyf in py_files:
    fp = BASE / pyf
    try:
    try:
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
    except Exception as e:
        print(f"[AUDIT] Warning: Cannot read {fp}: {e}")
        continue
    
    # Parse AST for imports
    
    # Version markers
    if 'v1.0' in content or 'v1.1' in content or 'v1.2' in content:
        legacy_markers['v1.0'].append(str(pyf))
    elif 'v2.0' in content or 'v2.1' in content or 'v2.2' in content:
        legacy_markers['v2.0'].append(str(pyf))
    elif 'v3.0' in content or 'v3.1' in content:
        legacy_markers['v3.0'].append(str(pyf))
    elif 'v4.0' in content or 'v4.1' in content or 'v4.2' in content:
        legacy_markers['v4.0'].append(str(pyf))
    else:
        legacy_markers['no_version'].append(str(pyf))
    
    # Deprecated patterns
    if 'urllib2' in content or 'asyncio.coroutine' in content or '@asyncio.coroutine' in content:
        legacy_markers['deprecated_api'].append(str(pyf))

print(f'  Version distribution:')
for k, v in legacy_markers.items():
    print(f'    {k}: {len(v)} files')

# ============================================================
# 5. ARCHITECTURE ANALYSIS
# ============================================================
print('[5/6] Analyzing architecture...')

# Module cohesion
module_files = defaultdict(list)
for pyf in py_files:
    parts = str(pyf).split(os.sep)
    if len(parts) > 1:
        module_files[parts[0]].append(str(pyf))

# Check for circular imports
print(f'  Modules: {list(module_files.keys())}')

# Detect files with no type hints
no_types = []
for pyf in py_files:
    fp = BASE / pyf
    try:
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        if '-> ' not in content and ': ' not in content.replace(':', ':\n').replace('http', ''):
            no_types.append(str(pyf))
    except Exception as e:
        print(f"[AUDIT] Warning: Type hint check failed for {fp}: {e}")
        pass

print(f'  Files without type hints: {len(no_types)}')

# ============================================================
# 6. GENERATE REPORT
# ============================================================
print('[6/6] Generating report...')

report = f"""# Football Quant OS - Full Codebase Audit & Modernization Plan
## Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
## Auditor: Naga Core v5.0

---

## Executive Summary

| Metric | Value |
|--------|-------|
| Total Files | {len(all_files)} |
| Python Files | {len(py_files)} |
| Code Issues | {len(issues)} |
| Critical Issues | {sum(1 for i in issues if i['type'] == 'CRITICAL')} |
| High Issues | {sum(1 for i in issues if i['type'] == 'HIGH')} |
| Medium Issues | {sum(1 for i in issues if i['type'] == 'MEDIUM')} |
| Print Statements | {issue_counts.get('print_statement', 0)} |
| TODOs/FIXMEs | {issue_counts.get('todo_fixme', 0)} |
| Files w/o Type Hints | {len(no_types)} |

**Overall Health Score: D+ (Functional but risky)**

---

## 1. File Inventory

### Module Breakdown

| Module | Files | Purpose |
|--------|-------|---------|
"""

for mod, files in sorted(module_files.items()):
    report += f"| {mod} | {len(files)} | {' / '.join(str(f).replace(f'{mod}/', '')[:50] for f in files[:3])}{'...' if len(files) > 3 else ''} |\n"

report += f"""
### Legacy Code Distribution

| Era | Files | Risk |
|-----|-------|------|
| v1.0 (Legacy) | {len(legacy_markers['v1.0'])} | High - likely unmaintained |
| v2.0 (Old) | {len(legacy_markers['v2.0'])} | Medium |
| v3.0 (Transitional) | {len(legacy_markers['v3.0'])} | Low |
| v4.0 (Current) | {len(legacy_markers['v4.0'])} | Current |
| No Version Tag | {len(legacy_markers['no_version'])} | Unknown age |
| Deprecated API Usage | {len(legacy_markers['deprecated_api'])} | Must update |

---

## 2. Dependency Map

### Internal Module Dependencies

```
"""

# Build simple ASCII dependency graph
for mod in sorted(internal_modules):
    deps = set()
    for pyf in py_files:
        if str(pyf).startswith(mod):
            for imported in imports.get(str(pyf), []):
                if imported in internal_modules and imported != mod:
                    deps.add(imported)
    if deps:
        report += f"{mod} -> {', '.join(sorted(deps))}\n"

report += """
```

### External Dependencies (Top 20)

| Package | Imported By | Risk |
|---------|-------------|------|
"""

# Count external imports
external_imports = defaultdict(int)
stdlib = {'os', 'sys', 'json', 're', 'math', 'datetime', 'typing', 'pathlib', 'asyncio', 'subprocess', 'hashlib', 'base64', 'time', 'random', 'string', 'itertools', 'collections', 'warnings', 'abc', 'copy', 'dataclasses', 'enum', 'html', 'http', 'urllib', 'xml', 'csv', 'io', 'tempfile', 'traceback', 'inspect', 'types', 'functools', 'decimal', 'fractions', 'numbers', 'statistics', 'pickle', 'shelve', 'dbm', 'sqlite3', 'socket', 'ssl', 'email', 'mailbox', 'calendar', 'locale', 'codecs', 'encodings', 'logging', 'unittest', 'doctest', 'pdb', 'profile', 'cProfile', 'timeit', 'trace', 'tracemalloc', 'gc', 'weakref', 'atexit', 'signal', 'threading', 'multiprocessing', 'concurrent', 'queue', 'contextvars', 'graphlib'}

for pyf, mods in imports.items():
    for mod in mods:
        if mod not in stdlib and mod not in internal_modules and not mod.startswith('__'):
            external_imports[mod] += 1

for mod, count in sorted(external_imports.items(), key=lambda x: -x[1])[:20]:
    risk = 'KNOWN' if mod in ['fastapi', 'redis', 'pydantic', 'httpx', 'pytest'] else 'UNKNOWN'
    report += f"| {mod} | {count} files | {risk} |\n"

report += f"""
---

## 3. Vulnerability Report

### Critical Issues (Must Fix Immediately)

| File | Line | Issue |
|------|------|-------|
"""

for issue in [i for i in issues if i['type'] == 'CRITICAL'][:30]:
    report += f"| {issue['file']} | {issue['line']} | {issue['msg']} |\n"

report += f"""
### High Issues (Fix This Week)

| File | Line | Issue |
|------|------|-------|
"""

for issue in [i for i in issues if i['type'] == 'HIGH'][:30]:
    report += f"| {issue['file']} | {issue['line']} | {issue['msg']} |\n"

report += f"""
---

## 4. Modernization Roadmap

### Phase 1: Foundation (Week 1) - CRITICAL

| Task | Effort | Impact | Files |
|------|--------|--------|-------|
| Replace all bare except with specific exceptions | 4h | CRITICAL | {issue_counts.get('bare_except', 0) + issue_counts.get('silent_pass', 0)} locations |
| Add logging to all silent passes | 2h | CRITICAL | {issue_counts.get('silent_pass', 0)} locations |
| Replace print with logger in core modules | 8h | HIGH | {issue_counts.get('print_statement', 0)} statements |
| Fix hardcoded paths | 4h | HIGH | {issue_counts.get('hardcoded_path', 0)} locations |

### Phase 2: Safety (Week 2) - HIGH

| Task | Effort | Impact |
|------|--------|--------|
| Add type hints to all public APIs | 16h | Medium |
| Write unit tests for Kelly, Matrix108, Predictor | 8h | High |
| Add input validation to all scrapers | 4h | High |
| Implement request rate limiting | 2h | Medium |

### Phase 3: Architecture (Week 3-4) - MEDIUM

| Task | Effort | Impact |
|------|--------|--------|
| Refactor sys.path.insert to proper package structure | 8h | High |
| Split monolithic scripts into testable modules | 16h | High |
| Add configuration management (dev/staging/prod) | 4h | Medium |
| Implement CI/CD pipeline | 8h | Medium |

### Phase 4: Optimization (Month 2) - LOW

| Task | Effort | Impact |
|------|--------|--------|
| Profile and optimize hot paths | 8h | Medium |
| Add caching layer for repeated calculations | 4h | Medium |
| Implement async batch processing | 8h | Medium |
| Database migration (if needed) | 16h | Low |

---

## 5. Inheritance Code Analysis

### Files with No Documentation

The following files have no module-level docstring:

"""

no_doc = []
for pyf in py_files:
    fp = BASE / pyf
    try:
        with open(fp, 'r', encoding='utf-8') as fh:
            content = fh.read()
        tree = ast.parse(content)
        has_docstring = False
        if isinstance(tree.body[0], ast.Expr) and isinstance(tree.body[0].value, ast.Constant) and isinstance(tree.body[0].value.value, str):
            has_docstring = True
        if not has_docstring:
            no_doc.append(str(pyf))
    except Exception as e:
        print(f"[AUDIT] Warning: Docstring check failed for {fp}: {e}")
        pass

for f in no_doc[:20]:
    report += f"- `{f}`\n"
if len(no_doc) > 20:
    report += f"- ... and {len(no_doc) - 20} more\n"

report += f"""
**Total undocumented files: {len(no_doc)} / {len(py_files)}**

---

## 6. Security Checklist

- [ ] Remove all hardcoded secrets (API keys, passwords)
- [ ] Add .env support for configuration
- [ ] Implement HTTPS-only for all external APIs
- [ ] Add request signing for webhooks
- [ ] Implement rate limiting on all endpoints
- [ ] Add audit logging for all financial operations
- [ ] Scan dependencies for known vulnerabilities (safety check)
- [ ] Add Content Security Policy headers

---

## 7. Priority Matrix

```
                    High Impact
                         ▲
    Bare except    ◆     │     ◆   Silent pass
    (system crash)       │          (money loss)
                         │
    No tests       ●     │     ●   Hardcoded paths
    (can't refactor)     │          (can't deploy)
                         │
    No types       ▲     │     ▲   No docs
    (dev slowdown)       │          (knowledge loss)
                         │
    ─────────────────────┼───────────────────────► Urgency
                         │
    Old API        □     │     □   Missing cache
    (future break)       │          (perf issue)
                         │
    Style issues   △     │     △   Logging format
    (cosmetic)           │          (minor)
                         │
                    Low Impact
```

---

*Audit Complete | Football Quant OS v4.2.1-naga | {datetime.now().strftime('%Y-%m-%d %H:%M')}*
"""

with open(OUTPUT, 'w', encoding='utf-8') as f:
    f.write(report)

print(f'\nReport saved: {OUTPUT}')
print(f'Issues: {len(issues)} total')
print(f'  CRITICAL: {sum(1 for i in issues if i["type"] == "CRITICAL")}')
print(f'  HIGH: {sum(1 for i in issues if i["type"] == "HIGH")}')
print(f'  MEDIUM: {sum(1 for i in issues if i["type"] == "MEDIUM")}')
