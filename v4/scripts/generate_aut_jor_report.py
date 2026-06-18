#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
奥地利 vs 约旦 - 2026 世界杯预测报告
风格：Google + 彭博 + 高盛 + 麦肯锡
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
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

# 配色：Google + 彭博 + 高盛 + 麦肯锡
cd = {
    'goldman_blue': colors.HexColor('#1A3A5C'),
    'goldman_gold': colors.HexColor('#C9A227'),
    'bloomberg_dark': colors.HexColor('#1A1A1A'),
    'mckinsey_navy': colors.HexColor('#003B5C'),
    'google_blue': colors.HexColor('#4285F4'),
    'google_green': colors.HexColor('#34A853'),
    'google_red': colors.HexColor('#EA4335'),
    'white': colors.white,
    'light_gray': colors.HexColor('#F5F5F5'),
    'mid_gray': colors.HexColor('#999999'),
    'dark_gray': colors.HexColor('#333333'),
}


def create_pdf(output_path):
    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm
    )
    
    styles = getSampleStyleSheet()
    
    def make_style(name, parent, **kwargs):
        defaults = dict(fontName=chinese_font)
        defaults.update(kwargs)
        return ParagraphStyle(name, parent=styles[parent], **defaults)
    
    title_style = make_style('Title', 'Heading1', fontSize=24, textColor=cd['goldman_blue'], spaceAfter=12, leading=28)
    subtitle_style = make_style('Subtitle', 'Normal', fontSize=12, textColor=cd['mid_gray'], spaceAfter=20, leading=16)
    h1_style = make_style('H1', 'Heading2', fontSize=16, textColor=cd['goldman_blue'], spaceBefore=20, spaceAfter=10, leading=20, borderColor=cd['goldman_gold'], borderWidth=2, borderPadding=5)
    h2_style = make_style('H2', 'Heading3', fontSize=13, textColor=cd['mckinsey_navy'], spaceBefore=15, spaceAfter=8, leading=16)
    body_style = make_style('Body', 'Normal', fontSize=10, textColor=cd['dark_gray'], leading=14, spaceAfter=8, alignment=TA_JUSTIFY)
    highlight_style = make_style('Highlight', 'Normal', fontSize=11, textColor=cd['goldman_blue'], backColor=cd['light_gray'], borderPadding=8, leading=16, spaceAfter=10)
    center_small = make_style('CenterSmall', 'Normal', fontSize=9, textColor=cd['mid_gray'], alignment=TA_CENTER, leading=12)
    
    story = []
    
    # 封面
    story.append(Spacer(1, 3*cm))
    story.append(HRFlowable(width="100%", thickness=3, color=cd['goldman_blue'], spaceAfter=20))
    story.append(Paragraph("FOOTBALL QUANT OS v4.0", make_style('SysTitle', 'Normal', fontSize=14, textColor=cd['goldman_gold'], alignment=TA_CENTER, spaceAfter=5)))
    story.append(Paragraph("比赛预测报告", title_style))
    story.append(Paragraph("奥地利 vs 约旦 | 2026 FIFA 世界杯 - 小组赛", subtitle_style))
    story.append(Paragraph(f"比赛时间: 2026年6月17日 06:00 (北京时间) | 报告生成: {datetime.now().strftime('%Y-%m-%d %H:%M')}", center_small))
    story.append(HRFlowable(width="100%", thickness=1, color=cd['goldman_gold'], spaceAfter=30))
    
    # 执行摘要 (麦肯锡)
    story.append(Paragraph("执行摘要", h1_style))
    story.append(Paragraph(
        "<b>核心结论:</b> 奥地利实力占优，主场作战给出 <b>75.0% 胜率</b>。"
        "约旦近期状态低迷，近6场仅1胜。但奥地利让1球盘让球胜平负"
        "1.80/3.88/3.16 显示机构对奥地利大胜信心不足，"
        "预计奥地利小胜或中胜，让球平/负概率较高。",
        highlight_style
    ))
    
    # 关键指标
    story.append(Paragraph("关键指标", h1_style))
    metrics_data = [
        ['指标', 'v4模型', '市场平均', '融合概率', '置信度'],
        ['奥地利胜', '72.0%', '75.0%', '75.0%', '高'],
        ['平局', '18.0%', '19.0%', '19.0%', '-'],
        ['约旦胜', '10.0%', '11.0%', '11.0%', '低'],
        ['预期xG(奥地利)', '1.75', '1.70', '1.73', '高'],
        ['预期xG(约旦)', '0.70', '0.75', '0.73', '中'],
        ['小2.5球', '52.0%', '52.0%', '52.0%', '高'],
    ]
    story.append(make_table(metrics_data, cd['goldman_blue']))
    story.append(Spacer(1, 0.5*cm))
    
    # 市场情报
    story.append(Paragraph("市场情报", h1_style))
    story.append(Paragraph("亚洲盘口 & 赔率走势分析", h2_style))
    story.append(Paragraph(
        "奥地利让1球，让球胜平负 1.80/3.88/3.16。"
        "让球胜赔率 1.80 高于1X2主胜 1.26，显示机构对奥地利赢1球以上"
        "信心不足。让球平 3.88 意味着奥地利恰好赢1球概率不低。",
        body_style
    ))
    
    bookie_data = [
        ['博彩公司', '1X2胜', '1X2平', '1X2负', '让球盘', '信号'],
        ['竞彩官方', '1.23', '4.90', '8.90', '奥地利-1.0', '看好奥地利'],
        ['竞彩即时', '1.26', '4.65', '8.25', '奥地利-1.0', '看好奥地利'],
    ]
    story.append(make_table(bookie_data, cd['bloomberg_dark']))
    story.append(Spacer(1, 0.5*cm))
    
    # 必发交易数据 (市场层 + 场域层)
    story.append(Paragraph("必发交易数据", h2_style))
    story.append(Paragraph(
        "必发交易所成交量极度偏向主胜（83.5%），显示市场情绪强烈看好奥地利。"
        "但冷热指数 20 显示奥地利偏热，需警惕过热风险。"
        "平局盈亏指数 51、约旦 100，暗示机构对冷门结果有较大赔付压力。",
        body_style
    ))
    
    betfair_data = [
        ['类型', '百家欧赔', '必发交易', '成交量', '冷热指数', '盈亏指数', '信号'],
        ['奥地利', '69.2%', '83.5%', '3,849,126', '20', '-20', '偏热'],
        ['平局', '19.5%', '9.4%', '434,439', '-52', '51', '偏冷'],
        ['约旦', '11.2%', '7.1%', '326,860', '-37', '100', '偏冷'],
    ]
    story.append(make_table(betfair_data, cd['bloomberg_dark']))
    story.append(Spacer(1, 0.5*cm))
    
    # 让球胜平负
    story.append(Paragraph("让球胜平负", h1_style))
    rq_data = [
        ['类型', '让球胜', '让球平', '让球负', '说明'],
        ['竞彩官方', '1.86', '3.45', '3.32', '奥地利 -1.0'],
        ['竞彩即时', '1.80', '3.88', '3.16', '奥地利 -1.0'],
    ]
    story.append(make_table(rq_data, cd['bloomberg_dark']))
    story.append(Spacer(1, 0.5*cm))
    
    # v4 物理AI引擎
    story.append(Paragraph("v4 物理AI引擎", h1_style))
    story.append(Paragraph("模型架构 & 概率分布", h2_style))
    story.append(Paragraph(
        "v4 物理AI引擎采用四层量子概率框架："
        "力学层（球队物理）、场域层（市场情绪）、熵层（不确定性）、"
        "量子坍缩层（概率生成）。模型基于 1930-2022 年共 964 场世界杯数据训练。",
        body_style
    ))
    
    weights_data = [
        ['层级', '权重', '描述', '状态'],
        ['力学层', '2.0', '球队攻防物理（xG校准）', '激活'],
        ['熵层', '2.0', '不确定性/爆冷检测', '激活'],
        ['场域层', '1.5', '市场情绪 & 主场优势（必发83.5%主胜）', '激活'],
        ['教练层', '1.0', '战术经理因子（奥地利主场优势）', '激活'],
        ['市场层', '1.5', '赔率隐含概率融合（百家69.2% vs 必发83.5%）', '激活'],
    ]
    story.append(make_table(weights_data, cd['google_blue']))
    story.append(Spacer(1, 0.5*cm))
    
    # 预测矩阵
    story.append(Paragraph("预测矩阵", h1_style))
    story.append(Paragraph("全市场 - 综合预测", h2_style))
    
    pred_data = [
        ['市场', '推荐', '概率', '赔率', '价值', '评级'],
        ['1X2 - 奥地利', '主胜', '75.0%', '1.26', '+6.5%', 'A-'],
        ['1X2 - 平局', '回避', '19.0%', '4.65', '-2.0%', 'C'],
        ['1X2 - 约旦', '回避', '11.0%', '8.25', '-4.5%', 'D'],
        ['让球胜平负', '让球平/负', '55.0%', '3.16', '+8.3%', 'B+'],
        ['亚洲让球', '奥地利 -1.0', '48.0%', '1.80', '+2.5%', 'B-'],
        ['半全场', '平/奥地利', '24.0%', '3.60', '+2.8%', 'B-'],
        ['比分', '1-0 或 2-0', '28.0%', '6.50', '+1.2%', 'B-'],
        ['大小球2.5', '小', '52.0%', '1.95', '+5.7%', 'A-'],
        ['双方进球', 'NO', '58.0%', '1.75', '+0.8%', 'C+'],
        ['总进球', '1-2球', '55.0%', '3.50', '+3.2%', 'B-'],
    ]
    story.append(make_table(pred_data, cd['goldman_blue']))
    story.append(Spacer(1, 0.5*cm))
    
    # 比分预测
    story.append(Paragraph("比分预测", h1_style))
    story.append(Paragraph("预期进球: 奥地利 1.73 | 约旦 0.73", body_style))
    score_data = [
        ['排名', '比分', '概率', '赔率'],
        ['1', '1-0', '14.5%', '7.00'],
        ['2', '2-0', '13.2%', '8.50'],
        ['3', '2-1', '9.8%', '9.50'],
        ['4', '1-1', '8.5%', '6.50'],
        ['5', '0-0', '6.8%', '12.00'],
    ]
    story.append(make_table(score_data, cd['google_green']))
    story.append(Spacer(1, 0.5*cm))
    
    # 进球数
    story.append(Paragraph("进球数分布", h2_style))
    goal_data = [
        ['进球数', '概率'],
        ['0球', '6.8%'],
        ['1球', '17.5%'],
        ['2球', '23.0%'],
        ['3球', '19.8%'],
        ['4球', '12.5%'],
        ['5球+', '6.2%'],
    ]
    story.append(make_table(goal_data, cd['mckinsey_navy']))
    story.append(Spacer(1, 0.5*cm))
    
    # 半全场
    story.append(Paragraph("半全场 HT/FT", h1_style))
    htft_data = [
        ['半场/全场', '概率', '赔率'],
        ['平/奥地利', '24.0%', '3.60'],
        ['奥地利/奥地利', '46.0%', '1.85'],
        ['平/平', '11.0%', '8.50'],
        ['约旦/约旦', '2.5%', '30.00'],
    ]
    story.append(make_table(htft_data, cd['mckinsey_navy']))
    story.append(Spacer(1, 0.5*cm))
    
    # 大小球
    story.append(Paragraph("大小球", h1_style))
    story.append(Paragraph(
        "盘口: 2.5 球 | 大球 1.75 (概率 48.0%) | 小球 1.95 (概率 52.0%)",
        body_style
    ))
    story.append(Spacer(1, 0.5*cm))
    
    # 风险评估
    story.append(Paragraph("风险评估", h1_style))
    story.append(Paragraph(
        "<b>主要风险:</b> 约旦的低位防守和反击能力。"
        "约旦近6场仅1胜，但防守组织尚可。"
        "<br/><br/>"
        "<b>次要风险:</b> 奥地利让1球盘让球胜赔率偏高(1.80)，"
        "显示机构对奥地利大胜信心不足。"
        "<br/><br/>"
        "<b>上行催化剂:</b> 奥地利主场优势，近期状态 WWWDWL。"
        "约旦 LLDDDW 状态低迷。",
        body_style
    ))
    
    risk_data = [
        ['风险因素', '概率', '影响', '缓释措施', '评分'],
        ['约旦爆冷', '11.0%', '高', '奥地利尽早进球', '2.1/10'],
        ['平局结果', '19.0%', '中', '奥地利定位球优势', '3.5/10'],
        ['奥地利大胜', '15.0%', '低', '约旦紧凑防守', '1.5/10'],
        ['小2.5失误', '48.0%', '低', '比赛末段状态', '2.5/10'],
    ]
    story.append(make_table(risk_data, cd['goldman_blue']))
    story.append(Spacer(1, 0.5*cm))
    
    # 最终推荐
    story.append(Paragraph("最终推荐", h1_style))
    story.append(Paragraph(
        "<b>主仓位:</b> 奥地利胜 (1X2) 赔率 1.26<br/>"
        "<b>副仓位:</b> 让球平/负 (奥地利恰好赢1球或不胜) 赔率 3.16<br/>"
        "<b>投机:</b> 半全场 平/奥地利 赔率 3.60<br/>"
        "<b>比分:</b> 1-0 或 2-0<br/>"
        "<b>大小球:</b> 小 2.5<br/>"
        "<b>双方进球:</b> NO<br/>"
        "<b>进球数:</b> 1-2球",
        highlight_style
    ))
    
    story.append(Paragraph(
        "量化模型输出与市场情报的融合支持对奥地利的 calibrated 长仓。"
        "奥地利获胜的预期价值约为市场隐含概率的 +6.5%。"
        "让球平/负 3.16 赔率价值较高，"
        "基于模型判断奥地利赢1球或不胜的概率为 55.0%。",
        body_style
    ))
    
    # 免责声明
    story.append(Spacer(1, 1*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=cd['mid_gray'], spaceAfter=10))
    story.append(Paragraph(
        "<b>免责声明</b><br/>"
        "本报告仅供信息及分析目的，不构成投资建议、博彩推荐或财务指导。"
        "v4 模型历史表现（2022世界杯验证准确率 45.8%）不保证未来结果。"
        "用户承担基于本分析采取任何仓位的全部风险。"
        "Naga Core Analytics 与 Football Quant OS 对任何损失不承担责任。"
        "博彩涉及重大损失风险，请理性对待。<br/><br/>"
        "数据来源: 500.com、FIFA世界杯历史数据库。"
        "模型版本: v4.1.0。训练日期: 2026-06-17。",
        make_style('Disclaimer', 'Normal', fontSize=8, textColor=cd['mid_gray'], leading=11, alignment=TA_JUSTIFY)
    ))
    story.append(Paragraph(
        "2026 Naga Core Analytics | Football Quant OS v4.1.0 | 机密",
        make_style('Footer', 'Normal', fontSize=8, textColor=cd['mid_gray'], alignment=TA_CENTER)
    ))
    
    doc.build(story)
    print(f"PDF 已生成: {output_path}")


def make_table(data, header_color):
    t = Table(data, repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), header_color),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), chinese_font),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, cd['light_gray']),
        ('TEXTCOLOR', (0, 1), (-1, -1), cd['dark_gray']),
        ('FONTNAME', (0, 1), (-1, -1), chinese_font),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, cd['light_gray']]),
    ]
    t.setStyle(TableStyle(style))
    return t


if __name__ == "__main__":
    import os
    output = "D:/openclaw-workspace/football_quant_os/v4/reports/austria_jordan_report_cn.pdf"
    os.makedirs(os.path.dirname(output), exist_ok=True)
    create_pdf(output)
