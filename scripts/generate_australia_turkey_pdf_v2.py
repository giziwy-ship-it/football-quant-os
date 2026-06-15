#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Google Material Design 风格 PDF 报告生成器 (修正版)
澳大利亚(主) vs 土耳其(客) - 2026世界杯六维预测报告
比分格式: 主队-客队
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

# 注册中文字体
pdfmetrics.registerFont(TTFont('SimHei', 'C:\\Windows\\Fonts\\simhei.ttf'))
pdfmetrics.registerFont(TTFont('SimKai', 'C:\\Windows\\Fonts\\simkai.ttf'))

DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')
OUTPUT_FILE = os.path.join(DESKTOP, "澳大利亚(主)vs土耳其_六维预测报告.pdf")

GOOGLE_BLUE = colors.HexColor("#4285F4")
GOOGLE_GREEN = colors.HexColor("#34A853")
GOOGLE_RED = colors.HexColor("#EA4335")
GOOGLE_YELLOW = colors.HexColor("#FBBC04")
GOOGLE_DARK = colors.HexColor("#202124")
GOOGLE_GRAY = colors.HexColor("#5F6368")
GOOGLE_LIGHT_GRAY = colors.HexColor("#F8F9FA")
GOOGLE_BORDER = colors.HexColor("#DADCE0")

def create_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='GoogleTitle', fontName='SimHei', fontSize=24, textColor=GOOGLE_DARK, spaceAfter=8, leading=30))
    styles.add(ParagraphStyle(name='GoogleSubtitle', fontName='SimHei', fontSize=14, textColor=GOOGLE_GRAY, spaceAfter=20, leading=18))
    styles.add(ParagraphStyle(name='GoogleSection', fontName='SimHei', fontSize=16, textColor=GOOGLE_BLUE, spaceAfter=12, spaceBefore=16, leading=20))
    styles.add(ParagraphStyle(name='GoogleBody', fontName='SimKai', fontSize=11, textColor=GOOGLE_DARK, spaceAfter=8, leading=16))
    styles.add(ParagraphStyle(name='GoogleHighlight', fontName='SimHei', fontSize=12, textColor=GOOGLE_GREEN, spaceAfter=6, leading=15))
    styles.add(ParagraphStyle(name='GoogleWarning', fontName='SimHei', fontSize=12, textColor=GOOGLE_RED, spaceAfter=6, leading=15))
    styles.add(ParagraphStyle(name='GoogleFooter', fontName='SimKai', fontSize=9, textColor=GOOGLE_GRAY, alignment=TA_CENTER, spaceBefore=20))
    return styles

def create_table(headers, data, highlight_col=None):
    table_data = [headers] + data
    col_width = 160 / len(headers) * mm
    table = Table(table_data, colWidths=[col_width] * len(headers))
    style = [
        ('FONTNAME', (0, 0), (-1, 0), 'SimHei'),
        ('FONTNAME', (0, 1), (-1, -1), 'SimKai'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 0), (-1, 0), GOOGLE_BLUE),
        ('TEXTCOLOR', (0, 1), (-1, -1), GOOGLE_DARK),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, GOOGLE_BORDER),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]
    if highlight_col is not None:
        for row in range(1, len(table_data)):
            style.append(('BACKGROUND', (highlight_col, row), (highlight_col, row), GOOGLE_LIGHT_GRAY))
    table.setStyle(TableStyle(style))
    return table

def generate_report():
    doc = SimpleDocTemplate(OUTPUT_FILE, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = create_styles()
    story = []
    
    # 标题
    story.append(Paragraph("Football Quant OS", styles['GoogleSubtitle']))
    story.append(Paragraph("六维预测报告", styles['GoogleTitle']))
    story.append(Spacer(1, 10))
    
    # 头部信息
    header_data = [
        ['比赛', '澳大利亚(主) vs 土耳其(客)'],
        ['赛事', '2026世界杯小组赛'],
        ['日期', '2026-06-14'],
        ['数据来源', 'odds.500.com + oddsportal.com'],
    ]
    header_table = Table(header_data, colWidths=[40*mm, 120*mm])
    header_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'SimHei'),
        ('FONTNAME', (1, 0), (1, -1), 'SimKai'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), GOOGLE_GRAY),
        ('TEXTCOLOR', (1, 0), (1, -1), GOOGLE_DARK),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, GOOGLE_BORDER),
        ('BACKGROUND', (0, 0), (0, -1), GOOGLE_LIGHT_GRAY),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 20))
    
    # 一、胜平负
    story.append(Paragraph("【一】胜平负 (1X2)", styles['GoogleSection']))
    story.append(create_table(
        ['项目', '澳大利亚(主)', '平局', '土耳其(客)'],
        [
            ['赔率', '5.20', '3.67', '1.70'],
            ['隐含概率', '18.3%', '25.9%', '55.8%'],
            ['模型概率', '19.8%', '24.7%', '55.5%'],
            ['Edge', '+1.5%', '-1.2%', '-0.3%'],
            ['凯利指数', '50', '66', '-47'],
        ],
        highlight_col=3
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("最可能: 土耳其胜 (55.5%)", styles['GoogleBody']))
    story.append(Paragraph("价值投注: 无 (最大Edge +1.5% < 5%)", styles['GoogleWarning']))
    story.append(Paragraph("注意: 土耳其凯利-47 = 热门风险", styles['GoogleWarning']))
    story.append(Spacer(1, 15))
    
    # 二、让球
    story.append(Paragraph("【二】让球胜平负 (Asian Handicap)", styles['GoogleSection']))
    story.append(create_table(
        ['盘口', '澳大利亚+1', '平局', '土耳其-1'],
        [
            ['赔率', '2.28', '2.95', '2.84'],
            ['隐含概率', '38.8%', '30.0%', '31.2%'],
            ['推荐', '✓ 受让', '-', '-'],
            ['Kelly', '125 EUR', '-', '-'],
        ],
        highlight_col=1
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph("推荐: 澳大利亚+1球 (受让有赢盘空间)", styles['GoogleHighlight']))
    story.append(Spacer(1, 15))
    
    # 三、半全场
    story.append(Paragraph("【三】半全场 (HT/FT)", styles['GoogleSection']))
    story.append(create_table(
        ['组合', '概率'],
        [
            ['土耳其/土耳其', '25.0%'],
            ['平局/土耳其', '22.2%'],
            ['土耳其/平局', '10.0%'],
        ],
        highlight_col=1
    ))
    story.append(Spacer(1, 15))
    
    # 四、比分 (修正格式: 主队-客队)
    story.append(Paragraph("【四】比分 (Correct Score)", styles['GoogleSection']))
    story.append(Paragraph("格式: 澳大利亚(主) - 土耳其(客)", styles['GoogleBody']))
    story.append(create_table(
        ['比分', '概率', '结果说明'],
        [
            ['0-1', '15.0%', '澳大利亚0-1土耳其'],
            ['0-2', '12.0%', '澳大利亚0-2土耳其'],
            ['1-2', '10.0%', '澳大利亚1-2土耳其'],
            ['1-1', '8.0%', '澳大利亚1-1土耳其'],
            ['1-0', '7.0%', '澳大利亚1-0土耳其'],
        ]
    ))
    story.append(Spacer(1, 15))
    
    # 五、进球数
    story.append(Paragraph("【五】进球数 (Total Goals)", styles['GoogleSection']))
    story.append(Paragraph("预期总进球: 2.2 球", styles['GoogleBody']))
    story.append(Paragraph("最可能: 2球 (35%)", styles['GoogleBody']))
    story.append(Paragraph("范围: 1-3球", styles['GoogleBody']))
    story.append(Spacer(1, 15))
    
    # 六、大小球
    story.append(Paragraph("【六】大小球 (Over/Under)", styles['GoogleSection']))
    story.append(create_table(
        ['盘口', '推荐', '理由'],
        [
            ['2.5球', '小球', '低赔支持0.73'],
        ],
        highlight_col=1
    ))
    story.append(Spacer(1, 15))
    
    # Kelly汇总
    story.append(Paragraph("【Kelly 注码建议】", styles['GoogleSection']))
    story.append(create_table(
        ['投注', '概率', '赔率', '半Kelly'],
        [
            ['澳大利亚+1', '44%', '2.28', '125 EUR'],
            ['小球2.5', '55%', '0.95', '跳过'],
            ['土耳其胜', '55.5%', '1.70', '不投注'],
        ]
    ))
    story.append(Spacer(1, 15))
    
    # 冷门评分
    story.append(Paragraph("【冷门评分】", styles['GoogleSection']))
    story.append(Paragraph("评分: 12/65 (低风险)", styles['GoogleBody']))
    story.append(Paragraph("说明: 土耳其实力占优，市场定价合理，无显著冷门信号", styles['GoogleBody']))
    story.append(Spacer(1, 15))
    
    # 六维总结
    story.append(Paragraph("【六维预测总结】", styles['GoogleSection']))
    story.append(create_table(
        ['市场', '预测', '置信度', '推荐'],
        [
            ['胜平负', '土耳其胜', '55.5%', '无价值'],
            ['让球', '澳大利亚+1', '44%', '可小额'],
            ['半全场', '土耳其/土耳其', '25%', '参考'],
            ['比分', '0-1/0-2', '-', '参考'],
            ['进球数', '2球', '35%', '参考'],
            ['大小球', '小球2.5', '55%', '推荐'],
        ]
    ))
    story.append(Spacer(1, 15))
    
    # 风险提示
    story.append(Paragraph("【风险提示】", styles['GoogleSection']))
    story.append(Paragraph("1. 土耳其凯利-47 = 热门风险，市场过度追捧", styles['GoogleWarning']))
    story.append(Paragraph("2. 澳大利亚+1球有受让价值，但土耳其仍可能赢2球", styles['GoogleBody']))
    story.append(Paragraph("3. 大小球市场分歧，建议小额或观望", styles['GoogleBody']))
    story.append(Paragraph("4. 无显著价值投注，建议控制仓位", styles['GoogleBody']))
    story.append(Spacer(1, 20))
    
    # 免责声明
    story.append(Paragraph("免责声明: 本报告为研究模型输出，不构成投资建议。", styles['GoogleFooter']))
    story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Football Quant OS v4.3.2", styles['GoogleFooter']))
    
    doc.build(story)
    print(f"PDF报告已生成: {OUTPUT_FILE}")
    return OUTPUT_FILE

if __name__ == "__main__":
    generate_report()
