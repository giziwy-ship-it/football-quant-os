import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.upset_detector import UpsetDetector, MatchStage
from datetime import datetime

detector = UpsetDetector()

print("=" * 60)
print("UpsetDetector - USA vs Paraguay (2026-06-13 09:00)")
print("Data Source: 500.com (实时投注分析)")
print("=" * 60)
print()

# 500.com 实时数据 (2026-06-12 23:57)
# 市场赔率: 2.06 / 3.24 / 3.79
# 投注流向: 74% / 15.9% / 10.1%
# 隐含概率: 45.8% / 29.2% / 25.0%

market_prob = {'home': 0.458, 'draw': 0.292, 'away': 0.250}
market_odds = {'home': 2.06, 'draw': 3.24, 'away': 3.79}
betting_flow = {'home': 0.74, 'away': 0.101}  # 74% vs 10.1%

# 模型概率 (假设更理性，排除热度偏差)
# 美国主场+实力优势，但74%投注过高
model_prob = {'home': 0.52, 'draw': 0.28, 'away': 0.20}  # 修正后概率

result = detector.calculate_upset_score(
    market_prob=market_prob,
    model_prob=model_prob,
    market_odds=market_odds,
    betting_flow=betting_flow,
    elo_home=1650, elo_away=1580,  # 假设ELO
    xg_home=1.6, xg_away=1.2,    # 假设xG
    injuries={
        'home': [{'player': 'Weah', 'importance': 'medium', 'position': 'RW'}],
        'away': []
    },
    motivation={'home': 0.95, 'away': 0.85},
    stage=MatchStage.GROUP_RD1,
)

print("[500.com 原始数据]")
print(f"  市场赔率: 主胜 {market_odds['home']} / 平 {market_odds['draw']} / 客胜 {market_odds['away']}")
print(f"  隐含概率: 主 {market_prob['home']*100:.1f}% / 平 {market_prob['draw']*100:.1f}% / 客 {market_prob['away']*100:.1f}%")
print(f"  投注流向: 主 {betting_flow['home']*100:.1f}% / 平 15.9% / 客 {betting_flow['away']*100:.1f}%")
print(f"  必发成交量: 主 7,638,172 / 平 1,636,272 / 客 1,044,225 (港币)")
print(f"  庄家盈亏: 主 -6,332,546 / 平 4,755,344 / 客 6,037,347")
print(f"  冷热指数: 主 61(热) / 平 -46 / 客 -60(冷)")
print()

print("[UpsetDetector 评分结果]")
print(f"  总分: {result['total_score']}/100")
print(f"  等级: {result['level'].upper()}")
print(f"  阶段冷门概率: {result['stage_upset_prob']*100:.0f}%")
print()

print("[因子分解]")
for factor, score in result['factors'].items():
    bar = "*" * int(score / 2) + "-" * (10 - int(score / 2))
    print(f"  {factor:20s} {bar} {score:.1f}")
print()

print("[价值投注]")
if result['value_bets']:
    for bet in result['value_bets']:
        print(f"  {bet['side'].upper()}: @{bet['odds']} edge +{bet['edge']}% [{bet['recommendation']}]")
else:
    print("  无显著价值投注")
print()

print("[建议]")
rec = result['recommendation']
print(f"  总体: {rec['overall']}")
print(f"  投注: {rec['value_bet']}")
if rec['avoid']:
    print(f"  避免: {rec['avoid']}")
if rec['stage_note']:
    print(f"  阶段: {rec['stage_note']}")
print()

# 大比分预测
print("[大比分预测]")
big = detector.calculate_big_score(
    xg_home=1.6, xg_away=1.2,
    xga_home=1.1, xga_away=1.3,
    pace_home=6.5, pace_away=5.5,
    historical_big_score_rate=0.25,
)
print(f"  大比分概率: {big['big_score_probability']}%")
print(f"  预期进球: {big['expected_goals']}")
print(f"  建议: {big['suggested_total']}")
print()

print("=" * 60)
print(f"Time: {datetime.now().isoformat()}")
print("=" * 60)
