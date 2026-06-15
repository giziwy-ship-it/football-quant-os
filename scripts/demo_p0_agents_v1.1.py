#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS v2.0 P0 Agent 优化版演示
展示 OddsPricingAgent v1.1 + TreasuryAgent v1.1 全部优化功能

新增：
- 角球/黄牌/首球/半全场/单双盘口
- 多博彩公司聚合 + 套利检测
- 赔率历史趋势
- 多币种支持
- 蒙特卡洛VaR
- 回撤分析
- Markowitz组合优化
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime
import importlib.util
import os

agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents')

# 加载 Agent
spec = importlib.util.spec_from_file_location("odds_pricing", os.path.join(agents_dir, "odds_pricing.py"))
odds_pricing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(odds_pricing)
OddsPricingAgent = odds_pricing.OddsPricingAgent
MarketConditions = odds_pricing.MarketConditions

spec2 = importlib.util.spec_from_file_location("treasury", os.path.join(agents_dir, "treasury.py"))
treasury = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(treasury)
TreasuryAgent = treasury.TreasuryAgent
Position = treasury.Position

print("=" * 80)
print("     Football Quant OS v2.0 - P0 Agent 优化版演示")
print("     OddsPricingAgent v1.1 + TreasuryAgent v1.1")
print("=" * 80)
print()

# ==================== OddsPricingAgent 优化 ====================
print("【OddsPricingAgent v1.1 - 新增功能】")
print("-" * 80)

pricing = OddsPricingAgent(profile="premium")
predictions = {"home": 0.55, "draw": 0.25, "away": 0.20}
conditions = MarketConditions(league_type="World Cup", market_liquidity=0.9, public_bias=0.1)

output = pricing.price_match(predictions, conditions)

# 1. 新盘口类型
print("1. 角球盘口")
corner = pricing.generate_corner_odds({"home": 0.55, "away": 0.45})
print(f"   让球: {corner['handicap']} | 上@{corner['upper']} | 下@{corner['lower']}")

print("\n2. 黄牌盘口")
card = pricing.generate_card_odds({"over_3.5": 0.55, "under_3.5": 0.45})
print(f"   3.5张 | 大@{card['over']} | 小@{card['under']}")

print("\n3. 首球盘口")
first = pricing.generate_first_goal_odds({"home": 0.50, "away": 0.40, "none": 0.10})
print(f"   主@{first['odds']['home']} | 客@{first['odds']['away']} | 无@{first['odds']['none']}")

print("\n4. 半全场盘口")
ht = pricing.generate_half_time_odds({"home": 0.35, "draw": 0.45, "away": 0.20})
print(f"   主@{ht['odds']['home']} | 平@{ht['odds']['draw']} | 客@{ht['odds']['away']}")

print("\n5. 单双数盘口")
oe = pricing.generate_odd_even_odds({"odd": 0.50, "even": 0.50})
print(f"   单@{oe['odds']['odd']} | 双@{oe['odds']['even']}")

# 2. 多博彩公司聚合
print("\n6. 多博彩公司聚合 + 套利检测")
bookmaker_odds = {
    "bet365": {"home": 2.10, "draw": 3.40, "away": 3.80},
    "pinnacle": {"home": 2.15, "draw": 3.35, "away": 3.90},
    "betfair": {"home": 2.12, "draw": 3.40, "away": 4.10},
    "william_hill": {"home": 2.05, "draw": 3.45, "away": 3.75}
}

agg = pricing.aggregate_bookmaker_odds(bookmaker_odds)
print(f"   聚合结果:")
for direction in ['home', 'draw', 'away']:
    data = agg['aggregated'].get(direction, {})
    if data:
        print(f"     {direction}: 最优@{data['best']} ({data['best_bookmaker']}) | 平均@{data['average']} | {data['count']}家")

if agg['arbitrage_opportunity']['exists']:
    print(f"   ⚠️ 套利机会发现！利润率: {agg['arbitrage_opportunity']['margin']:.2%}")
else:
    print(f"   无套利机会 (margin: {agg['arbitrage_opportunity']['margin']:.4f})")

print()

# ==================== TreasuryAgent 优化 ====================
print("【TreasuryAgent v1.1 - 新增功能】")
print("-" * 80)

treasury = TreasuryAgent(initial_bankroll=10000.0)

# 1. 多币种支持
print("1. 多币种资金汇总")
currencies = {"EUR": 5000, "USD": 3000, "GBP": 2000}
mc = treasury.multi_currency_support(currencies)
print(f"   总资金 (EUR): {mc['total_eur']} EUR")
for curr, data in mc['breakdown'].items():
    print(f"   {curr}: {data['amount']} → {data['eur_value']} EUR (汇率: {data['rate']})")

# 2. 蒙特卡洛VaR
print("\n2. 蒙特卡洛VaR (10,000次模拟)")
# 先创建几个持仓
for i in range(3):
    opp = {'probability': 0.55 + i*0.05, 'odds': 2.0 + i*0.1, 'confidence': 0.7}
    alloc = treasury.allocate_stake(opp, risk_level="medium")
    if alloc['action'] == 'bet':
        pos = Position(
            match_id=f"TEST_{i}", market="1X2", selection="home",
            odds=opp['odds'], stake=alloc['stake'],
            expected_value=alloc['expected_value'],
            model_confidence=opp['confidence'], timestamp=datetime.now()
        )
        treasury.place_bet(pos)

open_positions = [p for p in treasury.positions if p.status == "open"]
mc_var = treasury.monte_carlo_var(open_positions, n_simulations=10000)
print(f"   95% VaR: {mc_var['var_95']} EUR")
print(f"   99% VaR: {mc_var['var_99']} EUR")
print(f"   预期损失: {mc_var['expected_loss']} EUR")
print(f"   最坏情况: {mc_var['worst_case']} EUR")
print(f"   最好情况: +{mc_var['best_case']} EUR")

# 3. 回撤分析
print("\n3. 回撤分析")
# 模拟一些历史盈亏
for i in range(5):
    pos = Position(
        match_id=f"HIST_{i}", market="1X2", selection="home",
        odds=2.0, stake=100, expected_value=5.0,
        model_confidence=0.6, timestamp=datetime.now()
    )
    pos.status = "settled"
    pos.pnl = [50, -30, 80, -20, 40][i]  # 模拟盈亏
    treasury.position_history.append(pos)

dd = treasury.drawdown_analysis()
print(f"   最大回撤: {dd['max_drawdown']} EUR ({dd['max_drawdown_pct']}%)")
print(f"   当前回撤: {dd['current_drawdown']} EUR ({dd['current_drawdown_pct']}%)")
print(f"   状态: {dd['status']}")
print(f"   峰值: {dd['peak']} EUR | 当前: {dd['current']} EUR")

# 4. Markowitz组合优化
print("\n4. Markowitz组合优化")
opportunities = [
    {'probability': 0.58, 'odds': 2.07, 'confidence': 0.72, 'expected_value': 20.5},
    {'probability': 0.45, 'odds': 3.20, 'confidence': 0.55, 'expected_value': 44.0},
    {'probability': 0.35, 'odds': 4.50, 'confidence': 0.40, 'expected_value': 57.5},
    {'probability': 0.60, 'odds': 1.80, 'confidence': 0.80, 'expected_value': 8.0}
]

opt = treasury.markowitz_optimization(opportunities)
print(f"   最优配置:")
for i, alloc in enumerate(opt['optimal_allocation']):
    print(f"     {i+1}. Sharpe: {alloc['sharpe']} | 权重: {alloc['weight']:.0%} | 注码: {alloc['stake']} EUR | EV: {alloc['expected_value']}%")
print(f"   组合预期收益: {opt['expected_return']} EUR")
print(f"   总注码: {opt['total_stake']} EUR")
print(f"   组合风险: {opt['portfolio_risk']:.2%}")

print()
print("=" * 80)
print("  优化完成！所有新增功能已就绪")
print("=" * 80)
