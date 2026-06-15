#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Exception Handler Fixer - Football Quant OS
Replaces dangerous bare except and silent pass patterns
"""

import sys, os, re
sys.stdout.reconfigure(encoding='utf-8')

base = r'D:\openclaw-workspace\football_quant_os'

# Patterns to find
BARE_EXCEPT = re.compile(r'except\s*:\s*\n')
SILENT_PASS = re.compile(r'except[^:]*:\s*\n\s*pass')

fixes = []

for root, dirs, files in os.walk(base):
    dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', '.pytest_cache', '_trash_20260613']]
    for f in files:
        if not f.endswith('.py'):
            continue
        fp = os.path.join(root, f)
        try:
            with open(fp, 'r', encoding='utf-8') as fh:
                content = fh.read()
            
            original = content
            modified = False
            
            # Fix 1: except: → except Exception:
            if BARE_EXCEPT.search(content):
                content = BARE_EXCEPT.sub('except Exception:\n', content)
                modified = True
            
            # Fix 2: except: pass → except Exception: logger.error(...)
            # This is more complex, need line-by-line
            lines = content.split('\n')
            new_lines = []
            i = 0
            while i < len(lines):
                line = lines[i]
                # Check if this line is "except: pass" or similar
                if re.match(r'\s*except\s*:\s*$', line) and i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if re.match(r'\s*pass\s*$', next_line):
                        indent = len(line) - len(line.lstrip())
                        spaces = ' ' * indent
                        new_lines.append(f'{spaces}except Exception as e:')
                        new_lines.append(f'{spaces}    from core.logger import get_logger')
                        new_lines.append(f'{spaces}    logger = get_logger("naga_quant.fixer")')
                        new_lines.append(f'{spaces}    logger.error(f"Silent error suppressed: {{e}}", exc_info=True)')
                        i += 2
                        modified = True
                        continue
                
                # Check for "except Exception: pass" (already has Exception but still silent)
                if re.match(r'\s*except\s+Exception\s*:\s*$', line) and i + 1 < len(lines):
                    next_line = lines[i + 1]
                    if re.match(r'\s*pass\s*$', next_line):
                        indent = len(line) - len(line.lstrip())
                        spaces = ' ' * indent
                        new_lines.append(f'{spaces}except Exception as e:')
                        new_lines.append(f'{spaces}    from core.logger import get_logger')
                        new_lines.append(f'{spaces}    logger = get_logger("naga_quant.fixer")')
                        new_lines.append(f'{spaces}    logger.error(f"Silent error suppressed: {{e}}", exc_info=True)')
                        i += 2
                        modified = True
                        continue
                
                new_lines.append(line)
                i += 1
            
            if modified:
                content = '\n'.join(new_lines)
                with open(fp, 'w', encoding='utf-8') as fh:
                    fh.write(content)
                fixes.append(os.path.relpath(fp, base))
                
        except Exception as e:
            print(f'Error processing {fp}: {e}')

print(f'Fixed {len(fixes)} files:')
for f in fixes[:20]:
    print(f'  - {f}')
if len(fixes) > 20:
    print(f'  ... and {len(fixes) - 20} more')
