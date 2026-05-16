#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统集成测试 - Football Quant OS v2.0
验证资金流向完整链路
"""

import sys
import json
sys.stdout.reconfigure(encoding='utf-8')

# 添加项目路径
sys.path.insert(0, 'C:\\Users\\Administrator\\.openclaw\\workspace\\football_quant_os')

from agents.datascout_v2 import DataScout
from agents.analyst_v2 import Analyst
from agents.committee_v2 import Committee
from agents.risk_control_v2 import RiskControl

# 水晶宫 vs 西汉姆联 - 完整资金流向数据
MONEY_FLOW_DATA = {
    "match_id": "1202700",
    "match_time": "2026-04-21 03:00",
    "euro_home_odds": 2.57,
    "euro_draw_odds": 3.31,
    "euro_away_odds": 2.77,
    "euro_home_prob": 37.0,
    "euro_draw_prob": 28.7,
    "euro_away_prob": 34.3,
    "bf_home_price": 2.74,
    "bf_draw_price": 3.45,
    "bf_away_price": 2.88,
    "bf_home_volume": 950546,
    "bf_draw_volume": 575359,
    "bf_away_volume": 1000127,
    "bf_total_volume": 2526032,
    "bookmaker_home_pnl": -78464,
    "bookmaker_draw_pnl": 541043,
    "bookmaker_away_pnl": -354334,
    "profit_index_home": -4,
    "profit_index_draw": 21,
    "profit_index_away": -15,
    "cold_hot_index_home": 1,
    "cold_hot_index_draw": -21,
    "cold_hot_index_away": 15,
    "large_transactions": [
        {"direction": "主", "type": "买", "volume": 14674.0, "time": "2026-04-20 23:02", "ratio": "39.6%"},
        {"direction": "平", "type": "买", "volume": 2116.0, "time": "2026-04-20 23:02", "ratio": "21.2%"},
        {"direction": "客", "type": "卖", "volume": 10066.0, "time": "2026-04-20 23:02", "ratio": "39.2%"},
    ],
    "data_source": "500_auto",
    "fetch_time": "2026-04-20T23:25:00"
}

MATCH_DATA = {
    "home_team": "水晶宫",
    "away_team": "西汉姆联",
    "home_win": 37,
    "draw": 29,
    "away_win": 34,
    "market_odds": {"home_win": 2.57, "draw": 3.31, "away_win": 2.77},
    "expected_goals": 2.5,
    "base_kelly": 0.05,
    "bankroll": 10000
}

print("=" * 70)
print("Football Quant OS v2.0 - 资金流向集成测试")
print("=" * 70)

# ========== Phase 1: DataScout ==========
print("\n[Phase 1] DataScout v2.0")
print("-" * 50)

scout = DataScout()
match_data_with_money = {**MATCH_DATA, "money_flow_manual": MONEY_FLOW_DATA}
scout_result = scout.run(match_data_with_money)

print(f"Agent: {scout_result['agent']} v{scout_result['version']}")
print(f"基础预测: {scout_result['prediction']}")
print(f"推荐: {scout_result['recommendation']}")
print(f"信心: {scout_result['confidence']}")

if 'money_flow' in scout_result:
    mf = scout_result['money_flow']
    print(f"\n资金流向数据:")
    print(f"  总成交量: {mf['bf_total_volume']:,} 港币")
    print(f"  主胜成交: {mf['bf_home_volume']:,} ({mf['bf_home_volume']/mf['bf_total_volume']*100:.1f}%)")
    print(f"  平局成交: {mf['bf_draw_volume']:,} ({mf['bf_draw_volume']/mf['bf_total_volume']*100:.1f}%)")
    print(f"  客胜成交: {mf['bf_away_volume']:,} ({mf['bf_away_volume']/mf['bf_total_volume']*100:.1f}%)")

# ========== Phase 2: Analyst ==========
print("\n[Phase 2] Analyst v2.0")
print("-" * 50)

analyst = Analyst()
analyst_result = analyst.run(match_data_with_money)

print(f"Agent: {analyst_result['agent']} v{analyst_result['version']}")
print(f"预测调整: {analyst_result['prediction']}")
print(f"熵值: {analyst_result['entropy']}")

if 'money_flow_analysis' in analyst_result:
    mfa = analyst_result['money_flow_analysis']
    print(f"\n资金流向分析:")
    print(f"  信号: {mfa['signal']}")
    print(f"  信心: {mfa['confidence']}")
    print(f"  关键洞察:")
    for insight in mfa['key_insights']:
        print(f"    - {insight}")
    if mfa['risk_flags']:
        print(f"  风险标志:")
        for flag in mfa['risk_flags']:
            print(f"    ! {flag}")
    print(f"  建议: {mfa['recommendation']}")

# ========== Phase 3: Committee ==========
print("\n[Phase 3] Committee v2.0 - 资金信号加权")
print("-" * 50)

committee = Committee()

# 收集所有Agent观点
opinions = [
    scout_result,
    analyst_result
]

# 添加基因引擎观点（模拟）
opinions.append({
    "agent": "GeneEngine",
    "prediction": {"home_win": 42, "draw": 28, "away_win": 30},
    "confidence": 0.75
})

# 添加108矩阵观点（模拟）
opinions.append({
    "agent": "Matrix108",
    "prediction": {"home_win": 38, "draw": 29, "away_win": 33},
    "confidence": 0.8
})

committee.receive_other_opinions(opinions)

# 如果有资金信号，传递给Committee
if 'money_flow_analysis' in analyst_result:
    mfa = analyst_result['money_flow_analysis']
    signal_type = mfa['signal'].lower().replace(' ', '_')
    committee.receive_fund_signals([{
        "signal_type": signal_type,
        "confidence": mfa['confidence'],
        "direction": mfa.get('direction', 'neutral'),
        "strength": mfa.get('strength', 'neutral'),
        "source": "money_flow",
        "weight": 1.0
    }])

committee_result = committee.run(MATCH_DATA)

print(f"Agent: {committee_result['agent']} v{committee_result['version']}")
print(f"最终预测: {committee_result['prediction']}")
print(f"综合置信度: {committee_result['confidence']}")
print(f"推荐结果: {committee_result['recommended_outcome']}")
print(f"资金信号已应用: {committee_result['fund_signal_applied']}")
print(f"参与Agent数: {committee_result['agent_count']}")
print(f"\n关键因子:")
for factor in committee_result['key_factors']:
    print(f"  - {factor}")

# ========== Phase 4: RiskControl ==========
print("\n[Phase 4] RiskControl v2.0")
print("-" * 50)

risk_input = {
    **MATCH_DATA,
    "committee_prediction": committee_result['prediction'],
    "recommended_outcome": committee_result['recommended_outcome']
}

if 'money_flow_analysis' in analyst_result:
    risk_input["money_flow_analysis"] = analyst_result['money_flow_analysis']

risk = RiskControl()
risk_result = risk.run(risk_input)

print(f"Agent: {risk_result['agent']} v{risk_result['version']}")
print(f"风险等级: {risk_result['risk_level']}")
print(f"允许投注: {'是' if risk_result['allow'] else '否'}")

if risk_result['warnings']:
    print(f"\n警告:")
    for warning in risk_result['warnings']:
        print(f"  ! {warning}")

if 'kelly_adjustment' in risk_result:
    ka = risk_result['kelly_adjustment']
    print(f"\n凯利调整:")
    print(f"  基础凯利: {ka['base_kelly']:.2%}")
    print(f"  调整后: {ka['adjusted_kelly']:.2%}")
    print(f"  最大仓位: {ka['max_bet_pct']:.2%}")
    print(f"  调整原因: {ka['adjustment_reason']}")

# ========== 综合报告 ==========
print("\n" + "=" * 70)
print("综合决策报告")
print("=" * 70)

print(f"\n比赛: 水晶宫 vs 西汉姆联")
print(f"时间: 2026-04-21 03:00")

print(f"\n【基础面分析】")
print(f"  DataScout推荐: {scout_result['recommendation']}")
print(f"  Analyst信号: {analyst_result.get('money_flow_analysis', {}).get('signal', 'N/A')}")

print(f"\n【Committee综合决策】")
print(f"  最终预测: {committee_result['prediction']}")
print(f"  推荐: {committee_result['recommended_outcome']}")
print(f"  置信度: {committee_result['confidence']}")

print(f"\n【风控决策】")
print(f"  风险等级: {risk_result['risk_level']}")
print(f"  允许投注: {'是' if risk_result['allow'] else '否'}")
if 'kelly_adjustment' in risk_result:
    ka = risk_result['kelly_adjustment']
    print(f"  建议仓位: {ka['adjusted_kelly']:.2%} ({ka['adjusted_kelly']*MATCH_DATA['bankroll']:.0f}元)")

print(f"\n【资金流向洞察】")
if 'money_flow_analysis' in analyst_result:
    mfa = analyst_result['money_flow_analysis']
    for insight in mfa['key_insights']:
        print(f"  - {insight}")

print("\n" + "=" * 70)
print("系统集成测试完成")
print("=" * 70)
