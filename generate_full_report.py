#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整6市场预测报告生成器"""

import sys, os
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
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

# 配色
_BLUE = HexColor('#003366')
_DARK_BLUE = HexColor('#001a33')
_GRAY = HexColor('#666666')
_LIGHT_GRAY = HexColor('#999999')
_DARK_GRAY = HexColor('#333333')
_ACCENT_RED = HexColor('#CC0000')
_GREEN = HexColor('#006600')
_GOLD = HexColor('#B8860B')
_TABLE_HEADER = HexColor('#E8EEF4')
_VALUE_BG = HexColor('#E8F5E9')
_RISK_BG = HexColor('#FFF3CD')


def _create_styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('RTitle', fontName='YaHei-Bold', fontSize=26, leading=32, textColor=_BLUE, alignment=TA_CENTER, spaceAfter=4*mm))
    s.add(ParagraphStyle('RSub', fontName='YaHei', fontSize=14, leading=20, textColor=_GRAY, alignment=TA_CENTER, spaceAfter=2*mm))
    s.add(ParagraphStyle('RMeta', fontName='YaHei-Light', fontSize=9, leading=13, textColor=_LIGHT_GRAY, alignment=TA_CENTER, spaceAfter=6*mm))
    s.add(ParagraphStyle('RH1', fontName='YaHei-Bold', fontSize=16, leading=22, textColor=_DARK_BLUE, spaceBefore=8*mm, spaceAfter=4*mm, backColor=_TABLE_HEADER, leftIndent=3*mm, rightIndent=3*mm, topPadding=2*mm, bottomPadding=2*mm))
    s.add(ParagraphStyle('RH2', fontName='YaHei-Bold', fontSize=13, leading=19, textColor=_BLUE, spaceBefore=6*mm, spaceAfter=3*mm))
    s.add(ParagraphStyle('RH3', fontName='YaHei-Bold', fontSize=11, leading=17, textColor=_DARK_GRAY, spaceBefore=4*mm, spaceAfter=2*mm))
    s.add(ParagraphStyle('RBody', fontName='YaHei', fontSize=10.5, leading=16, textColor=_DARK_GRAY, alignment=TA_LEFT, spaceAfter=2*mm))
    s.add(ParagraphStyle('RSmall', fontName='YaHei', fontSize=9, leading=14, textColor=_GRAY, alignment=TA_LEFT, spaceAfter=1*mm))
    s.add(ParagraphStyle('RWarning', fontName='YaHei-Bold', fontSize=10, leading=15, textColor=_ACCENT_RED, alignment=TA_LEFT, spaceAfter=2*mm))
    s.add(ParagraphStyle('RValue', fontName='YaHei-Bold', fontSize=10, leading=15, textColor=_GREEN, alignment=TA_LEFT, spaceAfter=2*mm))
    s.add(ParagraphStyle('RDisclaimer', fontName='YaHei-Light', fontSize=8, leading=12, textColor=_LIGHT_GRAY, alignment=TA_LEFT, spaceAfter=2*mm))
    return s


def _table_style():
    return [
        ('FONTNAME', (0, 0), (-1, -1), 'YaHei'),
        ('FONTSIZE', (0, 0), (-1, -1), 9.5),
        ('TEXTCOLOR', (0, 0), (-1, -1), _DARK_GRAY),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, _LIGHT_GRAY),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('BACKGROUND', (0, 0), (-1, 0), _TABLE_HEADER),
        ('FONTNAME', (0, 0), (-1, 0), 'YaHei-Bold'),
        ('TEXTCOLOR', (0, 0), (-1, 0), _BLUE),
    ]


def _highlight_value(score):
    if score > 0:
        return f'<font color="#006600">+{score:.1f}%</font>'
    elif score < 0:
        return f'<font color="#CC0000">{score:.1f}%</font>'
    return f'{score:.1f}%'


class _Header:
    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(_DARK_BLUE)
        canvas.rect(0, doc.height + doc.topMargin - 12, doc.width + doc.leftMargin + doc.rightMargin, 12, fill=1, stroke=0)
        canvas.setFont('YaHei-Light', 8)
        canvas.setFillColor(_LIGHT_GRAY)
        canvas.drawString(doc.leftMargin, doc.bottomMargin - 18, f"Naga Quantitative | Confidential | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        canvas.drawRightString(doc.width + doc.leftMargin, doc.bottomMargin - 18, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()


def generate_full_report():
    output_path = r'C:\Users\Administrator\Desktop\Naga_Report_Brazil_vs_Morocco.pdf'
    styles = _create_styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=22*mm, bottomMargin=18*mm)
    story = []

    # ===== 封面 =====
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph("NAGA 量化投资决策报告", styles['RTitle']))
    story.append(Paragraph("巴西 vs 摩洛哥", styles['RSub']))
    story.append(Paragraph("2026 FIFA 世界杯小组赛 | 第1轮", styles['RSub']))
    story.append(Paragraph("Football Quant OS v4.2.1 | 六维预测引擎 | 2026-06-14 05:48", styles['RMeta']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_BLUE, spaceBefore=5*mm, spaceAfter=5*mm))

    # ===== 系统摘要 =====
    story.append(Paragraph("系统分析摘要", styles['RH1']))
    story.append(Paragraph('<b>核心发现：</b>市场隐含巴西胜率 60.6%，但模型评估仅 52.0%，存在 <b>8.6% 定价偏差</b>。巴西被严重高估，摩洛哥方向存在价值投注机会。', styles['RBody']))
    story.append(Paragraph('<b>CoachFactor：</b>雷格拉吉 CRI 7.4 vs 多里瓦尔 6.0，大赛经验碾压（世界杯4强 vs 新帅磨合期）。', styles['RBody']))
    story.append(Paragraph('<b>UpsetDetector：</b>冷门评分 17/100（正常），但资金流异常信号明显（83%投注流向巴西，赔率不降反升）。', styles['RBody']))
    story.append(Spacer(1, 3*mm))

    # ===== 1X2 胜平负 =====
    story.append(Paragraph("1 胜平负 (1X2)", styles['RH1']))
    data_1x2 = [
        ['结果', '市场赔率', '市场隐含概率', '模型概率', '价值差 (Edge)', '评级'],
        ['巴西胜', '1.65', '60.6%', '52.0%', _highlight_value(-8.6), '❌ 负价值'],
        ['平局', '3.78', '26.5%', '28.0%', _highlight_value(+1.5), '✅ 价值投注'],
        ['摩洛哥胜', '5.48', '18.2%', '20.0%', _highlight_value(+1.8), '价值投注'],
    ]
    t = Table(data_1x2, colWidths=[25*mm, 22*mm, 28*mm, 25*mm, 28*mm, 28*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>摩洛哥 不败（双选 平+客胜）或 单选 平局。巴西胜为负价值，应坚决避开。', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 让球胜平负 =====
    story.append(Paragraph("2 让球胜平负 (巴西 -1球)", styles['RH1']))
    data_ah = [
        ['结果', '市场赔率', '隐含概率', '模型概率', '价值差', '评级'],
        ['巴西(-1)胜', '2.80', '35.7%', '35.0%', '-0.7%', '⚠️ 中性'],
        ['走水', '3.26', '30.7%', '28.0%', '-2.7%', '❌'],
        ['摩洛哥(+1)胜', '2.15', '46.5%', '55.0%', _highlight_value(+8.5), '强价值'],
    ]
    t = Table(data_ah, colWidths=[30*mm, 22*mm, 25*mm, 25*mm, 25*mm, 28*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>摩洛哥+1球（Kelly +15.9%，最强价值投注）。摩洛哥10场不败+场均失0.3球，受让赢盘概率极高。', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 半全场 =====
    story.append(Paragraph("3 半全场 (HT/FT)", styles['RH1']))
    data_htft = [
        ['半全场组合', '模型概率', '判断'],
        ['巴西/巴西 (主/主)', '32.0%', '最可能，但赔率差'],
        ['平/巴西 (平/主)', '22.0%', '上半场闷住，下半场巴西破局'],
        ['平/平 (平/平)', '15.0%', '高赔价值'],
        ['摩洛哥/巴西 (客/主)', '8.0%', '摩洛哥先领先，被逆转'],
        ['巴西/平 (主/平)', '8.0%', '巴西领先被扳平'],
        ['平/摩洛哥 (平/客)', '8.0%', '冷门剧本'],
        ['摩洛哥/摩洛哥 (客/客)', '7.0%', '最大冷门'],
    ]
    t = Table(data_htft, colWidths=[55*mm, 30*mm, 75*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>平/平（高赔） | 平/巴西（稳健） | 摩洛哥/巴西（高赔剧本）', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 比分 =====
    story.append(Paragraph("4 比分预测 (Correct Score)", styles['RH1']))
    data_score = [
        ['比分', '模型概率', '市场隐含概率', '价值判断', '场景'],
        ['1:0', '15.0%', '~14%', '中性', '巴西小胜最常见'],
        ['1:1', '13.0%', '~8%', '✅ 价值', '摩洛哥能守'],
        ['2:0', '12.0%', '~12%', '中性', '巴西零封'],
        ['2:1', '11.0%', '~10%', '中性', '对攻剧本'],
        ['0:0', '9.0%', '~5%', '价值', '闷平'],
        ['0:1', '7.0%', '~4%', '高价值', '摩洛哥爆冷'],
        ['其他', '33.0%', '-', '-', ''],
    ]
    t = Table(data_score, colWidths=[20*mm, 25*mm, 30*mm, 25*mm, 60*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>1:1（高赔价值）| 1:0（最可能）| 0:1（冷门高赔）', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 进球数 =====
    story.append(Paragraph("5 进球数 (Total Goals)", styles['RH1']))
    data_goals = [
        ['进球数', '模型概率', '场景判断'],
        ['0球', '9.0%', '摩洛哥铁防+巴西磨合期'],
        ['1球', '21.0%', '最可能区间'],
        ['2球', '25.0%', '最可能区间'],
        ['3球', '22.0%', ''],
        ['4球', '15.0%', ''],
        ['5+球', '8.0%', '❌ 不看好'],
    ]
    t = Table(data_goals, colWidths=[25*mm, 30*mm, 105*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>1-2球（概率54%）| 摩洛哥近10场场均失0.3球，巴西未必打得穿。', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 大小球 =====
    story.append(Paragraph("6 大小球 (Over/Under)", styles['RH1']))
    data_ou = [
        ['盘口', '大球赔率', '小球赔率', '大球概率', '小球概率', '推荐'],
        ['2.0球', '1.05', '0.70', '低', '高', '❌ 盘口太浅'],
        ['2.25球', '0.89', '0.89', '42.0%', '58.0%', '小球'],
        ['2.5球', '1.05+', '0.70', '低', '高', '❌ 大球太贵'],
        ['2.5/3球', '0.95', '0.95', '45.0%', '55.0%', '小球'],
    ]
    t = Table(data_ou, colWidths=[22*mm, 22*mm, 22*mm, 22*mm, 22*mm, 30*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>小球 2.25（58%概率，大球0.89+水位不利）| 最强信号：摩洛哥近10场场均失0.3球。', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 综合策略矩阵 =====
    story.append(PageBreak())
    story.append(Paragraph("综合策略矩阵", styles['RH1']))
    data_matrix = [
        ['优先级', '玩法', '最佳选项', '赔率', '信心指数', '核心理由'],
        ['P0', '让球', '摩洛哥+1球', '2.15', '⭐⭐⭐⭐⭐', 'Kelly最优+15.9%'],
        ['P1', '大小球', '小球 2.25', '0.89', '⭐⭐⭐⭐⭐', '58%概率，摩洛哥铁防'],
        ['P2', '1X2', '平局', '3.78', '⭐⭐⭐⭐', '价值+1.5%，上半场闷'],
        ['P3', '1X2', '摩洛哥胜', '5.48', '⭐⭐⭐', '高赔价值+1.8%'],
        ['P4', '半全场', '平/平', '高赔', '⭐⭐⭐', '上半场闷住概率高'],
        ['P5', '比分', '1:1', '高赔', '⭐⭐⭐', '最可能高赔比分'],
        ['❌', '1X2', '巴西胜', '1.65', '❌', '负价值-8.6%，坚决避开'],
    ]
    t = Table(data_matrix, colWidths=[15*mm, 22*mm, 30*mm, 20*mm, 22*mm, 55*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Spacer(1, 3*mm))

    # ===== Kelly资金管理 =====
    story.append(Paragraph("Kelly 资金配置方案", styles['RH1']))
    story.append(Paragraph('<b>资金池：</b>10,000 EUR | <b>最大日风险：</b>1,500 EUR (15%) | <b>标准注码：</b>200 EUR (2%)', styles['RBody']))
    data_kelly = [
        ['投注选项', '赔率', 'Kelly比例', '半Kelly注码', '风险评级'],
        ['摩洛哥+1球', '2.15', '+15.9%', '793 EUR', 'Medium ⭐⭐⭐'],
        ['小球 2.25', '0.89', '+8.0%', '400 EUR', 'Low ⭐⭐⭐⭐'],
        ['平局', '3.78', '+2.1%', '105 EUR', 'Low ⭐⭐⭐⭐'],
        ['摩洛哥胜', '5.48', '+2.1%', '107 EUR', 'High ⭐⭐'],
    ]
    t = Table(data_kelly, colWidths=[30*mm, 20*mm, 25*mm, 30*mm, 35*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>建议：</b>优先执行摩洛哥+1球（793 EUR），其次叠加小球（400 EUR）。总风险1,193 EUR，在1,500 EUR日风险上限内。', styles['RBody']))
    story.append(Spacer(1, 3*mm))

    # ===== 风险提示 =====
    story.append(Paragraph("风险提示", styles['RH1']))
    warnings = [
        '1. 市场隐含巴西胜率60.6%，但模型仅52.0%，存在8.6%定价偏差。巴西胜为负价值投注。',
        '2. 摩洛哥近10场不败（7胜3平），场均失0.3球，防守数据为历史级别。',
        '3. 投注热度83%流向巴西，但赔率不降反升（1.55→1.65），大热倒灶信号。',
        '4. CoachFactor: 雷格拉吉CRI 7.4 vs 多里瓦尔6.0，大赛经验碾压（世界杯4强 vs 新帅）。',
        '5. UpsetDetector: 冷门评分17/100（正常），但存在市场定价错误，不是强冷门但巴西被高估。',
        '6. 所有预测基于概率模型，不代表必然结果。过往表现不代表未来收益。',
    ]
    for w in warnings:
        story.append(Paragraph(w, styles['RWarning']))
    story.append(Spacer(1, 3*mm))

    # ===== 核心洞察 =====
    story.append(Paragraph("核心洞察", styles['RH1']))
    story.append(Paragraph('<b>"巴西 1.65 的水配上 83% 的投注量，这不是送钱是送命。摩洛哥10场不败+场均失0.3球，不是来当配角的。"</b>', styles['RBody']))
    story.append(Paragraph('<b>系统判断：</b>这不是"强冷门"（UpsetDetector 17/100），而是"市场定价错误"——巴西被高估，摩洛哥被低估。不追爆冷门，抓价值差。', styles['RBody']))
    story.append(Spacer(1, 5*mm))

    # ===== 免责声明 =====
    story.append(HRFlowable(width="100%", thickness=0.5, color=_LIGHT_GRAY, spaceBefore=5*mm, spaceAfter=5*mm))
    story.append(Paragraph("免责声明", styles['RH2']))
    story.append(Paragraph("本报告仅供研究参考，不构成任何投资建议或财务建议。博彩涉及高风险，可能导致资金损失。过往表现不代表未来收益。请根据自身财务状况理性决策，切勿投入超出承受能力的资金。", styles['RDisclaimer']))
    story.append(Paragraph("Naga Quantitative Investment System v5.0 | Football Quant OS v4.2.1 | Generated by Naga Core", styles['RDisclaimer']))

    doc.build(story, onFirstPage=_Header(), onLaterPages=_Header())
    return output_path


if __name__ == '__main__':
    path = generate_full_report()
    print(f'PDF已生成: {path}')
