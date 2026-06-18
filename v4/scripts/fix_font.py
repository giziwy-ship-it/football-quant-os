import re

path = r'D:\openclaw-workspace\football_quant_os\v4\scripts\generate_report_cn.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern 1: standard tables
old1 = "('FONTSIZE', (0, 1), (-1, -1), 9),\n        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),"
new1 = "('FONTSIZE', (0, 1), (-1, -1), 9),\n        ('FONTNAME', (0, 1), (-1, -1), chinese_font),\n        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),"
content = content.replace(old1, new1)

# Pattern 2: weights_table with extra ALIGN LEFT
old2 = "('FONTSIZE', (0, 1), (-1, -1), 9),\n        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),\n        ('ALIGN', (2, 1), (2, -1), 'LEFT'),"
new2 = "('FONTSIZE', (0, 1), (-1, -1), 9),\n        ('FONTNAME', (0, 1), (-1, -1), chinese_font),\n        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),\n        ('ALIGN', (2, 1), (2, -1), 'LEFT'),"
content = content.replace(old2, new2)

with open(path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed all tables')
