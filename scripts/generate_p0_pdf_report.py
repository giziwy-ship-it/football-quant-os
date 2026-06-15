#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0修正六维预测报告 PDF生成器 - 加拿大vs波黑 + 美国vs巴拉圭"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os

# 注册中文字体
font_paths = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\msyhbd.ttc",
]

font_registered = False
for fp in font_paths:
    if os.path.exists(fp):
        try:
            if "msyhbd" in fp:
                pdfmetrics.registerFont(TTFont('YaHeiBold', fp, subfontIndex=0))
            elif "msyh" in fp:
                pdfmetrics.registerFont(TTFont('YaHei', fp, subfontIndex=0))
            elif "simhei" in fp:
                pdfmetrics.registerFont(TTFont('YaHei', fp))
                pdfmetrics.registerFont(TTFont('YaHeiBold', fp))
            font_registered = True
        except Exception:
            continue

if not font_registered:
    font_name = 'Helvetica'
    font_bold = 'Helvetica-Bold'
else:
    font_name = 'YaHei'
    font_bold = 'YaHeiBold'

output_path = os.path.join(os.path.expanduser("~"), "Desktop", "P0修正预测_加拿大波黑_美国巴拉圭_六维报告.pdf")

doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    rightMargin=2*cm,
    leftMargin=2*cm,
    topMargin=2*cm,
    bottomMargin=2*cm,
)

styles = getSampleStyleSheet()

style_title = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontName=font_bold, fontSize=22, textColor=colors.HexColor('#C00000'), spaceAfter=12, alignment=TA_CENTER)
style_subtitle = ParagraphStyle('CustomSubtitle', parent=styles['Heading2'], fontName=font_name, fontSize=14, textColor=colors.HexColor('#404040'), spaceAfter=20, alignment=TA_CENTER)
style_brand = ParagraphStyle('Brand', parent=styles['Normal'], fontName=font_bold, fontSize=16, textColor=colors.HexColor('#1F4E79'), spaceAfter=6, alignment=TA_CENTER)
style_brand2 = ParagraphStyle('Brand2', parent=styles['Normal'], fontName=font_name, fontSize=12, textColor=colors.HexColor('#2E75B6'), spaceAfter=20, alignment=TA_CENTER)
style_heading2 = ParagraphStyle('CustomH2', parent=styles['Heading2'], fontName=font_bold, fontSize=14, textColor=colors.HexColor('#1F4E79'), spaceAfter=10, spaceBefore=16)
style_heading3 = ParagraphStyle('CustomH3', parent=styles['Heading3'], fontName=font_bold, fontSize=12, textColor=colors.HexColor('#C00000'), spaceAfter=8, spaceBefore=10)
style_heading3_blue = ParagraphStyle('CustomH3Blue', parent=styles['Heading3'], fontName=font_bold, fontSize=12, textColor=colors.HexColor('#2E75B6'), spaceAfter=8, spaceBefore=10)
style_body = ParagraphStyle('CustomBody', parent=styles['Normal'], fontName=font_name, fontSize=10.5, textColor=colors.HexColor('#333333'), spaceAfter=6, alignment=TA_JUSTIFY, leading=16)
style_body_bold = ParagraphStyle('CustomBodyBold', parent=styles['Normal'], fontName=font_bold, fontSize=11, textColor=colors.HexColor('#C00000'), spaceAfter=6, leading=16)
style_body_green = ParagraphStyle('CustomBodyGreen', parent=styles['Normal'], fontName=font_bold, fontSize=11, textColor=colors.HexColor('#2E7D32'), spaceAfter=6, leading=16)
style_note = ParagraphStyle('CustomNote', parent=styles['Normal'], fontName=font_name, fontSize=9, textColor=colors.HexColor('#666666'), spaceAfter=4, leading=14)
style_highlight = ParagraphStyle('Highlight', parent=styles['Normal'], fontName=font_bold, fontSize=10.5, textColor=colors.HexColor('#1F4E79'), spaceAfter=6, leading=16, backColor=colors.HexColor('#E3F2FD'))

story = []

# 封面
story.append(Spacer(1, 30))
story.append(Paragraph("Football Quant OS", style_brand))
story.append(Paragraph("P0 Engine 修正六维预测报告", style_brand2))
story.append(Spacer(1, 20))
story.append(Paragraph("加拿大 vs 波黑 & 美国 vs 巴拉圭", style_title))
story.append(Paragraph("2026世界杯小组赛 | P0定价引擎修正版", style_subtitle))
story.append(Paragraph("2026-06-12 | 小娜迦 Naga Core", style_subtitle))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# P0引擎说明
story.append(Paragraph("一、P0 修正引擎说明", style_heading2))
story.append(Paragraph("本次报告使用 P0 层 Agent 进行修正：", style_body))
story.append(Paragraph("• OddsPricingAgent v1.1 - 赔率定价中心（公平赔率 + 盘口生成）", style_body))
story.append(Paragraph("• TreasuryAgent v1.1 - 资金管理中心（Kelly 注码 + 风险控制）", style_body))
story.append(Spacer(1, 6))
story.append(Paragraph("修正逻辑：", style_heading3_blue))
story.append(Paragraph("1. 原始预测概率 → 2. 公平赔率定价 → 3. 市场偏差识别 → 4. Kelly 最优注码", style_body))
story.append(Spacer(1, 6))
story.append(Paragraph("核心洞察：市场赔率融入公众偏见 + 流动性折扣，P0 引擎还原真实概率并给出最优注码", style_highlight))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# ==================== MATCH 1: Canada vs Bosnia ====================
story.append(Paragraph("二、比赛一：加拿大 vs 波黑", style_heading2))
story.append(Paragraph("WC2026-B1-007 | 2026-06-12 15:00 ET | Toronto BMO Field", style_subtitle))
story.append(Spacer(1, 6))

story.append(Paragraph("【基础数据】", style_heading3_blue))
story.append(Paragraph("• 用户预测：加拿大 72% | 平局 15% | 波黑 13%", style_body))
story.append(Paragraph("• AI 预测：Canada to win - tight win by a single goal", style_body))
story.append(Paragraph("• 市场赔率：加拿大 1.85 | 平局 3.45 | 波黑 4.60", style_body))
story.append(Spacer(1, 6))

story.append(Paragraph("【P0 定价修正】", style_heading3_blue))
story.append(Paragraph("• 公平赔率（无利润）：加拿大 @1.32 | 平局 @6.87 | 波黑 @7.93", style_body))
story.append(Paragraph("• 市场隐含概率：加拿大 54%（@1.85）", style_body))
story.append(Paragraph("• P0 修正概率：加拿大 72%（@1.39）", style_body_bold))
story.append(Paragraph("• 价值发现：市场低估加拿大 +33% edge", style_body_green))
story.append(Spacer(1, 6))

story.append(Paragraph("【六维预测】", style_heading3))

# 1X2
story.append(Paragraph("维度 1 - 1X2 胜平负", style_heading3_blue))
can_1x2 = [
    ['项目', '数值'],
    ['推荐', '加拿大 WIN'],
    ['公平赔率', '@1.32'],
    ['市场赔率', '@1.85'],
    ['P0 修正赔率', '@1.39'],
    ['市场偏差', '+33% edge'],
    ['信心', '★★★★☆'],
]
t1 = Table(can_1x2, colWidths=[4*cm, 6*cm])
t1.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), font_bold),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 1), (-1, -1), font_name),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
]))
story.append(t1)
story.append(Spacer(1, 6))

# Asian Handicap
story.append(Paragraph("维度 2 - 让球胜平负", style_heading3_blue))
story.append(Paragraph("• 盘口：加拿大 -0.75", style_body))
story.append(Paragraph("• 上盘水位：@0.80 | 下盘水位：@0.95", style_body))
story.append(Paragraph("★ 推荐：加拿大 -0.75 @0.80", style_body_bold))
story.append(Spacer(1, 6))

# Half/Full
story.append(Paragraph("维度 3 - 半全场", style_heading3_blue))
story.append(Paragraph("• 主/主：35%", style_body))
story.append(Paragraph("• 平/主：25%", style_body))
story.append(Paragraph("• 平/平：20%", style_body))
story.append(Paragraph("★ 推荐：主/主 (35%)", style_body_bold))
story.append(Spacer(1, 6))

# Score
story.append(Paragraph("维度 4 - 比分", style_heading3_blue))
can_score = [
    ['排名', '比分', '概率'],
    ['1', '1-0', '22%'],
    ['2', '2-0', '18%'],
    ['3', '1-1', '12%'],
    ['4', '2-1', '10%'],
]
t2 = Table(can_score, colWidths=[2*cm, 3*cm, 3*cm])
t2.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C00000')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), font_bold),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 1), (-1, -1), font_name),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
]))
story.append(t2)
story.append(Paragraph("★ 推荐：1-0, 2-0", style_body_bold))
story.append(Spacer(1, 6))

# Goals
story.append(Paragraph("维度 5 - 总进球数", style_heading3_blue))
story.append(Paragraph("• 0球: 5% | 1球: 20% | 2球: 35% | 3球: 25% | 4球: 10% | 5+: 5%", style_body))
story.append(Paragraph("★ 推荐：2球最可能", style_body_bold))
story.append(Spacer(1, 6))

# Over/Under
story.append(Paragraph("维度 6 - 大小球", style_heading3_blue))
story.append(Paragraph("• 盘口：2.5球 | 大 @0.95 | 小 @0.63", style_body))
story.append(Paragraph("★ 推荐：小 2.5 @0.63", style_body_bold))
story.append(Spacer(1, 6))

# Kelly
story.append(Paragraph("【Kelly 注码】", style_heading3_blue))
story.append(Paragraph("• 原始 Kelly：39.06%", style_body))
story.append(Paragraph("• 封顶后注码：500 EUR（5% bankroll）", style_body_bold))
story.append(Paragraph("• 期望值：+33.1%", style_body_green))
story.append(Spacer(1, 6))
story.append(Paragraph("推荐投注：加拿大 WIN @1.85（市场）500 EUR", style_highlight))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(PageBreak())

# ==================== MATCH 2: USA vs Paraguay ====================
story.append(Paragraph("三、比赛二：美国 vs 巴拉圭", style_heading2))
story.append(Paragraph("WC2026-D1-019 | 2026-06-12 18:00 PT | Los Angeles SoFi Stadium", style_subtitle))
story.append(Spacer(1, 6))

story.append(Paragraph("【基础数据】", style_heading3_blue))
story.append(Paragraph("• 用户预测：美国 90% | 平局 9% | 巴拉圭 1%", style_body))
story.append(Paragraph("• AI 预测：USA narrow 1-0 or 2-0, home crowd + Europe-based stars", style_body))
story.append(Paragraph("• 市场赔率：美国 2.07 | 平局 3.30 | 巴拉圭 3.87", style_body))
story.append(Spacer(1, 6))

story.append(Paragraph("【P0 定价修正】", style_heading3_blue))
story.append(Paragraph("• 公平赔率（无利润）：美国 @1.07 | 平局 @12.48 | 巴拉圭 @112.36", style_body))
story.append(Paragraph("• 市场隐含概率：美国 48%（@2.07）", style_body))
story.append(Paragraph("• P0 修正概率：美国 90%（@1.15）", style_body_bold))
story.append(Paragraph("• 价值发现：市场大幅低估美国 +88% edge", style_body_green))
story.append(Spacer(1, 6))

story.append(Paragraph("【六维预测】", style_heading3))

# 1X2
story.append(Paragraph("维度 1 - 1X2 胜平负", style_heading3_blue))
usa_1x2 = [
    ['项目', '数值'],
    ['推荐', '美国 WIN'],
    ['公平赔率', '@1.07'],
    ['市场赔率', '@2.07'],
    ['P0 修正赔率', '@1.15'],
    ['市场偏差', '+88% edge'],
    ['信心', '★★★★☆'],
]
t3 = Table(usa_1x2, colWidths=[4*cm, 6*cm])
t3.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), font_bold),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 1), (-1, -1), font_name),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
]))
story.append(t3)
story.append(Spacer(1, 6))

# Asian Handicap
story.append(Paragraph("维度 2 - 让球胜平负", style_heading3_blue))
story.append(Paragraph("• 盘口：美国 -1.0", style_body))
story.append(Paragraph("• 上盘水位：@0.80 | 下盘水位：@0.95", style_body))
story.append(Paragraph("★ 推荐：美国 -1.0 @0.80", style_body_bold))
story.append(Spacer(1, 6))

# Half/Full
story.append(Paragraph("维度 3 - 半全场", style_heading3_blue))
story.append(Paragraph("• 主/主：40%", style_body))
story.append(Paragraph("• 平/主：30%", style_body))
story.append(Paragraph("• 平/平：15%", style_body))
story.append(Paragraph("★ 推荐：主/主 (40%)", style_body_bold))
story.append(Spacer(1, 6))

# Score
story.append(Paragraph("维度 4 - 比分", style_heading3_blue))
usa_score = [
    ['排名', '比分', '概率'],
    ['1', '1-0', '25%'],
    ['2', '2-0', '20%'],
    ['3', '1-1', '12%'],
    ['4', '2-1', '10%'],
]
t4 = Table(usa_score, colWidths=[2*cm, 3*cm, 3*cm])
t4.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C00000')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), font_bold),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 1), (-1, -1), font_name),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
]))
story.append(t4)
story.append(Paragraph("★ 推荐：1-0, 2-0", style_body_bold))
story.append(Spacer(1, 6))

# Goals
story.append(Paragraph("维度 5 - 总进球数", style_heading3_blue))
story.append(Paragraph("• 0球: 10% | 1球: 25% | 2球: 35% | 3球: 20% | 4球: 8% | 5+: 2%", style_body))
story.append(Paragraph("★ 推荐：2球最可能", style_body_bold))
story.append(Spacer(1, 6))

# Over/Under
story.append(Paragraph("维度 6 - 大小球", style_heading3_blue))
story.append(Paragraph("• 盘口：2.5球 | 大 @0.95 | 小 @0.41", style_body))
story.append(Paragraph("★ 推荐：小 2.5 @0.41", style_body_bold))
story.append(Spacer(1, 6))

# Kelly
story.append(Paragraph("【Kelly 注码】", style_heading3_blue))
story.append(Paragraph("• 原始 Kelly：80.65%", style_body))
story.append(Paragraph("• 封顶后注码：500 EUR（5% bankroll）", style_body_bold))
story.append(Paragraph("• 期望值：+86.2%", style_body_green))
story.append(Spacer(1, 6))
story.append(Paragraph("⚠️ 风险提示：90% 预测极度激进，建议谨慎", style_body_bold))
story.append(Paragraph("推荐投注：美国 WIN @2.07（市场）500 EUR", style_highlight))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# ==================== SUMMARY ====================
story.append(Paragraph("四、修正总结对比", style_heading2))

summary_data = [
    ['项目', '加拿大 vs 波黑', '美国 vs 巴拉圭'],
    ['用户预测', '72%', '90%'],
    ['市场隐含概率', '54%', '48%'],
    ['P0 公平概率', '72%', '90%'],
    ['市场偏差', '+33% edge', '+88% edge'],
    ['Kelly 原始', '39.06%', '80.65%'],
    ['Kelly 封顶', '500 EUR', '500 EUR'],
    ['推荐市场赔率', '@1.85', '@2.07'],
]
t5 = Table(summary_data, colWidths=[4*cm, 5*cm, 5*cm])
t5.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), font_bold),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 1), (-1, -1), font_name),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8F5E9')),
    ('FONTNAME', (0, -1), (-1, -1), font_bold),
]))
story.append(t5)
story.append(Spacer(1, 10))

story.append(Paragraph("五、关键洞察", style_heading2))
story.append(Paragraph("1. 市场赔率融入公众偏见 + 流动性折扣，P0 引擎还原真实概率", style_body))
story.append(Paragraph("2. 加拿大市场隐含 54% 被低估，实际概率 72% → +33% edge", style_body))
story.append(Paragraph("3. 美国市场隐含 48% 大幅低估，实际概率 90% → +88% edge（极度激进）", style_body))
story.append(Paragraph("4. Kelly 注码封顶 5% bankroll，防止黑天鹅风险", style_body))
story.append(Paragraph("5. 两场比赛推荐小 2.5 球，2 球最可能", style_body))
story.append(Spacer(1, 10))

story.append(Paragraph("六、数据来源", style_heading2))
story.append(Paragraph("• OddsPricingAgent v1.1 - 赔率定价中心", style_body))
story.append(Paragraph("• TreasuryAgent v1.1 - 资金管理中心", style_body))
story.append(Paragraph("• 原始数据：OddsPortal / 500.com / Betfair Exchange", style_body))
story.append(Paragraph("• 修正时间：2026-06-12 21:58 GMT+8", style_body))
story.append(Spacer(1, 20))

# 页脚
story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))
story.append(Paragraph("Football Quant OS | Naga Core P0 Engine", style_brand))
story.append(Paragraph("OddsPricingAgent + TreasuryAgent", style_brand2))
story.append(Paragraph("本报告仅供研究学习使用，不构成任何投注建议。", style_note))

doc.build(story)
print(f"PDF已生成: {output_path}")
