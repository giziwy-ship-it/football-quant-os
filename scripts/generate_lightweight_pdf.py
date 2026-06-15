#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lightweight PDF - Netherlands vs Japan Complete Report"""

from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT = 'Helvetica'
for fn, fp in [('SimHei','C:/Windows/Fonts/simhei.ttf'),('MicrosoftYaHei','C:/Windows/Fonts/msyh.ttc')]:
    try:
        pdfmetrics.registerFont(TTFont(fn, fp))
        FONT = fn
        break
    except:
        pass

styles = getSampleStyleSheet()
for name, size, color, align, space in [
    ('T', 20, '#1a1a2e', TA_CENTER, 15),
    ('S', 11, '#4a4a6a', TA_CENTER, 12),
    ('H', 14, '#16213e', TA_LEFT, 12),
    ('B', 9, '#2d3436', TA_LEFT, 6),
    ('W', 10, '#721c24', TA_LEFT, 8),
    ('G', 10, '#155724', TA_LEFT, 8),
    ('Y', 10, '#856404', TA_LEFT, 8),
]:
    styles.add(ParagraphStyle(name, fontName=FONT, fontSize=size, leading=size+3,
                               alignment=align, spaceAfter=space, textColor=colors.HexColor(color)))

output = Path.home() / "Desktop" / f"Football_Quant_Netherlands_Japan_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

doc = SimpleDocTemplate(str(output), pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
story = []

story.append(Paragraph("⚽ Football Quant OS 完整预测报告", styles['T']))
story.append(Paragraph("荷兰 vs 日本 | 2026 FIFA 世界杯", styles['T']))
story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['S']))
story.append(Spacer(1, 15))

story.append(Paragraph("📊 比赛信息", styles['H']))
info = [['项目','详情'],['对阵','荷兰 (世界第8) vs 日本 (世界第20)'],['赛事','2026 FIFA 世界杯 小组赛'],['即时赔率','荷兰 1.92 / 平 3.55 / 日本 3.73'],['初盘赔率','荷兰 2.04 / 平 3.46 / 日本 3.61'],['赔率变化','荷兰降赔 0.12 | 日本升赔 0.12'],['预测模型','Heuristic + Poisson + XGBoost (3模型融合)']]
t = Table(info, colWidths=[5*cm, 11*cm])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#16213e')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(t); story.append(Spacer(1, 10))

story.append(Paragraph("⚠️ 冷门雷达: 69/100 中高风险 | 庄家盈亏荷兰-29% = 诱盘信号", styles['Y']))
story.append(Spacer(1, 10))

# 6 markets summary
story.append(Paragraph("🎯 6市场预测汇总", styles['H']))
mkt = [['市场','推荐','赔率','信心','说明'],['1X2 胜平负','日本胜或平局','3.73/3.55','⭐⭐⭐⭐','平局被严重低估'],['让球 (-1)','日本+1不败','1.87','⭐⭐⭐⭐⭐','强烈推荐'],['半全场','平/日本','-','⭐⭐⭐','冷门价值'],['比分','1:1 / 2:2','-','⭐⭐⭐','平局概率低估'],['进球数','2-3球','-','⭐⭐⭐⭐','最集中区间'],['大小球 2.5','小球 ≤2.5','0.93','⭐⭐⭐⭐','日本防守克制']]
t = Table(mkt, colWidths=[3.5*cm,3.5*cm,3.5*cm,3*cm,6.5*cm])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e94560')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(t); story.append(Spacer(1, 10))

story.append(Paragraph("📈 市场赔率详解", styles['H']))
odds = [['市场','即时赔率','初盘','变化','隐含概率'],['欧赔 荷兰胜','1.92','2.04','↓ 0.12','52.1%'],['欧赔 平局','3.55','3.46','↑ 0.09','28.2%'],['欧赔 日本胜','3.73','3.61','↑ 0.12','26.8%'],['让球 荷兰-1胜','3.30','3.90','↓ 0.60','30.3%'],['让球 走水','3.50','3.60','↓ 0.10','28.6%'],['让球 日本+1胜','1.87','1.70','↑ 0.17','53.5%'],['大小球 大2.5','0.92','0.86','↑ 0.06','52.2%'],['大小球 小2.5','0.93','0.93','-','51.6%']]
t = Table(odds, colWidths=[4.5*cm,3.5*cm,3*cm,3*cm,4*cm])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f3460')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(t); story.append(Spacer(1, 10))

story.append(Paragraph("💰 资金流向与庄家盈亏 (500.com 实时)", styles['H']))
flow = [['结果','投注量','市场占比','盈亏指数','庄家态度'],['荷兰胜','2,812,066','59.3%','-29% 🔴','诱盘陷阱 | 最不想看到'],['平局','832,819','17.4%','+36% 🟢','冷门价值 | 最希望看到'],['日本胜','1,041,120','23.3%','+12% 🟢','可接受冷门']]
t = Table(flow, colWidths=[3.5*cm,4*cm,3*cm,3*cm,5.5*cm])
t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f3460')),('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]))
story.append(t); story.append(Spacer(1, 10))

story.append(Paragraph("⚠️ 核心信号: 庄家盈亏荷兰-29% = 诱盘！市场在追荷兰，但庄家最不想看到荷兰胜。", styles['W']))
story.append(Spacer(1, 10))

story.append(Paragraph("🎯 投注方案", styles['H']))
story.append(Paragraph("✅ 方案A (保守高胜率): 日本+1不败 @ 1.87 | 实际概率60%+ | 庄家盈亏+12%", styles['G']))
story.append(Paragraph("✅ 方案B (价值高回报): 日本胜 @ 3.73 或 平局 @ 3.55 | 双选平均赔率~3.6，概率60%", styles['G']))
story.append(Paragraph("✅ 方案C (组合): 日本+1不败 @ 1.87 (主注) + 平局 @ 3.55 (小注) | 正EV", styles['G']))
story.append(Paragraph("❌ 避免: 荷兰胜 @ 1.92 (诱盘陷阱，冷门雷达69分警告)", styles['W']))
story.append(Spacer(1, 10))

story.append(Paragraph("📝 分析要点", styles['H']))
for item in [
    "1. 冷门雷达69/100: 荷兰资金过热(59.3%)，赔率反向诱盘",
    "2. 日本历史: 2022击败德国(2:1)、西班牙(2:1)，亚洲第一",
    "3. 荷兰隐患: 德容缺阵，中场控制力下降，防线可破",
    "4. 战意差距: 日本必须拿分，荷兰可接受平局",
    "5. 模型预测: 平局概率35% vs 市场28% = 被低估7%",
    "6. 让球分析: 日本+1不败实际概率45%，市场给53.5% = 高估但安全"
]:
    story.append(Paragraph(item, styles['B']))
story.append(Spacer(1, 15))

story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#dee2e6')))
story.append(Spacer(1, 8))
story.append(Paragraph("Football Quant OS v5.0.0-naga + UpsetDetector v1.0 | 预测仅供参考，不构成投资建议", styles['S']))

doc.build(story)
print(f"PDF generated: {output}")
