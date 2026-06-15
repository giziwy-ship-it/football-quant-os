import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.upset_detector import UpsetDetector, MatchStage

detector = UpsetDetector()

print("=" * 60)
print("UpsetDetector v1.0 - Mispricing Detection")
print("=" * 60)
print()

# Test 1: Saudi Arabia vs Argentina (2022 World Cup upset)
print("[Test 1] Saudi Arabia vs Argentina (2022 WC)")
print("Market: ARG 80% win | Model: ARG 45% / KSA 25%")

result1 = detector.calculate_upset_score(
    market_prob={'home': 0.08, 'draw': 0.12, 'away': 0.80},
    model_prob={'home': 0.25, 'draw': 0.30, 'away': 0.45},
    market_odds={'home': 12.5, 'draw': 8.33, 'away': 1.25},
    elo_home=1450, elo_away=1850,
    xg_home=1.2, xg_away=1.8,
    betting_flow={'home': 0.05, 'away': 0.95},
    injuries={'away': [{'player': 'Di Maria', 'importance': 'high', 'position': 'RW'}]},
    motivation={'home': 0.95, 'away': 0.85},
    stage=MatchStage.GROUP_RD1,
)

print(f"Score: {result1['total_score']}/100 - {result1['level'].upper()}")
print(f"Factors: {result1['factors']}")
print(f"Value Bets: {len(result1['value_bets'])} found")
for bet in result1['value_bets']:
    print(f"  {bet['side'].upper()}: @{bet['odds']} edge +{bet['edge']}%")
print(f"Recommendation: {result1['recommendation']['overall']}")
print()

# Test 2: South Korea vs Germany (2018 World Cup)
print("[Test 2] South Korea vs Germany (2018 WC)")
print("Germany already qualified, Korea fighting")

result2 = detector.calculate_upset_score(
    market_prob={'home': 0.10, 'draw': 0.15, 'away': 0.75},
    model_prob={'home': 0.20, 'draw': 0.25, 'away': 0.55},
    market_odds={'home': 10.0, 'draw': 6.67, 'away': 1.33},
    elo_home=1520, elo_away=1950,
    xg_home=1.0, xg_away=2.0,
    betting_flow={'home': 0.08, 'away': 0.92},
    motivation={'home': 1.0, 'away': 0.6},
    stage=MatchStage.GROUP_RD3,
)

print(f"Score: {result2['total_score']}/100 - {result2['level'].upper()}")
print(f"Factors: {result2['factors']}")
print(f"Value Bets: {len(result2['value_bets'])} found")
for bet in result2['value_bets']:
    print(f"  {bet['side'].upper()}: @{bet['odds']} edge +{bet['edge']}%")
print(f"Recommendation: {result2['recommendation']['overall']}")
print()

# Big score test
print("[Test 3] Big Score Prediction")
print("France vs Australia (high xG both sides)")

big = detector.calculate_big_score(
    xg_home=2.4, xg_away=1.8,
    xga_home=1.2, xga_away=1.5,
    pace_home=8.0, pace_away=7.0,
    historical_big_score_rate=0.35,
)

print(f"Big Score Prob: {big['big_score_probability']}%")
print(f"Expected Goals: {big['expected_goals']}")
print(f"Suggested: {big['suggested_total']}")
print(f"xG Sum: {big['xg_sum']} | xGA Sum: {big['xga_sum']}")
print()

print("=" * 60)
print("UpsetDetector - Ready for World Cup 2026")
print("=" * 60)
