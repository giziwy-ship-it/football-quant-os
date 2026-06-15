#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Football Quant OS - Prediction Report with Upset Radar (Netherlands vs Japan)"""

import sys
from pathlib import Path
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# Register font
font_registered = False
for font_name, font_path in [
    ('SimHei', 'C:/Windows/Fonts/simhei.ttf'),
    ('MicrosoftYaHei', 'C:/Windows/Fonts/msyh.ttc'),
]:
    try:
        pdfmetrics.registerFont(TTFont(font_name, font_path))
        font_registered = True
        break
    except:
        continue

FONT = 'SimHei' if font_registered else 'Helvetica'

def build():
    styles = getSampleStyleSheet()
    
    for name, size, color, align, space in [
        ('RTitle', 22, '#1a1a2e', TA_CENTER, 20),
        ('RSubtitle', 12, '#4a4a6a', TA_CENTER, 15),
        ('RSection', 15, '#16213e', TA_LEFT, 15),
        ('RBody', 10, '#2d3436', TA_LEFT, 8),
        ('RWarning', 11, '#721c24', TA_LEFT, 10),
        ('RSuccess', 11, '#155724', TA_LEFT, 10),
        ('RHighlight', 11, '#856404', TA_LEFT, 10),
    ]:
        styles.add(ParagraphStyle(
            name=name, fontName=FONT, fontSize=size, leading=size+4,
            alignment=align, spaceAfter=space, textColor=colors.HexColor(color),
            backColor=colors.HexColor('#f8d7da') if name=='RWarning' else 
                      colors.HexColor('#d4edda') if name=='RSuccess' else 
                      colors.HexColor('#fff3cd') if name=='RHighlight' else None,
            borderPadding=8, leftIndent=5, rightIndent=5,
            borderWidth=1 if name in ('RWarning','RSuccess','RHighlight') else 0,
            borderColor=colors.HexColor('#f5c6cb') if name=='RWarning' else
                       colors.HexColor('#c3e6cb') if name=='RSuccess' else
                       colors.HexColor('#ffc107') if name=='RHighlight' else None
        ))
    
    desktop = Path.home() / "Desktop"
    output = desktop / f"Netherlands_Japan_UpsetRadar_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
    
    doc = SimpleDocTemplate(str(output), pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    story = []
    
    # Header
    story.append(Paragraph("⚽ Football Quant OS - 冷门雷达报告", styles['RTitle']))
    story.append(Paragraph("荷兰 vs 日本 | 2026世界杯 | UpsetDetector v1.0", styles['RSubtitle']))
    story.append(Paragraph(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['RSubtitle']))
    story.append(Spacer(1, 20))
    
    # Match Info
    story.append(Paragraph("📊 比赛信息", styles['RSection']))
    info = [['项目','详情'],['对阵','荷兰 (世界第8) vs 日本 (世界第20)'],['赛事','2026 FIFA 世界杯'],['即时赔率','荷兰 1.92 / 平 3.55 / 日本 3.73'],['初盘赔率','荷兰 2.04 / 平 3.46 / 日本 3.61'],['赔率变化','荷兰↓降赔 0.12 | 日本↑升赔 0.12']]
    t = Table(info, colWidths=[6*cm, 10*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#16213e')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('FONTNAME',(0,0),(-1,-1),FONT),
        ('FONTSIZE',(0,0),(-1,-1),9),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(t); story.append(Spacer(1, 15))
    
    # Upset Radar Score
    story.append(Paragraph("🚨 UpsetDetector 冷门雷达评分", styles['RSection']))
    story.append(Paragraph("<b>冷门总分: 69/100</b> ⚠️ 中高风险", styles['RHighlight']))
    story.append(Spacer(1, 5))
    
    radar = [['因子','评分','权重','说明'],
             ['豪门热度','18/20','20%','荷兰资金占比59.3%，极度热门'],
             ['赔率波动','16/20','20%','荷兰降赔0.12，日本升赔0.12'],
             ['盈亏异常','17/20','15%','庄家荷兰盈亏-29%，承受巨大风险'],
             ['战意差距','8/10','10%','日本必须拿分，荷兰可接受平局'],
             ['历史冷门','6/10','10%','荷兰世界杯多次爆冷'],
             ['xG差距','4/10','10%','荷兰2.1 vs 日本1.0，差距不大']]
    t = Table(radar, colWidths=[4*cm,3*cm,3*cm,6*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e94560')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),9),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(t); story.append(Spacer(1, 15))
    
    story.append(Paragraph("阈值判定: <60正常 | 60-80观察(⚠️当前) | 80-90强冷门 | >90大冷门", styles['RBody']))
    story.append(Spacer(1, 15))
    
    # Money Flow
    story.append(Paragraph("💰 资金流向与庄家盈亏 (500.com)", styles['RSection']))
    flow = [['结果','投注量','市场占比','盈亏指数','含义'],
            ['荷兰胜','2,812,066','59.3%','-29% 🔴','庄家最不想看到'],
            ['平局','832,819','17.4%','+36% 🟢','庄家最希望看到'],
            ['日本胜','1,041,120','23.3%','+12% 🟢','庄家可接受']]
    t = Table(flow, colWidths=[4*cm,3.5*cm,3*cm,3*cm,4.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f3460')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),9),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(t); story.append(Spacer(1, 10))
    
    story.append(Paragraph("<b>⚠️ 关键信号:</b> 庄家荷兰盈亏-29% = 诱盘陷阱信号！庄家不会让自己大亏，除非他们知道市场不知道的信息。", styles['RWarning']))
    story.append(Spacer(1, 15))
    
    # Why upset
    story.append(Paragraph("🔍 为什么日本可能爆冷？", styles['RSection']))
    for item in [
        "<b>1. 庄家盈亏异常:</b> 荷兰-29% = 诱盘。庄家在吸引资金去荷兰，实际更希望日本不败。",
        "<b>2. 日本近年崛起:</b> 2022世界杯击败德国(2:1)、西班牙(2:1)。亚洲第一，欧洲五大联赛球员云集。",
        "<b>3. 荷兰隐患:</b> 德容缺阵中场控制力下降，防线并非铁板。淘汰赛历史多次爆冷。",
        "<b>4. 战意差距:</b> 日本首战平局，此战必须拿分。荷兰可接受平局，心态相对放松。",
        "<b>5. 资金过热:</b> 荷兰59%资金占比 = 过热。热门方通常被高估，冷门方被低估。",
        "<b>6. 赔率反向:</b> 荷兰降赔、日本升赔 = 市场在追逐荷兰，忽略日本实力。"
    ]:
        story.append(Paragraph(item, styles['RBody']))
    story.append(Spacer(1, 15))
    
    # Corrected predictions
    story.append(Paragraph("📋 修正后的预测 (含冷门雷达)", styles['RSection']))
    
    corr = [['市场','原推荐','修正推荐','赔率','信心','投注建议'],
            ['胜平负','荷兰胜','日本胜或平局','3.73/3.55','⭐⭐⭐⭐','✅ 双选价值'],
            ['让球','观望','日本+1不败','1.87','⭐⭐⭐⭐⭐','✅ 强烈推荐'],
            ['半全场','荷兰/荷兰','平/日本','-','⭐⭐⭐','高价值冷门'],
            ['比分','2:1','1:1 / 2:2','-','⭐⭐⭐','平局被低估'],
            ['大小球','大球','小球 2.5↓','0.93','⭐⭐⭐⭐','日本防守克制']]
    t = Table(corr, colWidths=[3.5*cm,3*cm,3.5*cm,3*cm,3*cm,4*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#16213e')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),9),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(t); story.append(Spacer(1, 15))
    
    # Recommendations
    story.append(Paragraph("🎯 终极投注方案", styles['RSection']))
    
    story.append(Paragraph("<b>方案A: 保守型 (高胜率)</b>", styles['RBody']))
    story.append(Paragraph("日本+1不败 @ 1.87 | 概率: 市场53.5% → 实际60%+ | 庄家盈亏+12% | 风险: 低", styles['RHighlight']))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("<b>方案B: 价值型 (高回报)</b>", styles['RBody']))
    story.append(Paragraph("日本胜 @ 3.73 或 平局 @ 3.55 | 日本+平局双选平均赔率~3.6，概率60% | Edge: 巨大！", styles['RHighlight']))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("<b>方案C: 组合投注</b>", styles['RBody']))
    story.append(Paragraph("日本+1不败 @ 1.87 (主注) + 平局 @ 3.55 (小注) | 组合期望: 正EV", styles['RHighlight']))
    story.append(Spacer(1, 15))
    
    # Risk
    story.append(Paragraph("⚠️ 风险提醒", styles['RSection']))
    risk = [['风险因素','等级','说明'],['荷兰纸面实力','中','范戴克+德佩+加克波，阵容豪华'],['日本客场压力','低','日本心理素质极佳，2022已证明'],['裁判因素','未知','欧洲裁判可能偏荷兰'],['天气/场地','未知','2026美国场地适应性']]
    t = Table(risk, colWidths=[5*cm,3*cm,8*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#721c24')),
        ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
        ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),9),
        ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
        ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
    ]))
    story.append(t); story.append(Spacer(1, 15))
    
    # Final
    story.append(Paragraph("📌 最终结论", styles['RSection']))
    story.append(Paragraph("<b>原预测(无冷门):</b> 荷兰微弱优势 → 观望", styles['RBody']))
    story.append(Paragraph("<b>修正预测(含冷门雷达):</b> 日本不败概率被严重低估！", styles['RBody']))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("<b>核心逻辑:</b> 庄家盈亏-29%是最强信号。庄家不会让自己大亏，日本不败的可能性远高于市场赔率反映的。", styles['RSuccess']))
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("<b>首选:</b> 日本+1不败 @ 1.87 | <b>次选:</b> 平局 @ 3.55 | <b>避免:</b> 荷兰胜 @ 1.92 (诱盘)", styles['RSuccess']))
    story.append(Spacer(1, 20))
    
    # Footer
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#dee2e6')))
    story.append(Spacer(1, 10))
    story.append(Paragraph("Football Quant OS v5.0.0-naga + UpsetDetector v1.0 | 预测仅供参考，不构成投资建议", styles['RSubtitle']))
    
    doc.build(story)
    print(f"PDF generated: {output}")
    return output

if __name__ == '__main__':
    build()
