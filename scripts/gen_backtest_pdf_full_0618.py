#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive backtest report for 2026-06-18 World Cup matches
Includes: 1X2, Asian Handicap, HT/FT, Correct Score, OU, Execution count
"""
import json, sys, os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

sys.stdout.reconfigure(encoding='utf-8')

# Register font
try:
    pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
    font_name = 'SimHei'
except:
    font_name = 'Helvetica'

# Load data
data_path = r'D:\openclaw-workspace\football_quant_os\reports\backtest_2026-06-18.json'
with open(data_path, 'r', encoding='utf-8') as f:
    matches = json.load(f)

# Calculate stats
correct_1x2 = sum(1 for m in matches if m.get('correct_1x2'))
correct_ou = sum(1 for m in matches if m.get('correct_ou'))
total = len(matches)

# Output path
pdf_path = r'C:\Users\Administrator\Desktop\回测报告_2026世界杯_6月18日_完整版.pdf'
doc = SimpleDocTemplate(pdf_path, pagesize=A4,
                        rightMargin=15*mm, leftMargin=15*mm,
                        topMargin=15*mm, bottomMargin=15*mm)
styles = getSampleStyleSheet()

title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName=font_name, fontSize=20, textColor=colors.HexColor('#1a5276'), alignment=1, spaceAfter=15, leading=28)
h1_style = ParagraphStyle('H1', parent=styles['Heading2'], fontName=font_name, fontSize=14, textColor=colors.HexColor('#2874a6'), spaceAfter=10, spaceBefore=15, leading=20, backColor=colors.HexColor('#f2f6f9'), borderPadding=5)
h2_style = ParagraphStyle('H2', parent=styles['Heading3'], fontName=font_name, fontSize=12, textColor=colors.HexColor('#5d6d7e'), spaceAfter=8, spaceBefore=10, leading=16)
body_style = ParagraphStyle('Body', parent=styles['Normal'], fontName=font_name, fontSize=10, leading=15, spaceAfter=6)
small_style = ParagraphStyle('Small', parent=styles['Normal'], fontName=font_name, fontSize=9, leading=13, spaceAfter=4, textColor=colors.HexColor('#666'))
highlight = ParagraphStyle('Highlight', parent=body_style, fontSize=11, backColor=colors.HexColor('#eaf2f8'), borderPadding=8, spaceAfter=10, textColor=colors.HexColor('#1a5276'))

story = []

# ===== COVER =====
story.append(Spacer(1, 25*mm))
story.append(Paragraph("🏆 2026 世界杯 · 回测报告（完整版）", title_style))
story.append(Paragraph("<b>2026年6月18日 · K组+L组首轮</b>", ParagraphStyle('Subtitle', parent=body_style, fontSize=14, alignment=1, textColor=colors.HexColor('#5d6d7e'))))
story.append(Spacer(1, 8*mm))
story.append(Paragraph("Football Quant OS v5.2.0 | 六模型融合 · XGBoost Ensemble", ParagraphStyle('Version', parent=body_style, fontSize=10, alignment=1, textColor=colors.HexColor('#888'))))
story.append(Spacer(1, 15*mm))

# Summary box
summary_data = [
    ['📊 回测综合统计', '', '', ''],
    ['', '胜平负(1X2)', '大小球(OU)', '综合'],
    ['命中', f'{correct_1x2}/{total}', f'{correct_ou}/{total}', f'{correct_1x2+correct_ou}/{total*2}'],
    ['准确率', f'{correct_1x2/total*100:.1f}%', f'{correct_ou/total*100:.1f}%', f'{(correct_1x2+correct_ou)/(total*2)*100:.1f}%'],
]
sum_tbl = Table(summary_data, colWidths=[3*cm, 4*cm, 4*cm, 4*cm])
sum_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a5276')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('SPAN', (0,0), (-1,0)),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('FONTNAME', (0,0), (-1,-1), font_name),
    ('FONTSIZE', (0,0), (-1,0), 14),
    ('FONTSIZE', (0,1), (-1,-1), 11),
    ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#2874a6')),
    ('TEXTCOLOR', (0,1), (-1,1), colors.white),
    ('BACKGROUND', (0,2), (-1,-1), colors.HexColor('#f2f6f9')),
    ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#ddd')),
    ('TOPPADDING', (0,0), (-1,-1), 10),
    ('BOTTOMPADDING', (0,0), (-1,-1), 10),
]))
story.append(sum_tbl)
story.append(Spacer(1, 10*mm))
story.append(Paragraph(f"🎯 <b>1X2 准确率 {correct_1x2/total*100:.0f}%</b> | 📈 <b>OU 准确率 {correct_ou/total*100:.0f}%</b> | 进行数: <b>{total}场</b>", highlight))
story.append(PageBreak())

# ===== MARKET OVERVIEW =====
story.append(Paragraph("📋 盘口覆盖总览", h1_style))
story.append(Spacer(1, 5*mm))

market_data = [
    ['盘口类型', '模型覆盖', '回测命中', '说明'],
    ['胜平负(1X2)', '✅ 已覆盖', f'{correct_1x2}/{total}', '主胜/平局/客胜 三方向概率'],
    ['让球胜平负', '⚠️ 部分覆盖', '—', '模型输出隐含概率，需结合盘口让球线换算'],
    ['半全场(HT/FT)', '❌ 未覆盖', '—', '需半场比分数据，当前系统未采集'],
    ['比分(Correct Score)', '⚠️ 部分覆盖', '—', 'Poisson模型输出比分分布，但未做精准预测'],
    ['大小球(OU)', '✅ 已覆盖', f'{correct_ou}/{total}', 'λ期望值 + 盘口线对比'],
]
market_tbl = Table(market_data, colWidths=[3.5*cm, 3*cm, 3*cm, 6*cm])
market_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a5276')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,-1), font_name),
    ('FONTSIZE', (0,0), (-1,0), 11),
    ('FONTSIZE', (0,1), (-1,-1), 10),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')),
    ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#e8f8e8')),
    ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#fff8e8')),
    ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#ffe8e8')),
    ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#fff8e8')),
    ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#e8f8e8')),
    ('TOPPADDING', (0,0), (-1,-1), 8),
    ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ('LEFTPADDING', (0,0), (-1,-1), 6),
    ('RIGHTPADDING', (0,0), (-1,-1), 6),
]))
story.append(market_tbl)
story.append(Spacer(1, 8*mm))
story.append(Paragraph("<i>注：让球胜平负与半全场需额外数据支持，当前回测仅覆盖 1X2 与 OU。下表展示可用数据的完整回测结果。</i>", small_style))
story.append(PageBreak())

# ===== MATCH-BY-MATCH =====
story.append(Paragraph("📌 逐场回测详情", h1_style))
story.append(Spacer(1, 5*mm))

for i, m in enumerate(matches, 1):
    pred = m.get('prediction', {})
    probs = pred.get('probabilities_1x2', {})
    
    # Match header
    story.append(Paragraph(f"{i}. {m['home_cn']} vs {m['away_cn']} ({m['group']}组)", h2_style))
    
    # ===== 1X2 =====
    c1x2 = '✅' if m.get('correct_1x2') else '❌'
    story.append(Paragraph(f"<b>【胜平负】</b> 实际: {m['actual']} → {m['actual_1x2']} | 预测: {pred.get('predicted_1x2','N/A')} {c1x2}", body_style))
    
    x2_data = [
        ['', '主胜', '平局', '客胜'],
        ['模型概率', f"{probs.get('home',0):.1%}", f"{probs.get('draw',0):.1%}", f"{probs.get('away',0):.1%}"],
        ['隐含概率', f"{1/m['odds_home']:.1%}", f"{1/m['odds_draw']:.1%}", f"{1/m['odds_away']:.1%}"],
    ]
    x2_tbl = Table(x2_data, colWidths=[3*cm, 4*cm, 4*cm, 4*cm])
    x2_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f0f8')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1a5276')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('FONTSIZE', (0,0), (-1,0), 10),
        ('FONTSIZE', (0,1), (-1,-1), 9),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f2f6f9')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#f8f8f8')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(x2_tbl)
    story.append(Spacer(1, 2*mm))
    
    # ===== 让球胜平负 (placeholder) =====
    story.append(Paragraph(f"<b>【让球胜平负】</b> 模型未直接输出 — 需根据让球盘口线换算。参考赔率: 主{m['odds_home']}/平{m['odds_draw']}/客{m['odds_away']}", small_style))
    story.append(Spacer(1, 2*mm))
    
    # ===== 半全场 (placeholder) =====
    story.append(Paragraph(f"<b>【半全场】</b> 系统未采集半场比分数据 — 暂不支持回测", small_style))
    story.append(Spacer(1, 2*mm))
    
    # ===== 比分 (Poisson distribution) =====
    story.append(Paragraph(f"<b>【比分】</b> Poisson λ={pred.get('lambda','N/A')} | 最可能比分需查分布表", small_style))
    story.append(Spacer(1, 2*mm))
    
    # ===== 大小球 =====
    cou = '✅' if m.get('correct_ou') else '❌'
    story.append(Paragraph(f"<b>【大小球】</b> 盘口: {m['ou_line']} | 实际: {m['actual_ou']} ({m['total_goals']}球) | 预测: {pred.get('predicted_ou','N/A')} {cou}", body_style))
    
    ou_data = [
        ['', '大球', '小球'],
        ['模型概率', f"{pred.get('ou_recommendation','N/A')}", f"—"],
        ['赔率', str(m['odds_over']), str(m['odds_under'])],
    ]
    ou_tbl = Table(ou_data, colWidths=[3*cm, 6*cm, 6*cm])
    ou_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f0f8')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1a5276')),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,-1), font_name),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(ou_tbl)
    story.append(Spacer(1, 2*mm))
    
    # Meta info
    upset = pred.get('upset_score', 0)
    story.append(Paragraph(f"冷门评分: {upset} | 置信度: {pred.get('confidence',0):.3f} | 进行数: 1", small_style))
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#eee')))
    story.append(Spacer(1, 3*mm))

story.append(PageBreak())

# ===== ANALYSIS =====
story.append(Paragraph("🔍 关键发现与优化建议", h1_style))
story.append(Spacer(1, 5*mm))

analysis_lines = [
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
    "<b>5. 盘口覆盖建议</b>",
    "· <b>让球胜平负</b>：需采集让球盘口数据，结合模型概率进行换算覆盖<br/>"
    "· <b>半全场</b>：需接入半场比分数据源，建立HT/FT独立模型<br/>"
    "· <b>比分</b>：Poisson已输出比分分布，需增加精确比分预测模块<br/>"
    "· <b>弱队OU</b>：首战弱队进球预期需更保守校准，建议增加'新军零封因子'",
]

for line in analysis_lines:
    if line:
        story.append(Paragraph(line, body_style))
    else:
        story.append(Spacer(1, 3*mm))

story.append(Spacer(1, 10*mm))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#ddd')))
story.append(Spacer(1, 5*mm))
story.append(Paragraph(f"<i>报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')} | Football Quant OS v5.2.0</i>", ParagraphStyle('Footer', parent=small_style, alignment=2, textColor=colors.HexColor('#999'))))

# Build
doc.build(story)
print(f"PDF报告已生成: {pdf_path}")
print(f"文件大小: {os.path.getsize(pdf_path):,} bytes ({os.path.getsize(pdf_path)/1024:.1f} KB)")
