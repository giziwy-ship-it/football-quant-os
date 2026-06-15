#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 组合投注推荐模块 (combination_betting.py)
支持: 2串1, 3串1, 4串1
包含: 动态相关性调整 + 市场多样性加分

Version: 5.1.0
Date: 2026-06-14
"""

from itertools import combinations
from typing import List, Dict, Any, Optional
from datetime import datetime
import json


def get_base_correlation_matrix() -> Dict:
    """基础市场相关性矩阵 (0~0.5)"""
    return {
        # 高相关性 - 避免组合
        ("1x2", "asian_handicap"): 0.38,
        ("1x2", "ht_ft"): 0.28,
        ("1x2", "correct_score"): 0.45,
        ("asian_handicap", "ht_ft"): 0.25,
        ("over_under", "total_goals"): 0.48,
        ("total_goals", "correct_score"): 0.42,
        ("1x2", "total_goals"): 0.20,
        
        # 中等相关性
        ("1x2", "over_under"): 0.15,
        ("ht_ft", "over_under"): 0.18,
        ("correct_score", "over_under"): 0.22,
        
        # 低相关性 - 推荐组合
        ("asian_handicap", "over_under"): 0.12,
        ("asian_handicap", "total_goals"): 0.10,
        ("ht_ft", "total_goals"): 0.15,
        ("ht_ft", "asian_handicap"): 0.18,
        ("1x2", "over_under_15"): 0.14,
        ("correct_score", "ht_ft"): 0.30,
    }


def get_correlation(market1: str, market2: str) -> float:
    """获取两个市场之间的相关性"""
    matrix = get_base_correlation_matrix()
    key = (market1, market2)
    reverse_key = (market2, market1)
    return matrix.get(key, matrix.get(reverse_key, 0.15))


def calculate_dynamic_correlation(bet1: Dict, bet2: Dict) -> float:
    """
    动态计算两个投注之间的相关性
    考虑因素: 是否同一天、是否同联赛
    """
    base_corr = get_correlation(
        bet1.get('market', ''), 
        bet2.get('market', '')
    )
    
    # 同一天比赛 -> 相关性增加
    date1 = bet1.get('match_date')
    date2 = bet2.get('match_date')
    if date1 and date2 and date1 == date2:
        base_corr += 0.08
    
    # 同联赛/同赛事 -> 相关性增加
    league1 = bet1.get('league', '')
    league2 = bet2.get('league', '')
    if league1 and league2 and league1 == league2:
        base_corr += 0.06
    
    return min(base_corr, 0.50)


def calculate_combined_odds(bets: List[Dict]) -> float:
    """计算组合总赔率"""
    total = 1.0
    for bet in bets:
        total *= bet['odds']
    return round(total, 2)


def calculate_combined_probability(bets: List[Dict]) -> float:
    """计算组合概率（含动态相关性调整）"""
    if not bets:
        return 0.0
    
    # 独立概率
    independent_prob = 1.0
    for bet in bets:
        independent_prob *= bet.get('probability', 0)
    
    if len(bets) <= 1:
        return round(independent_prob, 4)
    
    # 计算平均成对相关性
    total_corr = 0
    pair_count = 0
    
    for i in range(len(bets)):
        for j in range(i + 1, len(bets)):
            corr = calculate_dynamic_correlation(bets[i], bets[j])
            total_corr += corr
            pair_count += 1
    
    avg_correlation = total_corr / pair_count if pair_count > 0 else 0.12
    
    # 相关性惩罚
    decay_factor = 1 - (avg_correlation * (len(bets) - 1) * 0.22)
    decay_factor = max(0.55, min(decay_factor, 1.0))
    
    final_prob = independent_prob * decay_factor
    return round(max(0.01, final_prob), 4)


def calculate_combined_edge(combined_prob: float, combined_odds: float) -> float:
    """计算组合Edge"""
    implied_prob = 1 / combined_odds
    return round(combined_prob - implied_prob, 4)


def calculate_diversity_score(bets: List[Dict]) -> float:
    """
    计算市场多样性得分
    市场种类越多，分数越高 (0~1)
    """
    unique_markets = set(bet.get('market', '') for bet in bets)
    diversity = len(unique_markets) / len(bets) if bets else 0
    return round(diversity, 2)


def kelly_for_accumulator(combined_prob: float, combined_odds: float,
                          risk_level: str = "conservative") -> float:
    """
    串关Kelly计算
    
    Args:
        risk_level: "conservative"(1/5 Kelly) / "standard"(1/3 Kelly) / "aggressive"(半Kelly)
    """
    if combined_prob * combined_odds <= 1:
        return 0.0
    
    full_kelly = (combined_prob * combined_odds - 1) / (combined_odds - 1)
    multipliers = {
        "conservative": 0.20,  # 1/5 Kelly
        "standard": 0.33,      # 1/3 Kelly
        "aggressive": 0.50     # 半Kelly
    }
    return max(0, min(full_kelly * multipliers.get(risk_level, 0.25), 0.08))


def calculate_market_quality_score(bets: List[Dict]) -> float:
    """
    计算市场质量得分
    优先推荐: 让球+大小球 > 胜平负+大小球 > 半全场+大小球
    """
    markets = [b.get('market', '') for b in bets]
    unique_markets = set(markets)
    
    score = 0.0
    
    # 多样性加分
    if len(unique_markets) >= 2:
        score += 0.02
    if len(unique_markets) >= 3:
        score += 0.03
    
    # 推荐组合加分
    if "asian_handicap" in unique_markets and "over_under" in unique_markets:
        score += 0.025  # 让球+大小球 = 最佳组合
    
    if "1x2" in unique_markets and "over_under" in unique_markets:
        score += 0.015  # 胜平负+大小球 = 良好组合
    
    # 避免组合减分
    if "1x2" in unique_markets and "correct_score" in unique_markets:
        score -= 0.03
    if "over_under" in unique_markets and "total_goals" in unique_markets:
        score -= 0.03
    
    return score


def generate_combinations(bets: List[Dict], fold: int = 2,
                          min_edge: float = 0.03,
                          risk_level: str = "conservative",
                          bankroll: float = 10000,
                          max_results: int = 6) -> List[Dict]:
    """
    生成指定串关的推荐组合
    
    Args:
        bets: 投注列表
        fold: 串关数量 (2, 3, 4)
        min_edge: 单场最小Edge要求
        risk_level: 风险等级
        bankroll: 资金池
        max_results: 最大返回结果数
    """
    valid_bets = [b for b in bets if b.get('edge', 0) >= min_edge]
    
    if len(valid_bets) < fold:
        return []
    
    recommendations = []
    
    for combo in combinations(valid_bets, fold):
        combo_list = list(combo)
        
        combined_odds = calculate_combined_odds(combo_list)
        combined_prob = calculate_combined_probability(combo_list)
        combined_edge = calculate_combined_edge(combined_prob, combined_odds)
        
        if combined_edge <= 0:
            continue
        
        diversity_score = calculate_diversity_score(combo_list)
        quality_score = calculate_market_quality_score(combo_list)
        
        # 综合得分 = Edge + 多样性加分 + 质量加分
        final_score = combined_edge + (diversity_score * 0.02) + quality_score
        
        stake_fraction = kelly_for_accumulator(combined_prob, combined_odds, risk_level)
        stake = round(bankroll * stake_fraction, 2)
        
        if stake <= 0:
            continue
        
        recommendations.append({
            "type": f"{fold}串1",
            "matches": [f"{b['home']} vs {b['away']}" for b in combo_list],
            "selections": [b['selection'] for b in combo_list],
            "markets": [b['market'] for b in combo_list],
            "combined_odds": combined_odds,
            "combined_probability": combined_prob,
            "combined_edge": combined_edge,
            "diversity_score": diversity_score,
            "quality_score": round(quality_score, 4),
            "final_score": round(final_score, 4),
            "recommended_stake": stake,
            "stake_fraction": round(stake_fraction * 100, 2),
            "risk_level": risk_level,
            "expected_return": round(stake * combined_odds, 2),
        })
    
    recommendations.sort(key=lambda x: x['final_score'], reverse=True)
    return recommendations[:max_results]


def recommend_combinations(bets: List[Dict], bankroll: float = 10000,
                           risk_level: str = "conservative") -> Dict[str, List]:
    """
    一键生成 2串1, 3串1, 4串1 推荐
    
    Returns:
        {
            "2串1": [...],
            "3串1": [...],
            "4串1": [...]
        }
    """
    result = {
        "2串1": generate_combinations(bets, fold=2, risk_level=risk_level, bankroll=bankroll),
        "3串1": generate_combinations(bets, fold=3, risk_level=risk_level, bankroll=bankroll),
        "4串1": generate_combinations(bets, fold=4, risk_level=risk_level, bankroll=bankroll),
    }
    return result


def allocate_bankroll_to_combinations(recommendations: List[Dict],
                                       total_bankroll: float,
                                       max_total_risk: float = 0.20,
                                       allocation_method: str = "proportional") -> Dict:
    """
    对多个组合推荐进行全局资金分配

    Args:
        recommendations: 组合推荐列表（所有fold的合并列表）
        total_bankroll: 总资金池
        max_total_risk: 最大总风险敞口（默认本金的20%）
        allocation_method: 分配策略
            - "proportional": 按Edge比例分配（默认）
            - "equal": 等金额分配
            - "kelly": 纯Kelly（不缩减，可能超限）
            - "top_n": 只取Top N个组合，均分风险额度

    Returns:
        {
            "combinations": [...],
            "total_allocated": float,
            "total_risk_ratio": float,
            "max_risk_ratio": float,
            "bankroll_remaining": float,
            "method": str
        }
    """
    if not recommendations:
        return {
            "combinations": [],
            "total_allocated": 0.0,
            "total_risk_ratio": 0.0,
            "max_risk_ratio": max_total_risk,
            "bankroll_remaining": total_bankroll,
            "method": allocation_method
        }

    # 计算每个组合的独立Kelly金额
    for rec in recommendations:
        rec['kelly_stake'] = rec.get('recommended_stake', 0)

    total_kelly_stake = sum(rec['kelly_stake'] for rec in recommendations)
    max_allowed_stake = total_bankroll * max_total_risk

    if allocation_method == "kelly":
        # 纯Kelly，不缩减（风险可能超限）
        for rec in recommendations:
            rec['allocated_stake'] = rec['kelly_stake']
            rec['allocation_note'] = "纯Kelly分配（未缩减）"

    elif allocation_method == "equal":
        # 等金额分配
        per_combo = max_allowed_stake / len(recommendations) if recommendations else 0
        for rec in recommendations:
            rec['allocated_stake'] = round(min(per_combo, rec['kelly_stake']), 2)
            rec['allocation_note'] = f"等金额分配（每注{per_combo:.2f}）"

    elif allocation_method == "top_n":
        # 只取Top N个组合，均分风险额度
        top_n = min(3, len(recommendations))
        top_combos = recommendations[:top_n]
        per_combo = max_allowed_stake / top_n
        for rec in recommendations:
            if rec in top_combos:
                rec['allocated_stake'] = round(min(per_combo, rec['kelly_stake']), 2)
                rec['allocation_note'] = f"Top{top_n}均分（每注{per_combo:.2f}）"
            else:
                rec['allocated_stake'] = 0
                rec['allocation_note'] = "未入选Top组合"

    else:  # proportional - 默认按Edge比例分配
        if total_kelly_stake > max_allowed_stake:
            # 按Edge比例分配风险额度
            total_edge = sum(rec.get('combined_edge', 0) for rec in recommendations)
            if total_edge > 0:
                for rec in recommendations:
                    weight = rec.get('combined_edge', 0) / total_edge
                    rec['allocated_stake'] = round(max_allowed_stake * weight, 2)
                    rec['allocation_note'] = f"按Edge比例分配（权重{weight:.1%}）"
            else:
                # 无Edge则等分
                per_combo = max_allowed_stake / len(recommendations)
                for rec in recommendations:
                    rec['allocated_stake'] = round(per_combo, 2)
                    rec['allocation_note'] = "无Edge差异，等额分配"
        else:
            # 未超限，按Kelly独立分配
            for rec in recommendations:
                rec['allocated_stake'] = rec['kelly_stake']
                rec['allocation_note'] = "按独立Kelly分配（未超限）"

    # 计算总投入和风险占比
    total_allocated = sum(rec['allocated_stake'] for rec in recommendations)

    # 重新计算预期回报
    for rec in recommendations:
        rec['allocated_expected_return'] = round(rec['allocated_stake'] * rec['combined_odds'], 2)

    return {
        "combinations": recommendations,
        "total_allocated": round(total_allocated, 2),
        "total_risk_ratio": round(total_allocated / total_bankroll, 4) if total_bankroll > 0 else 0,
        "max_risk_ratio": max_total_risk,
        "bankroll_remaining": round(total_bankroll - total_allocated, 2),
        "method": allocation_method,
        "total_kelly_stake": total_kelly_stake,
        "risk_adjusted": total_kelly_stake > max_allowed_stake
    }


def format_allocation_result(result: Dict) -> str:
    """格式化资金分配结果"""
    lines = []
    lines.append("=" * 60)
    lines.append(f"组合投注资金分配报告 (策略: {result['method']})")
    lines.append("=" * 60)
    lines.append(f"总资金: ${result['total_allocated'] + result['bankroll_remaining']:.2f}")
    lines.append(f"已分配: ${result['total_allocated']:.2f} ({result['total_risk_ratio']:.1%})")
    lines.append(f"风险上限: {result['max_risk_ratio']:.1%}")
    lines.append(f"剩余资金: ${result['bankroll_remaining']:.2f}")
    lines.append(f"Kelly总和: ${result['total_kelly_stake']:.2f}")
    lines.append(f"是否缩减: {'是' if result['risk_adjusted'] else '否'}")
    lines.append("")

    for i, rec in enumerate(result['combinations'][:8], 1):
        if rec['allocated_stake'] <= 0:
            continue
        lines.append(f"组合 #{i} [{rec['type']}]")
        lines.append(f"  比赛: {' + '.join(rec['matches'])}")
        lines.append(f"  选项: {' + '.join(rec['selections'])}")
        lines.append(f"  赔率: {rec['combined_odds']}")
        lines.append(f"  Kelly: ${rec['kelly_stake']:.2f} -> 分配: ${rec['allocated_stake']:.2f}")
        lines.append(f"  预期回报: ${rec['allocated_expected_return']:.2f}")
        lines.append(f"  备注: {rec['allocation_note']}")
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_recommendations(recommendations: Dict[str, List]) -> str:
    """格式化输出推荐结果"""
    lines = []
    lines.append("=" * 60)
    lines.append("组合投注推荐 (Football Quant OS v5.1)")
    lines.append("=" * 60)
    
    for fold_type, recs in recommendations.items():
        lines.append(f"\n{'='*20} {fold_type} {'='*20}")
        if not recs:
            lines.append("暂无符合条件的推荐")
            continue
        
        for i, rec in enumerate(recs, 1):
            lines.append(f"\n组合 #{i}")
            lines.append(f"  比赛: {' + '.join(rec['matches'])}")
            lines.append(f"  选项: {' + '.join(rec['selections'])}")
            lines.append(f"  市场: {' + '.join(rec['markets'])}")
            lines.append(f"  总赔率: {rec['combined_odds']}")
            lines.append(f"  组合概率: {rec['combined_probability']:.2%}")
            lines.append(f"  组合Edge: {rec['combined_edge']:.2%}")
            lines.append(f"  多样性得分: {rec['diversity_score']}")
            lines.append(f"  推荐投注: {rec['recommended_stake']} ({rec['stake_fraction']}%)")
            lines.append(f"  预期回报: {rec['expected_return']}")
    
    lines.append("\n" + "=" * 60)
    return "\n".join(lines)


# ====================== 测试 ======================
if __name__ == "__main__":
    # 模拟多场有Edge的投注
    sample_bets = [
        {
            "home": "曼城", "away": "利物浦",
            "market": "1x2", "selection": "曼城胜",
            "odds": 1.85, "probability": 0.58, "edge": 0.04,
            "match_date": "2026-06-15", "league": "英超"
        },
        {
            "home": "阿森纳", "away": "切尔西",
            "market": "over_under", "selection": "大2.5",
            "odds": 1.95, "probability": 0.55, "edge": 0.03,
            "match_date": "2026-06-15", "league": "英超"
        },
        {
            "home": "皇马", "away": "巴萨",
            "market": "asian_handicap", "selection": "皇马-0.5",
            "odds": 2.10, "probability": 0.52, "edge": 0.05,
            "match_date": "2026-06-16", "league": "西甲"
        },
        {
            "home": "拜仁", "away": "多特",
            "market": "ht_ft", "selection": "主/主",
            "odds": 2.40, "probability": 0.48, "edge": 0.035,
            "match_date": "2026-06-16", "league": "德甲"
        },
        {
            "home": "瑞典", "away": "突尼斯",
            "market": "1x2", "selection": "平局",
            "odds": 3.45, "probability": 0.41, "edge": 0.12,
            "match_date": "2026-06-15", "league": "世界杯"
        },
        {
            "home": "瑞典", "away": "突尼斯",
            "market": "asian_handicap", "selection": "突尼斯+0.75",
            "odds": 1.93, "probability": 0.65, "edge": 0.08,
            "match_date": "2026-06-15", "league": "世界杯"
        },
    ]
    
    recommendations = recommend_combinations(sample_bets, bankroll=10000)
    print(format_recommendations(recommendations))
