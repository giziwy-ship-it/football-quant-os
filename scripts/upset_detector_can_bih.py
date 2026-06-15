import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.upset_detector import UpsetDetector, MatchStage
from datetime import datetime

detector = UpsetDetector()

print("=" * 60)
print("UpsetDetector - Canada vs Bosnia (2026-06-13 03:00)")
print("Data Source: 500.com (Real-time Betting Data)")
print("=" * 60)
print()

# 500.com Real-time Data (2026-06-13 00:13)
market_prob = {'home': 0.520, 'draw': 0.275, 'away': 0.205}
market_odds = {'home': 1.83, 'draw': 3.46, 'away': 4.66}
betting_flow = {'home': 0.801, 'away': 0.082}  # 80.1% vs 8.2%

# Model Probability (more rational, excluding hype bias)
model_prob = {'home': 0.58, 'draw': 0.25, 'away': 0.17}

result = detector.calculate_upset_score(
    market_prob=market_prob,
    model_prob=model_prob,
    market_odds=market_odds,
    betting_flow=betting_flow,
    elo_home=1600, elo_away=1500,
    xg_home=1.8, xg_away=1.0,
    injuries={
        'home': [],
        'away': [{'player': 'Dzeko', 'importance': 'high', 'position': 'ST'}]
    },
    motivation={'home': 0.95, 'away': 0.85},
    stage=MatchStage.GROUP_RD1,
)

print("[500.com Raw Data]")
print(f"  Market Odds: Home {market_odds['home']} / Draw {market_odds['draw']} / Away {market_odds['away']}")
print(f"  Implied Prob: Home {market_prob['home']*100:.1f}% / Draw {market_prob['draw']*100:.1f}% / Away {market_prob['away']*100:.1f}%")
print(f"  Betting Flow: Home {betting_flow['home']*100:.1f}% / Draw 11.8% / Away {betting_flow['away']*100:.1f}%")
print(f"  Bf Volume: Home 13,126,115 / Draw 1,934,503 / Away 1,336,481 (HKD)")
print(f"  Bookmaker PnL: Home -8,148,736 / Draw 9,432,888 / Away 9,313,750")
print(f"  Hot/Cold Index: Home 54(hot) / Draw -58(cold) / Away -61(cold)")
print()

print("[UpsetDetector Score]")
print(f"  Total Score: {result['total_score']}/100")
print(f"  Level: {result['level'].upper()}")
print(f"  Stage Upset Prob: {result['stage_upset_prob']*100:.0f}%")
print()

print("[Factor Breakdown]")
for factor, score in result['factors'].items():
    bar = "*" * int(score / 2) + "-" * (10 - int(score / 2))
    print(f"  {factor:20s} {bar} {score:.1f}")
print()

print("[Value Bets]")
if result['value_bets']:
    for bet in result['value_bets']:
        print(f"  {bet['side'].upper()}: @{bet['odds']} edge +{bet['edge']}% [{bet['recommendation']}]")
else:
    print("  No significant value bets")
print()

print("[Recommendation]")
rec = result['recommendation']
print(f"  Overall: {rec['overall']}")
print(f"  Bet: {rec['value_bet']}")
if rec['avoid']:
    print(f"  Avoid: {rec['avoid']}")
if rec['stage_note']:
    print(f"  Stage: {rec['stage_note']}")
print()

# Big Score Prediction
print("[Big Score Prediction]")
big = detector.calculate_big_score(
    xg_home=1.8, xg_away=1.0,
    xga_home=1.0, xga_away=1.2,
    pace_home=7.0, pace_away=5.0,
    historical_big_score_rate=0.30,
)
print(f"  Big Score Prob: {big['big_score_probability']}%")
print(f"  Expected Goals: {big['expected_goals']}")
print(f"  Suggested: {big['suggested_total']}")
print()

print("=" * 60)
print(f"Time: {datetime.now().isoformat()}")
print("=" * 60)
