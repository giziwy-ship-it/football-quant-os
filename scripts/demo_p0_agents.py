#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS v2.0 P0 Agent 协同演示
OddsPricingAgent + TreasuryAgent 联合运行

场景：美国 vs 巴拉圭（2026世界杯揭幕战）
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from datetime import datetime

# 模拟导入（实际运行时从agents目录导入）
import importlib.util
import os

agents_dir = os.path.join(os.path.dirname(__file__), '..', 'agents')

# 加载 OddsPricingAgent
spec = importlib.util.spec_from_file_location("odds_pricing", os.path.join(agents_dir, "odds_pricing.py"))
odds_pricing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(odds_pricing)
OddsPricingAgent = odds_pricing.OddsPricingAgent
MarketConditions = odds_pricing.MarketConditions

# 加载 TreasuryAgent
spec2 = importlib.util.spec_from_file_location("treasury", os.path.join(agents_dir, "treasury.py"))
treasury = importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(treasury)
TreasuryAgent = treasury.TreasuryAgent
Position = treasury.Position

print("=" * 80)
print("     Football Quant OS v2.0 - P0 Agent 协同演示")
print("     美国 vs 巴拉圭 | 2026世界杯 Group A")
print("=" * 80)
print()

# ==================== 第一步：AI预测（已有） ====================
print("【Step 1】AI预测中心输出")
print("-" * 80)
predictions = {
    "home": 0.582,    # 美国胜 58.2%
    "draw": 0.242,    # 平局 24.2%
    "away": 0.177     # 巴拉圭胜 17.7%
}
print(f"  预测概率: 美国{predictions['home']*100:.1f}% | 平局{predictions['draw']*100:.1f}% | 巴拉圭{predictions['away']*100:.1f}%")
print()

# ==================== 第二步：定价中心（新增） ====================
print("【Step 2】OddsPricingAgent - 赔率定价中心")
print("-" * 80)

pricing_agent = OddsPricingAgent(profile="premium")

market_conditions = MarketConditions(
    league_type="World Cup",
    match_importance="group",
    market_liquidity=0.9,
    public_bias=0.12,        # 公众强烈倾向美国（东道主）
    competition_stage="group",
    time_to_match=12.0
)

pricing_output = pricing_agent.price_match(predictions, market_conditions)

print("  赔率输出:")
print(f"    主胜(美国): @{pricing_output.odds['home']}")
print(f"    平局:       @{pricing_output.odds['draw']}")
print(f"    客胜(巴拉圭): @{pricing_output.odds['away']}")
print()
print("  公平赔率（无利润）:")
print(f"    主胜: @{pricing_output.fair_odds['home']} | 客胜: @{pricing_output.fair_odds['away']}")
print()
print(f"  利润率: Overround={pricing_output.overround:.2%} | Margin={pricing_output.margin:.2%}")
print(f"  定价置信度: {pricing_output.confidence:.1f}%")
print()

# 亚洲让球盘
asian_prob = {"home": 0.65, "away": 0.35}
handicap = pricing_agent.generate_handicap(asian_prob)
print(f"  亚洲让球盘: {handicap['handicap']} | 上盘@{handicap['upper']} | 下盘@{handicap['lower']}")

# 大小球盘
goals = {"0": 0.06, "1": 0.22, "2": 0.32, "3": 0.22, "4": 0.12, "5+": 0.06}
ou = pricing_agent.generate_over_under(goals, line=2.5)
print(f"  大小球盘: {ou['line']}球 | 大@{ou['over']} | 小@{ou['under']}")
print()

# 与市场价格对比
market_odds = {"home": 2.07, "draw": 3.30, "away": 3.87}
comparison = pricing_agent.compare_with_market(pricing_output.odds, market_odds)
if comparison['total_opportunities'] > 0:
    print("  价值投注发现:")
    for key, val in comparison['value_opportunities'].items():
        print(f"    {key}: 市场@{val['market_odds']} vs 我们@{val['our_odds']} (edge: +{val['edge']:.1f}%)")
else:
    print("  与市场价格一致，无价值投注机会")
print()

# ==================== 第三步：资金中心（新增） ====================
print("【Step 3】TreasuryAgent - 资金管理中心")
print("-" * 80)

treasury_agent = TreasuryAgent(
    initial_bankroll=10000.0,
    reserve_pct=0.10,
    daily_limit_pct=0.15,
    max_single_pct=0.05,
    kelly_fraction=0.5
)

print("  初始资金池:")
summary = treasury_agent.get_bankroll_summary()
print(f"    总资金: {summary['total_funds']} EUR")
print(f"    可用: {summary['available']} EUR | 锁定: {summary['locked']} EUR | 储备: {summary['reserve']} EUR")
print(f"    日限额: {summary['daily_limit']} EUR | 单位注码: {summary['unit_size']} EUR")
print()

# 注码分配（使用市场赔率，因为定价赔率含利润）
opportunity = {
    'probability': predictions['home'],
    'odds': market_odds['home'],  # 用市场赔率@2.07，不是定价@1.62
    'confidence': pricing_output.confidence / 100
}

allocation = treasury_agent.allocate_stake(opportunity, risk_level="medium")
print("  注码分配建议:")
print(f"    Kelly比例: {allocation['kelly']:.2%}")
if allocation['action'] == 'bet':
    print(f"    实际分数: {allocation['fraction']:.2%}")
    print(f"    建议注码: {allocation['stake']} EUR")
    print(f"    期望值: +{allocation['expected_value']:.1f}%")
    print(f"    执行后可用: {allocation['available_after']} EUR")
else:
    print(f"    状态: {allocation['action']} ({allocation['reason']})")
print()

# 执行投注
if allocation['action'] == 'bet':
    pos = Position(
        match_id="USA_PAR_20260613",
        market="1X2",
        selection="home",
        odds=pricing_output.odds['home'],
        stake=allocation['stake'],
        expected_value=allocation['expected_value'],
        model_confidence=pricing_output.confidence / 100,
        timestamp=datetime.now()
    )
    
    result = treasury_agent.place_bet(pos)
    print("  投注执行:")
    print(f"    状态: {'✅ 成功' if result['success'] else '❌ 失败'}")
    print(f"    投注额: {allocation['stake']} EUR @ {pricing_output.odds['home']}")
    print(f"    潜在回报: {allocation['stake'] * pricing_output.odds['home']:.2f} EUR")
    print()

# 风险监控
print("  风险仪表盘:")
dashboard = treasury_agent.get_risk_dashboard()
print(f"    风险分数: {dashboard['risk_score']:.0f}/100")
print(f"    警报级别: {dashboard['alert_level'].upper()}")
print(f"    敞口比例: {dashboard['portfolio']['exposure_pct']:.1%}")
print(f"    95% VaR: {dashboard['portfolio']['var_95']:.2f} EUR")
print()

# ==================== 第四步：实时调整（模拟） ====================
print("【Step 4】实时赔率调整（Book Balancing 模拟）")
print("-" * 80)

# 模拟大量投注涌入
flow = {"home": 85000, "draw": 12000, "away": 3000}  # 85%买美国
adjusted = pricing_agent.adjust_odds_realtime(pricing_output.odds, flow, {})

print(f"  原始赔率: 主@{pricing_output.odds['home']} 平@{pricing_output.odds['draw']} 客@{pricing_output.odds['away']}")
print(f"  调整后:   主@{adjusted['odds']['home']} 平@{adjusted['odds']['draw']} 客@{adjusted['odds']['away']}")
print(f"  调整原因:")
for key, reason in adjusted['adjustments'].items():
    print(f"    {key}: {reason}")
print(f"  资金流向: 主{adjusted['flow_ratio']['home']*100:.1f}% | 平{adjusted['flow_ratio']['draw']*100:.1f}% | 客{adjusted['flow_ratio']['away']*100:.1f}%")
print()

# ==================== 第五步：结算（模拟） ====================
print("【Step 5】模拟结算")
print("-" * 80)

# 假设美国1-0胜
settlement = treasury_agent.settle_position("USA_PAR_20260613", "win")
print(f"  比赛结果: 美国 1-0 巴拉圭")
print(f"  结算数量: {settlement['settled']}")
print(f"  P&L: {settlement['total_pnl']:+.2f} EUR")
print(f"  结算后总资金: {settlement['bankroll']['total_funds']} EUR")
print(f"  可用资金: {settlement['bankroll']['available']} EUR")
print()

# P&L报告
pnl = treasury_agent.get_pnl_report(days=7)
print("  P&L报告:")
print(f"    总盈亏: {pnl['total_pnl']:+.2f} EUR")
print(f"    ROI: {pnl['roi']:+.2f}%")
print(f"    胜率: {pnl['win_rate']:.1f}% ({pnl['win_count']}胜/{pnl['loss_count']}负)")
print()

print("=" * 80)
print("  演示完成！Football Quant OS v2.0 P0 Agent 已就绪")
print("  OddsPricingAgent + TreasuryAgent 协同运行正常")
print("=" * 80)
