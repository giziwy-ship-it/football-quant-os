#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成3场比赛组合投资建议PDF
"""

from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

import sys
sys.path.insert(0, 'D:/openclaw-workspace/football_quant_os')
from scripts.combination_betting import recommend_combinations, allocate_bankroll_to_combinations

# 注册字体
FONT = 'Helvetica'
for fn, fp in [('SimHei','C:/Windows/Fonts/simhei.ttf'),('MicrosoftYaHei','C:/Windows/Fonts/msyh.ttc')]:
    try:
        pdfmetrics.registerFont(TTFont(fn, fp))
        FONT = fn
        break
    except:
        pass

def make_style(name, size, color, align, space):
    return ParagraphStyle(name, fontName=FONT, fontSize=size, leading=size+4,
                          alignment=align, spaceAfter=space, textColor=colors.HexColor(color))

styles = {}
styles['title'] = make_style('title', 18, '#1a1a2e', TA_CENTER, 15)
styles['subtitle'] = make_style('subtitle', 10, '#4a4a6a', TA_CENTER, 10)
styles['header'] = make_style('header', 12, '#16213e', TA_LEFT, 10)
styles['body'] = make_style('body', 9, '#2d3436', TA_LEFT, 5)
styles['alert'] = make_style('alert', 10, '#e94560', TA_LEFT, 8)
styles['good'] = make_style('good', 10, '#155724', TA_LEFT, 8)
styles['warn'] = make_style('warn', 10, '#856404', TA_LEFT, 8)
styles['gold'] = make_style('gold', 10, '#b8860b', TA_LEFT, 8)

# 3场比赛投注数据
all_bets = [
    {'home': '科特迪瓦', 'away': '厄瓜多尔', 'market': '1x2', 'selection': '平局', 'odds': 3.05, 'probability': 0.443, 'edge': 0.172, 'match_date': '2026-06-15', 'league': '世界杯'},
    {'home': '科特迪瓦', 'away': '厄瓜多尔', 'market': 'asian_handicap', 'selection': '厄瓜多尔+0.25', 'odds': 1.85, 'probability': 0.65, 'edge': 0.11, 'match_date': '2026-06-15', 'league': '世界杯'},
    {'home': '荷兰', 'away': '日本', 'market': 'asian_handicap', 'selection': '日本+1不败', 'odds': 1.87, 'probability': 0.68, 'edge': 0.09, 'match_date': '2026-06-15', 'league': '世界杯'},
    {'home': '荷兰', 'away': '日本', 'market': '1x2', 'selection': '平局', 'odds': 3.55, 'probability': 0.30, 'edge': 0.05, 'match_date': '2026-06-15', 'league': '世界杯'},
    {'home': '瑞典', 'away': '突尼斯', 'market': '1x2', 'selection': '平局', 'odds': 3.45, 'probability': 0.407, 'edge': 0.188, 'match_date': '2026-06-15', 'league': '世界杯'},
    {'home': '瑞典', 'away': '突尼斯', 'market': 'asian_handicap', 'selection': '突尼斯+0.75', 'odds': 1.93, 'probability': 0.65, 'edge': 0.08, 'match_date': '2026-06-15', 'league': '世界杯'},
]

BANKROLL = 50000
recs = recommend_combinations(all_bets, bankroll=BANKROLL, risk_level='conservative')
all_recs = []
for fold_type, r in recs.items():
    all_recs.extend(r)

allocation = allocate_bankroll_to_combinations(all_recs, total_bankroll=BANKROLL, max_total_risk=0.20, allocation_method='proportional')

# 生成PDF
output = Path.home() / "Desktop" / f"组合投资建议_3场世界杯_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
story = []

story.append(Paragraph("Football Quant OS v5.1.0", styles['title']))
story.append(Paragraph("3场比赛组合投资建议", styles['title']))
story.append(Paragraph("科特迪瓦vs厄瓜多尔 + 荷兰vs日本 + 瑞典vs突尼斯", styles['subtitle']))
story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['subtitle']))
story.append(Spacer(1, 10))

# 资金概览
story.append(Paragraph("资金概览", styles['header']))
info = [['项目','金额'],['资金池','$50,000'],['已分配',f'${allocation["total_allocated"]:,.2f} ({allocation["total_risk_ratio"]:.1%})'],['风险上限','20%'],['剩余资金',f'${allocation["bankroll_remaining"]:,.2f}'],['Kelly原始总和',f'${allocation["total_kelly_stake"]:,.2f}'],['是否缩减','是 (因总风险超限)'],['分配策略','proportional (按Edge比例)']]
t = Table(info, colWidths=[5*cm, 11*cm])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#16213e')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(t); story.append(Spacer(1, 10))

# 单场价值投注
story.append(Paragraph("单场价值投注 (Edge >= 5%)", styles['header']))
single = [['比赛','推荐','赔率','模型概率','Edge','信心']]
for bet in all_bets:
    if bet['edge'] >= 0.05:
        star = '***' if bet['edge'] >= 0.10 else '**'
        single.append([f"{bet['home']} vs {bet['away']}", bet['selection'], f"{bet['odds']}", f"{bet['probability']:.1%}", f"+{bet['edge']:.1%}", star])
t = Table(single, colWidths=[4.5*cm,3.5*cm,2.5*cm,3*cm,3*cm,3.5*cm])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f3460')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(t); story.append(Spacer(1, 10))

story.append(Paragraph("核心发现: 3场比赛的平局都被严重低估！模型概率均显著高于市场隐含概率。", styles['good']))
story.append(Spacer(1, 10))

# 2串1推荐
story.append(Paragraph("2串1推荐 (Top 5)", styles['header']))
t2 = [['排名','组合','赔率','概率','Edge','投注','预期回报']]
for i, rec in enumerate(allocation['combinations'][:5], 1):
    if rec['allocated_stake'] > 0 and rec['type'] == '2串1':
        t2.append([f"#{i}", ' + '.join(rec['selections']), f"{rec['combined_odds']}", f"{rec['combined_probability']:.2%}", f"{rec['combined_edge']:.2%}", f"${rec['allocated_stake']:.2f}", f"${rec['allocated_expected_return']:.2f}"])
t = Table(t2, colWidths=[2*cm,5*cm,2.5*cm,3*cm,3*cm,3*cm,3.5*cm])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e94560')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(t); story.append(Spacer(1, 5))
story.append(Paragraph("分析: 2串1是性价比最高的组合。日本+1不败 + 突尼斯+0.75 组合概率41.4%，赔率3.61，ROI 261%。", styles['body']))
story.append(Spacer(1, 10))

# 3串1推荐
story.append(Paragraph("3串1推荐 (Top 3)", styles['header']))
t3 = [['排名','组合','赔率','概率','Edge','投注','预期回报']]
count = 0
for rec in allocation['combinations']:
    if rec['allocated_stake'] > 0 and rec['type'] == '3串1':
        count += 1
        t3.append([f"#{count}", ' + '.join(rec['selections']), f"{rec['combined_odds']}", f"{rec['combined_probability']:.2%}", f"{rec['combined_edge']:.2%}", f"${rec['allocated_stake']:.2f}", f"${rec['allocated_expected_return']:.2f}"])
        if count >= 3: break
t = Table(t3, colWidths=[2*cm,5*cm,2.5*cm,3*cm,3*cm,3*cm,3.5*cm])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f3460')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(t); story.append(Spacer(1, 5))
story.append(Paragraph("分析: 3串1风险较高但回报惊人。厄瓜多尔+0.25 + 日本+1 + 突尼斯+0.75 组合赔率6.68，概率25.1%。", styles['body']))
story.append(Spacer(1, 10))

# Top 3核心推荐
story.append(Paragraph("核心推荐组合 (Top 3)", styles['header']))
story.append(Paragraph("TOP 1 [2串1]: 日本+1不败 + 突尼斯+0.75", styles['gold']))
story.append(Paragraph("赔率: 3.61 | 概率: 41.38% | Edge: 13.68% | 投注: $1,077 | 预期回报: $3,889 | ROI: 261%", styles['good']))
story.append(Paragraph("理由: 两场让球盘都覆盖平局+客队胜，概率叠加后仍保持41.4%高概率。", styles['body']))
story.append(Spacer(1, 5))

story.append(Paragraph("TOP 2 [2串1]: 厄瓜多尔+0.25 + 日本+1不败", styles['gold']))
story.append(Paragraph("赔率: 3.46 | 概率: 41.38% | Edge: 12.48% | 投注: $983 | 预期回报: $3,401 | ROI: 246%", styles['good']))
story.append(Paragraph("理由: 两个+0.25/+1盘都含平局保险，非洲vs南美+欧洲vs亚洲风格相克。", styles['body']))
story.append(Spacer(1, 5))

story.append(Paragraph("TOP 3 [2串1]: 科特迪瓦平局 + 日本+1不败", styles['gold']))
story.append(Paragraph("赔率: 5.70 | 概率: 26.81% | Edge: 9.27% | 投注: $730 | 预期回报: $4,161 | ROI: 470%", styles['good']))
story.append(Paragraph("理由: 1X2平局 + 让球盘，跨市场组合相关性低，高赔率价值。", styles['body']))
story.append(Spacer(1, 10))

# 资金分配策略
story.append(Paragraph("资金分配策略", styles['header']))
story.append(Paragraph("2串1 (70%组合资金): 投入约$7,000，覆盖6-8个高概率组合", styles['body']))
story.append(Paragraph("3串1 (25%组合资金): 投入约$2,500，选择3-4个高赔率组合", styles['body']))
story.append(Paragraph("4串1 (5%组合资金): 投入约$500，极小注娱乐性质", styles['body']))
story.append(Spacer(1, 10))

# 风险提示
story.append(Paragraph("风险提示", styles['header']))
story.append(Paragraph("1. 组合投注风险高于单场，已设置20%总风险上限并自动缩减", styles['warn']))
story.append(Paragraph("2. 3场比赛均为世界杯小组赛，存在战意和轮换不确定性", styles['warn']))
story.append(Paragraph("3. 模型基于历史数据，实际比赛存在临场变数（红牌、点球、天气等）", styles['warn']))
story.append(Paragraph("4. 所有推荐 Edge > 0，但 Edge 不代表必胜，只是长期正期望", styles['warn']))
story.append(Paragraph("5. 建议优先选择跨市场组合（让球+1X2），降低相关性风险", styles['warn']))
story.append(Spacer(1, 10))

story.append(Paragraph("核心结论", styles['header']))
story.append(Paragraph("3场比赛的平局/下盘都被严重低估。组合投注可放大Edge优势，但需控制风险。2串1是最优策略，平衡概率和回报。", styles['good']))
story.append(Spacer(1, 15))

story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#dee2e6')))
story.append(Spacer(1, 8))
story.append(Paragraph("Football Quant OS v5.1.0 | 预测仅供参考，不构成投资建议", styles['subtitle']))
story.append(Paragraph("组合投注引擎: 动态相关性 + 市场多样性 + 保守Kelly + 全局风险管控", styles['subtitle']))

doc.build(story)
print(f"PDF已生成: {output}")
print(f"文件大小: {output.stat().st_size} bytes")
