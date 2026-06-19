import markdown
import subprocess
import os

# Read markdown file
md_path = r'D:\openclaw-workspace\football_quant_os\reports\MEX_KOR_2026WC_V3_FINAL.md'
with open(md_path, 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert to HTML body
html_body = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])

# CSS styling with Bloomberg + Goldman + McKinsey + Google hybrid style
html_template = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>墨西哥 vs 韩国 | 2026 FIFA World Cup 小组赛A组第2轮 - 量化预测报告（积分榜最终修正版）</title>
<style>
@page { size: A4; margin: 12mm; }
body {
    font-family: "Microsoft YaHei", "SimHei", "Helvetica Neue", Arial, sans-serif;
    font-size: 9.5pt;
    line-height: 1.55;
    color: #222;
    max-width: 920px;
    margin: 0 auto;
    padding: 15px;
}
h1 {
    font-size: 20pt;
    color: #0d47a1;
    border-bottom: 3px solid #0d47a1;
    padding-bottom: 10px;
    margin-top: 25px;
    font-weight: 700;
}
h2 {
    font-size: 14pt;
    color: #1565c0;
    border-bottom: 2px solid #1565c0;
    padding-bottom: 6px;
    margin-top: 22px;
    font-weight: 600;
}
h3 {
    font-size: 11pt;
    color: #37474f;
    margin-top: 18px;
    border-left: 4px solid #37474f;
    padding-left: 10px;
    font-weight: 600;
}
table {
    width: 100%;
    border-collapse: collapse;
    margin: 12px 0;
    font-size: 8.5pt;
}
th, td {
    border: 1px solid #bbb;
    padding: 5px 7px;
    text-align: left;
}
th {
    background-color: #0d47a1;
    color: white;
    font-weight: bold;
}
tr:nth-child(even) {
    background-color: #e3f2fd;
}
code {
    background: #f5f5f5;
    padding: 2px 5px;
    border-radius: 3px;
    font-size: 8.5pt;
}
pre {
    background: #f5f5f5;
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
    font-size: 8pt;
}
ul, ol {
    margin: 8px 0;
    padding-left: 22px;
}
li {
    margin: 3px 0;
}
strong {
    color: #0d47a1;
}
blockquote {
    border-left: 4px solid #0d47a1;
    margin: 10px 0;
    padding: 10px 15px;
    background: #e3f2fd;
    color: #333;
    font-size: 9.5pt;
}
hr {
    border: 0;
    border-top: 1px solid #ccc;
    margin: 18px 0;
}
.header-banner {
    background: linear-gradient(135deg, #0d47a1 0%, #1565c0 100%);
    color: white;
    padding: 15px 20px;
    border-radius: 5px;
    margin-bottom: 20px;
}
.header-banner h1 {
    color: white;
    border-bottom: none;
    margin: 0;
    padding: 0;
    font-size: 18pt;
}
</style>
</head>
<body>
<div class="header-banner">
<h1>🇲🇽 墨西哥 vs 韩国 🇰🇷 | 2026 FIFA World Cup 小组赛A组第2轮</h1>
<p style="margin:5px 0 0 0; font-size:10pt;">Naga Quant System v5.2.2-Final | 积分榜最终修正版 | Bloomberg + Goldman + McKinsey Hybrid Style</p>
</div>
''' + html_body + '''
</body>
</html>'''

# Save HTML file
html_path = r'D:\openclaw-workspace\football_quant_os\reports\MEX_KOR_2026WC_V3_FINAL.html'
with open(html_path, 'w', encoding='utf-8') as f:
    f.write(html_template)

print(f'HTML saved: {html_path}')

# Convert to PDF using Chrome headless
pdf_path = r'C:\Users\Administrator\Desktop\墨西哥vs韩国_小组赛第2轮_积分榜最终修正版.pdf'
chrome_paths = [
    r'C:\Program Files\Google\Chrome\Application\chrome.exe',
    r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
    r'C:\Users\Administrator\AppData\Local\Google\Chrome\Application\chrome.exe',
]

chrome_found = None
for cp in chrome_paths:
    if os.path.exists(cp):
        chrome_found = cp
        break

if chrome_found:
    cmd = [
        chrome_found,
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
else:
    print('Chrome not found. Trying Edge...')
    edge_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    if os.path.exists(edge_path):
        cmd = [
            edge_path,
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
            print(f'PDF generated (Edge): {pdf_path}')
            print(f'File size: {size:,} bytes ({size/1024:.1f} KB)')
        else:
            print('Edge headless failed:', result.stderr)
    else:
        print('No browser found for PDF generation. HTML report saved.')
