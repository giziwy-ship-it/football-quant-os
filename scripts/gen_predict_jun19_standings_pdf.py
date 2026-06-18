#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Generate PDF with GROUP STANDINGS comparison for 2026-06-19 predictions
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import sys, os

sys.stdout.reconfigure(encoding='utf-8')
try:
    pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
    font = 'SimHei'
except: font = 'Helvetica'

# Match data with comparison
matches = [
    {
        'home': '捷克', 'away': '南非', 'group': 'A', 'time': '00:00',
        'h_pts': 0, 'a_pts': 0, 'h_gd': -1, 'a_gd': -2,
        'no_pts': {'h': 36.6, 'd': 25.8, 'a': 37.6, 'pred': '客胜'},
        'with_pts': {'h': 34.5, 'd': 25.8, 'a': 39.7, 'pred': '客胜'},
        'change': '客队+2.1% (两队0分，必须赢球意增强)',
        'odds': '1.80/3.30/4.10', 'ou': '2.25线 Over',
    },
    {
        'home': '加拿大', 'away': '卡塔尔', 'group': 'B', 'time': '03:00',
        'h_pts': 1, 'a_pts': 1, 'h_gd': 0, 'a_gd': 0,
        'no_pts': {'h': 41.6, 'd': 26.8, 'a': 31.6, 'pred': '主胜'},
        'with_pts': {'h': 41.6, 'd': 26.8, 'a': 31.6, 'pred': '主胜'},
        'change': '无变化 (两队同积1分，战意均衡)',
        'odds': '1.75/3.50/5.00', 'ou': '2.5线 Over',
    },
    {
        'home': '瑞士', 'away': '波黑', 'group': 'B', 'time': '12:00',
        'h_pts': 1, 'a_pts': 1, 'h_gd': 0, 'a_gd': 0,
        'no_pts': {'h': 44.5, 'd': 27.7, 'a': 27.8, 'pred': '主胜'},
        'with_pts': {'h': 44.5, 'd': 27.7, 'a': 27.8, 'pred': '主胜'},
        'change': '无变化 (两队同积1分，战意均衡)',
        'odds': '1.65/3.60/6.00', 'ou': '2.5线 Over',
    },
    {
        'home': '墨西哥', 'away': '韩国', 'group': 'A', 'time': '12:00',
        'h_pts': 3, 'a_pts': 3, 'h_gd': 2, 'a_gd': 1,
        'no_pts': {'h': 39.7, 'd': 26.5, 'a': 33.8, 'pred': '主胜'},
        'with_pts': {'h': 38.7, 'd': 26.5, 'a': 34.8, 'pred': '主胜'},
        'change': '主胜-1.0% (两队同积3分，战意相对放松)',
        'odds': '1.85/3.40/4.20', 'ou': '2.5线 Over',
    },
]

pdf_path = r'C:\Users\Administrator\Desktop\预测报告_2026世界杯_6月19日_含积分对比.pdf'
doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
styles = getSampleStyleSheet()

title = ParagraphStyle('Title', parent=styles['Heading1'], fontName=font, fontSize=20, textColor=colors.HexColor('#1a5276'), alignment=1, spaceAfter=15, leading=28)
h1 = ParagraphStyle('H1', parent=styles['Heading2'], fontName=font, fontSize=14, textColor=colors.HexColor('#2874a6'), spaceAfter=10, spaceBefore=15, leading=20, backColor=colors.HexColor('#f2f6f9'), borderPadding=5)
h2 = ParagraphStyle('H2', parent=styles['Heading3'], fontName=font, fontSize=12, textColor=colors.HexColor('#5d6d7e'), spaceAfter=8, spaceBefore=10, leading=16)
body = ParagraphStyle('Body', parent=styles['Normal'], fontName=font, fontSize=10, leading=15, spaceAfter=6)
small = ParagraphStyle('Small', parent=styles['Normal'], fontName=font, fontSize=9, leading=13, spaceAfter=4, textColor=colors.HexColor('#666'))
warn = ParagraphStyle('Warn', parent=body, fontSize=11, backColor=colors.HexColor('#fff8e8'), borderPadding=8, spaceAfter=10, textColor=colors.HexColor('#8b6914'))

story = []

# Cover
story.append(Spacer(1, 20*mm))
story.append(Paragraph("🔮 2026 世界杯 · 预测报告", title))
story.append(Paragraph("<b>6月19日 · A组+B组 第二轮</b>", ParagraphStyle('Sub', parent=body, fontSize=14, alignment=1, textColor=colors.HexColor('#5d6d7e'))))
story.append(Spacer(1, 5*mm))
story.append(Paragraph("📊 <b>积分因素已纳入</b> | 对比: 无积分 vs 第一轮后真实积分", ParagraphStyle('Src', parent=body, fontSize=11, alignment=1, textColor=colors.HexColor('#2874a6'), backColor=colors.HexColor('#eaf2f8'), borderPadding=6)))
story.append(Spacer(1, 5*mm))
story.append(Paragraph("数据来源: 500.com + 模型v5.2.0 group_stage_context", ParagraphStyle('Ver', parent=body, fontSize=9, alignment=1, textColor=colors.HexColor('#888'))))
story.append(Spacer(1, 10*mm))
story.append(Paragraph("⚠️ <b>重要发现</b>: 本报告已考虑第一轮赛后的积分/净胜球/战意因素，与之前的'无积分'版本有差异。", warn))
story.append(PageBreak())

# Standings
story.append(Paragraph("📊 第一轮后积分榜", h1))
story.append(Spacer(1, 5*mm))

standings_data = [
    ['A组', '球队', '赛', '胜', '平', '负', '进', '失', '净', '分'],
    ['', '墨西哥', '1', '1', '0', '0', '2', '0', '+2', '3'],
    ['', '韩国', '1', '1', '0', '0', '2', '1', '+1', '3'],
    ['', '捷克', '1', '0', '0', '1', '1', '2', '-1', '0'],
    ['', '南非', '1', '0', '0', '1', '0', '2', '-2', '0'],
    ['B组', '球队', '赛', '胜', '平', '负', '进', '失', '净', '分'],
    ['', '瑞士', '1', '0', '1', '0', '1', '1', '0', '1'],
    ['', '加拿大', '1', '0', '1', '0', '1', '1', '0', '1'],
    ['', '波黑', '1', '0', '1', '0', '1', '1', '0', '1'],
    ['', '卡塔尔', '1', '0', '1', '0', '1', '1', '0', '1'],
]
std_tbl = Table(standings_data, colWidths=[1.5*cm, 3*cm]+[1.3*cm]*8)
std_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a5276')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('BACKGROUND', (0,5), (-1,5), colors.HexColor('#1a5276')), ('TEXTCOLOR', (0,5), (-1,5), colors.white),
    ('FONTNAME', (0,0), (-1,-1), font), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')),
    ('BACKGROUND', (0,1), (-1,4), colors.HexColor('#f2f6f9')),
    ('BACKGROUND', (0,6), (-1,9), colors.HexColor('#f8f8f8')),
    ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
]))
story.append(std_tbl)
story.append(PageBreak())

# Predictions with comparison
story.append(Paragraph("📋 预测对比: 无积分 vs 有积分", h1))
story.append(Spacer(1, 5*mm))

for m in matches:
    story.append(Paragraph(f"{m['home']} vs {m['away']} ({m['group']}组 · {m['time']})", h2))
    
    # Comparison table
    cmp_data = [
        ['', '无积分(默认)', '有积分(第一轮后)', '变化'],
        ['主胜', f"{m['no_pts']['h']:.1f}%", f"{m['with_pts']['h']:.1f}%", f"{m['with_pts']['h']-m['no_pts']['h']:+.1f}%"],
        ['平局', f"{m['no_pts']['d']:.1f}%", f"{m['with_pts']['d']:.1f}%", f"{m['with_pts']['d']-m['no_pts']['d']:+.1f}%"],
        ['客胜', f"{m['no_pts']['a']:.1f}%", f"{m['with_pts']['a']:.1f}%", f"{m['with_pts']['a']-m['no_pts']['a']:+.1f}%"],
        ['预测方向', m['no_pts']['pred'], m['with_pts']['pred'], '相同' if m['no_pts']['pred']==m['with_pts']['pred'] else '变化!'],
    ]
    cmp_tbl = Table(cmp_data, colWidths=[3*cm, 4*cm, 4*cm, 4*cm])
    cmp_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f0f8')), ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1a5276')),
        ('FONTNAME', (0,0), (-1,-1), font), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')),
        ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f2f6f9')),
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#f8f8f8')),
        ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#f2f6f9')),
        ('BACKGROUND', (0,4), (-1,4), colors.HexColor('#e8f8e8') if m['no_pts']['pred']==m['with_pts']['pred'] else colors.HexColor('#ffe8e8')),
        ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(cmp_tbl)
    
    story.append(Paragraph(f"<b>积分背景</b>: {m['home']} {m['h_pts']}分(净胜{m['h_gd']:+.0f}) | {m['away']} {m['a_pts']}分(净胜{m['a_gd']:+.0f})", body))
    story.append(Paragraph(f"<b>积分影响</b>: {m['change']}", body))
    story.append(Paragraph(f"<b>赔率参考</b>: {m['odds']} | OU: {m['ou']}", small))
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#eee')))
    story.append(Spacer(1, 3*mm))

story.append(PageBreak())

# Analysis
story.append(Paragraph("🔍 积分因素分析", h1))
story.append(Spacer(1, 5*mm))

analysis = [
    "<b>1. 捷克 vs 南非 — 积分因素影响最大</b>",
    "两队都是0分，必须赢球才能保留出线希望。模型v5.1的group_stage_context模块识别到这一点，将客队（南非）概率从37.6%上调至39.7%（+2.1%）。",
    "逻辑: 低排名球队在'必须赢'的压力下，往往爆发出更强的战斗意志，而强队（捷克）可能因急躁而失误。",
    "",
    "<b>2. 墨西哥 vs 韩国 — 积分因素轻微削弱主队</b>",
    "两队都是3分，相对放松。墨西哥主胜概率从39.7%降至38.7%（-1.0%）。",
    "逻辑: 领先球队不需要拼命，比赛节奏会放缓，强队优势被稀释。",
    "",
    "<b>3. B组两场 — 积分因素无影响</b>",
    "四队全积1分，形势胶着但均衡。模型认为战意对双方对称，概率无调整。",
    "",
    "<b>4. 半全场如何纳入积分因素</b>",
    "当前Poisson半场模型未考虑积分。建议方案:",
    "· 0分球队: 上半场进球λ +10%（抢开局）",
    "· 3分球队: 上半场进球λ -5%（保守开局）",
    "· 领先方半场后: 下半场λ -15%（收缩防守）",
    "· 落后方半场后: 下半场λ +15%（拼命进攻）",
    "这需要独立的HT/FT模型，当前系统暂不支持。",
]

for line in analysis:
    if line:
        story.append(Paragraph(line, body))
    else:
        story.append(Spacer(1, 3*mm))

story.append(Spacer(1, 10*mm))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#ddd')))
story.append(Paragraph(f"<i>生成: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Football Quant OS v5.2.0 | group_stage_context v1.0</i>", ParagraphStyle('Foot', parent=small, alignment=2, textColor=colors.HexColor('#999'))))

doc.build(story)
print(f"PDF已生成: {pdf_path}")
print(f"大小: {os.path.getsize(pdf_path):,} bytes ({os.path.getsize(pdf_path)/1024:.1f} KB)")
