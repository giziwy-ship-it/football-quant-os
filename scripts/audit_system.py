#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS v4.2.1-naga 技术审计
Project Auditor Report
"""

import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

base = r'D:\openclaw-workspace\football_quant_os'

print('=' * 75)
print('FOOTBALL QUANT OS v4.2.1-naga - TECHNICAL AUDIT')
print('=' * 75)
print()

# 1. Project Scale
print('[1. PROJECT SCALE]')
total_files = 0
py_files = 0
py_lines = 0

for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache']]
    for f in files:
        total_files += 1
        if f.endswith('.py'):
            py_files += 1
            try:
                with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                    py_lines += len(fh.readlines())
            except Exception as e:
                from core.logger import get_logger
                logger = get_logger("naga_quant.fixer")
                logger.error(f"Silent error suppressed: {e}", exc_info=True)

print(f'  Total files: {total_files}')
print(f'  Python files: {py_files}')
print(f'  Python lines: {py_lines:,}')
print()

# 2. Dependencies
print('[2. DEPENDENCIES]')
req_file = os.path.join(base, 'requirements.txt')
if os.path.exists(req_file):
    with open(req_file, 'r') as f:
        deps = [l.strip() for l in f if l.strip() and not l.startswith('#')]
    print(f'  Declared deps: {len(deps)}')
    for d in deps[:15]:
        print(f'    - {d}')
else:
    print('  MISSING: requirements.txt')
print()

# 3. Key files
print('[3. KEY FILES CHECK]')
key_files = [
    'app/tasks.py', 'app/main.py', 'app/api.py',
    'agents/multi_market_predictor.py', 'agents/coach_factor.py',
    'agents/odds_pricing.py', 'agents/treasury.py', 'agents/intelligence.py',
    'agents/trading.py', 'agents/risk_guardian.py',
    'core/config.py', 'core/scheduler.py', 'core/redis_cache.py',
    'models/matrix_108.py', 'models/kelly.py',
]
for kf in key_files:
    fp = os.path.join(base, kf)
    exists = 'OK' if os.path.exists(fp) else 'MISSING'
    print(f'  [{exists}] {kf}')
print()

# 4. Hardcoded paths
print('[4. HARDCODED PATHS]')
hardcoded = []
for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__']]
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(root, f)
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                    if 'sys.path.insert' in content:
                        hardcoded.append((os.path.relpath(fp, base), 'sys.path.insert'))
                    if 'C:\\Windows\\Fonts' in content:
                        hardcoded.append((os.path.relpath(fp, base), 'Windows font path'))
                    if 'D:\\\\openclaw-workspace' in content:
                        hardcoded.append((os.path.relpath(fp, base), 'Absolute workspace path'))
            except Exception as e:
                from core.logger import get_logger
                logger = get_logger("naga_quant.fixer")
                logger.error(f"Silent error suppressed: {e}", exc_info=True)

if hardcoded:
    print(f'  Found {len(hardcoded)} hardcoded paths:')
    for file, desc in hardcoded[:10]:
        print(f'    - {file}: {desc}')
else:
    print('  No hardcoded paths found')
print()

# 5. Error handling
print('[5. ERROR HANDLING]')
try_count = 0
bare_count = 0
pass_count = 0

for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(root, f)
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                    try_count += content.count('try:')
                    bare_count += len(re.findall(r'except\s*:', content))
                    pass_count += len(re.findall(r'except[^:]*:\s*\n\s*pass', content))
            except Exception as e:
                from core.logger import get_logger
                logger = get_logger("naga_quant.fixer")
                logger.error(f"Silent error suppressed: {e}", exc_info=True)

print(f'  try blocks: {try_count}')
print(f'  bare except: {bare_count} (DANGER: catches all)')
print(f'  silent pass: {pass_count} (CRITICAL: swallows errors)')
print()

# 6. Async code
print('[6. ASYNC CODE]')
async_defs = 0
awaits = 0
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(root, f)
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                    async_defs += content.count('async def')
                    awaits += content.count('await ')
            except Exception as e:
                from core.logger import get_logger
                logger = get_logger("naga_quant.fixer")
                logger.error(f"Silent error suppressed: {e}", exc_info=True)

print(f'  async def: {async_defs}')
print(f'  await: {awaits}')
print(f'  ratio: {awaits/max(async_defs,1):.1f}')
print()

# 7. Trash/temp files
print('[7. TEMP FILES]')
trash_dirs = []
for d in os.listdir(base):
    if '_trash_' in d or '_backup_' in d:
        trash_dirs.append(d)
if trash_dirs:
    print(f'  Found {len(trash_dirs)} trash dirs:')
    for td in trash_dirs:
        path = os.path.join(base, td)
        if os.path.isdir(path):
            count = len(os.listdir(path))
            print(f'    - {td}: {count} files')
else:
    print('  No trash dirs')
print()

# 8. Config files
print('[8. CONFIG FILES]')
config_dir = os.path.join(base, 'config')
if os.path.exists(config_dir):
    for f in os.listdir(config_dir):
        print(f'  - {f}')
else:
    print('  MISSING: config/')
print()

# 9. Check for print statements (should be logging)
print('[9. PRINT vs LOGGING]')
print_count = 0
logging_count = 0
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            fp = os.path.join(root, f)
            try:
                with open(fp, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                    print_count += content.count('print(')
                    logging_count += content.count('logging.')
            except Exception as e:
                from core.logger import get_logger
                logger = get_logger("naga_quant.fixer")
                logger.error(f"Silent error suppressed: {e}", exc_info=True)

print(f'  print(): {print_count}')
print(f'  logging: {logging_count}')
print(f'  ratio: {print_count/max(logging_count,1):.1f} (should be < 1.0)')
print()

# 10. Test files
print('[10. TEST COVERAGE]')
test_dir = os.path.join(base, 'tests')
if os.path.exists(test_dir):
    test_files = [f for f in os.listdir(test_dir) if f.endswith('.py')]
    print(f'  Test files: {len(test_files)}')
else:
    print('  MISSING: tests/')
print()

print('=' * 75)
print('AUDIT COMPLETE')
print('=' * 75)
