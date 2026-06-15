import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.datascout_v2 import DataScout

# 测试 USA vs Paraguay 数据抓取
print("=" * 60)
print("DataScout v2.0 测试 - USA vs Paraguay 投注流向")
print("=" * 60)

scout = DataScout()

match_data = {
    'home_team': 'USA',
    'away_team': 'Paraguay',
    'league': 'World Cup',
    'home_win': 65,
    'draw': 20,
    'away_win': 15
}

print("\n[测试] 抓取 USA vs Paraguay 投注流向...")
print(f"  主队: {match_data['home_team']}")
print(f"  客队: {match_data['away_team']}")
print(f"  联赛: {match_data['league']}")
print()

result = scout.run(match_data)

print("[结果]")
print(f"  Agent: {result['agent']} v{result['version']}")
print(f"  推荐: {result['recommendation']}")
print(f"  置信度: {result['confidence']}")
print(f"  预测: {result['prediction']}")
print(f"  关键因素: {result['key_factors']}")

if 'money_flow' in result:
    mf = result['money_flow']
    print(f"\n[投注流向数据]")
    print(f"  来源: {mf['data_source']}")
    print(f"  时间: {mf['fetch_time']}")
    print(f"  主胜赔率: {mf['euro_home_odds']}")
    print(f"  平局赔率: {mf['euro_draw_odds']}")
    print(f"  客胜赔率: {mf['euro_away_odds']}")
    print(f"  主胜概率: {mf['euro_home_prob']:.1%}")
    print(f"  平局概率: {mf['euro_draw_prob']:.1%}")
    print(f"  客胜概率: {mf['euro_away_prob']:.1%}")
    print(f"  必发主胜: {mf['bf_home_price']}")
    print(f"  必发平局: {mf['bf_draw_price']}")
    print(f"  必发客胜: {mf['bf_away_price']}")
    print(f"  必发主量: {mf['bf_home_volume']}")
    print(f"  必发平量: {mf['bf_draw_volume']}")
    print(f"  必发客量: {mf['bf_away_volume']}")
    print(f"  必发总量: {mf['bf_total_volume']}")
    print(f"  庄家主盈亏: {mf['bookmaker_home_pnl']}")
    print(f"  庄家平盈亏: {mf['bookmaker_draw_pnl']}")
    print(f"  庄家客盈亏: {mf['bookmaker_away_pnl']}")
    print(f"  利润指数主: {mf['profit_index_home']}")
    print(f"  利润指数平: {mf['profit_index_draw']}")
    print(f"  利润指数客: {mf['profit_index_away']}")
else:
    print("\n[投注流向] 未获取到数据")

print()
print("=" * 60)
print("测试完成")
print("=" * 60)
