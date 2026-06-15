#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 组合投注回测框架 (backtest_combinations.py)

支持:
- 按日期分组的历史数据回测
- 组合投注策略验证
- 多维度绩效分析 (ROI / 回撤 / 胜率)
- 不同串关类型对比

Version: 1.0.0
Date: 2026-06-14
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import json


@dataclass
class CombinationBacktestResult:
    """单场回测结果"""
    date: str
    match_group: List[str]  # 比赛列表
    total_stake: float
    total_return: float
    profit: float
    roi: float
    hit_count: int  # 中奖组合数
    total_combinations: int
    combination_type: str  # 2串1 / 3串1 / 4串1 / mixed


@dataclass
class BacktestSummary:
    """回测汇总"""
    total_stake: float = 0
    total_return: float = 0
    total_profit: float = 0
    overall_roi: float = 0
    max_drawdown: float = 0
    win_rate: float = 0
    avg_roi_per_bet: float = 0
    best_day: Optional[str] = None
    best_day_profit: float = 0
    worst_day: Optional[str] = None
    worst_day_profit: float = 0
    total_bets: int = 0
    winning_bets: int = 0
    losing_bets: int = 0
    by_type: Dict[str, Dict] = field(default_factory=dict)
    equity_curve: List[Dict] = field(default_factory=list)


def generate_recommendations_for_match_group(match_group: List[Dict],
                                              strategy_params: Dict) -> List[Dict]:
    """
    对一组比赛生成组合推荐
    
    Args:
        match_group: 同一天的多场比赛预测结果
        strategy_params: 策略参数
    
    Returns:
        组合推荐列表
    """
    from combination_betting import generate_combinations
    from combination_recommender import extract_value_bets_from_predictions

    # 提取有价值的投注
    all_bets = []
    for match in match_group:
        bets = extract_value_bets_from_predictions([match])
        all_bets.extend(bets)

    if len(all_bets) < 2:
        return []

    recommendations = []
    bankroll = strategy_params.get('bankroll', 10000)
    risk_level = strategy_params.get('risk_level', 'conservative')
    min_edge = strategy_params.get('min_edge', 0.03)

    # 生成2串1、3串1、4串1
    for fold in [2, 3, 4]:
        if strategy_params.get(f'enable_{fold}fold', True):
            recs = generate_combinations(
                all_bets, fold=fold,
                min_edge=min_edge,
                risk_level=risk_level,
                bankroll=bankroll
            )
            recommendations.extend(recs)

    return recommendations


def calculate_actual_profit(recommendations: List[Dict],
                               match_results: List[Dict]) -> float:
    """
    计算实际盈亏
    
    Args:
        recommendations: 组合推荐列表
        match_results: 实际比赛结果
    
    Returns:
        总盈亏
    """
    total_profit = 0
    total_stake = 0

    # 构建比赛结果查找表
    result_map = {}
    for match in match_results:
        key = f"{match['home']} vs {match['away']}"
        result_map[key] = match['result']

    for rec in recommendations:
        stake = rec.get('allocated_stake', rec.get('recommended_stake', 0))
        total_stake += stake

        # 检查组合是否中奖
        all_correct = True
        for match_str, selection in zip(rec['matches'], rec['selections']):
            actual_result = result_map.get(match_str, 'unknown')
            if not _is_selection_correct(selection, actual_result, match_str):
                all_correct = False
                break

        if all_correct:
            total_profit += stake * rec['combined_odds'] - stake
        else:
            total_profit -= stake

    return total_profit, total_stake


def _is_selection_correct(selection: str, actual_result: str, match_str: str) -> bool:
    """
    判断投注选项是否正确
    
    简化版判断逻辑:
    - "home" / "home_win" / "X胜" -> 主队胜
    - "draw" / "平局" -> 平局
    - "away" / "away_win" / "X胜" -> 客队胜
    - "over_X" / "大X" -> 大球
    - "under_X" / "小X" -> 小球
    """
    selection_lower = selection.lower()

    if 'home' in selection_lower or selection_lower.startswith('主'):
        return actual_result == 'home'
    elif 'away' in selection_lower or '客' in selection_lower:
        return actual_result == 'away'
    elif 'draw' in selection_lower or '平' in selection_lower:
        return actual_result == 'draw'
    elif 'over' in selection_lower or '大' in selection_lower:
        return actual_result == 'over'
    elif 'under' in selection_lower or '小' in selection_lower:
        return actual_result == 'under'

    return False


def backtest_combinations(historical_data: List[Dict],
                          strategy_params: Optional[Dict] = None) -> BacktestSummary:
    """
    组合投注回测主函数

    Args:
        historical_data: 历史数据列表，每项包含:
            {
                'date': '2026-06-15',
                'matches': [
                    {'home': 'A', 'away': 'B', 'result': 'home', 'odds': {...}},
                    ...
                ]
            }
        strategy_params: 策略参数

    Returns:
        BacktestSummary 回测汇总
    """
    if strategy_params is None:
        strategy_params = {
            'bankroll': 10000,
            'risk_level': 'conservative',
            'min_edge': 0.03,
            'max_total_risk': 0.20,
            'allocation_method': 'proportional',
            'enable_2fold': True,
            'enable_3fold': True,
            'enable_4fold': False,  # 默认关闭4串1（风险高）
        }

    from combination_betting import allocate_bankroll_to_combinations

    results = []
    cumulative_profit = 0
    peak_profit = 0
    max_drawdown = 0

    equity_curve = []

    for day_data in historical_data:
        date = day_data['date']
        match_group = day_data.get('matches', [])
        actual_results = day_data.get('results', match_group)

        # 生成推荐组合
        recommendations = generate_recommendations_for_match_group(
            match_group, strategy_params
        )

        if not recommendations:
            continue

        # 资金分配
        allocation = allocate_bankroll_to_combinations(
            recommendations,
            total_bankroll=strategy_params['bankroll'],
            max_total_risk=strategy_params.get('max_total_risk', 0.20),
            allocation_method=strategy_params.get('allocation_method', 'proportional')
        )

        # 计算实际盈亏
        profit, stake = calculate_actual_profit(
            allocation['combinations'], actual_results
        )

        cumulative_profit += profit
        if cumulative_profit > peak_profit:
            peak_profit = cumulative_profit

        drawdown = peak_profit - cumulative_profit
        if drawdown > max_drawdown:
            max_drawdown = drawdown

        # 统计中奖数
        hit_count = sum(1 for r in allocation['combinations']
                        if r.get('profit', 0) > 0)

        results.append({
            'date': date,
            'match_group': [f"{m['home']} vs {m['away']}" for m in match_group],
            'total_stake': stake,
            'total_return': stake + profit,
            'profit': profit,
            'roi': profit / stake if stake > 0 else 0,
            'hit_count': hit_count,
            'total_combinations': len(allocation['combinations']),
        })

        equity_curve.append({
            'date': date,
            'cumulative_profit': cumulative_profit,
            'drawdown': drawdown
        })

    # 汇总统计
    total_stake = sum(r['total_stake'] for r in results)
    total_return = sum(r['total_return'] for r in results)
    total_profit = total_return - total_stake
    winning_days = [r for r in results if r['profit'] > 0]
    losing_days = [r for r in results if r['profit'] <= 0]

    best_day = max(winning_days, key=lambda x: x['profit']) if winning_days else None
    worst_day = min(losing_days, key=lambda x: x['profit']) if losing_days else None

    summary = BacktestSummary(
        total_stake=total_stake,
        total_return=total_return,
        total_profit=total_profit,
        overall_roi=total_profit / total_stake if total_stake > 0 else 0,
        max_drawdown=max_drawdown,
        win_rate=len(winning_days) / len(results) if results else 0,
        avg_roi_per_bet=sum(r['roi'] for r in results) / len(results) if results else 0,
        best_day=best_day['date'] if best_day else None,
        best_day_profit=best_day['profit'] if best_day else 0,
        worst_day=worst_day['date'] if worst_day else None,
        worst_day_profit=worst_day['profit'] if worst_day else 0,
        total_bets=len(results),
        winning_bets=len(winning_days),
        losing_bets=len(losing_days),
        equity_curve=equity_curve
    )

    return summary


def format_backtest_summary(summary: BacktestSummary) -> str:
    """格式化回测汇总报告"""
    lines = []
    lines.append("=" * 60)
    lines.append("组合投注回测报告")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"总投注天数: {summary.total_bets}")
    lines.append(f"盈利天数: {summary.winning_bets} ({summary.win_rate:.1%})")
    lines.append(f"亏损天数: {summary.losing_bets}")
    lines.append("")
    lines.append(f"总投入: ${summary.total_stake:,.2f}")
    lines.append(f"总回报: ${summary.total_return:,.2f}")
    lines.append(f"总盈亏: ${summary.total_profit:,.2f}")
    lines.append(f"整体ROI: {summary.overall_roi:.2%}")
    lines.append(f"平均每注ROI: {summary.avg_roi_per_bet:.2%}")
    lines.append("")
    lines.append(f"最大回撤: ${summary.max_drawdown:,.2f}")
    lines.append("")
    if summary.best_day:
        lines.append(f"最佳单日: {summary.best_day} (+${summary.best_day_profit:,.2f})")
    if summary.worst_day:
        lines.append(f"最差单日: {summary.worst_day} (${summary.worst_day_profit:,.2f})")
    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ====================== 测试 ======================
if __name__ == "__main__":
    # 模拟历史回测数据
    historical_data = [
        {
            'date': '2026-06-15',
            'matches': [
                {'home': 'Sweden', 'away': 'Tunisia', 'result': 'draw'},
                {'home': 'Ivory Coast', 'away': 'Ecuador', 'result': 'draw'},
                {'home': 'Netherlands', 'away': 'Japan', 'result': 'away'},
            ]
        },
        {
            'date': '2026-06-16',
            'matches': [
                {'home': 'Germany', 'away': 'Curacao', 'result': 'home'},
                {'home': 'Brazil', 'away': 'Argentina', 'result': 'draw'},
            ]
        },
        {
            'date': '2026-06-17',
            'matches': [
                {'home': 'France', 'away': 'Spain', 'result': 'home'},
                {'home': 'England', 'away': 'Italy', 'result': 'away'},
                {'home': 'Portugal', 'away': 'Uruguay', 'result': 'draw'},
            ]
        }
    ]

    strategy_params = {
        'bankroll': 10000,
        'risk_level': 'conservative',
        'min_edge': 0.03,
        'max_total_risk': 0.18,
        'allocation_method': 'proportional',
        'enable_2fold': True,
        'enable_3fold': True,
        'enable_4fold': False,
    }

    summary = backtest_combinations(historical_data, strategy_params)
    print(format_backtest_summary(summary))
