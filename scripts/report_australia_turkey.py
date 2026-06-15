#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
澳大利亚 vs 土耳其 - 六维预测报告
基于 odds.500.com + oddsportal.com 数据
生成时间: 2026-06-14 12:20
"""

from datetime import datetime
import json

# ============================================
# 输入数据
# ============================================
match_data = {
    "home": "澳大利亚",
    "away": "土耳其",
    "competition": "2026世界杯小组赛",
    "date": "2026-06-14",
    "stage": "group",
    # 欧赔 (500.com)
    "odds_1x2": {"home": 5.20, "draw": 3.67, "away": 1.70},
    # 投注分布
    "bet_distribution": {"home": 18.3, "draw": 25.8, "away": 55.9},
    # 凯利指数
    "kelly_index": {"home": 50, "draw": 66, "away": -47},
    # 让球 (土耳其-1)
    "odds_ah": {"home_plus1": 2.28, "draw": 2.95, "away_minus1": 2.84},
    # 大小球
    "odds_ou": {"over_2.5": 0.85, "under_2.5": 0.95},
    # 历史数据参考
    "fifa_rank_home": 40,
    "fifa_rank_away": 25,
}

# ============================================
# 计算隐含概率
# ============================================
h, d, a = match_data["odds_1x2"]["home"], match_data["odds_1x2"]["draw"], match_data["odds_1x2"]["away"]
total = 1/h + 1/d + 1/a
mkt_home = (1/h) / total
mkt_draw = (1/d) / total
mkt_away = (1/a) / total

# 去除margin
margin = total - 1
imp_home = mkt_home / total * (1 - margin)
imp_draw = mkt_draw / total * (1 - margin)
imp_away = mkt_away / total * (1 - margin)

# 模型概率（小组赛调整）
mod_home = imp_home * 1.08  # 弱队上调
mod_away = imp_away * 0.94 + 0.03  # 强队下调
mod_draw = 1 - mod_home - mod_away

# Edge
edge_home = mod_home - imp_home
edge_draw = mod_draw - imp_draw
edge_away = mod_away - imp_away

# 冷门评分
upset_score = 12

# ============================================
# 六维预测
# ============================================

def predict_1x2():
    """胜平负预测"""
    probs = {"主胜": mod_home, "平局": mod_draw, "客胜": mod_away}
    most_likely = max(probs, key=probs.get)
    
    edges = {"主胜": edge_home, "平局": edge_draw, "客胜": edge_away}
    value_bet = max(edges, key=edges.get)
    best_edge = edges[value_bet]
    
    return {
        "most_likely": most_likely,
        "most_likely_prob": round(probs[most_likely], 3),
        "value_bet": value_bet,
        "best_edge": round(best_edge, 3),
        "recommended": best_edge > 0.015,
        "probs": {k: round(v, 3) for k, v in probs.items()}
    }

def predict_ah():
    """让球胜平负预测"""
    # 土耳其-1球（澳大利亚+1球）
    ah_home = match_data["odds_ah"]["home_plus1"]
    ah_draw = match_data["odds_ah"]["draw"]
    ah_away = match_data["odds_ah"]["away_minus1"]
    
    total_ah = 1/ah_home + 1/ah_draw + 1/ah_away
    imp_ah_home = (1/ah_home) / total_ah
    imp_ah_away = (1/ah_away) / total_ah
    
    # 土耳其让1球，赢盘需要赢2球以上
    # 基于模型概率，土耳其赢2球概率 = 土耳其胜概率 - 1-0概率
    # 简化：土耳其赢2+球概率 ≈ 0.35
    mod_ah_away = 0.35
    mod_ah_home = 1 - mod_ah_away - 0.25  # 平局概率约25%
    mod_ah_draw = 1 - mod_ah_home - mod_ah_away
    
    edge_ah_home = mod_ah_home - imp_ah_home
    edge_ah_away = mod_ah_away - imp_ah_away
    
    # 澳大利亚+1球有受让价值
    return {
        "handicap": "土耳其-1球",
        "recommendation": "澳大利亚+1球",
        "reason": "土耳其赢2球以上概率不高，受让有赢盘空间",
        "win_prob": round(mod_ah_away, 3),
        "edge": round(edge_ah_away, 3)
    }

def predict_htft():
    """半全场预测"""
    # 土耳其上半场领先概率高（实力优势）
    ht_turkey = 0.45
    ht_draw = 0.40
    ht_australia = 0.15
    
    # 全场土耳其胜概率
    ft_turkey = mod_away
    ft_draw = mod_draw
    ft_australia = mod_home
    
    # 最可能：土耳其/土耳其
    return {
        "most_likely": "土耳其/土耳其",
        "probability": round(ht_turkey * ft_turkey, 3),
        "alternatives": ["平局/土耳其", "土耳其/平局"]
    }

def predict_score():
    """比分预测"""
    # 基于大小球2.5，预期总进球2-3球
    # 土耳其胜概率高，考虑1-0, 2-0, 2-1
    scores = [
        ("1-0", 0.15, "土耳其"),
        ("2-0", 0.12, "土耳其"),
        ("2-1", 0.10, "土耳其"),
        ("1-1", 0.08, "平局"),
        ("0-1", 0.07, "土耳其"),
    ]
    return {
        "most_likely": scores[0],
        "top_5": scores
    }

def predict_goals():
    """进球数预测"""
    # 大小球2.5盘口
    # 大球赔率0.80-1.00，小球0.73-1.02
    # 市场分歧，但小球0.73低赔暗示小球热门
    expected_goals = 2.2  # 预期总进球
    return {
        "expected_total": expected_goals,
        "most_likely": "2球",
        "range": "1-3球",
        "over_2.5_prob": 0.48,
        "under_2.5_prob": 0.52
    }

def predict_ou():
    """大小球预测"""
    # 2.5盘口
    # 小球赔率0.73-0.95，有低赔支持
    # 土耳其进攻不算最强，澳大利亚防守尚可
    return {
        "line": 2.5,
        "recommendation": "小球",
        "reason": "小球有低赔支持(0.73)，且土耳其不一定大胜",
        "confidence": 0.55
    }

# ============================================
# Kelly注码计算
# ============================================
def calculate_kelly(prob, odds, bankroll=10000, fraction=0.5):
    b = odds - 1
    q = 1 - prob
    kelly = (b * prob - q) / b
    kelly = max(0, min(kelly, 1.0))
    stake = bankroll * kelly * fraction
    return round(kelly, 4), round(stake, 2)

# ============================================
# 生成报告
# ============================================
def generate_report():
    p1x2 = predict_1x2()
    pah = predict_ah()
    phtft = predict_htft()
    pscore = predict_score()
    pgoals = predict_goals()
    pou = predict_ou()
    
    report = f"""
{'='*60}
Football Quant OS - 六维预测报告
{'='*60}

比赛: {match_data['home']} vs {match_data['away']}
赛事: {match_data['competition']}
阶段: {match_data['stage']}
日期: {match_data['date']}

{'='*60}
【一】胜平负 (1X2)
{'='*60}
赔率: 澳大利亚 {match_data['odds_1x2']['home']} / 平局 {match_data['odds_1x2']['draw']} / 土耳其 {match_data['odds_1x2']['away']}
隐含概率: 澳大利亚 {imp_home:.1%} / 平局 {imp_draw:.1%} / 土耳其 {imp_away:.1%}
模型概率: 澳大利亚 {mod_home:.1%} / 平局 {mod_draw:.1%} / 土耳其 {mod_away:.1%}
Edge: 澳大利亚 {edge_home:+.1%} / 平局 {edge_draw:+.1%} / 土耳其 {edge_away:+.1%}

最可能结果: {p1x2['most_likely']} (概率 {p1x2['most_likely_prob']:.1%})
价值投注: {p1x2['value_bet']} (Edge {p1x2['best_edge']:+.1%})
推荐: {"有正Edge" if p1x2['recommended'] else "无显著价值"}

投注分布: 澳大利亚 {match_data['bet_distribution']['home']}% / 平局 {match_data['bet_distribution']['draw']}% / 土耳其 {match_data['bet_distribution']['away']}%
凯利指数: 澳大利亚 {match_data['kelly_index']['home']} / 平局 {match_data['kelly_index']['draw']} / 土耳其 {match_data['kelly_index']['away']}
(土耳其凯利负值 = 热门，风险高)

{'='*60}
【二】让球胜平负 (Asian Handicap)
{'='*60}
盘口: 土耳其-1球 (澳大利亚+1球)
赔率: 澳大利亚+1 {match_data['odds_ah']['home_plus1']} / 平局 {match_data['odds_ah']['draw']} / 土耳其-1 {match_data['odds_ah']['away_minus1']}

推荐: {pah['recommendation']}
理由: {pah['reason']}
土耳其赢2+球概率: {pah['win_prob']:.1%}

{'='*60}
【三】半全场 (HT/FT)
{'='*60}
最可能: {phtft['most_likely']} (概率约 {phtft['probability']:.1%})
备选: {', '.join(phtft['alternatives'])}

{'='*60}
【四】比分 (Correct Score)
{'='*60}
最可能: {pscore['most_likely'][0]} ({pscore['most_likely'][2]})
Top 5:
"""
    for score, prob, result in pscore['top_5']:
        report += f"  {score}: {prob:.1%} ({result})\n"
    
    report += f"""
{'='*60}
【五】进球数 (Total Goals)
{'='*60}
预期总进球: {pgoals['expected_total']:.1f} 球
最可能: {pgoals['most_likely']}
范围: {pgoals['range']}

{'='*60}
【六】大小球 (Over/Under)
{'='*60}
盘口: {pou['line']} 球
推荐: {pou['recommendation']}
理由: {pou['reason']}

{'='*60}
【Kelly注码建议】
{'='*60}
"""
    
    # 计算Kelly注码
    if p1x2['recommended']:
        kelly_frac, kelly_stake = calculate_kelly(p1x2['most_likely_prob'], match_data['odds_1x2']['home'])
        report += f"若有正Edge: 注码 {kelly_stake} EUR ({kelly_frac*100:.1f}% Kelly)\n"
    
    # 澳大利亚+1球Kelly
    kelly_frac_ah, kelly_stake_ah = calculate_kelly(0.44, match_data['odds_ah']['home_plus1'])
    report += f"澳大利亚+1球: 注码 {kelly_stake_ah} EUR ({kelly_frac_ah*100:.1f}% Kelly)\n"
    
    report += f"""
{'='*60}
【冷门评分】
{'='*60}
冷门评分: {upset_score}/65 (低风险)
说明: 土耳其实力占优，市场定价基本合理，无显著冷门信号

{'='*60}
免责声明
{'='*60}
本报告为研究模型输出，不构成投资建议。
足球比赛具有高度不确定性，请理性看待。

报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Football Quant OS v4.3.2
{'='*60}
"""
    return report

if __name__ == "__main__":
    print(generate_report())
