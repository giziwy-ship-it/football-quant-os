#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate PDF backtest report for 2026-06-18 World Cup matches
"""
import json
import sys
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics import renderPDF
import os

sys.stdout.reconfigure(encoding='utf-8')

# Register Chinese fonts
try:
    pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
    pdfmetrics.registerFont(TTFont('SimSun', 'C:/Windows/Fonts/simsun.ttc', subfontIndex=0))
    font_name = 'SimHei'
except:
    font_name = 'Helvetica'

# Load backtest data
data_path = r'D:\openclaw-workspace\football_quant_os\reports\backtest_2026-06-18.json'
with open(data_path, 'r', encoding='utf-8') as f:
    matches = json.load(f)

# Calculate stats
correct_1x2 = sum(1 for m in matches if m.get('correct_1x2'))
correct_ou = sum(1 for m in matches if m.get('correct_ou'))
total = len(matches)

# PDF output
pdf_path = r'C:\Users\Administrator\Desktop\回测报告_2026世界杯_6月18日.pdf'
doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                        rightMargin=15*mm, leftMargin=15*mm,
                        topMargin=15*mm, bottomMargin=15*mm)

styles = getSampleStyleSheet()

# Custom styles
title_style = ParagraphStyle(
    'TitleStyle', parent=styles['Heading1'],
    fontName=font_name, fontSize=22, textColor=colors.HexColor('#1a5276'),
    spaceAfter=20, alignment=1, leading=30
)

heading_style = ParagraphStyle(
    'HeadingStyle', parent=styles['Heading2'],
    fontName=font_name, fontSize=14, textColor=colors.HexColor('#2874a6'),
    spaceAfter=10, spaceBefore=15, leading=20,
    borderWidth=0, borderColor=colors.HexColor('#2874a6'),
    borderPadding=5, leftIndent=0, backColor=colors.HexColor('#f2f6f9')
)

subheading_style = ParagraphStyle(
    'SubHeading', parent=styles['Heading3'],
    fontName=font_name, fontSize=12, textColor=colors.HexColor('#5d6d7e'),
    spaceAfter=8, spaceBefore=10, leading=16
)

body_style = ParagraphStyle(
    'BodyStyle', parent=styles['Normal'],
    fontName=font_name, fontSize=10, leading=15,
    spaceAfter=6
)

small_style = ParagraphStyle(
    'SmallStyle', parent=styles['Normal'],
    fontName=font_name, fontSize=9, leading=13,
    spaceAfter=4
)

highlight_style = ParagraphStyle(
    'Highlight', parent=styles['Normal'],
    fontName=font_name, fontSize=11, leading=16,
    textColor=colors.HexColor('#1a5276'), backColor=colors.HexColor('#eaf2f8'),
    borderPadding=8, spaceAfter=10
)

story = []

# ===== COVER =====
story.append(Spacer(1, 30*mm))
story.append(Paragraph("🏆 2026 世界杯回测报告", title_style))
story.append(Spacer(1, 5*mm))
story.append(Paragraph(f"<b>2026年6月18日 · K组+L组首轮</b>", ParagraphStyle('Subtitle', parent=body_style, fontSize=14, alignment=1, textColor=colors.HexColor('#5d6d7e'))))
story.append(Spacer(1, 10*mm))
story.append(Paragraph(f"<b>Football Quant OS v5.2.0</b><br/>六模型融合 · XGBoost Ensemble", ParagraphStyle('Version', parent=body_style, fontSize=10, alignment=1, textColor=colors.HexColor('#888'))))
story.append(Spacer(1, 20*mm))

# Stats summary box
stats_data = [
    ['📊 回测统计', '', '', ''],
    ['', '1X2 方向', 'OU 大小球', '综合'],
    ['命中', f'{correct_1x2}/{total}', f'{correct_ou}/{total}', f'{correct_1x2+correct_ou}/{total*2}'],
    ['准确率', f'{correct_1x2/total*100:.1f}%', f'{correct_ou/total*100:.1f}%', f'{(correct_1x2+correct_ou)/(total*2)*100:.1f}%'],
]
stats_table = Table(stats_data, colWidths=[3*cm, 4*cm, 4*cm, 4*cm])
stats_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 0), (-1, 0), font_name),
    ('FONTSIZE', (0, 0), (-1, 0), 14),
    ('SPAN', (0, 0), (-1, 0)),
    ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#2874a6')),
    ('TEXTCOLOR', (0, 1), (-1, 1), colors.white),
    ('FONTNAME', (0, 1), (-1, -1), font_name),
    ('FONTSIZE', (0, 1), (-1, -1), 11),
    ('BACKGROUND', (0, 2), (-1, -1), colors.HexColor('#f2f6f9')),
    ('TEXTCOLOR', (0, 2), (-1, -1), colors.HexColor('#333')),
    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#ddd')),
    ('TOPPADDING', (0, 0), (-1, -1), 10),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
]))
story.append(stats_table)
story.append(Spacer(1, 15*mm))

# Accuracy highlight
story.append(Paragraph(f"🎯 <b>1X2 准确率 {correct_1x2/total*100:.0f}%</b> — 四场只错一场（葡萄牙冷门平局）<br/>📈 <b>OU 准确率 {correct_ou/total*100:.0f}%</b> — 大小球整体稳定", highlight_style))
story.append(PageBreak())

# ===== MATCH DETAILS =====
story.append(Paragraph("📋 逐场回测详情", heading_style))
story.append(Spacer(1, 5*mm))

for i, m in enumerate(matches, 1):
    pred = m.get('prediction', {})
    probs = pred.get('probabilities_1x2', {})
    
    # Match header
    match_title = f"{i}. {m['home_cn']} vs {m['away_cn']} ({m['group']}组)"
    story.append(Paragraph(match_title, subheading_style))
    
    # Result line
    c1x2 = '✅' if m.get('correct_1x2') else '❌'
    cou = '✅' if m.get('correct_ou') else '❌'
    result_line = f"实际比分 <b>{m['actual']}</b> | 1X2: {m['actual_1x2']} {c1x2} | OU: {m['actual_ou']} {cou}"
    story.append(Paragraph(result_line, body_style))
    
    # Prediction table
    pred_data = [
        ['', '模型概率', '预测', '实际', '结果'],
        ['主胜', f"{probs.get('home', 0):.1%}", pred.get('predicted_1x2', 'N/A'), m['actual_1x2'], c1x2],
        ['OU', f"λ={pred.get('lambda', 'N/A')}", pred.get('predicted_ou', 'N/A'), m['actual_ou'], cou],
    ]
    pred_table = Table(pred_data, colWidths=[3*cm, 4*cm, 4*cm, 3*cm, 2*cm])
    pred_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e8f0f8')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a5276')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('FONTNAME', (0, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#ddd')),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor('#f8fff8') if m.get('correct_1x2') else colors.HexColor('#fff8f8')),
        ('BACKGROUND', (0, 2), (-1, 2), colors.HexColor('#f8fff8') if m.get('correct_ou') else colors.HexColor('#fff8f8')),
    ]))
    story.append(pred_table)
    
    # Additional info
    upset = pred.get('upset_score', 0)
    info = f"冷门评分: {upset} | 置信度: {pred.get('confidence', 0):.3f}"
    story.append(Paragraph(info, small_style))
    story.append(Spacer(1, 8*mm))

story.append(PageBreak())

# ===== ANALYSIS =====
story.append(Paragraph("🔍 关键发现", heading_style))
story.append(Spacer(1, 5*mm))

analysis = [
    "<b>1. 最大冷门：葡萄牙 1-1 刚果(金)</b>",
    "模型预测主胜 37.3%，平局概率 35.8% — 已经非常接近，但模型仍偏向主队。这是本届世界杯首场真正冷门，说明对于时隔52年回归的非洲球队，模型低估了他们的韧性。",
    "",
    "<b>2. 英格兰 4-2 克罗地亚 — 完美命中</b>",
    "1X2主胜 + OU Over 双中。模型λ=2.60，实际6球大比分。两队放开对攻，超出预期。",
    "",
    "<b>3. 加纳 1-0 巴拿马 — OU偏差</b>",
    "模型预测Over(λ=2.60)但实际仅1球。弱队之间交手，防守强度高于预期。",
    "",
    "<b>4. 乌兹别克斯坦 1-3 哥伦比亚 — 完美命中</b>",
    "客胜 + Over 双中。模型对强弱分明的比赛判断准确，哥伦比亚南美技术优势发挥明显。",
    "",
    "<b>5. 优化建议</b>",
    "· 弱队首战进球预期需更保守校准<br/>"
    "· 新军球队（时隔多年回归）需增加韧性因子<br/>"
    "· 非洲球队在世界杯的爆冷概率高于模型预期",
]

for line in analysis:
    if line:
        story.append(Paragraph(line, body_style))
    else:
        story.append(Spacer(1, 3*mm))

story.append(Spacer(1, 10*mm))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#ddd')))
story.append(Spacer(1, 5*mm))
story.append(Paragraph(f"<i>报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} | Football Quant OS v5.2.0</i>", ParagraphStyle('Footer', parent=small_style, alignment=2, textColor=colors.HexColor('#999'))))

# Build PDF
doc.build(story)
print(f"PDF报告已生成: {pdf_path}")
print(f"文件大小: {os.path.getsize(pdf_path):,} bytes ({os.path.getsize(pdf_path)/1024:.1f} KB)")
