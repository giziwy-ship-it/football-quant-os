#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""加拿大 vs 波黑 完整预测报告 - PDF生成器"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os
import sys

# 注册中文字体
font_paths = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\simhei.ttf",
    r"C:\Windows\Fonts\simsun.ttc",
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
            else:
                pdfmetrics.registerFont(TTFont('SimSun', fp, subfontIndex=0))
            font_registered = True
        except Exception:
            continue

if not font_registered:
    font_name = 'Helvetica'
    font_bold = 'Helvetica-Bold'
else:
    font_name = 'YaHei'
    font_bold = 'YaHeiBold'

output_path = os.path.join(os.path.expanduser("~"), "Desktop", "加拿大vs波黑_2026世界杯预测报告.pdf")

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
style_note = ParagraphStyle('CustomNote', parent=styles['Normal'], fontName=font_name, fontSize=9, textColor=colors.HexColor('#666666'), spaceAfter=4, leading=14)

story = []

# 封面
story.append(Spacer(1, 30))
story.append(Paragraph("植根金融 精于法律 赋能未来", style_brand))
story.append(Paragraph("律动 | Legal 体育量化预测中心", style_brand2))
story.append(Spacer(1, 30))
story.append(Paragraph("加拿大 vs 波黑", style_title))
story.append(Paragraph("2026世界杯 Group B 第1轮", style_subtitle))
story.append(Paragraph("2026-06-13 03:00 | 多伦多 BMO Field", style_subtitle))
story.append(Spacer(1, 20))
story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# 基础信息
story.append(Paragraph("一、赛事基础信息", style_heading2))
story.append(Paragraph("• 赛事：2026世界杯 Group B 第1轮", style_body))
story.append(Paragraph("• 对阵：加拿大 (东道主) vs 波黑", style_body))
story.append(Paragraph("• 时间：2026-06-13 03:00 (UTC-4)", style_body))
story.append(Paragraph("• 地点：多伦多 BMO Field (加拿大主场揭幕战)", style_body))
story.append(Paragraph("• 历史交锋：无直接交锋记录", style_body))
story.append(Paragraph("• 综合概率：加拿大57.5% | 平局23.8% | 波黑18.7%", style_body))
story.append(Spacer(1, 10))

# 赔率数据
story.append(Paragraph("二、多平台赔率数据汇总", style_heading2))
story.append(Paragraph("OddsPortal (18家博彩公司平均)", style_heading3_blue))

odds_data = [
    ['博彩公司', '加拿大', '平局', '波黑', '返还率'],
    ['Mozzartbet', '1.95', '3.54', '4.75', '97.2% ★'],
    ['Mostbet', '1.95', '3.54', '4.75', '97.2%'],
    ['Betfair', '1.90', '3.65', '4.90', '99.2% (Back)'],
    [' averages', '1.85', '3.45', '4.60', '96.0%'],
    ['500.com', '2.38', '3.16', '2.64', '95.3%'],
]

odds_table = Table(odds_data, colWidths=[3.5*cm, 2.5*cm, 2.5*cm, 2.5*cm, 2.5*cm])
odds_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), font_bold),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 1), (-1, -1), font_name),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E8E8E8')),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
]))
story.append(odds_table)
story.append(Spacer(1, 6))
story.append(Paragraph("Betfair Exchange: Back 1.90/3.65/4.90 (99.2%) | Lay 1.91/3.70/5.00 (100.8%)", style_note))
story.append(Spacer(1, 6))

story.append(Paragraph("500.com (亚洲盘口)", style_heading3_blue))
story.append(Paragraph("• 欧赔：加拿大2.38 | 平局3.16 | 波黑2.64", style_body))
story.append(Paragraph("• 必发指数：主38.7% | 平28.3% | 客32.9%", style_body))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# 六维度预测
story.append(Paragraph("三、六维度预测结果", style_heading2))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度1】胜平负 (1X2)", style_heading3))
story.append(Paragraph("隐含概率：加拿大51.6% | 平局27.7% | 波黑20.7%", style_body))
story.append(Paragraph("用户预测：加拿大72% | 平局15% | 波黑13%", style_body))
story.append(Paragraph("AI预测：Canada to win - tight Canadian win by a single goal", style_body))
story.append(Paragraph("综合概率：加拿大57.5% | 平局23.8% | 波黑18.7%", style_body))
story.append(Paragraph("★ 推荐：加拿大胜 @1.85 | 信心：★★★★☆", style_body_bold))
story.append(Paragraph("最佳赔率：Mozzartbet 1.95 (返还率97.2%)", style_body))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度2】让球胜平负 (Asian Handicap)", style_heading3))
story.append(Paragraph("盘口：加拿大-0.75 / 加拿大-1", style_body))
story.append(Paragraph("隐含概率：加拿大约60% | 平局约25% | 波黑约15%", style_body))
story.append(Paragraph("★ 推荐：加拿大让胜 (-0.75) @1.75-1.80 | 信心：★★★★☆", style_body_bold))
story.append(Paragraph("理由：主场揭幕战，加拿大 athleticism + depth优势", style_body))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度3】半全场 (HT/FT)", style_heading3))
htft_data = [
    ['半全场', '概率', '可视化'],
    ['主/主', '35%', '█████████████████'],
    ['平/主', '28%', '██████████████'],
    ['平/平', '18%', '█████████'],
    ['主/平', '8%', '████'],
    ['平/客', '5%', '██'],
]
htft_table = Table(htft_data, colWidths=[3*cm, 2*cm, 5*cm])
htft_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C00000')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), font_bold),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 1), (-1, -1), font_name),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
]))
story.append(htft_table)
story.append(Paragraph("★ 推荐：主/主 (35%) 或 平/主 (28%) | 信心：★★★☆☆", style_body_bold))
story.append(Paragraph("理由：主场揭幕战，加拿大上半场可能领先", style_body))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度4】比分 (Correct Score)", style_heading3))
score_data = [
    ['排名', '比分', '概率', '说明'],
    ['1', '1-0', '22%', 'AI最看好，加拿大小胜'],
    ['2', '2-0', '18%', '加拿大完胜'],
    ['3', '1-1', '15%', '双方各进一球'],
    ['4', '2-1', '12%', '加拿大险胜'],
    ['5', '0-0', '10%', '全场闷平'],
]
score_table = Table(score_data, colWidths=[2*cm, 2*cm, 2*cm, 6*cm])
score_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#C00000')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), font_bold),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 1), (-1, -1), font_name),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
]))
story.append(score_table)
story.append(Paragraph("★ 推荐：1-0, 2-0, 1-1 | 信心：★★★☆☆", style_body_bold))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度5】总进球数 (Total Goals)", style_heading3))
goal_data = [
    ['进球数', '0球', '1球', '2球', '3球', '4球', '5球+'],
    ['概率', '8%', '22%', '28%', '22%', '12%', '8%'],
]
goal_table = Table(goal_data, colWidths=[2.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2*cm])
goal_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1F4E79')),
    ('TEXTCOLOR', (0, 0), (0, -1), colors.white),
    ('FONTNAME', (0, 0), (-1, -1), font_name),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
]))
story.append(goal_table)
story.append(Paragraph("大2.5：42% | 小2.5：58%", style_body))
story.append(Paragraph("★ 推荐：2球最可能 | 信心：★★★★☆", style_body_bold))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度6】大小球 (Over/Under)", style_heading3))
story.append(Paragraph("OddsPortal AI: 'both teams have been involved in tight, draw-heavy stretches rather than wild, end-to-end contests'", style_body))
story.append(Paragraph("盘口：2.5球 | 小2.5 @1.68-1.75 | 大2.5 @2.10+", style_body))
story.append(Paragraph("★ 推荐：小2.5球 @1.68 | 信心：★★★★☆", style_body_bold))
story.append(Paragraph("★ 备选：双方进球-否 @1.80 | 信心：★★★☆☆", style_body_bold))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# Kelly模型
story.append(Paragraph("四、Kelly最优注码模型", style_heading2))
story.append(Paragraph("资金池：10,000 EUR | 最大单注：500 EUR (5%)", style_body))
story.append(Paragraph("Kelly公式：f* = (bp - q) / b", style_note))
story.append(Spacer(1, 6))

kelly_data = [
    ['推荐', '概率', '赔率', 'Kelly', '半Kelly', '建议注码', '期望值'],
    ['加拿大胜@1.85', '57.5%', '1.85', '7.5%', '3.7%', '373 EUR', '+6.3%'],
    ['小2.5球@1.68', '60.0%', '1.68', '1.2%', '0.6%', '59 EUR', '+0.8%'],
    ['双方进球-否@1.80', '55.0%', '1.80', '-1.2%', '-', '不投注', '-1.0%'],
]
kelly_table = Table(kelly_data, colWidths=[3.5*cm, 2*cm, 2*cm, 2*cm, 2*cm, 2.5*cm, 2*cm])
kelly_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1F4E79')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTNAME', (0, 0), (-1, 0), font_bold),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('FONTNAME', (0, 1), (-1, -1), font_name),
    ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CCCCCC')),
    ('TOPPADDING', (0, 0), (-1, -1), 3),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
]))
story.append(kelly_table)
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# 近期战绩
story.append(Paragraph("五、近期战绩", style_heading2))
story.append(Paragraph("加拿大近5场：2胜3平 不败 | 主场：1-1爱尔兰、2-0乌兹别克", style_body))
story.append(Paragraph("波黑近5场：1胜4平 不败 | 客场：1-1巴拿马、0-0北马其顿", style_body))
story.append(Paragraph("OddsPortal AI：'the most believable storyline is a tight Canadian win by a single goal'", style_body))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# 风险提示
story.append(Paragraph("六、风险提示", style_heading2))
story.append(Paragraph("⚠ 加拿大近5场仅2胜，进攻效率不高", style_body))
story.append(Paragraph("⚠ 波黑近5场4平，防守韧性极强", style_body))
story.append(Paragraph("⚠ 历史交锋无记录，双方陌生", style_body))
story.append(Paragraph("⚠ 加拿大作为东道主，压力可能比动力更大", style_body))
story.append(Paragraph("⚠ 建议单场投注，控制注码在5%以内", style_body))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# 数据来源
story.append(Paragraph("七、数据来源", style_heading2))
story.append(Paragraph("• OddsPortal - 18家博彩公司赔率 + AI预测 + 用户预测", style_body))
story.append(Paragraph("• 500.com - 亚洲盘口 + 必发指数", style_body))
story.append(Paragraph("• Betfair Exchange - 官方交易数据", style_body))
story.append(Paragraph("• 数据抓取时间：2026-06-12 17:12", style_body))
story.append(Spacer(1, 20))

# 版权页脚
story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))
story.append(Paragraph("律动 | Legal", style_brand))
story.append(Paragraph("植根金融 精于法律 赋能未来", style_brand2))
story.append(Paragraph("本报告仅供研究学习使用，不构成任何投注建议。", style_note))

doc.build(story)
print(f"PDF已生成: {output_path}")
