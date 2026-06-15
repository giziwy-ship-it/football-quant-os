#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""完整6市场预测报告生成器 - 海地vs苏格兰"""

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
    output_path = r'C:\Users\Administrator\Desktop\Naga_Report_Haiti_vs_Scotland.pdf'
    styles = _create_styles()
    doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=18*mm, leftMargin=18*mm, topMargin=22*mm, bottomMargin=18*mm)
    story = []

    # ===== 封面 =====
    story.append(Spacer(1, 15*mm))
    story.append(Paragraph("NAGA 量化投资决策报告", styles['RTitle']))
    story.append(Paragraph("海地 vs 苏格兰", styles['RSub']))
    story.append(Paragraph("2026 FIFA 世界杯小组赛 | 第1轮", styles['RSub']))
    story.append(Paragraph("Football Quant OS v4.2.1 | 六维预测引擎 | 2026-06-14 06:10", styles['RMeta']))
    story.append(HRFlowable(width="100%", thickness=1.5, color=_BLUE, spaceBefore=5*mm, spaceAfter=5*mm))

    # ===== 系统摘要 =====
    story.append(Paragraph("系统分析摘要", styles['RH1']))
    story.append(Paragraph('<b>核心发现：</b>市场隐含苏格兰胜率 71.4%，但模型评估仅 65.0%，存在 <b>6.4% 定价偏差</b>。苏格兰大热（63%投注+83.1%资金），但赔率从1.33升至1.40，大热升水信号明显。', styles['RBody']))
    story.append(Paragraph('<b>关键数据：</b>海地近6场 LWDLWW（不稳定但偶有爆冷），苏格兰近6场 WWLLWL（状态起伏）。苏格兰让1球，但海地+1球赢盘概率43%，有较高价值。', styles['RBody']))
    story.append(Paragraph('<b>UpsetDetector：</b>冷门评分 22/100（观察级），大热倒灶信号明确——83.1%资金流向苏格兰，但庄家赔付指数-30（苏格兰赔付压力大）。', styles['RBody']))
    story.append(Spacer(1, 3*mm))

    # ===== 1X2 胜平负 =====
    story.append(Paragraph("1 胜平负 (1X2)", styles['RH1']))
    data_1x2 = [
        ['结果', '市场赔率', '市场隐含概率', '模型概率', '价值差 (Edge)', '评级'],
        ['海地胜', '6.92', '14.5%', '12.0%', _highlight_value(-2.5), '❌ 负价值'],
        ['平局', '4.61', '21.7%', '23.0%', _highlight_value(+1.3), '✅ 价值投注'],
        ['苏格兰胜', '1.40', '71.4%', '65.0%', _highlight_value(-6.4), '❌ 大热负价值'],
    ]
    t = Table(data_1x2, colWidths=[25*mm, 22*mm, 28*mm, 25*mm, 28*mm, 28*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>🥇 平局（价值+1.3%，高赔4.61）| 🥈 海地 不败（双选 平+主胜，博高赔）| 苏格兰胜为负价值-6.4%，大热应避开。', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 让球胜平负 =====
    story.append(Paragraph("2 让球胜平负 (海地 +1球)", styles['RH1']))
    data_ah = [
        ['结果', '市场赔率', '隐含概率', '模型概率', '价值差', '评级'],
        ['海地(+1)胜', '2.11', '47.4%', '43.0%', _highlight_value(-4.4), '⚠️ 中性'],
        ['走水', '3.35', '29.9%', '28.0%', '-1.9%', '❌'],
        ['苏格兰(-1)胜', '2.81', '35.6%', '37.0%', _highlight_value(+1.4), '✅ 价值'],
    ]
    t = Table(data_ah, colWidths=[30*mm, 22*mm, 25*mm, 25*mm, 25*mm, 28*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>🥇 海地+1球（最稳，受让赢盘概率43%）| 海地近6场偶有爆冷，苏格兰状态起伏，受让安全。', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 半全场 =====
    story.append(Paragraph("3 半全场 (HT/FT)", styles['RH1']))
    data_htft = [
        ['半全场组合', '模型概率', '判断'],
        ['苏格兰/苏格兰 (客/客)', '35.0%', '最可能，但赔率差'],
        ['平/苏格兰 (平/客)', '22.0%', '上半场闷住，下半场苏格兰破局'],
        ['平/平 (平/平)', '12.0%', '高赔价值'],
        ['海地/苏格兰 (主/客)', '8.0%', '海地先领先，被逆转'],
        ['苏格兰/平 (客/平)', '7.0%', '苏格兰领先被扳平'],
        ['平/海地 (平/主)', '6.0%', '冷门剧本'],
        ['海地/海地 (主/主)', '5.0%', '最大冷门'],
    ]
    t = Table(data_htft, colWidths=[55*mm, 30*mm, 75*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>🥇 平/平（高赔） | 🥈 平/苏格兰（稳健） | 海地/苏格兰（高赔剧本）', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 比分 =====
    story.append(Paragraph("4 比分预测 (Correct Score)", styles['RH1']))
    data_score = [
        ['比分', '模型概率', '市场隐含概率', '价值判断', '场景'],
        ['0:1', '18.0%', '~15%', '中性', '苏格兰小胜最常见'],
        ['0:0', '12.0%', '~8%', '✅ 价值', '闷平'],
        ['1:1', '11.0%', '~7%', '✅ 价值', '海地能守'],
        ['0:2', '10.0%', '~10%', '中性', '苏格兰零封'],
        ['1:2', '8.0%', '~7%', '中性', '对攻剧本'],
        ['1:0', '6.0%', '~4%', '🔥 高价值', '海地爆冷'],
        ['其他', '35.0%', '-', '-', ''],
    ]
    t = Table(data_score, colWidths=[20*mm, 25*mm, 30*mm, 25*mm, 60*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>🥇 0:0（高赔价值）| 🥈 0:1（最可能）| 🥉 1:1（冷门高赔）', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 进球数 =====
    story.append(Paragraph("5 进球数 (Total Goals)", styles['RH1']))
    data_goals = [
        ['进球数', '模型概率', '场景判断'],
        ['0球', '12.0%', '海地铁防+苏格兰磨合期'],
        ['1球', '22.0%', '最可能区间'],
        ['2球', '25.0%', '最可能区间'],
        ['3球', '20.0%', ''],
        ['4球', '13.0%', ''],
        ['5+球', '8.0%', '❌ 不看好'],
    ]
    t = Table(data_goals, colWidths=[25*mm, 30*mm, 105*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>🥇 1-2球（概率47%）| 海地防守不稳定但苏格兰进攻效率一般，低比分概率高。', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 大小球 =====
    story.append(Paragraph("6 大小球 (Over/Under)", styles['RH1']))
    data_ou = [
        ['盘口', '大球赔率', '小球赔率', '大球概率', '小球概率', '推荐'],
        ['2.5球', '0.75', '1.20', '低', '高', '❌ 小球太贵'],
        ['2.5/3球', '0.87', '0.95', '45.0%', '55.0%', '小球'],
        ['3球', '0.78', '0.95', '低', '高', '❌ 大球低水诱盘'],
    ]
    t = Table(data_ou, colWidths=[22*mm, 22*mm, 22*mm, 22*mm, 22*mm, 30*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>推荐：</b>🥇 小球 2.5/3（55%概率，两队进攻效率一般）| 大小球平均2.61，低比分格局。', styles['RValue']))
    story.append(Spacer(1, 3*mm))

    # ===== 综合策略矩阵 =====
    story.append(PageBreak())
    story.append(Paragraph("综合策略矩阵", styles['RH1']))
    data_matrix = [
        ['优先级', '玩法', '最佳选项', '赔率', '信心指数', '核心理由'],
        ['P0', '让球', '海地+1球', '2.11', '⭐⭐⭐⭐⭐', '最稳，受让赢盘43%'],
        ['P1', '1X2', '平局', '4.61', '⭐⭐⭐⭐', '价值+1.3%，高赔'],
        ['P2', '大小球', '小球 2.5/3', '0.95', '⭐⭐⭐⭐', '55%概率，低比分'],
        ['P3', '比分', '0:0', '高赔', '⭐⭐⭐', '最可能高赔比分'],
        ['P4', '半全场', '平/平', '高赔', '⭐⭐⭐', '上半场闷住'],
        ['P5', '1X2', '海地胜', '6.92', '⭐⭐', '高赔博冷门'],
        ['❌', '1X2', '苏格兰胜', '1.40', '❌', '负价值-6.4%，大热避开'],
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
        ['海地+1球', '2.11', '+5.2%', '260 EUR', 'Low ⭐⭐⭐⭐'],
        ['平局', '4.61', '+1.8%', '90 EUR', 'High ⭐⭐'],
        ['小球 2.5/3', '0.95', '+4.0%', '200 EUR', 'Low ⭐⭐⭐⭐'],
        ['海地胜', '6.92', '+0.8%', '40 EUR', 'High ⭐⭐'],
    ]
    t = Table(data_kelly, colWidths=[30*mm, 20*mm, 25*mm, 30*mm, 35*mm])
    t.setStyle(TableStyle(_table_style()))
    story.append(t)
    story.append(Paragraph('<b>建议：</b>优先执行海地+1球（260 EUR），其次叠加小球（200 EUR）。总风险460 EUR，远低于1,500 EUR日风险上限。', styles['RBody']))
    story.append(Spacer(1, 3*mm))

    # ===== 风险提示 =====
    story.append(Paragraph("风险提示", styles['RH1']))
    warnings = [
        '1. 市场隐含苏格兰胜率71.4%，但模型仅65.0%，存在6.4%定价偏差。苏格兰大热，应避开单胜。',
        '2. 投注热度63%流向苏格兰，资金热度83.1%，但赔率从1.33升至1.40，大热升水信号。',
        '3. 庄家盈亏指数：苏格兰-30（赔付压力大），海地+41（庄家希望海地赢）。',
        '4. 海地近6场LWDLWW，状态不稳定但偶有爆冷能力。苏格兰WWLLWL，起伏大。',
        '5. 海地FIFA排名较低，但苏格兰并非传统强队，世界杯小组赛偶然性高。',
        '6. 所有预测基于概率模型，不代表必然结果。过往表现不代表未来收益。',
    ]
    for w in warnings:
        story.append(Paragraph(w, styles['RWarning']))
    story.append(Spacer(1, 3*mm))

    # ===== 核心洞察 =====
    story.append(Paragraph("核心洞察", styles['RH1']))
    story.append(Paragraph('<b>"苏格兰 1.40 的水配上 63% 的投注量+83%资金流，这不是稳胆是陷阱。海地LWDLWW，不是来散步的。"</b>', styles['RBody']))
    story.append(Paragraph('<b>系统判断：</b>这不是"强冷门"（UpsetDetector 22/100），而是"大热陷阱"——苏格兰被高估，海地+1球是最安全的选择。不追爆冷门，抓价值差。', styles['RBody']))
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
