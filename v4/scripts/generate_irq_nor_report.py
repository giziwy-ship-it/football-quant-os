#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
伊拉克 vs 挪威 - 2026 世界杯预测报告 PDF 生成
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime

# 注册中文字体
chinese_font = 'Helvetica'
try:
    pdfmetrics.registerFont(TTFont('MSYH', 'C:/Windows/Fonts/msyh.ttc', subfontIndex=0))
    chinese_font = 'MSYH'
except:
    try:
        pdfmetrics.registerFont(TTFont('SimHei', 'C:/Windows/Fonts/simhei.ttf'))
        chinese_font = 'SimHei'
    except:
        pass

# 配色
cd = {
    'primary': colors.HexColor('#1A3A5C'),
    'accent': colors.HexColor('#C9A227'),
    'secondary': colors.HexColor('#2874A6'),
    'success': colors.HexColor('#34A853'),
    'danger': colors.HexColor('#EA4335'),
    'white': colors.white,
    'light_gray': colors.HexColor('#F5F5F5'),
    'mid_gray': colors.HexColor('#999999'),
    'dark_gray': colors.HexColor('#333333'),
}


def create_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    def make_style(name, parent, **kwargs):
        defaults = dict(fontName=chinese_font)
        defaults.update(kwargs)
        return ParagraphStyle(name, parent=styles[parent], **defaults)
    
    title_style = make_style('Title', 'Heading1', fontSize=22, textColor=cd['primary'], spaceAfter=10, leading=26)
    h1_style = make_style('H1', 'Heading2', fontSize=16, textColor=cd['primary'], spaceBefore=18, spaceAfter=8, leading=20)
    h2_style = make_style('H2', 'Heading3', fontSize=13, textColor=cd['secondary'], spaceBefore=12, spaceAfter=6, leading=16)
    body_style = make_style('Body', 'Normal', fontSize=10, textColor=cd['dark_gray'], leading=14, spaceAfter=6, alignment=TA_JUSTIFY)
    highlight = make_style('Highlight', 'Normal', fontSize=11, textColor=cd['primary'], backColor=cd['light_gray'], borderPadding=8, leading=16, spaceAfter=10)
    center_small = make_style('CenterSmall', 'Normal', fontSize=9, textColor=cd['mid_gray'], alignment=TA_CENTER, leading=12)
    
    story = []
    
    # 标题
    story.append(Spacer(1, 2*cm))
    story.append(HRFlowable(width="100%", thickness=3, color=cd['primary'], spaceAfter=15))
    story.append(Paragraph("FOOTBALL QUANT OS v4.0", make_style('SysTitle', 'Normal', fontSize=13, textColor=cd['accent'], alignment=TA_CENTER)))
    story.append(Paragraph("比赛预测报告", title_style))
    story.append(Paragraph("伊拉克 vs 挪威 | 2026 FIFA 世界杯 - 小组赛", center_small))
    story.append(Paragraph(f"比赛时间: 2026年6月17日 06:00 | 报告生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}", center_small))
    story.append(HRFlowable(width="100%", thickness=1, color=cd['accent'], spaceAfter=20))
    
    # 执行摘要
    story.append(Paragraph("执行摘要", h1_style))
    story.append(Paragraph(
        "<b>核心结论:</b> 挪威实力明显占优，获胜概率高达 68.4%。"
        "伊拉克虽主场作战，但阵容实力差距悬殊。"
        "盘口从受两球降至受球半/两球，机构对挪威大胜信心略有减弱，"
        "但挪威水位仍维持在较低水平。",
        highlight
    ))
    
    # 关键指标
    story.append(Paragraph("关键指标", h1_style))
    metrics = [
        ['指标', 'v4模型', '市场平均', '融合概率', '置信度'],
        ['挪威胜', '65.0%', '67.9%', '68.4%', '高'],
        ['平局', '22.0%', '19.9%', '19.4%', '-'],
        ['伊拉克胜', '13.0%', '12.2%', '11.4%', '低'],
        ['预期xG(挪威)', '2.10', '2.05', '2.08', '高'],
        ['预期xG(伊拉克)', '0.65', '0.70', '0.68', '中'],
        ['大2.5球', '52.0%', '51.9%', '51.9%', '中'],
    ]
    story.append(make_table(metrics, cd['primary']))
    story.append(Spacer(1, 0.4*cm))
    
    # 1X2
    story.append(Paragraph("1X2 胜平负", h1_style))
    story.append(Paragraph(
        "市场一致看好挪威获胜，平均赔率 1.35 显示强烈信心。"
        "伊拉克胜赔高达 7.50+，爆冷概率极低。",
        body_style
    ))
    
    bookie_1x2 = [
        ['博彩公司', '伊拉克胜', '平局', '挪威胜', '信号'],
        ['William Hill', '8.00', '4.50', '1.29', '强烈看好挪威'],
        ['立博', '8.00', '4.60', '1.40', '看好挪威'],
        ['Bet365', '6.00', '4.50', '1.40', '看好挪威'],
        ['Interwetten', '7.00', '4.70', '1.45', '看好挪威'],
        ['SBOBET', '10.00', '5.75', '1.25', '强烈看好挪威'],
        ['Pinnacle', '6.19', '4.32', '1.48', '看好挪威'],
    ]
    story.append(make_table(bookie_1x2, cd['secondary']))
    story.append(Spacer(1, 0.3*cm))
    
    # 亚盘
    story.append(Paragraph("亚洲让球", h1_style))
    story.append(Paragraph(
        "伊拉克受让 1.75 球(球半/两球)，挪威水位 0.86 处于低位。"
        "注意部分公司从受两球降盘至受球半/两球，盘口收窄。",
        body_style
    ))
    
    ah_data = [
        ['博彩公司', '盘口', '伊拉克水位', '挪威水位', '变化'],
        ['William Hill', '受球半/两球', '0.83', '0.80', '无'],
        ['澳门', '受球半/两球', '1.02', '0.82', '无'],
        ['立博', '受球半', '1.20', '0.60', '无'],
        ['Bet365', '受球半/两球', '1.03', '0.83', '无'],
        ['Interwetten', '受两球(降)', '0.63', '1.15', '降盘'],
        ['伟德', '受球半/两球(降)', '1.01', '0.83', '降盘'],
    ]
    story.append(make_table(ah_data, cd['secondary']))
    story.append(Spacer(1, 0.4*cm))
    
    # 预测矩阵
    story.append(Paragraph("预测矩阵", h1_style))
    pred_data = [
        ['市场', '推荐', '概率', '赔率', '评级'],
        ['胜平负 - 挪威', '主胜', '68.4%', '1.35', 'A-'],
        ['胜平负 - 平局', '回避', '19.4%', '4.60', 'C'],
        ['胜平负 - 伊拉克', '回避', '11.4%', '7.50', 'D'],
        ['亚洲让球', '挪威 -1.75', '55.0%', '0.86', 'B+'],
        ['半全场', '平/挪威', '26.0%', '3.80', 'B'],
        ['比分', '0-2 或 1-2', '23.3%', '7.50', 'B-'],
        ['大小球2.5', '大', '51.9%', '1.90', 'B-'],
        ['双方进球', 'YES', '41.9%', '1.95', 'C+'],
        ['总进球', '2-3球', '46.3%', '3.20', 'B'],
    ]
    story.append(make_table(pred_data, cd['primary']))
    story.append(Spacer(1, 0.4*cm))
    
    # 比分预测
    story.append(Paragraph("比分预测", h1_style))
    story.append(Paragraph("预期进球: 伊拉克 0.68 | 挪威 2.08", body_style))
    score_data = [
        ['排名', '比分', '概率'],
        ['1', '0-2', '14.1%'],
        ['2', '0-1', '13.4%'],
        ['3', '0-3', '9.9%'],
        ['4', '1-2', '9.2%'],
        ['5', '1-1', '8.7%'],
    ]
    story.append(make_table(score_data, cd['success']))
    story.append(Spacer(1, 0.4*cm))
    
    # 风险评估
    story.append(Paragraph("风险评估", h1_style))
    story.append(Paragraph(
        "<b>主要风险:</b> 伊拉克主场优势。主场氛围可能激发超水平发挥。"
        "<br/><br/>"
        "<b>次要风险:</b> 盘口降盘信号。部分公司从受两球降至受球半/两球，"
        "暗示机构对挪威大胜的信心在减弱，可能预期比分较为接近。"
        "<br/><br/>"
        "<b>利好因素:</b> 挪威拥有厄德高和哈兰德等世界级球星，"
        "阵容实力碾压。近6场仅1负，状态稳定。",
        body_style
    ))
    
    risk_data = [
        ['风险因素', '概率', '影响', '评分'],
        ['伊拉克爆冷', '11.4%', '高', '2.1/10'],
        ['平局结果', '19.4%', '中', '3.5/10'],
        ['挪威小胜', '25.0%', '低', '2.0/10'],
        ['大球失误', '48.1%', '低', '2.5/10'],
    ]
    story.append(make_table(risk_data, cd['primary']))
    story.append(Spacer(1, 0.4*cm))
    
    # 最终推荐
    story.append(Paragraph("最终推荐", h1_style))
    story.append(Paragraph(
        "<b>主仓位:</b> 挪威胜 (1X2) 赔率 1.35<br/>"
        "<b>副仓位:</b> 挪威 -1.75 亚盘<br/>"
        "<b>投机:</b> 半全场 平/挪威<br/>"
        "<b>比分:</b> 0-2 或 1-2<br/>"
        "<b>大小球:</b> 大 2.5/3<br/>"
        "<b>双方进球:</b> YES",
        highlight
    ))
    
    story.append(Paragraph(
        "挪威实力明显占优，市场共识强烈。"
        "伊拉克虽有主场之利，但阵容差距难以弥补。"
        "建议重点投资挪威获胜，适当配置让球盘。"
        "盘口降盘信号提示不宜过度追大球。",
        body_style
    ))
    
    # 免责声明
    story.append(Spacer(1, 0.8*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=cd['mid_gray'], spaceAfter=10))
    story.append(Paragraph(
        "<b>免责声明</b><br/>"
        "本报告仅供信息及分析目的，不构成投资建议或博彩推荐。"
        "用户承担基于本分析采取任何仓位的全部风险。"
        "数据来源: oddsportal.com、500.com。",
        make_style('Disclaimer', 'Normal', fontSize=8, textColor=cd['mid_gray'], leading=11, alignment=TA_JUSTIFY)
    ))
    story.append(Paragraph(
        "2026 Naga Core Analytics | Football Quant OS v4.1.0 | 机密",
        make_style('Footer', 'Normal', fontSize=8, textColor=cd['mid_gray'], alignment=TA_CENTER)
    ))
    
    doc.build(story)
    print(f"PDF 已生成: {output_path}")


def make_table(data, header_color):
    """创建统一风格的表格"""
    t = Table(data, repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 7),
        ('TOPPADDING', (0, 0), (-1, 0), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, cd['light_gray']),
        ('TEXTCOLOR', (0, 1), (-1, -1), cd['dark_gray']),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
        ('TOPPADDING', (0, 1), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, cd['light_gray']]),
    ]
    t.setStyle(TableStyle(style))
    return t


if __name__ == "__main__":
    import os
    output = "D:/openclaw-workspace/football_quant_os/v4/reports/iraq_norway_report_cn.pdf"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    create_pdf(output)
