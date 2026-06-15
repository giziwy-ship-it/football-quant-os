import markdown
import subprocess
import os

# Read markdown file
md_path = r'D:\openclaw-workspace\football_quant_os\reports\MEX_RSA_FINAL_COMPLETE_REPORT.md'
with open(md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert to HTML body
html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

# CSS styling
html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>墨西哥 vs 南非 | 2026 世界杯揭幕战 - 完整预测报告</title>
<style>
@page { size: A4; margin: 15mm; }
body {
    font-family: "Microsoft YaHei", "SimHei", "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #333;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}
h1 {
    font-size: 18pt;
    color: #1a5276;
    border-bottom: 3px solid #1a5276;
    padding-bottom: 8px;
    margin-top: 30px;
}
h2 {
    font-size: 14pt;
    color: #2874a6;
    border-bottom: 2px solid #2874a6;
    padding-bottom: 5px;
    margin-top: 25px;
}
h3 {
    font-size: 12pt;
    color: #5d6d7e;
    margin-top: 20px;
    border-left: 4px solid #5d6d7e;
    padding-left: 10px;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 9pt;
}
th, td {
    border: 1px solid #bbb;
    padding: 6px 8px;
    text-align: left;
}
th {
    background-color: #1a5276;
    color: white;
    font-weight: bold;
}
tr:nth-child(even) {
    background-color: #f2f6f9;
}
code {
    background: #f4f4f4;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 9pt;
}
pre {
    background: #f4f4f4;
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
}
ul, ol {
    margin: 10px 0;
    padding-left: 25px;
}
li {
    margin: 4px 0;
}
strong {
    color: #1a5276;
}
blockquote {
    border-left: 4px solid #1a5276;
    margin: 10px 0;
    padding: 10px 15px;
    background: #f2f6f9;
    color: #555;
}
hr {
    border: 0;
    border-top: 1px solid #ddd;
    margin: 20px 0;
}
</style>
</head>
<body>
''' + html_body + '''
</body>
</html>'''

# Save HTML file
html_path = r'D:\openclaw-workspace\football_quant_os\reports\MEX_RSA_FINAL_COMPLETE_REPORT.html'
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f'HTML saved: {html_path}')

# Convert to PDF using Chrome headless
pdf_path = r'C:\Users\Administrator\Desktop\墨西哥vs南非_2026世界杯揭幕战_完整预测报告.pdf'
chrome_path = r'C:\Program Files\Google\Chrome\Application\chrome.exe'

cmd = [
    chrome_path,
    '--headless',
    '--disable-gpu',
    '--no-sandbox',
    '--print-to-pdf=' + pdf_path,
    '--run-all-compositor-stages-before-draw',
    '--virtual-time-budget=10000',
    'file:///' + html_path.replace('\\', '/')
]

result = subprocess.run(cmd, capture_output=True, text=True)
if result.returncode == 0 or os.path.exists(pdf_path):
    size = os.path.getsize(pdf_path)
    print(f'PDF generated: {pdf_path}')
    print(f'File size: {size:,} bytes ({size/1024:.1f} KB)')
else:
    print('Chrome headless failed:', result.stderr)
    print('stdout:', result.stdout)
