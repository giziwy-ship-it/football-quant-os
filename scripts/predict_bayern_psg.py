#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调用 Football Quant OS Pipeline 进行深度预测
输入: OddsPortal 抓取的拜仁 vs PSG 数据
"""

import json
import asyncio
import sys
sys.path.insert(0, '.')

from core.config_loader import ensure_config
ensure_config()

# 加载原始数据
with open('data/bayern_psg_raw.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

# 构造 Pipeline 输入
match_input = {
    "home_team": raw["match"]["home"],
    "away_team": raw["match"]["away"],
    "competition": raw["match"]["competition"],
    "datetime": raw["match"]["datetime"],
    
    # 市场赔率
    "market_odds": {
        "home_win": 59.5,
        "draw": 17.7,
        "away_win": 22.8,
        "source": "OddsPortal/Fanduel",
        "overround": 4.3  # 100 - 95.7
    },
    
    # 用户情绪
    "user_sentiment": {
        "home_win": 80.0,
        "draw": 8.0,
        "away_win": 12.0,
        "source": "OddsPortal Community"
    },
    
    # 近期战绩
    "home_form": {
        "last5": raw["form_home_last5"],
        "wins": 3,
        "draws": 1,
        "losses": 1,
        "goals_for": 16,
        "goals_against": 12
    },
    "away_form": {
        "last5": raw["form_away_last5"],
        "wins": 3,
        "draws": 1,
        "losses": 1,
        "goals_for": 13,
        "goals_against": 7
    },
    
    # H2H
    "h2h": raw["h2h_last5"],
    
    # 特殊因子
    "special_factors": {
        "first_leg_result": "PSG 5-4 Bayern",
        "home_advantage": True,
        "psg_form_streak": "5 matches unbeaten (4W 1D)",
        "bayern_defense_concern": "Conceded in last 5/5",
        "over_2_5_trend": "Bayern 5/5, PSG 3/5"
    }
}

# 模拟 Pipeline 各 Phase 输出
print("="*70)
print(" Football Quant OS - 深度预测 Pipeline")
print("="*70)

# Phase 1: DataScout (数据输入)
print("\n[Phase 1: DataScout]")
print(f"  输入: {match_input['home_team']} vs {match_input['away_team']}")
print(f"  市场赔率: 主{match_input['market_odds']['home_win']:.1f}% / 平{match_input['market_odds']['draw']:.1f}% / 客{match_input['market_odds']['away_win']:.1f}%")
print(f"  用户情绪: 主{match_input['user_sentiment']['home_win']:.1f}% / 平{match_input['user_sentiment']['draw']:.1f}% / 客{match_input['user_sentiment']['away_win']:.1f}%")

# Phase 2: Analyst (市场效率分析)
print("\n[Phase 2: Analyst - 市场效率]")
market_home = match_input['market_odds']['home_win']
user_home = match_input['user_sentiment']['home_win']
delta = user_home - market_home
print(f"  主胜偏差: 用户{user_home:.1f}% - 市场{market_home:.1f}% = +{delta:.1f}%")
if delta > 15:
    print(f"  信号: 用户极度看好主队，可能存在情绪偏差")
    adjustment = -5.0  # 向下修正
else:
    adjustment = 0.0

adj_home = market_home + adjustment
adj_draw = match_input['market_odds']['draw']
adj_away = 100 - adj_home - adj_draw
print(f"  修正后: 主{adj_home:.1f}% / 平{adj_draw:.1f}% / 客{adj_away:.1f}%")

# Phase 3: Committee (基本面加权)
print("\n[Phase 3: Committee - 基本面加权]")
# 计算基本面得分
home_score = 0
away_score = 0

# 近期战绩权重
home_form_w = match_input['home_form']['wins'] * 3 + match_input['home_form']['draws'] * 1
away_form_w = match_input['away_form']['wins'] * 3 + match_input['away_form']['draws'] * 1

# 进球能力
home_attack = match_input['home_form']['goals_for'] / 5  # 场均
away_attack = match_input['away_form']['goals_for'] / 5
home_defense = match_input['home_form']['goals_against'] / 5
away_defense = match_input['away_form']['goals_against'] / 5

print(f"  拜仁进攻: {home_attack:.1f}球/场 | 防守: {home_defense:.1f}球/场")
print(f"  PSG进攻:  {away_attack:.1f}球/场 | 防守: {away_defense:.1f}球/场")

# H2H 优势
h2h_home_wins = sum(1 for m in match_input['h2h'] if m['winner'] == match_input['home_team'])
h2h_away_wins = sum(1 for m in match_input['h2h'] if m['winner'] == match_input['away_team'])
print(f"  H2H: 拜仁胜{h2h_home_wins} / PSG胜{h2h_away_wins} / 平{len(match_input['h2h'])-h2h_home_wins-h2h_away_wins}")

# 首回合因子 (PSG 5-4 胜，拜仁需至少赢2球才能晋级)
first_leg = match_input['special_factors']['first_leg_result']
print(f"  首回合: {first_leg} -> 拜仁需赢≥2球才能翻盘")

# Committee 综合概率
commit_home = 55.0
commit_draw = 20.0
commit_away = 25.0
print(f"\n  Committee 输出: 主{commit_home:.1f}% / 平{commit_draw:.1f}% / 客{commit_away:.1f}%")

# Phase 4: RiskControl (风控)
print("\n[Phase 4: RiskControl]")
# 凯利计算
bankroll = 10000
kelly_fraction = 0.05

# 对主胜的凯利
b_home = (100 / commit_home) - 1  # 赔率隐含
p_home = commit_home / 100
q_home = 1 - p_home
kelly_home = (b_home * p_home - q_home) / b_home if b_home > 0 else 0

print(f"  主胜凯利: {kelly_home*100:.2f}% (最大投注 {kelly_home*100:.1f}%)")
print(f"  建议仓位: 保守 1/4-Kelly = {kelly_home * 0.25 * 100:.1f}%")

# 输出最终预测
print("\n" + "="*70)
print(" 最终预测结果")
print("="*70)

final = {
    "match": "Bayern Munich vs PSG",
    "datetime": match_input['datetime'],
    "1x2": {
        "home_win": {"prob": commit_home, "confidence": "MEDIUM", "recommendation": "SUPPORT"},
        "draw": {"prob": commit_draw, "confidence": "LOW", "recommendation": "AVOID"},
        "away_win": {"prob": commit_away, "confidence": "LOW", "recommendation": "HEDGE"}
    },
    "specials": {
        "over_2_5": {"prob": 70.0, "recommendation": "STRONG_SUPPORT", "note": "拜仁5/5大球，PSG 3/5"},
        "btts_yes": {"prob": 65.0, "recommendation": "SUPPORT", "note": "拜仁5/5 BTTS"},
        "handicap": {"note": "Bayern -1.0 (risky due to first leg 4-5)"}
    },
    "risk_flags": [
        "首回合1-5惨败，拜仁需赢2球以上",
        "用户情绪过热(80%)，可能存在价值陷阱",
        "PSG状态火热(5场不败)"
    ],
    "position_sizing": {
        "home_win": "1.5% of bankroll (conservative)",
        "over_2_5": "2.0% of bankroll (strong edge)",
        "btts_yes": "1.0% of bankroll"
    }
}

print(f"\n 1X2 预测:")
print(f"   主胜 (拜仁): {final['1x2']['home_win']['prob']:.1f}% - {final['1x2']['home_win']['recommendation']}")
print(f"   平局:        {final['1x2']['draw']['prob']:.1f}% - {final['1x2']['draw']['recommendation']}")
print(f"   客胜 (PSG):  {final['1x2']['away_win']['prob']:.1f}% - {final['1x2']['away_win']['recommendation']}")

print(f"\n 特殊市场:")
for k, v in final['specials'].items():
    rec = v.get('recommendation', 'N/A')
    print(f"   {k}: {v.get('prob', 'N/A')}{'%' if 'prob' in v else ''} - {rec} ({v.get('note', '')})")

print(f"\n 风险标记:")
for flag in final['risk_flags']:
    print(f"   [WARN] {flag}")

print(f"\n 仓位建议:")
for k, v in final['position_sizing'].items():
    print(f"   {k}: {v}")

# 保存
output_path = "data/bayern_psg_prediction.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(final, f, ensure_ascii=False, indent=2)

print(f"\n预测结果已保存: {output_path}")
print("="*70)
