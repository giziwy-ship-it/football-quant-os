#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kelly 仓位管理模块 (v1.0)
支持：全Kelly、半Kelly、动态风险分级、最大回撤控制
"""

from typing import Dict, Any
import math


def calculate_kelly(probability: float, odds: float) -> float:
    """
    计算全Kelly比例
    probability: 模型认为的胜率 (0~1)
    odds: 赔率 (如 2.10 表示净赔率 b=1.10)
    返回：建议投注比例 (0~1)
    """
    if odds <= 1 or probability <= 0 or probability >= 1:
        return 0.0

    b = odds - 1  # 净赔率
    q = 1 - probability
    kelly = (b * probability - q) / b
    return max(0.0, min(kelly, 1.0))  # 限制在 0~1 之间


def get_kelly_suggestion(probability: float, odds: float,
                         risk_level: str = "standard",
                         current_bankroll: float = 10000,
                         max_drawdown: float = 0.15) -> Dict[str, Any]:
    """
    获取 Kelly 建议（推荐使用此函数）

    risk_level: conservative / standard / aggressive
    current_bankroll: 当前本金
    max_drawdown: 最大可承受回撤比例（默认15%）
    """
    full_kelly = calculate_kelly(probability, odds)

    # 风险等级系数
    risk_multipliers = {
        "conservative": 0.25,  # 保守：只用 1/4 Kelly
        "standard": 0.5,  # 标准：半Kelly（最推荐）
        "aggressive": 0.75  # 激进：3/4 Kelly
    }

    multiplier = risk_multipliers.get(risk_level, 0.5)
    recommended_fraction = full_kelly * multiplier

    # 最大单场风险限制（防止极端情况）
    max_single_bet = max_drawdown * 0.6  # 单场最多用总回撤额的60%
    recommended_fraction = min(recommended_fraction, max_single_bet)

    stake = current_bankroll * recommended_fraction
    stake = max(0, min(stake, current_bankroll * 0.2))  # 单场最多不超过本金20%

    # 风险等级判断
    if recommended_fraction < 0.02:
        risk = "低风险"
    elif recommended_fraction < 0.05:
        risk = "中等风险"
    elif recommended_fraction < 0.08:
        risk = "较高风险"
    else:
        risk = "高风险"

    return {
        "probability": round(probability, 4),
        "odds": odds,
        "full_kelly": round(full_kelly, 4),
        "recommended_fraction": round(recommended_fraction, 4),
        "stake": round(stake, 2),
        "risk_level": risk_level,
        "risk_description": risk,
        "bankroll_after_bet": round(current_bankroll - stake, 2),
        "notes": f"使用 {multiplier*100:.0f}% Kelly，单场风险控制在 {recommended_fraction*100:.1f}% 以内"
    }


def portfolio_kelly(bets: list, total_bankroll: float, risk_level: str = "standard") -> Dict[str, Any]:
    """
    多场比赛组合 Kelly（简单版本）
    bets: [{"probability": 0.58, "odds": 2.10, "edge": 0.05}, ...]
    """
    results = []
    total_stake = 0

    for bet in bets:
        suggestion = get_kelly_suggestion(
            probability=bet["probability"],
            odds=bet["odds"],
            risk_level=risk_level,
            current_bankroll=total_bankroll
        )
        results.append({
            "selection": bet.get("selection", "未知"),
            "stake": suggestion["stake"],
            "fraction": suggestion["recommended_fraction"]
        })
        total_stake += suggestion["stake"]

    # 如果总投注超过本金，进行等比例缩减
    if total_stake > total_bankroll * 0.25:
        scale = (total_bankroll * 0.25) / total_stake
        for r in results:
            r["stake"] *= scale
            r["fraction"] *= scale
        total_stake = total_bankroll * 0.25

    return {
        "bets": results,
        "total_stake": round(total_stake, 2),
        "total_fraction": round(total_stake / total_bankroll, 4),
        "remaining_bankroll": round(total_bankroll - total_stake, 2)
    }


if __name__ == "__main__":
    # 测试
    result = get_kelly_suggestion(
        probability=0.58,
        odds=2.10,
        risk_level="standard",
        current_bankroll=10000
    )
    print(result)
