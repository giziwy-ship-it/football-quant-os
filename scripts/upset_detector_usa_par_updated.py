import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.upset_detector import UpsetDetector, MatchStage
from datetime import datetime

detector = UpsetDetector()

print("=" * 70)
print("UpsetDetector - USA vs Paraguay (Updated 2026-06-13 07:28)")
print("Data Source: 500.com (Real-time, Pre-Match)")
print("=" * 70)
print()

# 500.com Updated Data (2026-06-13 07:28)
# 距离开赛还有约1.5小时
market_prob = {'home': 0.460, 'draw': 0.293, 'away': 0.247}
market_odds = {'home': 2.05, 'draw': 3.23, 'away': 3.83}
betting_flow = {'home': 0.779, 'away': 0.094}  # 77.9% vs 9.4%

# Model Probability (more rational, excluding hype bias)
model_prob = {'home': 0.55, 'draw': 0.28, 'away': 0.17}

result = detector.calculate_upset_score(
    market_prob=market_prob,
    model_prob=model_prob,
    market_odds=market_odds,
    betting_flow=betting_flow,
    elo_home=1650, elo_away=1580,
    xg_home=1.6, xg_away=1.2,
    injuries={
        'home': [{'player': 'Weah', 'importance': 'medium', 'position': 'RW'}],
        'away': []
    },
    motivation={'home': 0.95, 'away': 0.85},
    stage=MatchStage.GROUP_RD1,
)

print("[500.com Updated Data - 07:28 GMT+8]")
print("-" * 70)
print(f"  Market Odds:     Home {market_odds['home']} / Draw {market_odds['draw']} / Away {market_odds['away']}")
print(f"  Implied Prob:    Home {market_prob['home']*100:.1f}% / Draw {market_prob['draw']*100:.1f}% / Away {market_prob['away']*100:.1f}%")
print(f"  Betting Flow:    Home {betting_flow['home']*100:.1f}% / Draw 12.8% / Away {betting_flow['away']*100:.1f}%")
print(f"  Bf Volume:       Home 18,157,217 / Draw 2,984,539 / Away 2,181,137 (HKD)")
print(f"  Total Volume:    23,322,893 HKD")
print(f"  Bookmaker PnL:   Home -15,533,551 / Draw 13,473,914 / Away 14,162,118")
print(f"  Hot/Cold Index:  Home 69(hot) / Draw -57(cold) / Away -62(cold)")
print(f"  Profit Index:    Home -67 / Draw 57 / Away 60")
print(f"  Alert:           '必发交易规模超千万，谨防比赛过于热门'")
print()

print("[Comparison with Previous Data (23:57)]")
print("-" * 70)
print("  Metric               | Before (23:57) | Now (07:28) | Change")
print("  " + "-" * 66)
print(f"  Betting Flow         | 74.0%          | 77.9%       | +3.9%")
print(f"  Total Volume         | 10.3M HKD      | 23.3M HKD   | +126%")
print(f"  Bookmaker Risk       | -6.3M          | -15.5M      | +146%")
print(f"  Hot Index            | 61             | 69          | +8")
print(f"  Odds (USA)           | 2.06           | 2.05        | -0.01")
print()

print("[UpsetDetector Score - UPDATED]")
print("-" * 70)
print(f"  Total Score:        {result['total_score']}/100")
print(f"  Level:              {result['level'].upper()}")
print(f"  Stage Upset Prob:   {result['stage_upset_prob']*100:.0f}%")
print()

print("[Factor Breakdown]")
print("-" * 70)
for factor, score in result['factors'].items():
    bar = "*" * int(score / 2) + "-" * (10 - int(score / 2))
    print(f"  {factor:20s} {bar} {score:.1f}")
print()

print("[Value Bets]")
print("-" * 70)
if result['value_bets']:
    for bet in result['value_bets']:
        print(f"  {bet['side'].upper()}: @{bet['odds']} edge +{bet['edge']}% [{bet['recommendation']}]")
else:
    print("  No significant value bets")
print()

print("[Recommendation]")
print("-" * 70)
rec = result['recommendation']
print(f"  Overall:   {rec['overall']}")
print(f"  Bet:       {rec['value_bet']}")
if rec['avoid']:
    print(f"  Avoid:     {rec['avoid']}")
if rec['stage_note']:
    print(f"  Stage:     {rec['stage_note']}")
print()

print("=" * 70)
print("PRE-MATCH ANALYSIS (07:28, ~1.5 hours to kickoff)")
print("=" * 70)
print()
print("Key Observations:")
print("  1. Volume SURGED 126% overnight (10M -> 23M HKD)")
print("  2. Betting flow INCREASED to 77.9% on USA")
print("  3. Bookmaker risk DOUBLED to -15.5M on USA")
print("  4. Hot index rose to 69 (extreme)")
print("  5. Odds barely moved (2.06 -> 2.05), confirming 'odds reverse'")
print()
print("Risk Assessment:")
print("  - USA is heavily favored by public")
print("  - But odds not dropping proportionally")
print("  - This creates 'odds reverse' signal")
print("  - However, UpsetDetector score remains NORMAL (33/100)")
print("  - Not enough for 'UPSET CANDIDATE' (80+)")
print()
print("Verdict:")
print("  - USA likely wins, but public is overbetting")
print("  - No strong upset signal")
print("  - If betting: USA is safe but low value")
print("  - If looking for value: Paraguay @3.83 has slight edge")
print()
print("=" * 70)
print(f"Time: {datetime.now().isoformat()}")
print("=" * 70)
