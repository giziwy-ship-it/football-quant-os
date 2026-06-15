#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""美国 vs 巴拉圭 完整预测报告 - PDF生成器"""

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

output_path = os.path.join(os.path.expanduser("~"), "Desktop", "美国vs巴拉圭_2026世界杯预测报告.pdf")

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
story.append(Paragraph("美国 vs 巴拉圭", style_title))
story.append(Paragraph("2026世界杯 Group A 第1轮", style_subtitle))
story.append(Paragraph("2026-06-13 09:00 | 洛杉矶 SoFi Stadium", style_subtitle))
story.append(Spacer(1, 20))
story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# 基础信息
story.append(Paragraph("一、赛事基础信息", style_heading2))
story.append(Paragraph("• 赛事：2026世界杯 Group A 第1轮", style_body))
story.append(Paragraph("• 对阵：美国 (东道主) vs 巴拉圭", style_body))
story.append(Paragraph("• 时间：2026-06-13 09:00 (UTC-7)", style_body))
story.append(Paragraph("• 地点：洛杉矶 SoFi Stadium (美国主场揭幕战)", style_body))
story.append(Paragraph("• 历史交锋：美国 4胜1负", style_body))
story.append(Paragraph("• 近两次：2025年11月 美国2-1巴拉圭 | 2018年3月 美国1-0巴拉圭", style_body))
story.append(Paragraph("• 综合概率：美国58.2% | 平局24.2% | 巴拉圭17.7%", style_body))
story.append(Spacer(1, 10))

# 赔率数据
story.append(Paragraph("二、多平台赔率数据汇总", style_heading2))
story.append(Paragraph("OddsPortal (18家博彩公司平均)", style_heading3_blue))

odds_data = [
    ['博彩公司', '美国', '平局', '巴拉圭', '返还率'],
    ['Mozzartbet', '2.15', '3.42', '4.00', '98.5% ★'],
    ['Megapari', '2.15', '3.42', '4.00', '98.5%'],
    ['Betfair', '2.12', '3.40', '4.10', '99.0% (Back)'],
    ['平均值', '2.07', '3.30', '3.87', '96.5%'],
    ['500.com', '2.05', '3.30', '3.90', '95.3%'],
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
story.append(Paragraph("Betfair Exchange: Back 2.12/3.40/4.10 (99.0%) | Lay 2.13/3.45/4.15 (100.4%)", style_note))
story.append(Spacer(1, 6))

story.append(Paragraph("500.com (亚洲盘口)", style_heading3_blue))
story.append(Paragraph("• 欧赔：美国2.05 | 平局3.30 | 巴拉圭3.90", style_body))
story.append(Paragraph("• 必发指数：主胜38.7% | 平局28.3% | 客胜32.9%", style_body))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# 六维度预测
story.append(Paragraph("三、六维度预测结果", style_heading2))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度1】胜平负 (1X2)", style_heading3))
story.append(Paragraph("隐含概率：美国48.3% | 平局30.3% | 巴拉圭21.4%", style_body))
story.append(Paragraph("用户预测：美国90% | 平局9% | 巴拉圭1%", style_body))
story.append(Paragraph("AI预测：USA to win - narrow 1-0 or 2-0, home crowd + Europe-based stars", style_body))
story.append(Paragraph("综合概率：美国58.2% | 平局24.2% | 巴拉圭17.7%", style_body))
story.append(Paragraph("★ 推荐：美国胜 @2.07 | 信心：★★★★☆", style_body_bold))
story.append(Paragraph("最佳赔率：Mozzartbet/Megapari 2.15 (返还率98.5%)", style_body))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度2】让球胜平负 (Asian Handicap)", style_heading3))
story.append(Paragraph("盘口：美国-0.5 / 美国-0.75", style_body))
story.append(Paragraph("隐含概率：美国约55% | 平局约25% | 巴拉圭约20%", style_body))
story.append(Paragraph("★ 推荐：美国让胜 (-0.5) @1.75-1.80 | 信心：★★★★☆", style_body_bold))
story.append(Paragraph("理由：主场揭幕战，Pulisic/Reyna/Balogun欧洲球星", style_body))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度3】半全场 (HT/FT)", style_heading3))
htft_data = [
    ['半全场', '概率', '可视化'],
    ['主/主', '40%', '████████████████████'],
    ['平/主', '30%', '███████████████'],
    ['平/平', '15%', '███████'],
    ['主/平', '8%', '████'],
    ['平/客', '4%', '██'],
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
story.append(Paragraph("★ 推荐：主/主 (40%) 或 平/主 (30%) | 信心：★★★☆☆", style_body_bold))
story.append(Paragraph("理由：美国上半场可能进球，巴拉圭防守反击上半场谨慎", style_body))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度4】比分 (Correct Score)", style_heading3))
score_data = [
    ['排名', '比分', '概率', '说明'],
    ['1', '1-0', '25%', 'AI最看好，历史近两次1-0'],
    ['2', '2-0', '20%', '美国完胜'],
    ['3', '1-1', '12%', '双方各进一球'],
    ['4', '2-1', '10%', '美国险胜'],
    ['5', '0-0', '8%', '全场闷平'],
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
    ['概率', '6%', '22%', '32%', '22%', '12%', '6%'],
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
story.append(Paragraph("大2.5：40% | 小2.5：60%", style_body))
story.append(Paragraph("★ 推荐：2球最可能 | 信心：★★★★☆", style_body_bold))
story.append(Spacer(1, 6))

story.append(Paragraph("【维度6】大小球 (Over/Under)", style_heading3))
story.append(Paragraph("OddsPortal AI: 'World Cup openers between evenly matched sides are often cagey'", style_body))
story.append(Paragraph("盘口：2.5球 | 小2.5 @1.58 (GGBET最高) | 大2.5 @2.30+", style_body))
story.append(Paragraph("★ 推荐：小2.5球 @1.58 | 信心：★★★★☆", style_body_bold))
story.append(Paragraph("★ 推荐：双方进球-否 @1.78 | 信心：★★★★☆", style_body_bold))
story.append(Paragraph("理由：AI预测巴拉圭低位防守，美国可能零封，1-0/2-0最可能", style_body))
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
    ['美国胜@2.07', '58.2%', '2.07', '20.4%', '10.2%', '500 EUR', '+20.4%'],
    ['小2.5球@1.58', '60.0%', '1.58', '1.2%', '0.6%', '59 EUR', '+0.8%'],
    ['双方进球-否@1.78', '65.0%', '1.78', '15.7%', '7.8%', '500 EUR', '+15.7%'],
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
story.append(Paragraph("美国近5场：2胜3负 | 3-2塞内加尔、5-1乌拉圭亮眼", style_body))
story.append(Paragraph("巴拉圭近5场：3胜2负 | 客场2-1墨西哥、2-1摩洛哥惊艳", style_body))
story.append(Paragraph("OddsPortal AI：'the most believable storyline is a tight 1-0 or 2-0 victory'", style_body))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# 风险提示
story.append(Paragraph("六、风险提示", style_heading2))
story.append(Paragraph("⚠ 美国近5场仅2胜，0-2负巴西、1-4负巴西表现差", style_body))
story.append(Paragraph("⚠ 巴拉圭客场2-1墨西哥，客场战力不容小觑", style_body))
story.append(Paragraph("⚠ 历史交锋美国4胜1负，但2018年曾0-1负巴拉圭", style_body))
story.append(Paragraph("⚠ 美国作为东道主，压力可能比动力更大", style_body))
story.append(Paragraph("⚠ 建议单场投注，控制注码在5%以内", style_body))
story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))

# 数据来源
story.append(Paragraph("七、数据来源", style_heading2))
story.append(Paragraph("• OddsPortal - 18家博彩公司赔率 + AI预测 + 用户预测", style_body))
story.append(Paragraph("• 500.com - 亚洲盘口 + 必发指数", style_body))
story.append(Paragraph("• Betfair Exchange - 官方交易数据", style_body))
story.append(Paragraph("• 数据抓取时间：2026-06-12 19:05", style_body))
story.append(Spacer(1, 20))

# 版权页脚
story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1F4E79')))
story.append(Spacer(1, 10))
story.append(Paragraph("律动 | Legal", style_brand))
story.append(Paragraph("植根金融 精于法律 赋能未来", style_brand2))
story.append(Paragraph("本报告仅供研究学习使用，不构成任何投注建议。", style_note))

doc.build(story)
print(f"PDF已生成: {output_path}")
