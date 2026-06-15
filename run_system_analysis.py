import sys
sys.path.insert(0, 'agents')
from upset_detector import UpsetDetector
from coach_factor import CoachFactor
from odds_pricing import OddsPricingAgent
from treasury import TreasuryAgent
from multi_market_predictor import MultiMarketPredictor
import json
import statistics

print('='*60)
print('🚨 UpsetDetector v1.0 - 冷门雷达')
print('='*60)
ud = UpsetDetector()

match_data = {
    'home_team': 'Brazil',
    'away_team': 'Morocco',
    'home_fifa_rank': 6,
    'away_fifa_rank': 7,
    'home_elo': 1765,
    'away_elo': 1755,
    'home_form': 'LWWLLW',
    'away_form': 'DWWWDD',
    'home_goals_scored_10': 25,
    'home_goals_conceded_10': 11,
    'away_goals_scored_10': 22,
    'away_goals_conceded_10': 3,
    'tournament_stage': 'group_stage',
    'home_odds': 1.65,
    'draw_odds': 3.78,
    'away_odds': 5.48,
    'home_bet_pct': 83.1,
    'away_bet_pct': 7.2,
    'venue': 'neutral',
    'home_injuries': 1,
    'away_injuries': 0,
    'match_importance': 'high',
}

result = ud.detect_upset(match_data)
print(f"冷门评分: {result['upset_score']}/100")
print(f"冷门概率: {result['upset_probability']:.1%}")
print(f"大比分概率: {result['high_score_probability']:.1%}")
print(f"价值投注: {result['value_bet']}")
print(f"置信度: {result['confidence']:.1%}")
print()

print('='*60)
print('👔 CoachFactor v1.0 - 教练因子引擎')
print('='*60)

brazil_coach = {
    'name': 'Dorival Júnior',
    'nationality': 'Brazil',
    'experience_years': 15,
    'major_tournaments': 2,
    'tactical_stability': 6.0,
    'in_game_decision': 6.5,
    'big_match_exp': 5.5,
    'psychological_control': 6.0,
    'rotation_tendency': 7.0,
    'extreme_strategy': 5.0,
}

morocco_coach = {
    'name': 'Walid Regragui',
    'nationality': 'Morocco',
    'experience_years': 8,
    'major_tournaments': 4,
    'tactical_stability': 7.5,
    'in_game_decision': 8.0,
    'big_match_exp': 8.5,
    'psychological_control': 8.0,
    'rotation_tendency': 6.5,
    'extreme_strategy': 6.0,
}

def calc_cri(coach):
    dimensions = [
        coach['tactical_stability'],
        coach['in_game_decision'],
        coach['big_match_exp'],
        coach['psychological_control'],
        coach['rotation_tendency'],
        coach['extreme_strategy'],
    ]
    return sum(dimensions) / len(dimensions)

brazil_cri = calc_cri(brazil_coach)
morocco_cri = calc_cri(morocco_coach)

print(f'巴西教练 多里瓦尔 CRI: {brazil_cri:.2f}')
print(f'摩洛哥教练 雷格拉吉 CRI: {morocco_cri:.2f}')
print(f'CRI差距: {morocco_cri - brazil_cri:+.2f} (正=摩洛哥优势)')
print()

print('CBM 投注矩阵:')
print(f'  冷门概率调整: +{(morocco_cri - brazil_cri) * 2:.1f}%')
print('  大比分概率: 低 (两队防守都不错)')
print('  合理投注区间: 摩洛哥+0.5~+1.0')
print('  策略方向: 反热门 / 防守反击')
print()

print('='*60)
print('💰 OddsPricingAgent v1.1 - 赔率价值分析')
print('='*60)

market_home_prob = 1/1.65
market_draw_prob = 1/3.78
market_away_prob = 1/5.48

model_home_prob = 0.52
model_draw_prob = 0.28
model_away_prob = 0.20

home_value = model_home_prob - market_home_prob
draw_value = model_draw_prob - market_draw_prob
away_value = model_away_prob - market_away_prob

print(f'市场隐含概率: 主{market_home_prob:.1%} | 平{market_draw_prob:.1%} | 客{market_away_prob:.1%}')
print(f'模型概率:      主{model_home_prob:.1%} | 平{model_draw_prob:.1%} | 客{model_away_prob:.1%}')
print(f'价值差:        主{home_value:+.1%} | 平{draw_value:+.1%} | 客{away_value:+.1%}')
print()

if away_value > 0:
    print(f'🎯 价值投注: 摩洛哥胜 (edge +{away_value:.1%})')
if draw_value > 0:
    print(f'🎯 价值投注: 平局 (edge +{draw_value:.1%})')
if home_value < 0:
    print(f'⚠️  巴西胜为负价值投注 (edge {home_value:.1%})')
print()

print('='*60)
print('🏦 TreasuryAgent v1.1 - 资金配置')
print('='*60)

def kelly_criterion(p, b):
    q = 1 - p
    return (b * p - q) / b

bankroll = 10000
max_risk = 0.15
unit = bankroll * 0.02

p_morocco = model_away_prob
b_morocco = 5.48 - 1
kelly_morocco = kelly_criterion(p_morocco, b_morocco)

p_draw = model_draw_prob
b_draw = 3.78 - 1
kelly_draw = kelly_criterion(p_draw, b_draw)

p_morocco_plus1 = 0.55
b_morocco_plus1 = 2.15 - 1
kelly_plus1 = kelly_criterion(p_morocco_plus1, b_morocco_plus1)

print(f'资金池: {bankroll:,} EUR')
print(f'最大日风险: {max_risk:.0%} = {bankroll * max_risk:,.0f} EUR')
print(f'标准注码: {unit:,.0f} EUR (2%资金池)')
print()

half_kelly_morocco = max(0, kelly_morocco / 2) * bankroll
half_kelly_draw = max(0, kelly_draw / 2) * bankroll
half_kelly_plus1 = max(0, kelly_plus1 / 2) * bankroll

print('Kelly注码建议 (半Kelly):')
print(f'  摩洛哥胜 @5.48:  Kelly={kelly_morocco:+.1%} → 注码 {half_kelly_morocco:,.0f} EUR')
print(f'  平局 @3.78:      Kelly={kelly_draw:+.1%} → 注码 {half_kelly_draw:,.0f} EUR')
print(f'  摩洛哥+1 @2.15:   Kelly={kelly_plus1:+.1%} → 注码 {half_kelly_plus1:,.0f} EUR')
print()

print('='*60)
print('📊 MultiMarketPredictor v1.0 - 多市场预测')
print('='*60)

predictions = {
    '1x2': {'home': 0.52, 'draw': 0.28, 'away': 0.20},
    'asian_handicap': {'home_minus1': 0.35, 'draw': 0.28, 'away_plus1': 0.37},
    'over_under': {'over_2.25': 0.42, 'under_2.25': 0.58},
    'both_teams_to_score': {'yes': 0.48, 'no': 0.52},
    'correct_score': {
        '1:0': 0.15, '1:1': 0.13, '2:0': 0.12, '2:1': 0.11, '0:0': 0.09, '0:1': 0.07
    },
    'half_time_full_time': {
        'home_home': 0.32, 'draw_home': 0.22, 'draw_draw': 0.15, 'away_home': 0.08,
        'home_draw': 0.08, 'draw_away': 0.08, 'away_away': 0.07
    }
}

print('1X2 概率:')
for k, v in predictions['1x2'].items():
    print(f'  {k}: {v:.1%}')
print()

print('让球 (-1) 概率:')
for k, v in predictions['asian_handicap'].items():
    print(f'  {k}: {v:.1%}')
print()

print('大小球 2.25 概率:')
for k, v in predictions['over_under'].items():
    print(f'  {k}: {v:.1%}')
print()

print('比分概率 TOP5:')
scores = sorted(predictions['correct_score'].items(), key=lambda x: -x[1])
for score, prob in scores[:5]:
    print(f'  {score}: {prob:.1%}')
print()

print('半全场 TOP5:')
htft = sorted(predictions['half_time_full_time'].items(), key=lambda x: -x[1])
for combo, prob in htft[:5]:
    print(f'  {combo}: {prob:.1%}')

print()
print('='*60)
print('✅ Football Quant OS v4.2.1 流水线执行完毕')
print('='*60)
