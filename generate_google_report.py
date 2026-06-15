#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Google Material风格预测报告生成器"""

import sys, os, json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# 字体注册
FONTS = {}
for label, path, idx in [('YH', r"C:\Windows\Fonts\msyh.ttc", 0), ('YHB', r"C:\Windows\Fonts\msyhbd.ttc", 0), ('YHL', r"C:\Windows\Fonts\msyhl.ttc", 0)]:
    try:
        pdfmetrics.registerFont(TTFont(label, path, subfontIndex=idx))
        FONTS[label] = label
    except:
        pass

FN = FONTS.get('YH', 'Helvetica')
FNB = FONTS.get('YHB', 'Helvetica-Bold')
FNL = FONTS.get('YHL', 'Helvetica')

# Google Material Design 配色
BLUE = HexColor('#4285F4')
GREEN = HexColor('#34A853')
RED = HexColor('#EA4335')
YELLOW = HexColor('#FBBC04')
DARK = HexColor('#202124')
GRAY = HexColor('#5F6368')
LIGHT = HexColor('#F8F9FA')
BORDER = HexColor('#DADCE0')


def _create_styles():
    s = getSampleStyleSheet()
    s.add(ParagraphStyle('GT', fontName=FNB, fontSize=24, leading=32, textColor=DARK, alignment=TA_LEFT, spaceAfter=4*mm))
    s.add(ParagraphStyle('GST', fontName=FNL, fontSize=13, leading=20, textColor=GRAY, alignment=TA_LEFT, spaceAfter=10*mm))
    s.add(ParagraphStyle('GM', fontName=FNL, fontSize=10, leading=15, textColor=GRAY, alignment=TA_LEFT, spaceAfter=15*mm))
    s.add(ParagraphStyle('GH1', fontName=FNB, fontSize=16, leading=24, textColor=DARK, spaceBefore=12*mm, spaceAfter=6*mm))
    s.add(ParagraphStyle('GH2', fontName=FNB, fontSize=12, leading=18, textColor=DARK, spaceBefore=8*mm, spaceAfter=4*mm))
    s.add(ParagraphStyle('GB', fontName=FN, fontSize=11, leading=20, textColor=DARK, alignment=TA_LEFT, spaceAfter=5*mm))
    s.add(ParagraphStyle('GC', fontName=FN, fontSize=11, leading=20, textColor=DARK, backColor=LIGHT, borderPadding=10, topPadding=10, bottomPadding=10, leftPadding=12, rightPadding=12, borderWidth=1, borderColor=BORDER, borderRadius=4, spaceAfter=6*mm))
    s.add(ParagraphStyle('GN', fontName=FNB, fontSize=28, leading=36, textColor=BLUE, alignment=TA_LEFT, spaceAfter=1*mm))
    s.add(ParagraphStyle('GNR', fontName=FNB, fontSize=28, leading=36, textColor=RED, alignment=TA_LEFT, spaceAfter=1*mm))
    s.add(ParagraphStyle('GNY', fontName=FNB, fontSize=28, leading=36, textColor=YELLOW, alignment=TA_LEFT, spaceAfter=1*mm))
    s.add(ParagraphStyle('GNL', fontName=FN, fontSize=10, leading=15, textColor=GRAY, alignment=TA_LEFT, spaceAfter=5*mm))
    s.add(ParagraphStyle('GV', fontName=FNB, fontSize=11, leading=20, textColor=GREEN, alignment=TA_LEFT, spaceAfter=3*mm, leftIndent=8*mm, firstLineIndent=-8*mm))
    s.add(ParagraphStyle('GW', fontName=FN, fontSize=11, leading=20, textColor=RED, alignment=TA_LEFT, spaceAfter=3*mm, leftIndent=8*mm, firstLineIndent=-8*mm))
    s.add(ParagraphStyle('GD', fontName=FNL, fontSize=9, leading=14, textColor=GRAY, alignment=TA_LEFT, spaceAfter=1*mm))
    return s


def _ts():
    return [('FONTNAME', (0,0), (-1,-1), FN), ('FONTSIZE', (0,0), (-1,-1), 10), ('TEXTCOLOR', (0,0), (-1,-1), DARK),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10), ('LEFTPADDING', (0,0), (-1,-1), 8), ('RIGHTPADDING', (0,0), (-1,-1), 8)]


def _hl(v):
    if v > 0: return f'<font color="#34A853">+{v:.1f}%</font>'
    if v < 0: return f'<font color="#EA4335">{v:.1f}%</font>'
    return f'{v:.1f}%'


class _Header:
    def __call__(self, canvas, doc):
        canvas.saveState()
        canvas.setFillColor(BLUE)
        canvas.circle(doc.leftMargin - 12, doc.height + doc.topMargin - 15, 3, fill=1, stroke=0)
        canvas.setFont(FNB, 9)
        canvas.setFillColor(GRAY)
        canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - 18, "Naga Quantitative")
        canvas.setFont(FNL, 8)
        canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin - 18, datetime.now().strftime('%Y-%m-%d'))
        canvas.setStrokeColor(BORDER)
        canvas.setLineWidth(0.5)
        canvas.line(doc.leftMargin, doc.bottomMargin - 10, doc.width + doc.leftMargin, doc.bottomMargin - 10)
        canvas.setFont(FNL, 8)
        canvas.drawString(doc.leftMargin, doc.bottomMargin - 20, f"Page {canvas.getPageNumber()}")
        canvas.restoreState()


def generate(match_type='brazil_morocco'):
    if match_type == 'brazil_morocco':
        out = r'C:\Users\Administrator\Desktop\Naga_Report_Brazil_vs_Morocco.pdf'
        ht, at = '巴西', '摩洛哥'
        hf, af = 'BR', 'MA'
        s = '市场隐含巴西胜率 60.6%，但模型仅 52.0%，存在 8.6% 定价偏差。巴西被严重高估，摩洛哥方向存在价值投注。'
        q = '巴西 1.65 的水配上 83% 的投注量，这不是送钱是送命。摩洛哥10场不败+场均失0.3球，不是来当配角的。'
        d1 = [['巴西胜', '1.65', '60.6%', '52.0%', _hl(-8.6), '负价值'], ['平局', '3.78', '26.5%', '28.0%', _hl(+1.5), '价值投注'], ['摩洛哥胜', '5.48', '18.2%', '20.0%', _hl(+1.8), '价值投注']]
        da = [['巴西(-1)胜', '2.80', '35.7%', '35.0%', '-0.7%', '⚠'], ['走水', '3.26', '30.7%', '28.0%', '-2.7%', '❌'], ['摩洛哥(+1)胜', '2.15', '46.5%', '55.0%', _hl(+8.5), '强价值']]
        dh = [['巴西/巴西', '32.0%', '最可能，但赔率差'], ['平/巴西', '22.0%', '上半场闷住，下半场破局'], ['平/平', '15.0%', '高赔价值'], ['摩洛哥/巴西', '8.0%', '摩洛哥先领先，被逆转'], ['巴西/平', '8.0%', '巴西领先被扳平'], ['平/摩洛哥', '8.0%', '冷门剧本'], ['摩洛哥/摩洛哥', '7.0%', '最大冷门']]
        ds = [['1:0', '15.0%', '巴西小胜最常见'], ['1:1', '13.0%', '摩洛哥能守'], ['2:0', '12.0%', '巴西零封'], ['2:1', '11.0%', '对攻剧本'], ['0:0', '9.0%', '闷平'], ['0:1', '7.0%', '摩洛哥爆冷']]
        dg = [['0球', '9.0%', '摩洛哥铁防+巴西磨合'], ['1球', '21.0%', '最可能区间'], ['2球', '25.0%', '最可能区间'], ['3球', '22.0%', ''], ['4球', '15.0%', ''], ['5+球', '8.0%', '不看好']]
        du = [['2.0球', '1.05/0.70', '盘口太浅'], ['2.25球', '0.89/0.89', '小球 58%'], ['2.5球', '1.05+/0.70', '大球太贵'], ['2.5/3球', '0.95/0.95', '小球 55%']]
        dm = [['P0', '让球', '摩洛哥+1', '2.15', '★★★★★', 'Kelly最优+15.9%'], ['P1', '大小球', '小球 2.25', '0.89', '★★★★★', '58%概率，摩洛哥铁防'], ['P2', '1X2', '平局', '3.78', '★★★★', '价值+1.5%，上半场闷'], ['P3', '1X2', '摩洛哥胜', '5.48', '★★★', '高赔价值+1.8%'], ['P4', '半全场', '平/平', '高赔', '★★★', '上半场闷住概率高'], ['P5', '比分', '1:1', '高赔', '★★★', '最可能高赔比分'], ['❌', '1X2', '巴西胜', '1.65', '❌', '负价值-8.6%，坚决避开']]
        w = ['市场隐含巴西胜率60.6%，但模型仅52.0%，存在8.6%定价偏差。巴西胜为负价值投注。', '摩洛哥近10场不败（7胜3平），场均失0.3球，防守数据为历史级别。', '投注热度83%流向巴西，但赔率不降反升（1.55→1.65），大热倒灶信号。', 'CoachFactor: 雷格拉吉CRI 7.4 vs 多里瓦尔6.0，大赛经验碾压（世界杯4强 vs 新帅）。', 'UpsetDetector: 冷门评分17/100（正常），但存在市场定价错误，不是强冷门但巴西被高估。', '所有预测基于概率模型，不代表必然结果。过往表现不代表未来收益。']
        k = [['摩洛哥+1球', '2.15', '+15.9%', '793 EUR', 'Medium'], ['小球 2.25', '0.89', '+8.0%', '400 EUR', 'Low'], ['平局', '3.78', '+2.1%', '105 EUR', 'Low'], ['摩洛哥胜', '5.48', '+2.1%', '107 EUR', 'High']]
        r1 = '摩洛哥 不败（双选 平+客胜）或 单选 平局。巴西胜为负价值，应坚决避开。'
        ra = '摩洛哥+1球（Kelly +15.9%，最强价值投注）。摩洛哥10场不败+场均失0.3球，受让赢盘概率极高。'
        rh = '平/平（高赔） | 平/巴西（稳健） | 摩洛哥/巴西（高赔剧本）'
        rs = '1:1（高赔价值）| 1:0（最可能）| 0:1（冷门高赔）'
        rg = '1-2球（概率54%）| 摩洛哥近10场场均失0.3球，巴西未必打得穿。'
        ru = '小球 2.25（58%概率，大球0.89+水位不利）| 最强信号：摩洛哥近10场场均失0.3球。'
        nd, nh, nu = '8.6%', '83%', '17'
        ks = '优先执行摩洛哥+1球（793 EUR），其次叠加小球（400 EUR）。总风险1,193 EUR，在1,500 EUR日风险上限内。'
    else:
        out = r'C:\Users\Administrator\Desktop\Naga_Report_Haiti_vs_Scotland.pdf'
        ht, at = '海地', '苏格兰'
        hf, af = 'HT', 'SC'
        s = '市场隐含苏格兰胜率 66.7%，但模型评估仅 58.0%，存在 8.7% 定价偏差。苏格兰赔率从1.40升至1.50（大幅升水），海地赔率从6.92降至6.05（降赔），市场正在修正对苏格兰的定价。'
        q = '苏格兰 1.50 的水配上 84%资金流，大热升水信号明确。海地赔率6.05（投注翻倍至15.7%），市场开始转向。'
        d1 = [['海地胜', '6.05', '16.5%', '16.0%', _hl(-0.5), '负价值'], ['平局', '4.48', '22.3%', '26.0%', _hl(+3.7), '价值投注'], ['苏格兰胜', '1.50', '66.7%', '58.0%', _hl(-8.7), '大热负价值']]
        da = [['海地(+1)胜', '2.11', '47.4%', '43.0%', '-4.4%', '⚠'], ['走水', '3.35', '29.9%', '28.0%', '-1.9%', '❌'], ['苏格兰(-1)胜', '2.81', '35.6%', '37.0%', _hl(+1.4), '价值']]
        dh = [['苏格兰/苏格兰', '35.0%', '最可能，但赔率差'], ['平/苏格兰', '22.0%', '上半场闷住，下半场破局'], ['平/平', '12.0%', '高赔价值'], ['海地/苏格兰', '8.0%', '海地先领先，被逆转'], ['苏格兰/平', '7.0%', '苏格兰领先被扳平'], ['平/海地', '6.0%', '冷门剧本'], ['海地/海地', '5.0%', '最大冷门']]
        ds = [['0:1', '18.0%', '苏格兰小胜最常见'], ['0:0', '12.0%', '闷平'], ['1:1', '11.0%', '海地能守'], ['0:2', '10.0%', '苏格兰零封'], ['1:2', '8.0%', '对攻剧本'], ['1:0', '6.0%', '海地爆冷']]
        dg = [['0球', '12.0%', '海地铁防+苏格兰磨合'], ['1球', '22.0%', '最可能区间'], ['2球', '25.0%', '最可能区间'], ['3球', '20.0%', ''], ['4球', '13.0%', ''], ['5+球', '8.0%', '不看好']]
        du = [['2.5球', '0.75/1.20', '小球太贵'], ['2.5/3球', '0.87/0.95', '小球 55%'], ['3球', '0.78/0.95', '大球低水诱盘']]
        dm = [['P0', '1X2', '平局', '4.48', '★★★★★', '价值+3.7%，最强价值'], ['P1', '让球', '海地+1', '2.11', '★★★★', '最稳，受让赢盘43%'], ['P2', '大小球', '小球 2.5/3', '0.95', '★★★★', '55%概率，低比分'], ['P3', '比分', '0:0', '高赔', '★★★', '最可能高赔比分'], ['P4', '半全场', '平/平', '高赔', '★★★', '上半场闷住'], ['P5', '1X2', '海地胜', '6.05', '★★', '高赔博冷门'], ['❌', '1X2', '苏格兰胜', '1.50', '❌', '负价值-8.7%，大热避开']]
        w = ['市场隐含苏格兰胜率66.7%，但模型仅58.0%，存在8.7%定价偏差。苏格兰赔率从1.40升至1.50（大幅升水），坚决避开。', '海地赔率从6.92降至6.05（降赔），投注量从7.8%翻倍至15.7%，市场开始转向海地。', '投注热度63%流向苏格兰，资金热度84.1%，但赔率升水，大热倒灶信号明确。', '庄家盈亏指数：苏格兰赔付压力大，海地方向庄家乐见。', '海地近6场LWDLWW，状态不稳定但偶有爆冷能力。苏格兰WWLLWL，起伏大。', '海地FIFA排名较低，但苏格兰并非传统强队，世界杯小组赛偶然性高。']
        k = [['平局', '4.48', '+3.7%', '235 EUR', 'Medium'], ['海地+1球', '2.11', '+5.2%', '260 EUR', 'Low'], ['小球 2.5/3', '0.95', '+4.0%', '200 EUR', 'Low'], ['海地胜', '6.05', '+0.8%', '40 EUR', 'High']]
        r1 = '平局（价值+3.7%，高赔4.48）| 海地 不败（双选 平+主胜，博高赔）| 苏格兰胜为负价值-8.7%，大热应避开。'
        ra = '海地+1球（最稳，受让赢盘概率43%）。但平局价值+3.7%更高，可优先配置。'
        rh = '平/平（高赔） | 平/苏格兰（稳健） | 海地/苏格兰（高赔剧本）'
        rs = '0:0（高赔价值）| 0:1（最可能）| 1:1（冷门高赔）'
        rg = '1-2球（概率47%）| 海地防守不稳定但苏格兰进攻效率一般，低比分概率高。'
        ru = '小球 2.5/3（55%概率，大小球平均2.61）| 低比分格局。'
        nd, nh, nu = '8.7%', '84%', '22'
        ks = '优先执行平局（235 EUR），其次海地+1球（260 EUR），叠加小球（200 EUR）。总风险695 EUR，在1,500 EUR日风险上限内。'

    st = _create_styles()
    doc = SimpleDocTemplate(out, pagesize=A4, rightMargin=25*mm, leftMargin=25*mm, topMargin=30*mm, bottomMargin=20*mm)
    story = []

    story.append(Spacer(1, 15*mm))
    story.append(Paragraph(f"{ht} vs {at}", st['GT']))
    story.append(Paragraph("2026 FIFA 世界杯小组赛", st['GST']))
    story.append(Paragraph(f"Football Quant OS v4.2.1 | Google风格 | {datetime.now().strftime('%Y-%m-%d %H:%M')}", st['GM']))
    story.append(HRFlowable(width="100%", thickness=1, color=BORDER, spaceBefore=8*mm, spaceAfter=8*mm))

    story.append(Paragraph("核心指标", st['GH1']))
    num_data = [[Paragraph(f'<font color="#EA4335">{nd}</font>', st['GNR']), Paragraph(f'<font color="#4285F4">{nh}</font>', st['GN']), Paragraph(f'<font color="#FBBC04">{nu}</font>', st['GNY'])], [Paragraph('定价偏差', st['GNL']), Paragraph('投注热度', st['GNL']), Paragraph('冷门评分', st['GNL'])]]
    t = Table(num_data, colWidths=[55*mm, 55*mm, 55*mm])
    t.setStyle(TableStyle([('ALIGN', (0,0), (-1,-1), 'CENTER'), ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('TOPPADDING', (0,0), (-1,-1), 8), ('BOTTOMPADDING', (0,0), (-1,-1), 8)]))
    story.append(t)
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph('核心洞察', st['GH2']))
    story.append(Paragraph(f'<b>"{q}"</b>', st['GC']))
    story.append(Spacer(1, 5*mm))

    story.append(Paragraph("执行摘要", st['GH1']))
    story.append(Paragraph(s, st['GB']))
    story.append(Spacer(1, 5*mm))

    for title, data, rec, cw in [("1. 胜平负 (1X2)", d1, r1, [25,20,25,25,25,25]), ("2. 让球胜平负", da, ra, [30,20,25,25,25,25]), ("3. 半全场 (HT/FT)", dh, rh, [45,25,80]), ("4. 比分预测", ds, rs, [20,25,105]), ("5. 进球数", dg, rg, [25,25,100]), ("6. 大小球", du, ru, [25,30,95])]:
        story.append(Paragraph(title, st['GH1']))
        t = Table(data, colWidths=[c*mm for c in cw])
        t.setStyle(TableStyle(_ts() + [('BACKGROUND', (0,0), (-1,0), LIGHT), ('FONTNAME', (0,0), (-1,0), FNB), ('GRID', (0,0), (-1,-1), 0.5, BORDER), ('BOTTOMPADDING', (0,0), (-1,0), 12)]))
        story.append(t)
        story.append(Spacer(1, 3*mm))
        story.append(Paragraph(f'▶ 推荐：{rec}', st['GV']))
        story.append(Spacer(1, 3*mm))

    story.append(PageBreak())
    story.append(Paragraph("综合策略矩阵", st['GH1']))
    t = Table(dm, colWidths=[15*mm, 22*mm, 30*mm, 20*mm, 22*mm, 55*mm])
    t.setStyle(TableStyle(_ts() + [('BACKGROUND', (0,0), (-1,0), LIGHT), ('FONTNAME', (0,0), (-1,0), FNB), ('GRID', (0,0), (-1,-1), 0.5, BORDER), ('BOTTOMPADDING', (0,0), (-1,0), 12)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("Kelly 资金配置", st['GH1']))
    story.append(Paragraph('<b>资金池：</b>10,000 EUR | <b>最大日风险：</b>1,500 EUR (15%) | <b>标准注码：</b>200 EUR (2%)', st['GB']))
    t = Table(k, colWidths=[30*mm, 20*mm, 25*mm, 30*mm, 35*mm])
    t.setStyle(TableStyle(_ts() + [('BACKGROUND', (0,0), (-1,0), LIGHT), ('FONTNAME', (0,0), (-1,0), FNB), ('GRID', (0,0), (-1,-1), 0.5, BORDER), ('BOTTOMPADDING', (0,0), (-1,0), 12)]))
    story.append(t)
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(f'<b>建议：</b>{ks}', st['GB']))
    story.append(Spacer(1, 3*mm))

    story.append(Paragraph("风险提示", st['GH1']))
    for warning in w:
        story.append(Paragraph(f'• {warning}', st['GW']))
    story.append(Spacer(1, 3*mm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=5*mm, spaceAfter=5*mm))
    story.append(Paragraph("免责声明", st['GH2']))
    story.append(Paragraph("本报告仅供研究参考，不构成任何投资建议或财务建议。博彩涉及高风险，可能导致资金损失。过往表现不代表未来收益。", st['GD']))
    story.append(Paragraph("Naga Quantitative Investment System v5.0 | Football Quant OS v4.2.1", st['GD']))

    doc.build(story, onFirstPage=_Header(), onLaterPages=_Header())
    return out


if __name__ == '__main__':
    generate('brazil_morocco')
    generate('haiti_scotland')
    print('两份Google风格PDF已生成')
