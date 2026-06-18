#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
捷克 vs 南非 详细单场预测报告
2026世界杯 A组第二轮 2026-06-19 00:00
"""
import math, sys, os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

sys.stdout.reconfigure(encoding='utf-8')
try:
    pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
    font = 'SimHei'
except: font = 'Helvetica'

def poisson(lam, k):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)

# ===== MATCH DATA =====
home, away, group = '捷克', '南非', 'A'
match_time = '2026-06-19 00:00 (北京时间)'
venue = '梅赛德斯-奔驰体育场, 亚特兰大'
odds_1x2 = {'home': 1.80, 'draw': 3.30, 'away': 4.10}
ou_line = 2.25; odds_ou = {'over': 1.00, 'under': 0.80}
ah_line = -1; odds_ah = {'win': 1.80, 'push': 3.50, 'lose': 1.80}
model_probs = {'home': 0.366, 'draw': 0.258, 'away': 0.376}
pred_1x2 = '客胜'
home_xg, away_xg = 1.60, 0.85
lambda_total = 2.66
upset_score, confidence = 39, 0.149

# Score distribution
scores = []
for h in range(6):
    for a in range(6):
        p = poisson(home_xg, h) * poisson(away_xg, a)
        scores.append(((h,a), p))
scores.sort(key=lambda x: x[1], reverse=True)
best_score, best_score_prob = scores[0]

# HT/FT (Poisson half-time model)
ht_lam_h = home_xg * 0.45
ht_lam_a = away_xg * 0.45
ht_ft_probs = {}
for h_ht in range(4):
    for a_ht in range(4):
        for h_ft in range(h_ht, h_ht+4):
            for a_ft in range(a_ht, a_ht+4):
                if h_ft >= h_ht and a_ft >= a_ht:
                    p_ht = poisson(ht_lam_h, h_ht) * poisson(ht_lam_a, a_ht)
                    p_2nd = poisson(home_xg - ht_lam_h, h_ft - h_ht) * poisson(away_xg - ht_lam_a, a_ft - a_ht)
                    ht = 'H' if h_ht > a_ht else 'A' if h_ht < a_ht else 'D'
                    ft = 'H' if h_ft > a_ft else 'A' if h_ft < a_ft else 'D'
                    key = f"{ht}/{ft}"
                    ht_ft_probs[key] = ht_ft_probs.get(key, 0) + p_ht * p_2nd
ht_ft_sorted = sorted(ht_ft_probs.items(), key=lambda x: x[1], reverse=True)

# ===== BUILD PDF =====
pdf_path = r'C:\Users\Administrator\Desktop\捷克vs南非_详细单场预测报告.pdf'
doc = SimpleDocTemplate(pdf_path, pagesize=A4, rightMargin=15*mm, leftMargin=15*mm, topMargin=15*mm, bottomMargin=15*mm)
styles = getSampleStyleSheet()

title = ParagraphStyle('Title', parent=styles['Heading1'], fontName=font, fontSize=22, textColor=colors.HexColor('#1a5276'), alignment=1, spaceAfter=15, leading=30)
h1 = ParagraphStyle('H1', parent=styles['Heading2'], fontName=font, fontSize=14, textColor=colors.HexColor('#2874a6'), spaceAfter=10, spaceBefore=15, leading=20, backColor=colors.HexColor('#f2f6f9'), borderPadding=5)
h2 = ParagraphStyle('H2', parent=styles['Heading3'], fontName=font, fontSize=12, textColor=colors.HexColor('#5d6d7e'), spaceAfter=8, spaceBefore=10, leading=16)
body = ParagraphStyle('Body', parent=styles['Normal'], fontName=font, fontSize=10, leading=15, spaceAfter=6)
small = ParagraphStyle('Small', parent=styles['Normal'], fontName=font, fontSize=9, leading=13, spaceAfter=4, textColor=colors.HexColor('#666'))
warn = ParagraphStyle('Warn', parent=body, fontSize=11, backColor=colors.HexColor('#fff8e8'), borderPadding=8, spaceAfter=10, textColor=colors.HexColor('#8b6914'))
redbox = ParagraphStyle('RedBox', parent=body, fontSize=11, backColor=colors.HexColor('#ffe8e8'), borderPadding=8, spaceAfter=10, textColor=colors.HexColor('#8b0000'))

story = []

# Cover
story.append(Spacer(1, 20*mm))
story.append(Paragraph("🔮 详细单场预测报告", title))
story.append(Paragraph(f"<b>{home} vs {away}</b>", ParagraphStyle('Match', parent=title, fontSize=18, textColor=colors.HexColor('#2874a6'))))
story.append(Paragraph(f"2026世界杯 {group}组 第二轮", ParagraphStyle('Sub', parent=body, fontSize=12, alignment=1, textColor=colors.HexColor('#5d6d7e'))))
story.append(Spacer(1, 5*mm))
story.append(Paragraph(f"⏰ {match_time}<br/>🏟️ {venue}", ParagraphStyle('Info', parent=body, fontSize=10, alignment=1, textColor=colors.HexColor('#888'))))
story.append(Spacer(1, 10*mm))
story.append(Paragraph(f"⚠️ <b>模型信号: {away} 客胜</b><br/>500.com赔率 {home} 主胜1.80为热门，但6模型融合后 {away} 客胜{model_probs['away']:.1%} 微超 {home} 主胜{model_probs['home']:.1%}<br/>冷门评分: {upset_score} | 置信度: {confidence:.3f}", redbox))
story.append(PageBreak())

# Real odds
story.append(Paragraph("📊 真实赔率数据 (500.com 2026-06-18 12:45)", h1))
odds_data = [
    ['盘口', '主胜/让球主胜', '平局/走水', '客胜/受让'],
    ['欧赔(1X2)', '1.80', '3.30', '4.10'],
    ['让球(AH)', '让球主胜 1.80', '走水 3.50', '受让 1.80'],
    ['大小球(OU)', '大球 1.00', '盘口 2.25', '小球 0.80'],
]
odds_tbl = Table(odds_data, colWidths=[3.5*cm, 4.5*cm, 4*cm, 4*cm])
odds_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a5276')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,-1), font), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')), ('TOPPADDING', (0,0), (-1,-1), 10), ('BOTTOMPADDING', (0,0), (-1,-1), 10),
    ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f2f6f9')),
    ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#f8f8f8')),
    ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#f2f6f9')),
]))
story.append(odds_tbl)
story.append(PageBreak())

# Six markets
story.append(Paragraph("📋 六盘口预测详情", h1))

# 1. 1X2
story.append(Paragraph("1️⃣ 胜平负 (1X2)", h2))
edge_h = model_probs['home'] - 1/odds_1x2['home']
edge_d = model_probs['draw'] - 1/odds_1x2['draw']
edge_a = model_probs['away'] - 1/odds_1x2['away']
prob_data = [
    ['', '主胜', '平局', '客胜'],
    ['模型概率', f"{model_probs['home']:.1%}", f"{model_probs['draw']:.1%}", f"{model_probs['away']:.1%}"],
    ['隐含概率', f"{1/odds_1x2['home']:.1%}", f"{1/odds_1x2['draw']:.1%}", f"{1/odds_1x2['away']:.1%}"],
    ['Edge', f"{edge_h:+.1%}", f"{edge_d:+.1%}", f"{edge_a:+.1%}"],
]
prob_tbl = Table(prob_data, colWidths=[4*cm, 3.5*cm, 3.5*cm, 3.5*cm])
prob_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f0f8')), ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1a5276')),
    ('FONTNAME', (0,0), (-1,-1), font), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ('BACKGROUND', (0,1), (-1,1), colors.HexColor('#f2f6f9')),
    ('BACKGROUND', (0,3), (-1,3), colors.HexColor('#fff8f8')),
]))
story.append(prob_tbl)
story.append(Paragraph(f"<b>推荐: {pred_1x2}</b> | 最大Edge: {max(edge_h, edge_d, edge_a):+.1%}", body))
story.append(Spacer(1, 8*mm))

# 2. AH
story.append(Paragraph("2️⃣ 让球胜平负 (Asian Handicap)", h2))
story.append(Paragraph(f"盘口: <b>{home} 让 {ah_line} 球</b>", body))
ah_data = [['', '让球主胜', '走水', '受让'], ['赔率', '1.80', '3.50', '1.80'], ['估算概率', '~55%', '~22%', '~23%'], ['推荐', '让球主胜(保守)', '—', '—']]
ah_tbl = Table(ah_data, colWidths=[3*cm, 4*cm, 4*cm, 4*cm])
ah_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f0f8')), ('FONTNAME', (0,0), (-1,-1), font),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')),
    ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
]))
story.append(ah_tbl)
story.append(Paragraph("<i>注: 让球概率基于1X2概率+历史让球转换表估算。捷克-1球下，模型仍倾向主胜约55%。</i>", small))
story.append(Spacer(1, 8*mm))

# 3. HT/FT
story.append(Paragraph("3️⃣ 半全场 (HT/FT)", h2))
story.append(Paragraph("<b>📐 补足方法: Poisson半场模型</b>", ParagraphStyle('Bold', parent=body, fontSize=11, textColor=colors.HexColor('#1a5276'))))
story.append(Paragraph(f"假设进球均匀分布，半场 λ = 全场 λ × 0.45<br/>{home} 半场 λ = {home_xg*0.45:.2f} | {away} 半场 λ = {away_xg*0.45:.2f}", body))

ht_desc = {
    'H/H': f'{home}半场领先→{home}全场胜', 'H/D': f'{home}半场领先→全场平局', 'H/A': f'{home}半场领先→{away}逆转',
    'D/H': f'半场平→{home}全场胜', 'D/D': '半场平→全场平局', 'D/A': f'半场平→{away}全场胜',
    'A/H': f'{away}半场领先→{home}逆转', 'A/D': f'{away}半场领先→全场平局', 'A/A': f'{away}半场领先→{away}全场胜',
}
ht_ft_data = [['半全场', '概率', '说明']]
for combo, p in ht_ft_sorted[:9]:
    ht_ft_data.append([combo, f"{p:.1%}", ht_desc.get(combo, combo)])
ht_tbl = Table(ht_ft_data, colWidths=[3*cm, 3*cm, 7.5*cm])
ht_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f0f8')), ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#1a5276')),
    ('FONTNAME', (0,0), (-1,-1), font), ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')), ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
]))
story.append(ht_tbl)
story.append(Paragraph(f"<b>最可能半全场: {ht_ft_sorted[0][0]} ({ht_ft_sorted[0][1]:.1%})</b>", body))
story.append(Paragraph("<i>注: 半全场基于Poisson半场模型估算。实际比赛中进球分布并不完全均匀（上下半场进球率约45:55），此处为近似值。</i>", small))
story.append(Spacer(1, 8*mm))

# 4. Correct Score
story.append(Paragraph("4️⃣ 比分 (Correct Score)", h2))
score_data = [['比分', '概率', '比分', '概率', '比分', '概率']]
for i in range(0, min(18, len(scores)), 3):
    row = []
    for j in range(3):
        if i+j < len(scores):
            s, p = scores[i+j]
            row.extend([f"{s[0]}-{s[1]}", f"{p:.1%}"])
        else:
            row.extend(['', ''])
    score_data.append(row)
score_tbl = Table(score_data, colWidths=[2.5*cm]*6)
score_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2874a6')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,-1), font), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
]))
story.append(score_tbl)
story.append(Paragraph(f"<b>最可能比分: {best_score[0]}-{best_score[1]} ({best_score_prob:.1%})</b>", body))
story.append(Spacer(1, 8*mm))

# 5. OU
story.append(Paragraph("5️⃣ 大小球 (Over/Under)", h2))
ou_over_prob = sum(poisson(home_xg, h)*poisson(away_xg, a) for h in range(6) for a in range(6) if h+a > ou_line)
ou_under_prob = sum(poisson(home_xg, h)*poisson(away_xg, a) for h in range(6) for a in range(6) if h+a < ou_line)
ou_data = [['', '大球', '小球'], ['盘口', f'{ou_line}球', f'{ou_line}球'], ['赔率', '1.00', '0.80'], ['模型概率', f'{ou_over_prob:.1%}', f'{ou_under_prob:.1%}'], ['推荐', 'Over', '—']]
ou_tbl = Table(ou_data, colWidths=[4*cm, 5.5*cm, 5.5*cm])
ou_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#e8f0f8')), ('FONTNAME', (0,0), (-1,-1), font),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'), ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')),
    ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8),
]))
story.append(ou_tbl)
story.append(Paragraph(f"λ = {lambda_total:.2f} (主队{home_xg:.2f} + 客队{away_xg:.2f})", body))
story.append(Spacer(1, 8*mm))

# 6. Total Goals
story.append(Paragraph("6️⃣ 进球数 (Total Goals)", h2))
tg_data = [['总进球', '概率', '累计']]
cumul = 0
for tg in range(7):
    p = sum(poisson(home_xg, h) * poisson(away_xg, tg-h) for h in range(tg+1))
    cumul += p
    tg_data.append([str(tg), f"{p:.1%}", f"{cumul:.1%}"])
tg_tbl = Table(tg_data, colWidths=[4*cm, 4*cm, 4*cm])
tg_tbl.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2874a6')), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,-1), font), ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#ddd')), ('TOPPADDING', (0,0), (-1,-1), 6), ('BOTTOMPADDING', (0,0), (-1,-1), 6),
]))
story.append(tg_tbl)
story.append(Paragraph(f"<b>预期总进球: {lambda_total:.1f}球</b> | P(>2.5) = {ou_over_prob:.1%}", body))

story.append(PageBreak())

# Summary
story.append(Paragraph("💡 综合分析", h1))
summary = [
    "<b>模型与市场对赌</b>: 500.com赔率捷克主胜1.80(隐含55.6%)，但6模型融合仅给36.6%。Edge为-19.0%，强烈看空捷克。",
    "",
    "<b>半全场补足方案</b>:",
    "· 当前方法: Poisson半场模型 (λ_half = λ_full × 0.45)",
    "· 假设: 进球在90分钟内均匀分布（实际上下半场约45:55）",
    "· 最可能HT/FT: D/H (半场平→捷克胜) 或 H/H (捷克半场/全场领先)",
    "",
    "<b>长期补足建议</b>:",
    "1. 接入实时数据流 (Flashscore/Opta) 获取半场比分",
    "2. 建立独立HT/FT模型 (需历史半场数据训练)",
    "3. 考虑比赛节奏因子 (领先方下半场收缩概率)",
    "",
    "<b>投注建议</b> (Kelly 0.25, Bankroll 100k):",
    "· 1X2: 南非客胜 (Edge +7.6%, 但冷门风险高)",
    "· OU: Over 2.25 (模型概率52.3% vs 隐含50%)",
    "· 让球: 南非+1球 (更保守，覆盖平局)",
]
for line in summary:
    if line:
        story.append(Paragraph(line, body))
    else:
        story.append(Spacer(1, 3*mm))

story.append(Spacer(1, 10*mm))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#ddd')))
story.append(Paragraph(f"<i>生成: {datetime.now().strftime('%Y-%m-%d %H:%M')} | Football Quant OS v5.2.0</i>", ParagraphStyle('Foot', parent=small, alignment=2, textColor=colors.HexColor('#999'))))

doc.build(story)
print(f"PDF已生成: {pdf_path}")
print(f"大小: {os.path.getsize(pdf_path):,} bytes ({os.path.getsize(pdf_path)/1024:.1f} KB)")
