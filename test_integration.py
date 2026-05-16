#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 集成测试
验证 FastAPI + 异步调度 + 新系统 + 回测
"""

import sys
import asyncio
sys.stdout.reconfigure(encoding='utf-8')

# 测试1: 直接调用任务
async def test_analyze():
    print("=" * 70)
    print("测试1: 比赛分析任务")
    print("=" * 70)
    
    from app.tasks import run_match_task
    
    match = {
        "home_team": "皇家马德里",
        "away_team": "拜仁慕尼黑",
        "league": "Champions League",
        "home_team_rank": 2,
        "away_team_rank": 3,
        "home_recent_5": ["W", "W", "D", "W", "W"],
        "away_recent_5": ["W", "L", "W", "W", "D"],
        "home_team_genes": {
            "逆转基因": 0.35, "追平基因": 0.45, "守住基因": 0.72,
            "痛失好局基因": 0.15, "被追平基因": 0.22, "平局大师基因": 0.18
        },
        "away_team_genes": {
            "逆转基因": 0.55, "追平基因": 0.60, "守住基因": 0.48,
            "痛失好局基因": 0.25, "被追平基因": 0.30, "平局大师基因": 0.20
        },
        "market_odds": {"home_win": 2.18, "draw": 3.55, "away_win": 3.32},
        "bankroll": 10000
    }
    
    result = await run_match_task(match)
    
    print(f"状态: {result['status']}")
    print(f"决策: {result['decision'].get('recommended_outcome', 'N/A')}")
    print(f"建议投注: {result['stake']['stake']}")
    print(f"凯利比例: {result['stake']['safe_fraction'] * 100}%")
    print(f"实力差距: {result['team_strengths'].get('matchup_type', 'N/A')}")
    print(f"108矩阵: 主胜{result['matrix_108']['probabilities']['home_win']}%")
    print(f"基因洞察: {result['gene_analysis'].get('insight', 'N/A')[:40]}...")
    print()


# 测试2: 回测引擎
def test_backtest():
    print("=" * 70)
    print("测试2: 回测引擎")
    print("=" * 70)
    
    from backtest.engine import BacktestEngine, compare_strategies
    
    # 单策略回测
    engine = BacktestEngine(bankroll=1000, strategy="kelly_compressed")
    result = engine.run()
    
    print(f"策略: {result['strategy']}")
    print(f"初始资金: {result['initial_bankroll']}")
    print(f"最终资金: {result['final_bankroll']}")
    print(f"胜率: {result['win_rate']}%")
    print(f"ROI: {result['roi']}%")
    print(f"最大回撤: {result['max_drawdown']}%")
    print()
    
    # 策略对比
    print("策略对比:")
    comparison = compare_strategies()
    for name, res in comparison['comparison'].items():
        print(f"  {name:20s}: 最终={res['final_bankroll']:8.2f} | ROI={res['roi']:6.2f}% | 回撤={res['max_drawdown']:5.2f}%")
    print(f"  最优策略: {comparison['best_strategy']}")
    print()


# 测试3: 108矩阵查询
def test_matrix():
    print("=" * 70)
    print("测试3: 108组合概率矩阵")
    print("=" * 70)
    
    from models.matrix_108 import ProbabilityMatrix108
    
    matrix = ProbabilityMatrix108()
    
    # 查询特定组合
    cell = matrix.get_probability("strong_vs_weak", "home", "76-90")
    print(f"组合: 强vs弱_主队先进球_收官阶段")
    print(f"概率: 主胜{cell.home_win_prob:.1f}% | 平局{cell.draw_prob:.1f}% | 客胜{cell.away_win_prob:.1f}%")
    print(f"标签: {', '.join(cell.tags)}")
    print()
    
    # 赛前综合
    pre_match = matrix.apply_to_match("even")
    print(f"赛前综合(实力接近): 主胜{pre_match['probabilities']['home_win']}% | "
          f"平局{pre_match['probabilities']['draw']}% | "
          f"客胜{pre_match['probabilities']['away_win']}%")
    print()


async def main():
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Football Quant OS - 集成测试" + " " * 25 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    await test_analyze()
    test_backtest()
    test_matrix()
    
    print("=" * 70)
    print("✅ 所有测试通过")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
