#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
McKinsey-Style PDF Report Generator
USA vs Paraguay - 2026 FIFA World Cup Analysis
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
from datetime import datetime

OUTPUT_FILE = "USA_vs_Paraguay_McKinsey_Report.pdf"

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
        fontName='Helvetica-Bold',
        fontSize=28,
        textColor=MCKINSEY_BLUE,
        spaceAfter=12,
        leading=34,
        alignment=TA_LEFT
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseySubtitle',
        fontName='Helvetica',
        fontSize=14,
        textColor=MCKINSEY_GRAY,
        spaceAfter=20,
        leading=18,
        alignment=TA_LEFT
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseySection',
        fontName='Helvetica-Bold',
        fontSize=16,
        textColor=MCKINSEY_BLUE,
        spaceBefore=20,
        spaceAfter=10,
        leading=20,
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseySubsection',
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=MCKINSEY_DARK_GRAY,
        spaceBefore=14,
        spaceAfter=6,
        leading=16
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyBody',
        fontName='Helvetica',
        fontSize=10,
        textColor=MCKINSEY_DARK_GRAY,
        spaceAfter=8,
        leading=14,
        alignment=TA_JUSTIFY
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyBullet',
        fontName='Helvetica',
        fontSize=10,
        textColor=MCKINSEY_DARK_GRAY,
        spaceAfter=6,
        leading=14,
        leftIndent=15,
        bulletIndent=5,
        bulletFontName='Helvetica-Bold',
        bulletFontSize=10,
        bulletColor=MCKINSEY_ACCENT
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyInsight',
        fontName='Helvetica-Bold',
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
        fontName='Helvetica-Bold',
        fontSize=9,
        textColor=colors.white,
        alignment=TA_CENTER,
        leading=12
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyTableCell',
        fontName='Helvetica',
        fontSize=9,
        textColor=MCKINSEY_DARK_GRAY,
        alignment=TA_CENTER,
        leading=12
    ))
    
    styles.add(ParagraphStyle(
        name='McKinseyFooter',
        fontName='Helvetica',
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
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
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
    style_commands.append(('FONTNAME', (0, 1), (-1, -1), 'Helvetica'))
    style_commands.append(('FONTSIZE', (0, 1), (-1, -1), 9))
    table.setStyle(TableStyle(style_commands))
    return table

def build_pdf(filename):
    doc = SimpleDocTemplate(filename, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
    styles = create_styles()
    story = []
    
    # COVER PAGE
    story.append(Spacer(1, 30))
    story.append(Paragraph("2026 FIFA WORLD CUP", styles['McKinseyTitle']))
    story.append(blue_header_bar())
    story.append(Paragraph("Match Analysis: USA vs Paraguay", styles['McKinseySubtitle']))
    story.append(Spacer(1, 10))
    
    meta_data = [
        ['Match', 'USA vs Paraguay'],
        ['Group', 'Group D'],
        ['Round', 'Round 1'],
        ['Date', 'June 13, 2026'],
        ['Time', '09:00 GMT+8'],
        ['Venue', 'USA (Host)'],
    ]
    meta_table = Table(meta_data, colWidths=[120, 300])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), MCKINSEY_LIGHT_BLUE),
        ('TEXTCOLOR', (0, 0), (0, -1), MCKINSEY_BLUE),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
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
        f"<b>Report Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        f"<b>System:</b> Naga Core Football Quant OS v2.0 | "
        f"<b>Data:</b> 500.com, FIFA, Historical",
        styles['McKinseyBody']
    ))
    story.append(PageBreak())
    
    # EXECUTIVE SUMMARY
    story.append(Paragraph("EXECUTIVE SUMMARY", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "USA enters the opening match of the 2026 World Cup as the host nation, "
        "facing Paraguay in Group D. While the United States holds a 24-position "
        "FIFA ranking advantage (#17 vs #41), market signals indicate significant "
        "public overconfidence, with 77.9% of betting volume concentrated on the USA "
        "despite fair odds implying only a 46% win probability.",
        styles['McKinseyBody']
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "KEY INSIGHT: The market exhibits an 'odds reverse' pattern—heavy betting "
        "flow (77.9%) on the USA without proportional odds compression (2.05), "
        "suggesting bookmakers may be pricing in defensive risk. USA's recent form "
        "shows vulnerability (1.7 goals conceded per game), while Paraguay's compact "
        "defense and counter-attack capability pose a credible upset threat.",
        styles['McKinseyInsight']
    ))
    story.append(Spacer(1, 10))
    
    summary_data = [
        ['Metric', 'USA', 'Paraguay', 'Assessment'],
        ['FIFA Ranking', '#17 (1671 pts)', '#41 (1505 pts)', 'Advantage USA'],
        ['Recent Form', '5W-1D-4L', '4W-2D-4L', 'Even'],
        ['Home Advantage', 'Host Nation', 'Away', 'Strong USA'],
        ['Market Flow', '77.9% bets', '9.4% bets', 'Distortion'],
        ['Defense (GA/game)', '1.7', '1.0', 'Advantage PAR'],
        ['Attack (GF/game)', '1.8', '1.2', 'Advantage USA'],
        ['UpsetDetector Score', '48/100', '—', 'Normal Risk'],
    ]
    summary_table = create_table(summary_data, [130, 110, 110, 110])
    story.append(summary_table)
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "<b>Bottom Line:</b> USA is the rightful favorite, but the market has overpriced "
        "their probability. The optimal risk-adjusted position favors either no bet or "
        "a small value stake on Paraguay at 3.83, given the defensive vulnerabilities "
        "exposed in USA's recent friendlies.",
        styles['McKinseyBody']
    ))
    story.append(PageBreak())
    
    # SIX-DIMENSION ANALYSIS
    story.append(Paragraph("SIX-DIMENSION ANALYSIS", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    
    dimensions = [
        ("1. ELO RATING & FIFA RANKING",
         "USA holds a 24-position FIFA ranking advantage (#17 vs #41) with a 166-point gap. "
         "ELO model suggests ~58% win probability. However, ranking gaps of 20-30 positions "
         "in World Cup openers have historically produced upsets in 18% of cases."),
        ("2. RECENT FORM & PERFORMANCE",
         "USA last 10: 5W-1D-4L, 1.8 GF, 1.7 GA. Paraguay last 10: 4W-2D-4L, 1.2 GF, 1.0 GA. "
         "Paraguay's recent form is actually stronger (3W-1D-1L in last 5 vs USA's 2W-3L). "
         "USA's defensive record is concerning—conceding 17 goals in 10 friendlies."),
        ("3. HOME ADVANTAGE & MOTIVATION",
         "Host nations in World Cup openers have 72% win rate. USA motivation: 0.95/1.0. "
         "Paraguay underdog mentality reduces pressure, motivation: 0.85/1.0. Travel favors USA."),
        ("4. MARKET SIGNAL & BETTING FLOW",
         "500.com data: 77.9% volume on USA, 9.4% on Paraguay. Implied prob: 46.0% USA, 24.7% PAR. "
         "+31.9% flow-probability gap = 'odds reverse' signal. Bookmaker PnL: -15.5M on USA win."),
        ("5. INJURY & SQUAD STRENGTH",
         "USA: Weah (RW) injured. Key players: Pulisic, McKennie, Balogun, Adams. "
         "Paraguay: No injuries. Key players: Almiron, Enciso, Sanabria, Gomez. "
         "Paraguay's squad is more experienced defensively."),
        ("6. HISTORICAL H2H & TACTICAL MATCHUP",
         "Last 5 H2H: USA 3W-2L, 5-5 goals. Tactical battle: USA high press vs Paraguay compact counter. "
         "Key vulnerability: USA defense (1.7 GA) exposed by pace—Almiron and Enciso are ideal weapons.")
    ]
    for title, text in dimensions:
        story.append(Paragraph(title, styles['McKinseySubsection']))
        story.append(Paragraph(text, styles['McKinseyBody']))
        story.append(Spacer(1, 5))
    story.append(PageBreak())
    
    # MARKET INTELLIGENCE
    story.append(Paragraph("MARKET INTELLIGENCE", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "Real-time data from 500.com captured at 07:28 GMT+8, ~1.5 hours before kickoff. "
        "Total traded volume: 23.3M HKD.", styles['McKinseyBody']
    ))
    story.append(Spacer(1, 10))
    
    market_data = [
        ['Outcome', 'Odds', 'Implied Prob', 'Betting Flow', 'Bf Volume', 'Bookmaker PnL', 'Hot Index'],
        ['USA Win', '2.05', '46.0%', '77.9%', '18.2M HKD', '-15.5M HKD', '69 (Hot)'],
        ['Draw', '3.23', '29.3%', '12.8%', '3.0M HKD', '+13.5M HKD', '-57 (Cold)'],
        ['Paraguay Win', '3.83', '24.7%', '9.4%', '2.2M HKD', '+14.2M HKD', '-62 (Cold)'],
    ]
    market_table = create_table(market_data, [80, 55, 70, 70, 80, 90, 65])
    story.append(market_table)
    story.append(Spacer(1, 15))
    
    story.append(Paragraph("Market Signals Analysis", styles['McKinseySubsection']))
    signals = [
        "<b>Odds Reverse Signal (15/20):</b> 77.9% volume on USA, yet odds at 2.05 (46%). Efficient market would compress to ~1.70.",
        "<b>Abnormal Flow (12/15):</b> Flow imbalance 77.9% vs 9.4%. Historically, >70% imbalance produces upsets in 22% of cases.",
        "<b>Bookmaker Risk:</b> -15.5M HKD PnL on USA win. If Paraguay wins, bookmakers collect +14.2M HKD.",
        "<b>Volume Surge:</b> Total volume increased 126% overnight (10.3M to 23.3M HKD), suggesting retail money.",
    ]
    for signal in signals:
        story.append(Paragraph(signal, styles['McKinseyBullet'], bulletText='•'))
    story.append(PageBreak())
    
    # COMPLETE PREDICTIONS
    story.append(Paragraph("COMPLETE PREDICTIONS", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    
    story.append(Paragraph("1. Match Result (1X2)", styles['McKinseySubsection']))
    x2_data = [
        ['Outcome', 'Model Prob', 'Fair Odds', 'Market Odds', 'Edge', 'Recommendation'],
        ['USA Win', '46.4%', '2.16', '2.05', '-5.1%', 'No Value'],
        ['Draw', '24.9%', '4.02', '3.23', '-19.7%', 'No Value'],
        ['Paraguay Win', '28.7%', '3.48', '3.83', '+10.1%', 'Slight Value'],
    ]
    story.append(create_table(x2_data, [80, 70, 70, 70, 60, 100]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("2. Asian Handicap", styles['McKinseySubsection']))
    ah_data = [
        ['Handicap', 'USA Win', 'Push', 'USA Lose', 'Recommendation'],
        ['USA -1', '24.1%', '22.6%', '53.3%', 'Avoid'],
        ['USA -0.5', '46.4%', '—', '53.6%', 'Avoid'],
        ['Draw No Bet (0)', '46.4%', '24.9%', '28.7%', 'Neutral'],
        ['USA +0.5', '71.3%', '—', '28.7%', 'Safe'],
        ['USA +1', '88.3%', '16.9%', '11.7%', 'Conservative'],
    ]
    story.append(create_table(ah_data, [100, 70, 60, 70, 120]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("3. Half-Time / Full-Time", styles['McKinseySubsection']))
    htft_data = [
        ['HT / FT', 'Description', 'Probability'],
        ['D / H', 'Draw at HT → USA Win', '19.2%'],
        ['H / H', 'USA Lead at HT → USA Win', '17.1%'],
        ['D / A', 'Draw at HT → PAR Win', '11.9%'],
        ['H / A', 'USA Lead at HT → PAR Win (Upset)', '10.6%'],
        ['D / D', 'Draw at HT → Draw', '10.3%'],
    ]
    story.append(create_table(htft_data, [70, 250, 80]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("4. Correct Score (Top 10)", styles['McKinseySubsection']))
    score_data = [
        ['Rank', 'Score', 'Probability', 'Cumulative'],
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
    story.append(create_table(score_data, [50, 70, 80, 80]))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("5. Total Goals & Over/Under", styles['McKinseySubsection']))
    ou_data = [
        ['Line', 'Over Prob', 'Under Prob', 'Expected', 'Recommendation'],
        ['Over 1.5', '76.9%', '23.1%', '—', 'Over'],
        ['Over 2.0', '65.0%', '35.0%', '—', 'Over'],
        ['Over 2.5', '53.1%', '46.9%', '2.8 goals', 'Marginal Over'],
        ['Over 3.0', '41.9%', '58.1%', '—', 'Under'],
        ['Over 3.5', '30.8%', '69.2%', '—', 'Under'],
    ]
    story.append(create_table(ou_data, [80, 70, 70, 80, 110]))
    story.append(PageBreak())
    
    # UPSETDETECTOR ANALYSIS
    story.append(Paragraph("UPSETDETECTOR ANALYSIS", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "UpsetDetector v1.0 evaluates seven factors on a 100-point scale. "
        "Score >80 = strong upset candidate; 60-80 = watch closely; <60 = normal risk.",
        styles['McKinseyBody']
    ))
    story.append(Spacer(1, 10))
    
    upset_data = [
        ['Factor', 'Score', 'Max', 'Signal', 'Key Driver'],
        ['Big Team Hype', '10.0', '20', 'Moderate', 'Canada hype higher than USA'],
        ['Odds Reverse', '15.0', '20', 'Strong', '77.9% flow vs 46% implied'],
        ['Abnormal Flow', '12.0', '15', 'Strong', 'Extreme betting imbalance'],
        ['Injury Risk', '2.0', '15', 'Low', 'Weah injury (medium impact)'],
        ['ELO Overvalued', '5.0', '10', 'Moderate', 'Rank gap not fully justified'],
        ['xG Undervalued', '4.0', '10', 'Low', 'USA xG 1.6 vs PAR 1.2'],
        ['Motivation Gap', '0.0', '10', 'None', 'Both teams highly motivated'],
    ]
    story.append(create_table(upset_data, [100, 50, 40, 80, 150]))
    story.append(Spacer(1, 15))
    story.append(Paragraph(
        "<b>Total Score: 48.0/100 — NORMAL RISK</b><br/><br/>"
        "Score falls well below 80-point 'Upset Candidate' threshold. Odds reverse and abnormal flow "
        "signals are strong (27/35 combined), but absence of ELO overvaluation, significant injury, "
        "or motivation asymmetry keeps risk in normal range.",
        styles['McKinseyBody']
    ))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "<b>Comparison with CAN-BIH:</b> Canada vs Bosnia scored 49/100, slightly higher due to "
        "Dzeko injury (7 pts) and greater big-team hype (10 pts). Neither reaches upset candidacy.",
        styles['McKinseyInsight']
    ))
    story.append(PageBreak())
    
    # RECOMMENDATIONS
    story.append(Paragraph("STRATEGIC RECOMMENDATIONS", styles['McKinseySection']))
    story.append(blue_header_bar())
    story.append(Spacer(1, 5))
    story.append(Paragraph(
        "Three tiers of recommendations for different risk appetites.",
        styles['McKinseyBody']
    ))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Tier 1: Conservative (Low Risk)", styles['McKinseySubsection']))
    rec1 = [
        "<b>Primary:</b> USA +0.5 (AH) at ~1.50 — 71.4% probability of not losing",
        "<b>Secondary:</b> Under 2.5 at ~1.85 — 46.9% probability",
        "<b>Size:</b> 1.0% of bankroll",
        "<b>Rationale:</b> Host nations in openers have 72% win rate; +0.5 captures draw insurance",
    ]
    for r in rec1:
        story.append(Paragraph(r, styles['McKinseyBullet'], bulletText='•'))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Tier 2: Balanced (Moderate Risk)", styles['McKinseySubsection']))
    rec2 = [
        "<b>Primary:</b> USA Win (1X2) at 2.05 — Model 46.4%, no edge",
        "<b>Secondary:</b> Exact Score 2:1 at ~8.00 — 9.3% probability",
        "<b>Size:</b> 0.5% of bankroll",
        "<b>Rationale:</b> USA is rightful favorite, but market offers no value",
    ]
    for r in rec2:
        story.append(Paragraph(r, styles['McKinseyBullet'], bulletText='•'))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Tier 3: Aggressive (Value Seeking)", styles['McKinseySubsection']))
    rec3 = [
        "<b>Primary:</b> Paraguay Win at 3.83 — Model 28.7%, market 24.7%, +10.1% edge",
        "<b>Secondary:</b> Paraguay +0.5 (AH) at ~1.90 — 53.6% probability",
        "<b>Size:</b> 0.3% of bankroll (Kelly: 0.27% for 10% edge, 23% prob)",
        "<b>Rationale:</b> Only bet with positive model edge. USA defense (1.7 GA) vulnerable to counter",
    ]
    for r in rec3:
        story.append(Paragraph(r, styles['McKinseyBullet'], bulletText='•'))
    story.append(Spacer(1, 15))
    
    story.append(Paragraph(
        "<b>Final Verdict:</b> USA is the rightful favorite but the market has overpriced their probability. "
        "The optimal risk-adjusted position is either no bet or a small value stake on Paraguay at 3.83. "
        "The 'odds reverse' signal suggests bookmakers are pricing in defensive risk, creating asymmetric "
        "value for the underdog.",
        styles['McKinseyInsight']
    ))
    story.append(Spacer(1, 20))
    
    # FOOTER
    story.append(Paragraph("—", styles['McKinseyBody']))
    story.append(Paragraph(
        f"<b>Naga Core Football Quant OS v2.0</b> | Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} | "
        "Data: 500.com, FIFA, Historical | Confidential & Proprietary",
        styles['McKinseyFooter']
    ))
    
    doc.build(story)
    print(f"PDF generated: {filename}")

if __name__ == "__main__":
    build_pdf(OUTPUT_FILE)
