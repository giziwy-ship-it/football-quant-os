#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
McKinsey 风格 PDF 报告生成器（中文版）
USA vs Paraguay - 2026 世界杯分析报告
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, HRFlowable
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import os

# 注册中文字体
pdfmetrics.registerFont(TTFont('SimHei', 'C:\\Windows\\Fonts\\simhei.ttf'))
pdfmetrics.registerFont(TTFont('SimKai', 'C:\\Windows\\Fonts\\simkai.ttf'))

# 桌面路径
DESKTOP = os.path.join(os.path.expanduser('~'), 'Desktop')
OUTPUT_FILE = os.path.join(DESKTOP, "USA_vs_Paraguay_分析报告_2026世界杯.pdf")

MCKINSEY_BLUE = colors.HexColor("#003366")
MCKINSEY_LIGHT_BLUE = colors.HexColor("#E6EEF7")
MCKINSEY_ACCENT = colors.HexColor("#0055A4")
MCKINSEY_GRAY = colors.HexColor("#666666")
MCKINSEY_LIGHT_GRAY = colors.HexColor("#F5F5F5")
MCKINSEY_DARK_GRAY = colors.HexColor("#333333")

def create_styles():
    styles = getSampleStyleSheet()
    
    styles.add(ParagraphStyle(
        name='McKinseyTitle',
        fontName='SimHei',
        fontSize=26,
        textColor=MCKINSEY_BLUE,
        spaceAfter=12,
        leading=32,
        alignment=TA_LEFT
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseySubtitle',
        fontName='SimHei',
        fontSize=14,
        textColor=MCKINSEY_GRAY,
        spaceAfter=20,
        leading=18,
        alignment=TA_LEFT
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseySection',
        fontName='SimHei',
        fontSize=16,
        textColor=MCKINSEY_BLUE,
        spaceBefore=20,
        spaceAfter=10,
        leading=20,
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseySubsection',
        fontName='SimHei',
        fontSize=12,
        textColor=MCKINSEY_DARK_GRAY,
        spaceBefore=14,
        spaceAfter=6,
        leading=16
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyBody',
        fontName='SimHei',
        fontSize=10,
        textColor=MCKINSEY_DARK_GRAY,
        spaceAfter=8,
        leading=14,
        alignment=TA_JUSTIFY
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyBullet',
        fontName='SimHei',
        fontSize=10,
        textColor=MCKINSEY_DARK_GRAY,
        spaceAfter=6,
        leading=14,
        leftIndent=15,
        bulletIndent=5,
        bulletFontName='SimHei',
        bulletFontSize=10,
        bulletColor=MCKINSEY_ACCENT
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyInsight',
        fontName='SimHei',
        fontSize=11,
        textColor=MCKINSEY_BLUE,
        spaceAfter=10,
        leading=16,
        leftIndent=10,
        rightIndent=10,
        borderWidth=1,
        borderColor=MCKINSEY_ACCENT,
        borderPadding=10,
        backColor=MCKINSEY_LIGHT_BLUE
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyTableHeader',
        fontName='SimHei',
        fontSize=9,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=12
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyTableCell',
        fontName='SimHei',
        fontSize=9,
        textColor=MCKINSEY_DARK_GRAY,
        alignment=TA_CENTER,
        leading=12
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyFooter',
        fontName='SimHei',
        fontSize=8,
        textColor=MCKINSEY_GRAY,
        alignment=TA_CENTER
    ))
    
    return styles

def blue_header_bar(width=520):
    return HRFlowable(width=width, thickness=3, color=MCKINSEY_BLUE, spaceBefore=0, spaceAfter=15)

def create_table(data, col_widths, header_bg=MCKINSEY_BLUE, alternate_row=True):
    table = Table(data, colWidths=col_widths, repeatRows=1)
    style_commands = [
        ('BACKGROUND', (0, 0), (-1, 0), header_bg),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'SimHei'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]
    if alternate_row:
        for i in range(1, len(data)):
            if i % 2 == 0:
                style_commands.append(('BACKGROUND', (0, i), (-1, i), MCKINSEY_LIGHT_GRAY))
    style_commands.append(('FONTNAME', (0, 1), (-1, -1), 'SimHei'))
    style_commands.append(('FONTSIZE', (0, 1), (-1, -1), 9))
    table.setStyle(TableStyle(style_commands))
    return table

def build_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = create_styles()
    story = []
    
    # 封面页
    story.append(Spacer(1, 30))
    story.append(Paragraph("2026 国际足联世界杯", styles['McKinseyTitle']))
    story.append(blue_header_bar())
    story.append(Paragraph("比赛分析：美国 vs 巴拉圭", styles['McKinseySubtitle']))
    story.append(Spacer(1, 10))
    
    meta_data = [
        ['比赛', '美国 vs 巴拉圭'],
        ['小组', 'D 组'],
        ['轮次', '第一轮'],
        ['日期', '2026年6月13日'],
        ['时间', '09:00 (GMT+8)'],
        ['场地', '美国（东道主）'],
    ]
    meta_table = Table(meta_data, colWidths=[120, 300])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), MCKINSEY_LIGHT_BLUE),
        ('TEXTCOLOR', (0, 0), (0, -1), MCKINSEY_BLUE),
        ('FONTNAME', (0, 0), (-1, -1), 'SimHei'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))
    story.append(Paragraph(
        f"<b>报告生成时间：</b>{datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"<b>系统：</b>Naga Core 足球量化系统 v2.0 | "
        f"<b>数据来源：</b>500.com、FIFA、历史数据",
        styles['McKinseyBody']
    ))
    story.append(PageBreak())
    
    # 执行摘要
    story.append(Paragraph("执行摘要", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "美国作为2026年世界杯东道主，在D组首轮迎战巴拉圭。虽然美国拥有24位的FIFA排名优势（#17 vs #41），"
        "但市场信号显示公众存在严重过度自信——77.9%的投注量集中在美国，而公平赔率仅隐含46%的胜率。",
        styles['McKinseyBody']
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "核心洞察：市场呈现「赔率逆向」模式——大量投注流向美国（77.9%），但赔率并未相应压缩（2.05），"
        "表明庄家可能在定价防守风险。美国近期状态显示防守脆弱（场均失1.7球），而巴拉圭的紧凑防守和"
        "反击能力构成了可信的冷门威胁。",
        styles['McKinseyInsight']
    ))
    story.append(Spacer(1, 10))
    
    summary_data = [
        ['指标', '美国', '巴拉圭', '评估'],
        ['FIFA排名', '#17 (1671分)', '#41 (1505分)', '美国优势'],
        ['近期状态', '5胜1平4负', '4胜2平4负', '持平'],
        ['主场优势', '东道主', '客场', '美国强优势'],
        ['市场资金流向', '77.9% 投注', '9.4% 投注', '市场扭曲'],
        ['防守（场均失球）', '1.7', '1.0', '巴拉圭优势'],
        ['进攻（场均进球）', '1.8', '1.2', '美国优势'],
        ['冷门雷达评分', '48/100', '—', '正常风险'],
    ]
    summary_table = create_table(summary_data, [130, 110, 110, 110])
    story.append(summary_table)
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "<b>结论：</b>美国是合理的热门，但市场已过度定价其概率。最优风险调整后的策略是："
        "不投注，或小额价值投注巴拉圭 @3.83，鉴于美国近期友谊赛暴露的防守漏洞。",
        styles['McKinseyBody']
    ))
    story.append(PageBreak())
    
    # 六维分析
    story.append(Paragraph("六维深度分析", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    
    dimensions = [
        ("1. ELO 评分与 FIFA 排名",
         "美国拥有24位的FIFA排名优势（#17 vs #41），分差166分（1671 vs 1505）。ELO模型估算美国胜率约58%。"
         "然而，世界杯揭幕战中20-30位的排名差距 historically 产生冷门的概率为18%。"),
        ("2. 近期状态与表现",
         "美国近10场：5胜1平4负，场均进1.8球、失1.7球。巴拉圭近10场：4胜2平4负，场均进1.2球、失1.0球。"
         "值得注意的是，巴拉圭近期状态实际上更好（近5场3胜1平1负 vs 美国2胜3负）。"
         "美国防守记录令人担忧——10场友谊赛失17球。"),
        ("3. 主场优势与战意",
         "世界杯东道主在揭幕战中的历史胜率为72%。美国战意评分：0.95/1.0。巴拉圭作为弱旅心态压力较小，"
         "战意评分：0.85/1.0。旅行疲劳有利于美国（零旅行 vs 南美长途飞行）。"),
        ("4. 市场信号与资金流向",
         "500.com实时数据（07:28 GMT+8）：77.9%投注量在美国，9.4%在巴拉圭。赔率隐含概率：46.0%美国，24.7%巴拉圭。"
         "+31.9%的流向-概率差距形成「赔率逆向」信号。庄家盈亏暴露：美国胜-1550万港币，巴拉圭胜+1420万港币。"),
        ("5. 伤病与阵容实力",
         "美国：蒂莫西·维阿（右翼，尤文图斯）受伤——减少宽度和进攻多样性。关键球员：普利西奇、麦肯尼、巴洛贡、亚当斯。"
         "巴拉圭：无重大伤病。关键球员：阿尔米隆、恩西索、萨纳夫里亚、戈麦斯。巴拉圭阵容防守经验更丰富。"),
        ("6. 历史交锋与战术对位",
         "近5次交锋：美国3胜2负，总进球5-5。最近一次：美国2:1巴拉圭（2025年11月）。"
         "战术博弈：美国高位逼抢 vs 巴拉圭紧凑反击。关键弱点：美国防线（1.7场均失球）易被速度冲击——"
         "阿尔米隆和恩西索是理想的武器。巴拉圭的防守稳固性（1.0场均失球）vs 美国进攻是决定性对位。")
    ]
    for title, text in dimensions:
        story.append(Paragraph(title, styles['McKinseySubsection']))
        story.append(Paragraph(text, styles['McKinseyBody']))
        story.append(Spacer(1, 5))
    story.append(PageBreak())
    
    # 市场情报
    story.append(Paragraph("市场情报", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "500.com（亚洲最大博彩交易所）实时数据，采集于07:28 GMT+8，开赛前约1.5小时。总交易量：2330万港币。",
        styles['McKinseyBody']
    ))
    story.append(Spacer(1, 10))
    
    market_data = [
        ['结果', '赔率', '隐含概率', '投注比例', '必发成交量', '庄家盈亏', '冷热指数'],
        ['美国胜', '2.05', '46.0%', '77.9%', '1815万港币', '-1553万港币', '69 (热)'],
        ['平局', '3.23', '29.3%', '12.8%', '298万港币', '+1347万港币', '-57 (冷)'],
        ['巴拉圭胜', '3.83', '24.7%', '9.4%', '218万港币', '+1416万港币', '-62 (冷)'],
    ]
    market_table = create_table(market_data, [70, 50, 65, 65, 80, 85, 65])
    story.append(market_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("市场信号分析", styles['McKinseySubsection']))
    signals = [
        "<b>赔率逆向信号（15/20）：</b>77.9%投注量在美国，但赔率仍维持2.05（隐含46%）。有效市场中，此流量应压缩赔率至~1.70。",
        "<b>异常资金流（12/15）：</b>投注极度不平衡（77.9% vs 9.4%）。历史上，世界杯揭幕战>70%不平衡产生冷门的概率为22%。",
        "<b>庄家风险暴露：</b>美国胜的-1550万港币盈亏表明庄家风险巨大。若巴拉圭胜，庄家获利+1416万港币。",
        "<b>成交量激增：</b>总成交量一夜之间增长126%（1030万→2330万港币），多数集中在美国，显示散户资金。",
    ]
    for signal in signals:
        story.append(Paragraph(signal, styles['McKinseyBullet'], bulletText='•'))
    story.append(PageBreak())
    
    # 完整预测
    story.append(Paragraph("完整预测", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("1. 胜平负（1X2）", styles['McKinseySubsection']))
    x2_data = [
        ['结果', '模型概率', '公平赔率', '市场赔率', '优势', '建议'],
        ['美国胜', '46.4%', '2.16', '2.05', '-5.1%', '无价值'],
        ['平局', '24.9%', '4.02', '3.23', '-19.7%', '无价值'],
        ['巴拉圭胜', '28.7%', '3.48', '3.83', '+10.1%', '轻微价值'],
    ]
    story.append(create_table(x2_data, [70, 65, 65, 65, 55, 75]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("2. 让球胜平负（亚盘）", styles['McKinseySubsection']))
    ah_data = [
        ['盘口', '美国赢盘', '走水', '美国输盘', '建议'],
        ['美国 -1', '24.1%', '22.6%', '53.3%', '避免'],
        ['美国 -0.5', '46.4%', '—', '53.6%', '避免'],
        ['平手 (0)', '46.4%', '24.9%', '28.7%', '中性'],
        ['美国 +0.5', '71.3%', '—', '28.7%', '安全'],
        ['美国 +1', '88.3%', '16.9%', '11.7%', '保守'],
    ]
    story.append(create_table(ah_data, [90, 65, 50, 65, 100]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("3. 半全场", styles['McKinseySubsection']))
    htft_data = [
        ['半场/全场', '描述', '概率'],
        ['平/美国', '半场平 → 美国胜', '19.2%'],
        ['美国/美国', '半场美国领先 → 美国胜', '17.1%'],
        ['平/巴拉圭', '半场平 → 巴拉圭胜', '11.9%'],
        ['美国/巴拉圭', '半场美国领先 → 巴拉圭逆转（冷门）', '10.6%'],
        ['平/平', '全场平局', '10.3%'],
    ]
    story.append(create_table(htft_data, [70, 230, 70]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("4. 比分（前10）", styles['McKinseySubsection']))
    score_data = [
        ['排名', '比分', '概率', '累计'],
        ['1', '1:1', '11.7%', '11.7%'],
        ['2', '1:0', '9.7%', '21.4%'],
        ['3', '2:1', '9.3%', '30.7%'],
        ['4', '2:0', '7.8%', '38.5%'],
        ['5', '0:1', '7.3%', '45.8%'],
        ['6', '1:2', '7.0%', '52.8%'],
        ['7', '0:0', '6.1%', '58.9%'],
        ['8', '2:2', '5.6%', '64.5%'],
        ['9', '3:1', '5.0%', '69.5%'],
        ['10', '0:2', '4.4%', '73.9%'],
    ]
    story.append(create_table(score_data, [45, 60, 70, 70]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("5. 总进球与大小球", styles['McKinseySubsection']))
    ou_data = [
        ['盘口', '大球概率', '小球概率', '预期进球', '建议'],
        ['大1.5', '76.9%', '23.1%', '—', '大'],
        ['大2.0', '65.0%', '35.0%', '—', '大'],
        ['大2.5', '53.1%', '46.9%', '2.8球', '边缘大'],
        ['大3.0', '41.9%', '58.1%', '—', '小'],
        ['大3.5', '30.8%', '69.2%', '—', '小'],
    ]
    story.append(create_table(ou_data, [70, 65, 65, 70, 95]))
    story.append(PageBreak())
    
    # 冷门雷达
    story.append(Paragraph("冷门雷达分析（UpsetDetector v1.0）", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "UpsetDetector v1.0 算法评估七个因子，满分100分。>80分 = 强冷门信号；60-80分 = 密切关注；<60分 = 正常风险。",
        styles['McKinseyBody']
    ))
    story.append(Spacer(1, 10))
    
    upset_data = [
        ['因子', '得分', '满分', '信号强度', '关键驱动'],
        ['豪门热度过高', '10.0', '20', '中等', '加拿大热度高于美国'],
        ['赔率逆向波动', '15.0', '20', '强', '77.9%流向 vs 46%隐含概率'],
        ['异常资金流', '12.0', '15', '强', '投注极度不平衡'],
        ['伤病隐患', '2.0', '15', '低', '维阿受伤（中等影响）'],
        ['ELO高估', '5.0', '10', '中等', '排名差距未完全合理化'],
        ['xG低估', '4.0', '10', '低', '美国xG 1.6 vs 巴拉圭 1.2'],
        ['战意差异', '0.0', '10', '无', '双方战意都很高'],
    ]
    story.append(create_table(upset_data, [90, 45, 35, 70, 140]))
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "<b>总分：48.0/100 — 正常风险</b><br/><br/>"
        "分数远低于80分的「冷门候选」阈值。虽然赔率逆向和异常资金流信号较强（合计27/35），"
        "但缺乏ELO高估、重大伤病或战意不对称等因素，使整体风险保持在正常范围。",
        styles['McKinseyBody']
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>与加拿大-波黑对比：</b>加拿大vs波黑评分49/100，略高（哲科受伤+7分、豪门热度+10分）。"
        "两场比赛均显示赔率逆向模式，但均未达到冷门候选。",
        styles['McKinseyInsight']
    ))
    story.append(PageBreak())
    
    # 战略建议
    story.append(Paragraph("战略建议", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "基于六维分析、市场情报和冷门雷达评分，提供三级建议方案。",
        styles['McKinseyBody']
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("方案一：保守型（低风险）", styles['McKinseySubsection']))
    rec1 = [
        "<b>主选：</b>美国 +0.5（亚盘）约1.50 — 71.4%不败概率",
        "<b>次选：</b>小2.5球 约1.85 — 46.9%概率，预期进球2.8显示边缘",
        "<b>仓位：</b>资金1.0%（Kelly准则：1X2负优势→0%）",
        "<b>逻辑：</b>东道主揭幕战历史胜率72%；+0.5包含平局保险",
    ]
    for r in rec1:
        story.append(Paragraph(r, styles['McKinseyBullet'], bulletText='•'))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("方案二：平衡型（中等风险）", styles['McKinseySubsection']))
    rec2 = [
        "<b>主选：</b>美国胜（1X2）2.05 — 模型46.4%，无优势",
        "<b>次选：</b>精确比分 2:1 约8.00 — 9.3%概率，高方差",
        "<b>仓位：</b>资金0.5%（Kelly：负优势，不建议）",
        "<b>逻辑：</b>美国是合理热门，但市场无价值。仅娱乐投注",
    ]
    for r in rec2:
        story.append(Paragraph(r, styles['McKinseyBullet'], bulletText='•'))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("方案三：激进型（价值寻找）", styles['McKinseySubsection']))
    rec3 = [
        "<b>主选：</b>巴拉圭胜 3.83 — 模型28.7%，市场24.7%，+10.1%优势",
        "<b>次选：</b>巴拉圭 +0.5（亚盘）约1.90 — 53.6%不败概率",
        "<b>仓位：</b>资金0.3%（Kelly：10%优势、23%概率→0.27%）",
        "<b>逻辑：</b>唯一正优势的投注。美国防守（1.7场均失球）易受反击",
    ]
    for r in rec3:
        story.append(Paragraph(r, styles['McKinseyBullet'], bulletText='•'))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph(
        "<b>最终结论：</b>美国是合理热门，但市场已过度定价其概率。最优风险调整后策略是："
        "不投注，或小额价值投注巴拉圭 @3.83。「赔率逆向」信号表明庄家在定价防守风险，"
        "为弱队创造了非对称价值。",
        styles['McKinseyInsight']
    ))
    story.append(Spacer(1, 20))
    
    # 页脚
    story.append(Paragraph("—", styles['McKinseyBody']))
    story.append(Paragraph(
        f"<b>Naga Core 足球量化系统 v2.0</b> | 生成时间 {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        "数据来源：500.com、FIFA、历史数据 | 机密与专有",
        styles['McKinseyFooter']
    ))
    
    doc.build(story)
    print(f"PDF已生成：{filename}")

if __name__ == "__main__":
    build_pdf(OUTPUT_FILE)
