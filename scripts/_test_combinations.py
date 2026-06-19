import sys
sys.path.insert(0, 'scripts')
from predict_v6 import PredictorV6

p = PredictorV6(bankroll=100000)

# 测试1: 单场比赛组合投注
print("="*60)
print("TEST 1: 单场比赛 - 多市场组合")
print("="*60)
result = p.predict('Germany', 'Japan', odds_home=1.8, odds_draw=3.4, odds_away=4.2)

if result.combination and result.combination.get('status') == 'recommended':
    single = result.combination.get('single_match', [])
    print(f"\n找到 {len(single)} 个单场组合:")
    for combo in single:
        print(f"\n  [{combo.get('type', '')}] {combo.get('name', '')}")
        print(f"  赔率: {combo.get('combined_odds', 0):.2f} | EV: {combo.get('ev', 0):+.3f}")
        print(f"  Kelly注码: ${combo.get('kelly_stake', 0):.2f}")
        print(f"  推荐: {combo.get('recommendation', '')}")
        for leg in combo.get('legs', []):
            print(f"    - {leg['market']}: {leg['selection']} @ {leg.get('odds', 'N/A')}")
else:
    print("无组合推荐")

# 测试2: 批量预测 + 多场比赛组合
print("\n" + "="*60)
print("TEST 2: 多场比赛 - 2串1/3串1/4串1")
print("="*60)

matches = [
    {'home': 'Germany', 'away': 'Japan', 'odds_home': 1.8, 'odds_draw': 3.4, 'odds_away': 4.2},
    {'home': 'France', 'away': 'Brazil', 'odds_home': 2.2, 'odds_draw': 3.2, 'odds_away': 3.0},
    {'home': 'Spain', 'away': 'Argentina', 'odds_home': 2.5, 'odds_draw': 3.3, 'odds_away': 2.6},
    {'home': 'England', 'away': 'Netherlands', 'odds_home': 2.0, 'odds_draw': 3.5, 'odds_away': 3.2},
]

results = []
for m in matches:
    r = p.predict(**m)
    results.append(r.to_dict())

print(f"\n预测了 {len(results)} 场比赛")

# 生成多场比赛组合
for fold in [2, 3, 4]:
    if len(results) >= fold:
        combos = p.generate_multi_match_combinations(results, fold=fold, risk_level='conservative')
        print(f"\n{fold}串1 组合: {len(combos)}个")
        for combo in combos[:3]:  # 只显示前3个
            print(f"\n  赔率: {combo.get('combined_odds', 0):.2f}")
            print(f"  Edge: {combo.get('combined_edge', 0):+.4f}")
            print(f"  Kelly: ${combo.get('recommended_stake', 0):.2f}")
            for match_str in combo.get('matches', []):
                print(f"    - {match_str}")

print("\n" + "="*60)
print("组合投注测试完成!")
print("="*60)
