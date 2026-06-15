#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""麦肯锡风格6市场预测报告生成器 v2.0"""

import sys, os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 注册字体
_FONTS = {
    'YaHei': r"C:\Windows\Fonts\msyh.ttc",
    'YaHei-Bold': r"C:\Windows\Fonts\msyhbd.ttc",
    'YaHei-Light': r"C:\Windows\Fonts\msyhl.ttc",
}
for name, path in _FONTS.items():
    try:
        pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))
    except:
        pass

# 麦肯锡配色
_MC_BLUE = HexColor('#002B5C')
_MC_LIGHT_BLUE = HexColor('#E8EFF6')
_MC_GRAY = HexColor('#6C757D')
_MC_LIGHT_GRAY = HexColor('#F5F5F5')
_MC_DARK = HexColor('#212529')
_MC_GREEN = HexColor('#006400')
_MC_RED = HexColor('#8B0000')
_MC_GOLD = HexColor('#B8860B')


def _create_styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('MCTitle', fontName='YaHei-Bold', fontSize=22, leading=28, textColor=_MC_BLUE, alignment=TA_LEFT, spaceAfter=3*mm, leftIndent=0))
    s.add(ParagraphStyle('MCSubtitle', fontName='YaHei-Light', fontSize=12, leading=18, textColor=_MC_GRAY, alignment=TA_LEFT, spaceAfter=8*mm, leftIndent=0))
    s.add(ParagraphStyle('MCMeta', fontName='YaHei-Light', fontSize=9, leading=13, textColor=_MC_GRAY, alignment=TA_LEFT, spaceAfter=15*mm, leftIndent=0))
    s.add(ParagraphStyle('MCH1', fontName='YaHei-Bold', fontSize=14, leading=20, textColor=_MC_BLUE, spaceBefore=10*mm, spaceAfter=5*mm, leftIndent=0, bottomPadding=2*mm, topPadding=2*mm))
    s.add(ParagraphStyle('MCH2', fontName='YaHei-Bold', fontSize=11, leading=16, textColor=_MC_DARK, spaceBefore=6*mm, spaceAfter=3*mm, leftIndent=0))
    s.add(ParagraphStyle('MCH3', fontName='YaHei-Bold', fontSize=10, leading=15, textColor=_MC_GRAY, spaceBefore=4*mm, spaceAfter=2*mm, leftIndent=0))
    s.add(ParagraphStyle('MCBody', fontName='YaHei', fontSize=10, leading=18, textColor=_MC_DARK, alignment=TA_JUSTIFY, spaceAfter=4*mm, leftIndent=0, rightIndent=0))
    s.add(ParagraphStyle('MCBullet', fontName='YaHei', fontSize=10, leading=18, textColor=_MC_DARK, alignment=TA_LEFT, spaceAfter=2*mm, leftIndent=6*mm, firstLineIndent=-6*mm, bulletIndent=0))
    s.add(ParagraphStyle('MCBulletBold', fontName='YaHei-Bold', fontSize=10, leading=18, textColor=_MC_DARK, alignment=TA_LEFT, spaceAfter=2*mm, leftIndent=6*mm, firstLineIndent=-6*mm, bulletIndent=0))
    s.add(ParagraphStyle('MCInsight', fontName='YaHei-Bold', fontSize=11, leading=18, textColor=_MC_BLUE, alignment=TA_LEFT, spaceAfter=6*mm, leftIndent=0, rightIndent=0, backColor=_MC_LIGHT_BLUE, borderPadding=8, topPadding=6, bottomPadding=6, leftPadding=8, rightPadding=8))
    s.add(ParagraphStyle('MCNum', fontName='YaHei-Bold', fontSize=18, leading=24, textColor=_MC_BLUE, alignment=TA_LEFT, spaceAfter=1*mm, leftIndent=0))
    s.add(ParagraphStyle('MCNumLabel', fontName='YaHei', fontSize=9, leading=13, textColor=_MC_GRAY, alignment=TA_LEFT, spaceAfter=4*mm, leftIndent=0))
    s.add(ParagraphStyle('MCSmall', fontName='YaHei-Light', fontSize=8, leading=12, textColor=_MC_GRAY, alignment=TA_LEFT, spaceAfter=2*mm, leftIndent=0))
    s.add(ParagraphStyle('MCDisclaimer', fontName='YaHei-Light', fontSize=8, leading=12, textColor=_MC_GRAY, alignment=TA_LEFT, spaceAfter=1*mm, leftIndent=0))
    s.add(ParagraphStyle('MCWarning', fontName='YaHei', fontSize=10, leading=18, textColor=_MC_RED, alignment=TA_LEFT, spaceAfter=2*mm, leftIndent=6*mm, firstLineIndent=-6*mm, bulletIndent=0))
    s.add(ParagraphStyle('MCValue', fontName='YaHei-Bold', fontSize=10, leading=18, textColor=_MC_GREEN, alignment=TA_LEFT, spaceAfter=2*mm, leftIndent=6*mm, firstLineIndent=-6*mm, bulletIndent=0))
    return s


def _table_style():
    return [
        ('FONTNAME', (0, 0), (-1, -1), 'YaHei'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, -1), _MC_DARK),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]


def _highlight_value(score):
    if score > 0:
        return f'<font color="#006400">+{score:.1f}%</font>'
    elif score < 0:
        return f'<font color="#8B0000">{score:.1f}%</font>'
    return f'{score:.1f}%'


class _McKinseyHeader:
    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(_MC_LIGHT_BLUE)
        canvas.rect(0, doc.height + doc.topMargin - 20, doc.width + doc.leftMargin + doc.rightMargin, 20, fill=1, stroke=0)
        canvas.setFont('YaHei-Bold', 9)
        canvas.setFillColor(_MC_BLUE)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 13, "NAGA QUANTITATIVE")
        canvas.setFont('YaHei-Light', 8)
        canvas.setFillColor(_MC_GRAY)
        canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin - 13, "CONFIDENTIAL")
        canvas.setFont('YaHei-Light', 7)
        canvas.setFillColor(_MC_GRAY)
        canvas.drawString(doc.leftMargin, doc.bottomMargin - 15, f"Page {canvas.getPageNumber()}")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.bottomMargin - 15, f"{datetime.now().strftime('%Y-%m-%d')}")
        canvas.restoreState()


def generate_mckinsey_report(match_type='brazil_morocco'):
    if match_type == 'brazil_morocco':
        output_path = r'C:\Users\Administrator\Desktop\Naga_Report_Brazil_vs_Morocco.pdf'
        home_team, away_team = '巴西', '摩洛哥'
        home_flag, away_flag = '🇧🇷', '🇲🇦'
        mkt_h, mkt_d, mkt_a = 1/1.65, 1/3.78, 1/5.48
        mod_h, mod_d, mod_a = 0.52, 0.28, 0.20
        edge_h, edge_d, edge_a = mod_h - mkt_h, mod_d - mkt_d, mod_a - mkt_a
        summary = '市场隐含巴西胜率 60.6%，但模型评估仅 52.0%，存在 8.6% 定价偏差。巴西被严重高估，摩洛哥方向存在价值投注。'
        insight_quote = '"巴西 1.65 的水配上 83% 的投注量，这不是送钱是送命。摩洛哥10场不败+场均失0.3球，不是来当配角的。"'
        data_1x2 = [['巴西胜', '1.65', '60.6%', '52.0%', _highlight_value(edge_h), '❌ 负价值'],['平局', '3.78', '26.5%', '28.0%', _highlight_value(edge_d), '✅ 价值投注'],['摩洛哥胜', '5.48', '18.2%', '20.0%', _highlight_value(edge_a), '🎯 价值投注']]
        data_ah = [['巴西(-1)胜', '2.80', '35.7%', '35.0%', '-0.7%', '⚠️'],['走水', '3.26', '30.7%', '28.0%', '-2.7%', '❌'],['摩洛哥(+1)胜', '2.15', '46.5%', '55.0%', _highlight_value(+8.5), '🥇 强价值']]
        data_htft = [['巴西/巴西', '32.0%', '最可能，但赔率差'],['平/巴西', '22.0%', '上半场闷住，下半场破局'],['平/平', '15.0%', '🎯 高赔价值'],['摩洛哥/巴西', '8.0%', '摩洛哥先领先，被逆转'],['巴西/平', '8.0%', '巴西领先被扳平'],['平/摩洛哥', '8.0%', '冷门剧本'],['摩洛哥/摩洛哥', '7.0%', '🔥 最大冷门']]
        data_score = [['1:0', '15.0%', '巴西小胜最常见'],['1:1', '13.0%', '🎯 摩洛哥能守'],['2:0', '12.0%', '巴西零封'],['2:1', '11.0%', '对攻剧本'],['0:0', '9.0%', '闷平'],['0:1', '7.0%', '🔥 摩洛哥爆冷']]
        data_goals = [['0球', '9.0%', '摩洛哥铁防+巴西磨合'],['1球', '21.0%', '最可能区间'],['2球', '25.0%', '最可能区间'],['3球', '22.0%', ''],['4球', '15.0%', ''],['5+球', '8.0%', '❌ 不看好']]
        data_ou = [['2.0球', '1.05/0.70', '❌ 盘口太浅'],['2.25球', '0.89/0.89', '🥇 小球 58%'],['2.5球', '1.05+/0.70', '❌ 大球太贵'],['2.5/3球', '0.95/0.95', '🥈 小球 55%']]
        matrix_data = [['P0', '让球', '摩洛哥+1', '2.15', '⭐⭐⭐⭐⭐', 'Kelly最优+15.9%'],['P1', '大小球', '小球 2.25', '0.89', '⭐⭐⭐⭐⭐', '58%概率，摩洛哥铁防'],['P2', '1X2', '平局', '3.78', '⭐⭐⭐⭐', '价值+1.5%，上半场闷'],['P3', '1X2', '摩洛哥胜', '5.48', '⭐⭐⭐', '高赔价值+1.8%'],['P4', '半全场', '平/平', '高赔', '⭐⭐⭐', '上半场闷住概率高'],['P5', '比分', '1:1', '高赔', '⭐⭐⭐', '最可能高赔比分'],['❌', '1X2', '巴西胜', '1.65', '❌', '负价值-8.6%，坚决避开']]
        warnings = ['市场隐含巴西胜率60.6%，但模型仅52.0%，存在8.6%定价偏差。巴西胜为负价值投注。','摩洛哥近10场不败（7胜3平），场均失0.3球，防守数据为历史级别。','投注热度83%流向巴西，但赔率不降反升（1.55→1.65），大热倒灶信号。','CoachFactor: 雷格拉吉CRI 7.4 vs 多里瓦尔6.0，大赛经验碾压（世界杯4强 vs 新帅）。','UpsetDetector: 冷门评分17/100（正常），但存在市场定价错误，不是强冷门但巴西被高估。','所有预测基于概率模型，不代表必然结果。过往表现不代表未来收益。']
        kelly_data = [['摩洛哥+1球', '2.15', '+15.9%', '793 EUR', 'Medium'],['小球 2.25', '0.89', '+8.0%', '400 EUR', 'Low'],['平局', '3.78', '+2.1%', '105 EUR', 'Low'],['摩洛哥胜', '5.48', '+2.1%', '107 EUR', 'High']]
        rec_1x2 = '摩洛哥 不败（双选 平+客胜）或 单选 平局。巴西胜为负价值，应坚决避开。'
        rec_ah = '摩洛哥+1球（Kelly +15.9%，最强价值投注）。摩洛哥10场不败+场均失0.3球，受让赢盘概率极高。'
        rec_htft = '平/平（高赔） | 平/巴西（稳健） | 摩洛哥/巴西（高赔剧本）'
        rec_score = '1:1（高赔价值）| 1:0（最可能）| 0:1（冷门高赔）'
        rec_goals = '1-2球（概率54%）| 摩洛哥近10场场均失0.3球，巴西未必打得穿。'
        rec_ou = '🥇 小球 2.25（58%概率，大球0.89+水位不利）| 最强信号：摩洛哥近10场场均失0.3球。'
        num_dev = '8.6%'
        num_heat = '83%'
        num_upset = '17'
        kelly_suggest = '优先执行摩洛哥+1球（793 EUR），其次叠加小球（400 EUR）。总风险1,193 EUR，在1,500 EUR日风险上限内。'
        
    else:
        output_path = r'C:\Users\Administrator\Desktop\Naga_Report_Haiti_vs_Scotland.pdf'
        home_team, away_team = '海地', '苏格兰'
        home_flag, away_flag = '🇭🇹', '🏴󠁧󠁢󠁳󠁣󠁴󠁿'
        mkt_h, mkt_d, mkt_a = 1/6.92, 1/4.61, 1/1.40
        mod_h, mod_d, mod_a = 0.12, 0.23, 0.65
        edge_h, edge_d, edge_a = mod_h - mkt_h, mod_d - mkt_d, mod_a - mkt_a
        summary = '市场隐含苏格兰胜率 71.4%，但模型评估仅 65.0%，存在 6.4% 定价偏差。苏格兰大热（63%投注+83.1%资金），但赔率从1.33升至1.40，大热升水信号明显。'
        insight_quote = '"苏格兰 1.40 的水配上 63% 的投注量+83%资金流，这不是稳胆是陷阱。海地LWDLWW，不是来散步的。"'
        data_1x2 = [['海地胜', '6.92', '14.5%', '12.0%', _highlight_value(-2.5), '❌ 负价值'],['平局', '4.61', '21.7%', '23.0%', _highlight_value(+1.3), '✅ 价值投注'],['苏格兰胜', '1.40', '71.4%', '65.0%', _highlight_value(-6.4), '❌ 大热负价值']]
        data_ah = [['海地(+1)胜', '2.11', '47.4%', '43.0%', '-4.4%', '⚠️'],['走水', '3.35', '29.9%', '28.0%', '-1.9%', '❌'],['苏格兰(-1)胜', '2.81', '35.6%', '37.0%', _highlight_value(+1.4), '✅ 价值']]
        data_htft = [['苏格兰/苏格兰', '35.0%', '最可能，但赔率差'],['平/苏格兰', '22.0%', '上半场闷住，下半场破局'],['平/平', '12.0%', '🎯 高赔价值'],['海地/苏格兰', '8.0%', '海地先领先，被逆转'],['苏格兰/平', '7.0%', '苏格兰领先被扳平'],['平/海地', '6.0%', '冷门剧本'],['海地/海地', '5.0%', '🔥 最大冷门']]
        data_score = [['0:1', '18.0%', '苏格兰小胜最常见'],['0:0', '12.0%', '🎯 闷平'],['1:1', '11.0%', '✅ 海地能守'],['0:2', '10.0%', '苏格兰零封'],['1:2', '8.0%', '对攻剧本'],['1:0', '6.0%', '🔥 海地爆冷']]
        data_goals = [['0球', '12.0%', '海地铁防+苏格兰磨合'],['1球', '22.0%', '最可能区间'],['2球', '25.0%', '最可能区间'],['3球', '20.0%', ''],['4球', '13.0%', ''],['5+球', '8.0%', '❌ 不看好']]
        data_ou = [['2.5球', '0.75/1.20', '❌ 小球太贵'],['2.5/3球', '0.87/0.95', '🥇 小球 55%'],['3球', '0.78/0.95', '❌ 大球低水诱盘']]
        matrix_data = [['P0', '让球', '海地+1', '2.11', '⭐⭐⭐⭐⭐', '最稳，受让赢盘43%'],['P1', '1X2', '平局', '4.61', '⭐⭐⭐⭐', '价值+1.3%，高赔'],['P2', '大小球', '小球 2.5/3', '0.95', '⭐⭐⭐⭐', '55%概率，低比分'],['P3', '比分', '0:0', '高赔', '⭐⭐⭐', '最可能高赔比分'],['P4', '半全场', '平/平', '高赔', '⭐⭐⭐', '上半场闷住'],['P5', '1X2', '海地胜', '6.92', '⭐⭐', '高赔博冷门'],['❌', '1X2', '苏格兰胜', '1.40', '❌', '负价值-6.4%，大热避开']]
        warnings = ['市场隐含苏格兰胜率71.4%，但模型仅65.0%，存在6.4%定价偏差。苏格兰大热，应避开单胜。','投注热度63%流向苏格兰，资金热度83.1%，但赔率从1.33升至1.40，大热升水信号。','庄家盈亏指数：苏格兰-30（赔付压力大），海地+41（庄家希望海地赢）。','海地近6场LWDLWW，状态不稳定但偶有爆冷能力。苏格兰WWLLWL，起伏大。','海地FIFA排名较低，但苏格兰并非传统强队，世界杯小组赛偶然性高。','所有预测基于概率模型，不代表必然结果。过往表现不代表未来收益。']
        kelly_data = [['海地+1球', '2.11', '+5.2%', '260 EUR', 'Low'],['小球 2.5/3', '0.95', '+4.0%', '200 EUR', 'Low'],['平局', '4.61', '+1.8%', '90 EUR', 'High'],['海地胜', '6.92', '+0.8%', '40 EUR', 'High']]
        rec_1x2 = '平局（价值+1.3%，高赔4.61）| 海地 不败（双选 平+主胜，博高赔）| 苏格兰胜为负价值-6.4%，大热应避开。'
        rec_ah = '海地+1球（最稳，受让赢盘概率43%）。海地近6场偶有爆冷，苏格兰状态起伏，受让安全。'
        rec_htft = '平/平（高赔） | 平/苏格兰（稳健） | 海地/苏格兰（高赔剧本）'
        rec_score = '0:0（高赔价值）| 0:1（最可能）| 1:1（冷门高赔）'
        rec_goals = '1-2球（概率47%）| 海地防守不稳定但苏格兰进攻效率一般，低比分概率高。'
        rec_ou = '🥇 小球 2.5/3（55%概率，大小球平均2.61）| 低比分格局。'
        num_dev = '6.4%'
        num_heat = '83%'
        num_upset = '22'
        kelly_suggest = '优先执行海地+1球（260 EUR），其次叠加小球（200 EUR）。总风险460 EUR，远低于1,500 EUR日风险上限。'

    styles = _create_styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=25*mm, leftMargin=25*mm, topMargin=30*mm, bottomMargin=20*mm)
    story = []

    # 封面
    story.append(Spacer(1, 20*mm))
    story.append(Paragraph(f"{home_flag} {home_team} vs {away_team} {away_flag}", styles['MCTitle']))
    story.append(Paragraph("2026 FIFA 世界杯小组赛 | 第1轮", styles['MCSubtitle']))
    story.append(Paragraph(f"Football Quant OS v4.2.1 | 麦肯锡风格量化报告 | {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['MCMeta']))
    story.append(HRFlowable(width="100%", thickness=0.5, color=_MC_GRAY, spaceBefore=10*mm, spaceAfter=10*mm))

    # 执行摘要
    story.append(Paragraph("EXECUTIVE SUMMARY", styles['MCH1']))
    story.append(Paragraph(summary, styles['MCBody']))
    story.append(Spacer(1, 3*mm))
    
    # 核心数字
    story.append(Paragraph(f'<font color="#002B5C">{num_dev}</font>', styles['MCNum']))
    story.append(Paragraph("定价偏差（被高估方）", styles['MCNumLabel']))
    story.append(Paragraph(f'<font color="#002B5C">{num_heat}</font>', styles['MCNum']))
    story.append(Paragraph("投注热度（大热倒灶信号）", styles['MCNumLabel']))
    story.append(Paragraph(f'<font color="#002B5C">{num_upset}</font>', styles['MCNum']))
    story.append(Paragraph("冷门评分（UpsetDetector）", styles['MCNumLabel']))
    story.append(Spacer(1, 5*mm))

    # 关键洞察框
    story.append(Paragraph(f'核心洞察：{insight_quote}', styles['MCInsight']))
    story.append(Spacer(1, 5*mm))

    # 1X2
    story.append(Paragraph("1. 胜平负 (1X2)", styles['MCH1']))
    story.append(Paragraph("市场隐含概率 vs 模型概率对比", styles['MCH2']))
    t = Table(data_1x2, colWidths=[25*mm, 20*mm, 25*mm, 25*mm, 25*mm, 25*mm])
    t.setStyle(TableStyle(_table_style() + [('BACKGROUND', (0, 0), (-1, 0), _MC_LIGHT_BLUE),('FONTNAME', (0, 0), (-1, 0), 'YaHei-Bold'),('TEXTCOLOR', (0, 0), (-1, 0), _MC_BLUE),('GRID', (0, 0), (-1, -1), 0.5, _MC_LIGHT_GRAY)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f'• <b>推荐：</b>{rec_1x2}', styles['MCValue']))
    story.append(Spacer(1, 3*mm))

    # 让球
    story.append(Paragraph("2. 让球胜平负", styles['MCH1']))
    story.append(Paragraph(f"{home_team} +1球" if match_type=='haiti_scotland' else f"{away_team} +1球", styles['MCH2']))
    t = Table(data_ah, colWidths=[30*mm, 20*mm, 25*mm, 25*mm, 25*mm, 25*mm])
    t.setStyle(TableStyle(_table_style() + [('BACKGROUND', (0, 0), (-1, 0), _MC_LIGHT_BLUE),('FONTNAME', (0, 0), (-1, 0), 'YaHei-Bold'),('TEXTCOLOR', (0, 0), (-1, 0), _MC_BLUE),('GRID', (0, 0), (-1, -1), 0.5, _MC_LIGHT_GRAY)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f'• <b>推荐：</b>{rec_ah}', styles['MCValue']))
    story.append(Spacer(1, 3*mm))

    # 半全场
    story.append(Paragraph("3. 半全场 (HT/FT)", styles['MCH1']))
    story.append(Paragraph("上半场/下半场结果组合概率", styles['MCH2']))
    t = Table(data_htft, colWidths=[45*mm, 25*mm, 80*mm])
    t.setStyle(TableStyle(_table_style() + [('BACKGROUND', (0, 0), (-1, 0), _MC_LIGHT_BLUE),('FONTNAME', (0, 0), (-1, 0), 'YaHei-Bold'),('TEXTCOLOR', (0, 0), (-1, 0), _MC_BLUE),('GRID', (0, 0), (-1, -1), 0.5, _MC_LIGHT_GRAY)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f'• <b>推荐：</b>{rec_htft}', styles['MCValue']))
    story.append(Spacer(1, 3*mm))

    # 比分
    story.append(Paragraph("4. 比分预测", styles['MCH1']))
    story.append(Paragraph("Correct Score 概率分布（TOP6）", styles['MCH2']))
    t = Table(data_score, colWidths=[20*mm, 25*mm, 105*mm])
    t.setStyle(TableStyle(_table_style() + [('BACKGROUND', (0, 0), (-1, 0), _MC_LIGHT_BLUE),('FONTNAME', (0, 0), (-1, 0), 'YaHei-Bold'),('TEXTCOLOR', (0, 0), (-1, 0), _MC_BLUE),('GRID', (0, 0), (-1, -1), 0.5, _MC_LIGHT_GRAY)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f'• <b>推荐：</b>{rec_score}', styles['MCValue']))
    story.append(Spacer(1, 3*mm))

    # 进球数
    story.append(Paragraph("5. 进球数", styles['MCH1']))
    story.append(Paragraph("Total Goals 概率分布", styles['MCH2']))
    t = Table(data_goals, colWidths=[25*mm, 25*mm, 100*mm])
    t.setStyle(TableStyle(_table_style() + [('BACKGROUND', (0, 0), (-1, 0), _MC_LIGHT_BLUE),('FONTNAME', (0, 0), (-1, 0), 'YaHei-Bold'),('TEXTCOLOR', (0, 0), (-1, 0), _MC_BLUE),('GRID', (0, 0), (-1, -1), 0.5, _MC_LIGHT_GRAY)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f'• <b>推荐：</b>{rec_goals}', styles['MCValue']))
    story.append(Spacer(1, 3*mm))

    # 大小球
    story.append(Paragraph("6. 大小球", styles['MCH1']))
    story.append(Paragraph("Over/Under 盘口分析", styles['MCH2']))
    t = Table(data_ou, colWidths=[25*mm, 30*mm, 95*mm])
    t.setStyle(TableStyle(_table_style() + [('BACKGROUND', (0, 0), (-1, 0), _MC_LIGHT_BLUE),('FONTNAME', (0, 0), (-1, 0), 'YaHei-Bold'),('TEXTCOLOR', (0, 0), (-1, 0), _MC_BLUE),('GRID', (0, 0), (-1, -1), 0.5, _MC_LIGHT_GRAY)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f'• <b>推荐：</b>{rec_ou}', styles['MCValue']))
    story.append(Spacer(1, 3*mm))

    # 综合策略矩阵
    story.append(PageBreak())
    story.append(Paragraph("综合策略矩阵", styles['MCH1']))
    t = Table(matrix_data, colWidths=[15*mm, 22*mm, 30*mm, 20*mm, 22*mm, 55*mm])
    t.setStyle(TableStyle(_table_style() + [('BACKGROUND', (0, 0), (-1, 0), _MC_LIGHT_BLUE),('FONTNAME', (0, 0), (-1, 0), 'YaHei-Bold'),('TEXTCOLOR', (0, 0), (-1, 0), _MC_BLUE),('GRID', (0, 0), (-1, -1), 0.5, _MC_LIGHT_GRAY)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))

    # Kelly资金管理
    story.append(Paragraph("Kelly 资金配置方案", styles['MCH1']))
    story.append(Paragraph('<b>资金池：</b>10,000 EUR | <b>最大日风险：</b>1,500 EUR (15%) | <b>标准注码：</b>200 EUR (2%)', styles['MCBody']))
    t = Table(kelly_data, colWidths=[30*mm, 20*mm, 25*mm, 30*mm, 35*mm])
    t.setStyle(TableStyle(_table_style() + [('BACKGROUND', (0, 0), (-1, 0), _MC_LIGHT_BLUE),('FONTNAME', (0, 0), (-1, 0), 'YaHei-Bold'),('TEXTCOLOR', (0, 0), (-1, 0), _MC_BLUE),('GRID', (0, 0), (-1, -1), 0.5, _MC_LIGHT_GRAY)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f'<b>建议：</b>{kelly_suggest}', styles['MCBody']))
    story.append(Spacer(1, 3*mm))

    # 风险提示
    story.append(Paragraph("风险提示", styles['MCH1']))
    for w in warnings:
        story.append(Paragraph(f'• {w}', styles['MCWarning']))
    story.append(Spacer(1, 3*mm))

    # 免责声明
    story.append(HRFlowable(width="100%", thickness=0.5, color=_MC_LIGHT_GRAY, spaceBefore=5*mm, spaceAfter=5*mm))
    story.append(Paragraph("免责声明", styles['MCH2']))
    story.append(Paragraph("本报告仅供研究参考，不构成任何投资建议或财务建议。博彩涉及高风险，可能导致资金损失。过往表现不代表未来收益。请根据自身财务状况理性决策，切勿投入超出承受能力的资金。", styles['MCDisclaimer']))
    story.append(Paragraph("Naga Quantitative Investment System v5.0 | Football Quant OS v4.2.1 | Generated by Naga Core", styles['MCDisclaimer']))

    doc.build(story, onFirstPage=_McKinseyHeader(), onLaterPages=_McKinseyHeader())
    return output_path


if __name__ == '__main__':
    generate_mckinsey_report('brazil_morocco')
    generate_mckinsey_report('haiti_scotland')
    print('两份麦肯锡风格PDF已生成')
