import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from datetime import datetime

print("=" * 70)
print("UpsetDetector - World Cup 2026 Day 1 Comparison")
print("=" * 70)
print()

print("[Match 1] USA vs Paraguay (2026-06-13 09:00)")
print("-" * 70)
print("500.com Data:")
print("  Market Odds:     2.06 / 3.24 / 3.79")
print("  Implied Prob:    45.8% / 29.2% / 25.0%")
print("  Betting Flow:    74.0% / 15.9% / 10.1%")
print("  Bf Volume:       7,638,172 / 1,636,272 / 1,044,225 (HKD)")
print("  Bookmaker PnL:   -6,332,546 / 4,755,344 / 6,037,347")
print("  Hot/Cold Index:  61(hot) / -46 / -60(cold)")
print()
print("UpsetDetector Result:")
print("  Score:   33.0/100 (NORMAL)")
print("  Factors: big_team_hype=0, odds_reverse=15, abnormal_flow=12,")
print("           injury_risk=2, elo_overvalued=0, xg_undervalued=4,")
print("           motivation_gap=0")
print("  Signal:  Moderate odds reverse, high flow imbalance")
print("  Verdict: Watch but not strong upset candidate")
print()

print("[Match 2] Canada vs Bosnia (2026-06-13 03:00)")
print("-" * 70)
print("500.com Data:")
print("  Market Odds:     1.83 / 3.46 / 4.66")
print("  Implied Prob:    52.0% / 27.5% / 20.5%")
print("  Betting Flow:    80.1% / 11.8% / 8.2%")
print("  Bf Volume:       13,126,115 / 1,934,503 / 1,336,481 (HKD)")
print("  Bookmaker PnL:   -8,148,736 / 9,432,888 / 9,313,750")
print("  Hot/Cold Index:  54(hot) / -58(cold) / -61(cold)")
print()
print("UpsetDetector Result:")
print("  Score:   49.0/100 (NORMAL)")
print("  Factors: big_team_hype=10, odds_reverse=15, abnormal_flow=10,")
print("           injury_risk=7, elo_overvalued=0, xg_undervalued=7,")
print("           motivation_gap=0")
print("  Signal:  Stronger hype, Dzeko injury risk, xG undervalued")
print("  Verdict: Higher score than USA-PAR, but still NORMAL")
print()

print("=" * 70)
print("COMPARISON SUMMARY")
print("=" * 70)
print()

comparison = [
    ("Metric", "USA vs PAR", "CAN vs BIH", "Higher Risk"),
    ("-" * 15, "-" * 15, "-" * 15, "-" * 15),
    ("Upset Score", "33.0/100", "49.0/100", "CAN-BIH (+16)"),
    ("Betting Flow", "74.0%", "80.1%", "CAN-BIH (+6.1%)"),
    ("Implied Prob", "45.8%", "52.0%", "CAN-BIH (more justified)"),
    ("Flow-Prob Gap", "+28.2%", "+28.1%", "Similar"),
    ("Bookmaker Risk", "-6.3M", "-8.1M", "CAN-BIH (more exposure)"),
    ("Hot Index", "61", "54", "USA-PAR (hotter)"),
    ("Odds Reverse", "15.0", "15.0", "Equal"),
    ("Abnormal Flow", "12.0", "10.0", "USA-PAR (+2)"),
    ("Big Team Hype", "0.0", "10.0", "CAN-BIH (+10)"),
    ("Injury Risk", "2.0", "7.0", "CAN-BIH (Dzeko)"),
    ("xG Undervalued", "4.0", "7.0", "CAN-BIH (+3)"),
]

for row in comparison:
    print(f"{row[0]:15s} {row[1]:15s} {row[2]:15s} {row[3]:25s}")

print()
print("=" * 70)
print("KEY INSIGHTS")
print("=" * 70)
print()
print("1. CAN-BIH has HIGHER upset score (49 vs 33)")
print("   - More betting flow imbalance (80.1% vs 74.0%)")
print("   - Dzeko injury adds 7 points to risk")
print("   - But still NORMAL level (<60)")
print()
print("2. Both matches show 'ODDS REVERSE' signal (15/20)")
print("   - Heavy betting on favorite but odds not dropping proportionally")
print("   - Suggests market may be pricing in some risk")
print()
print("3. Neither is a 'UPSET CANDIDATE' (80+)")
print("   - Need more factors: ELO gap, motivation difference, xG surprise")
print("   - Or betting flow >90% with odds staying flat")
print()
print("4. If you MUST bet on upset:")
print("   - CAN-BIH: Bosnia @4.66 has more value than Paraguay @3.79")
print("   - But both are long shots with low probability")
print()
print("=" * 70)
print(f"Time: {datetime.now().isoformat()}")
print("=" * 70)
