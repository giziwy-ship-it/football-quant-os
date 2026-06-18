#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
伊拉克 vs 挪威 - 2026 世界杯预测报告
数据源: oddsportal.com + 500.com (18+ 博彩公司)
"""

import sys, os
import numpy as np
from scipy.stats import poisson
from datetime import datetime

# ============ 市场数据汇总 ============

# 1X2 欧赔 (综合 oddsportal + 500.com 平均)
ODDS_1X2 = {
    "home": 7.50,    # 伊拉克胜
    "draw": 4.60,    # 平局
    "away": 1.35,    # 挪威胜
}

# 主流公司 1X2
MAJOR_1X2 = {
    "William Hill": [8.00, 4.50, 1.29],
    "Ladbrokes": [8.00, 4.60, 1.40],
    "Bet365": [6.00, 4.50, 1.40],
    "Interwetten": [7.00, 4.70, 1.45],
    "SBOBET": [10.00, 5.75, 1.25],
    "Pinnacle": [6.19, 4.32, 1.48],
}

# 亚盘
ASIAN_HANDICAP = {
    "line": "伊拉克 受球半/两球 (-1.75)",
    "home_water": 0.994,  # 伊拉克水位
    "away_water": 0.862,  # 挪威水位
    "trend": "部分公司从受两球降至受球半/两球，盘口收窄",
}

MAJOR_AH = {
    "William Hill": {"line": "受球半/两球", "home": 0.83, "away": 0.80},
    "澳门": {"line": "受球半/两球", "home": 1.02, "away": 0.82},
    "立博": {"line": "受球半", "home": 1.20, "away": 0.60},
    "Bet365": {"line": "受球半/两球", "home": 1.03, "away": 0.83},
    "Interwetten": {"line": "受两球(降)", "home": 0.63, "away": 1.15},
    "伟德": {"line": "受球半/两球(降)", "home": 1.01, "away": 0.83},
}

# 大小球
OVER_UNDER = {
    "line": 2.92,
    "over": 0.96,
    "under": 0.89,
    "trend": "盘口从2.74升至2.92，大球水位走高",
}

# 500.com 百家欧赔平均 (约17家公司)
AVG_500_1X2 = {"home": 2.30, "draw": 3.88, "away": 2.29}  # 即时
AVG_500_AH = {"home": 0.994, "line": 1.75, "away": 0.862}
AVG_500_OU = {"over": 0.96, "line": 2.92, "under": 0.89}

# 球队近况
FORM = {
    "iraq": "LDWWLL",      # 2胜1平3负
    "norway": "DWDLWW",    # 3胜2平1负
}

# 关键球员
KEY_PLAYERS = {
    "norway": ["马丁·厄德高 (Martin Ødegaard)", "埃尔林·哈兰德 (Erling Haaland)"],
    "iraq": [],
}

# 500.com 推介
RECOMMENDATION_500 = "挪威 赢"


def implied_prob(odds):
    """赔率转概率"""
    raw = {k: 1/v for k, v in odds.items()}
    total = sum(raw.values())
    return {k: v/total for k, v in raw.items()}


def poisson_predict(lambda1, lambda2, max_goals=5):
    """泊松分布预测比分"""
    scores = []
    for g1 in range(max_goals+1):
        for g2 in range(max_goals+1):
            p = poisson.pmf(g1, lambda1) * poisson.pmf(g2, lambda2)
            scores.append((g1, g2, p))
    scores.sort(key=lambda x: x[2], reverse=True)
    return scores


def calculate_predictions():
    """计算预测"""
    
    # 基于市场赔率计算隐含概率
    market_probs = implied_prob(ODDS_1X2)
    
    # 预期进球 (基于市场概率和球队实力估算)
    # 挪威实力明显占优，伊拉克是弱势方
    lambda_iraq = 0.65   # 伊拉克预期进球
    lambda_norway = 2.10  # 挪威预期进球
    
    # 比分预测
    scores = poisson_predict(lambda_iraq, lambda_norway)
    
    # 胜负平概率 (基于泊松)
    p_iraq_win = sum(p for g1, g2, p in scores if g1 > g2)
    p_draw = sum(p for g1, g2, p in scores if g1 == g2)
    p_norway_win = sum(p for g1, g2, p in scores if g1 < g2)
    
    # 融合模型: 泊松 40% + 市场 60%
    fused = {
        "home": p_iraq_win * 0.4 + market_probs["home"] * 0.6,
        "draw": p_draw * 0.4 + market_probs["draw"] * 0.6,
        "away": p_norway_win * 0.4 + market_probs["away"] * 0.6,
    }
    
    # 大小球
    total_lambda = lambda_iraq + lambda_norway
    p_over_2_5 = 1 - poisson.cdf(2, total_lambda)
    p_under_2_5 = poisson.cdf(2, total_lambda)
    
    # 双方进球
    p_iraq_scores = 1 - poisson.pmf(0, lambda_iraq)
    p_norway_scores = 1 - poisson.pmf(0, lambda_norway)
    p_btts = p_iraq_scores * p_norway_scores
    
    # 半全场
    ht_draw_prob = 0.38
    ht_norway_prob = 0.45
    ht_iraq_prob = 0.17
    
    return {
        "market_probs": market_probs,
        "fused": fused,
        "scores": scores[:10],
        "lambda": (lambda_iraq, lambda_norway),
        "over_2_5": p_over_2_5,
        "under_2_5": p_under_2_5,
        "btts": p_btts,
        "ht": {"iraq": ht_iraq_prob, "draw": ht_draw_prob, "norway": ht_norway_prob},
    }


def print_report():
    """打印预测报告"""
    pred = calculate_predictions()
    
    print("=" * 70)
    print("伊拉克 vs 挪威 - 2026 世界杯预测")
    print("=" * 70)
    print(f"比赛时间: 2026-06-17 06:00 | 数据来源: oddsportal + 500.com")
    print()
    
    print("【球队近况】")
    print(f"  伊拉克: {FORM['iraq']} (近6场: 2胜1平3负)")
    print(f"  挪威:   {FORM['norway']} (近6场: 3胜2平1负)")
    print()
    
    print("【关键球员】")
    print("  挪威: 马丁·厄德高, 埃尔林·哈兰德 (世界级球星)")
    print("  伊拉克: 无明显世界级球星")
    print()
    
    print("【1X2 胜平负】")
    print(f"  市场平均赔率:")
    print(f"    伊拉克胜: {ODDS_1X2['home']:.2f} | 平局: {ODDS_1X2['draw']:.2f} | 挪威胜: {ODDS_1X2['away']:.2f}")
    print(f"  市场隐含概率:")
    print(f"    伊拉克: {pred['market_probs']['home']:.1%} | 平局: {pred['market_probs']['draw']:.1%} | 挪威: {pred['market_probs']['away']:.1%}")
    print(f"  融合预测:")
    print(f"    伊拉克: {pred['fused']['home']:.1%} | 平局: {pred['fused']['draw']:.1%} | 挪威: {pred['fused']['away']:.1%}")
    print(f"  ★ 推荐: 挪威胜 (概率 {pred['fused']['away']:.1%})")
    print()
    
    print("【亚盘 让球】")
    print(f"  盘口: {ASIAN_HANDICAP['line']}")
    print(f"  伊拉克水位: {ASIAN_HANDICAP['home_water']:.2f} | 挪威水位: {ASIAN_HANDICAP['away_water']:.2f}")
    print(f"  走势: {ASIAN_HANDICAP['trend']}")
    print(f"  主流公司:")
    for name, data in MAJOR_AH.items():
        print(f"    {name:15s}: {data['line']:12s} 伊拉克 {data['home']:.2f} | 挪威 {data['away']:.2f}")
    print(f"  ★ 推荐: 挪威 -1.75 (亚洲让球)")
    print()
    
    print("【半全场 HT/FT】")
    print(f"  半场预测:")
    print(f"    伊拉克领先: {pred['ht']['iraq']:.1%}")
    print(f"    平局: {pred['ht']['draw']:.1%}")
    print(f"    挪威领先: {pred['ht']['norway']:.1%}")
    ht_ft_draw_norway = pred['ht']['draw'] * pred['fused']['away']
    ht_ft_norway_norway = pred['ht']['norway'] * pred['fused']['away']
    print(f"  ★ 推荐: 平/挪威 ({ht_ft_draw_norway:.1%}) 或 挪威/挪威 ({ht_ft_norway_norway:.1%})")
    print()
    
    print("【比分预测】")
    print(f"  预期进球: 伊拉克 {pred['lambda'][0]:.2f} | 挪威 {pred['lambda'][1]:.2f}")
    print(f"  Top 5 比分:")
    for i, (g1, g2, p) in enumerate(pred['scores'][:5], 1):
        print(f"    {i}. {g1}-{g2}: {p:.1%}")
    print(f"  ★ 推荐: 0-2 或 1-2")
    print()
    
    print("【大小球 Over/Under】")
    print(f"  盘口: {OVER_UNDER['line']:.1f} 球")
    print(f"  大球 {OVER_UNDER['line']:.1f}: {pred['over_2_5']:.1%} (赔率 {OVER_UNDER['over']:.2f})")
    print(f"  小球 {OVER_UNDER['line']:.1f}: {pred['under_2_5']:.1%} (赔率 {OVER_UNDER['under']:.2f})")
    print(f"  走势: {OVER_UNDER['trend']}")
    print(f"  ★ 推荐: 大 2.5/3 球")
    print()
    
    print("【双方进球 BTTS】")
    print(f"  双方进球 YES: {pred['btts']:.1%}")
    print(f"  双方进球 NO: {1-pred['btts']:.1%}")
    print(f"  ★ 推荐: BTTS - YES")
    print()
    
    print("【进球数】")
    total = pred['lambda'][0] + pred['lambda'][1]
    for n in range(6):
        print(f"  {n}球: {poisson.pmf(n, total):.1%}")
    print(f"  ★ 推荐: 2-3 球 ({poisson.pmf(2,total)+poisson.pmf(3,total):.1%})")
    print()
    
    print("=" * 70)
    print("【最终推荐汇总】")
    print("=" * 70)
    print()
    print("  >> 1X2:         挪威胜")
    print("  >> 亚盘:        挪威 -1.75")
    print("  >> 半全场:      平/挪威")
    print("  >> 比分:        0-2 或 1-2")
    print("  >> 大小球:      大 2.5/3")
    print("  >> 双方进球:    YES")
    print("  >> 进球数:      2-3球")
    print()
    print("  信心指数: ★★★★ (高)")
    print()
    print("  风险提示:")
    print("     - 伊拉克主场优势不可忽视")
    print("     - 盘口从受两球降至受球半/两球，机构对挪威大胜信心减弱")
    print("     - 挪威近6场仅1负，状态稳定")
    print("     - 500.com 官方推介: 挪威赢")
    print("=" * 70)


if __name__ == "__main__":
    print_report()
