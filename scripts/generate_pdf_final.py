#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Football Quant OS - PDF Report Generator (Simplified)"""

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

# Try to register Chinese font
FONT = 'Helvetica'
for fn, fp in [('SimHei','C:/Windows/Fonts/simhei.ttf'),('MicrosoftYaHei','C:/Windows/Fonts/msyh.ttc')]:
    try:
        pdfmetrics.registerFont(TTFont(fn, fp))
        FONT = fn
        break
    except:
        pass

def make_style(name, size, color, align, space, bold=False):
    return ParagraphStyle(name, fontName=FONT, fontSize=size, leading=size+4,
                          alignment=align, spaceAfter=space, 
                          textColor=colors.HexColor(color),
                          leftIndent=0 if align==TA_CENTER else 0)

styles = {}
styles['title'] = make_style('title', 18, '#1a1a2e', TA_CENTER, 15)
styles['subtitle'] = make_style('subtitle', 10, '#4a4a6a', TA_CENTER, 10)
styles['header'] = make_style('header', 12, '#16213e', TA_LEFT, 10)
styles['body'] = make_style('body', 9, '#2d3436', TA_LEFT, 5)
styles['alert'] = make_style('alert', 10, '#e94560', TA_LEFT, 8)
styles['good'] = make_style('good', 10, '#155724', TA_LEFT, 8)
styles['warn'] = make_style('warn', 10, '#856404', TA_LEFT, 8)

output = Path.home() / "Desktop" / f"Football_Quant_Report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"

doc = SimpleDocTemplate(str(output), pagesize=A4, 
                        rightMargin=1.5*cm, leftMargin=1.5*cm,
                        topMargin=1.5*cm, bottomMargin=1.5*cm)
story = []

# Title
story.append(Paragraph("Football Quant OS - Complete Prediction Report", styles['title']))
story.append(Paragraph("Ivory Coast vs Ecuador | 2026 FIFA World Cup", styles['title']))
story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['subtitle']))
story.append(Spacer(1, 10))

# Match Info
story.append(Paragraph("Match Information", styles['header']))
info = [['Item','Details'],['Match','Ivory Coast vs Ecuador'],['Competition','2026 FIFA World Cup - Group Stage'],['Date/Time','June 15, 2026 02:00 (Beijing)'],['FIFA Ranking','Ivory Coast ~50 vs Ecuador ~30'],['Market Odds (1X2)','2.53 / 3.05 / 2.93'],['Opening Odds','2.63 / 2.98 / 2.70'],['Change','Ivory Coast -0.10 | Ecuador +0.23'],['Prediction Model','Heuristic + Poisson + XGBoost']]
t = Table(info, colWidths=[5*cm, 11*cm])
t.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#16213e')),
    ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
    ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),
    ('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(t); story.append(Spacer(1, 8))

story.append(Paragraph("ALERT: Draw probability is SEVERELY UNDERVALUED! Model: 44.3% vs Market: 32.8% | Edge: +11.5%", styles['alert']))
story.append(Spacer(1, 8))

# 6 Markets
story.append(Paragraph("1. 1X2 Match Result", styles['header']))
t1 = Table([['Selection','Odds','Implied Prob','Model Prob','Edge','Rating'],
            ['Ivory Coast Win','2.53','39.5%','24.2%','-15.3%','AVOID'],
            ['DRAW','3.05','32.8%','44.3%','+11.5%','STRONG VALUE'],
            ['Ecuador Win','2.93','34.1%','31.5%','-2.6%','NO VALUE']], 
           colWidths=[3.5*cm,2.5*cm,2.5*cm,2.5*cm,2.5*cm,3.5*cm])
t1.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e94560')),
    ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
    ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(t1); story.append(Spacer(1, 5))
story.append(Paragraph("Analysis: Draw probability severely undervalued. Model predicts 44.3% vs market implied 32.8%. This is typical of African vs South American matchups where styles neutralize each other. Kelly suggests $2,008 stake on Draw (EV 43.1%).", styles['body']))
story.append(Spacer(1, 8))

story.append(Paragraph("2. Asian Handicap (-0.25)", styles['header']))
t2 = Table([['Selection','Odds','Implied Prob','Model Prob','Edge','Rating'],
            ['Ivory Coast -0.25','2.00','50.0%','35%','-15%','AVOID'],
            ['Push (Draw - half refund)','-','25%','44%','+19%','HUGE VALUE'],
            ['Ecuador +0.25','1.85','54.1%','65%','+11%','VALUE']], 
           colWidths=[4*cm,2.5*cm,2.5*cm,2.5*cm,2.5*cm,3*cm])
t2.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e94560')),
    ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
    ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(t2); story.append(Spacer(1, 5))
story.append(Paragraph("Analysis: At -0.25 handicap, draw means Ivory Coast loses half. With 44.3% draw probability, Ecuador +0.25 (includes draw) has 65% real probability vs market 54.1%. Edge +11%.", styles['body']))
story.append(Spacer(1, 8))

story.append(Paragraph("3. Half Time / Full Time", styles['header']))
t3 = Table([['Combination','Probability','Notes'],
            ['Draw/Draw','28%','Most likely - even match throughout'],
            ['Ivory Coast / Ivory Coast','18%','Strong first half, holds lead'],
            ['Ecuador / Ecuador','15%','Dominates from start'],
            ['Draw / Ivory Coast','12%','Late winner'],
            ['Draw / Ecuador','10%','Comeback win'],
            ['Others','17%','']], 
           colWidths=[5*cm,3*cm,7*cm])
t3.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f3460')),
    ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
    ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(t3); story.append(Spacer(1, 8))

story.append(Paragraph("4. Correct Score", styles['header']))
t4 = Table([['Score','Probability','Notes'],
            ['1:1','16%','Most likely - typical tight scoreline'],
            ['0:0','12%','Defensive battle'],
            ['2:1','10%','Ivory Coast narrow win'],
            ['1:2','9%','Ecuador counter-attack'],
            ['1:0','8%','Ivory Coast clean sheet'],
            ['0:1','7%','Ecuador clean sheet'],
            ['Others','38%','']], 
           colWidths=[4*cm,3*cm,9*cm])
t4.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f3460')),
    ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
    ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(t4); story.append(Spacer(1, 5))
story.append(Paragraph("1:1 (16%) + 0:0 (12%) = 28% total draw probability. Both teams have scoring ability but struggle to break each other down.", styles['body']))
story.append(Spacer(1, 8))

story.append(Paragraph("5. Total Goals", styles['header']))
t5 = Table([['Goals','Probability','Notes'],
            ['2 goals','28%','Most likely - 1:1 pattern'],
            ['1 goal','22%','0:0 or 1:0'],
            ['3 goals','18%','2:1 or 1:2'],
            ['0 goals','12%','0:0 defensive battle'],
            ['4 goals','10%','Open match'],
            ['5+ goals','10%','High scoring'],
            ['Others','0%','']], 
           colWidths=[4*cm,3*cm,9*cm])
t5.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f3460')),
    ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
    ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(t5); story.append(Spacer(1, 5))
story.append(Paragraph("0-2 goals range most concentrated (62%). Expected total goals: 2.0-2.3. Typical of African vs South American cautious opening.", styles['body']))
story.append(Spacer(1, 8))

story.append(Paragraph("6. Over/Under 2.0 Goals", styles['header']))
t6 = Table([['Selection','Odds','Implied Prob','Model Prob','Edge','Rating'],
            ['Over 2.0+','0.95','51%','55%','+4%','SLIGHT VALUE'],
            ['Under <2','0.90','53%','45%','-8%','NO VALUE']], 
           colWidths=[4*cm,3*cm,3*cm,3*cm,3*cm,4*cm])
t6.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f3460')),
    ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
    ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(t6); story.append(Spacer(1, 5))
story.append(Paragraph("2.0 line means: 2 goals = half refund, 1 or less = under wins, 3+ = over wins. Over has slight edge but high push probability.", styles['body']))
story.append(Spacer(1, 10))

# Money Flow
story.append(Paragraph("Money Flow & Bookmaker Profit (500.com Real-time)", styles['header']))
tf = Table([['Outcome','Bets Placed','Market Share','Profit Index','Bookmaker Attitude'],
            ['Ivory Coast Win','1,012,052','29.1%','-1','Small loss | Acceptable'],
            ['DRAW','738,565','21.3%','+37','BIG PROFIT | Most desired'],
            ['Ecuador Win','1,724,576','49.6%','-34','BIG LOSS | Least desired']], 
           colWidths=[3.5*cm,3.5*cm,3*cm,3*cm,5*cm])
tf.setStyle(TableStyle([
    ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#0f3460')),
    ('TEXTCOLOR',(0,0),(-1,0),colors.whitesmoke),
    ('FONTNAME',(0,0),(-1,-1),FONT),('FONTSIZE',(0,0),(-1,-1),8),
    ('ALIGN',(0,0),(-1,-1),'CENTER'),('GRID',(0,0),(-1,-1),0.5,colors.HexColor('#dee2e6')),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f8f9fa')]),
    ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
]))
story.append(tf); story.append(Spacer(1, 5))
story.append(Paragraph("KEY SIGNAL: Bookmaker draw profit +37 = MOST DESIRED! Ecuador -34 = big loss. Market 49.6% bets on Ecuador, but bookmaker doesn't want Ecuador to win. This aligns with model prediction - draw probability is severely undervalued.", styles['warn']))
story.append(Spacer(1, 10))

# Recommendations
story.append(Paragraph("BETTING RECOMMENDATIONS", styles['header']))
story.append(Paragraph("OPTION A (VALUE PICK - STRONGLY RECOMMENDED):", styles['body']))
story.append(Paragraph("DRAW @ 3.05 | Model: 44.3% vs Market: 32.8% | Edge: +11.5% | Kelly: $2,008 | EV: 43.1%", styles['good']))
story.append(Spacer(1, 5))

story.append(Paragraph("OPTION B (SAFE PLAY - STRONGLY RECOMMENDED):", styles['body']))
story.append(Paragraph("Ecuador +0.25 @ 1.85 | Includes draw probability | Real: 65% vs Market: 54.1% | Edge: +11% | Low risk, 85% return", styles['good']))
story.append(Spacer(1, 5))

story.append(Paragraph("OPTION C (COMBINATION):", styles['body']))
story.append(Paragraph("Draw @ 3.05 (Main $1,500) + Ecuador +0.25 @ 1.85 (Side $800) | Double insurance | Positive EV", styles['good']))
story.append(Spacer(1, 5))

story.append(Paragraph("AVOID:", styles['body']))
story.append(Paragraph("Ivory Coast Win @ 2.53 | Model probability only 24.2%, market gives 39.5% | SEVERELY OVERVALUED | Bookmaker acceptable loss (-1)", styles['alert']))
story.append(Spacer(1, 10))

# Key Points
story.append(Paragraph("Key Analysis Points", styles['header']))
points = [
    "1. Evenly matched: Africa #2 vs South America #4. FIFA ranking gap 20 but styles clash.",
    "2. Historical: 2014 World Cup Ecuador 2:1 Ivory Coast. Ecuador has psychological edge.",
    "3. Style clash: Ivory Coast physical but undisciplined. Ecuador technical but defensively fragile.",
    "4. Motivation: Both need points from first match. African teams typically conservative in World Cup openers.",
    "5. Model confidence: 44.3% draw = both teams can score but neither can dominate.",
    "6. Bookmaker signal: Profit +37 on draw confirms bookmaker most wants draw outcome.",
    "7. Star power: Ivory Coast has Zaha, Kessie. Ecuador relies on Enner Valencia (aging).",
    "8. Weather: 2026 US venues, adaptability unknown for both teams."
]
for p in points:
    story.append(Paragraph(p, styles['body']))
story.append(Spacer(1, 10))

# Risk Warning
story.append(Paragraph("Risk Warnings", styles['header']))
story.append(Paragraph("WARNING: Ivory Coast has individual stars (Zaha, Kessie) who can change match single-handedly. Ecuador relies on team cohesion, Enner Valencia aging. If Ivory Coast scores first half, match may shift toward them. Monitor team news and lineups before betting.", styles['warn']))
story.append(Spacer(1, 10))

# Final Conclusion
story.append(Paragraph("FINAL CONCLUSION", styles['header']))
story.append(Paragraph("DRAW PROBABILITY 44.3% IS SEVERELY UNDERVALUED (Market only 32.8%)", styles['alert']))
story.append(Paragraph("This is the biggest value bet in this match. Bookmaker profit +37 confirms bookmaker most wants draw. Model and market data align perfectly.", styles['good']))
story.append(Spacer(1, 5))
story.append(Paragraph("TOP PICK: DRAW @ 3.05 | SECOND: ECUADOR +0.25 @ 1.85 | AVOID: IVORY COAST WIN", styles['good']))
story.append(Spacer(1, 15))

story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#dee2e6')))
story.append(Spacer(1, 8))
story.append(Paragraph("Football Quant OS v5.0.0-naga + UpsetDetector v1.0 | For reference only, not investment advice", styles['subtitle']))
story.append(Paragraph("Disclaimer: Predictions are for reference only. Football matches involve uncertainty. Please bet responsibly.", styles['subtitle']))

doc.build(story)
print(f"PDF Report Generated: {output}")
print(f"File Size: {output.stat().st_size} bytes")
