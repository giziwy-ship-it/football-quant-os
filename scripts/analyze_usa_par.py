#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""美国 vs 巴拉圭 | 六维度预测报告 v5.2"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("           娜迦足球量化决策系统 v5.2 - 六维度预测报告")
print("              美国 vs 巴拉圭 | 2026世界杯 Group A")
print("              2026-06-13 09:00 | 洛杉矶 SoFi Stadium")
print("=" * 80)
print()

# 综合数据
match_data = {
    "home": "美国", "away": "巴拉圭",
    "date": "2026-06-13 09:00", "venue": "洛杉矶 SoFi Stadium (美国主场)",
    "oddsportal": {
        "avg_home": 2.07, "avg_draw": 3.30, "avg_away": 3.87,
        "best_home": 2.15, "best_draw": 3.42, "best_away": 4.00,
        "best_bookmaker": "Mozzartbet/Megapari",
        "payout_avg": 96.5,
    },
    "betfair": {"back_home": 2.12, "back_draw": 3.40, "back_away": 4.10, "payout": 99.0},
    "user_pred": {"home": 90, "draw": 9, "away": 1},
    "ai": "USA to win - narrow 1-0 or 2-0 victory, home crowd and Europe-based stars",
    "500_odds": {"home": 2.05, "draw": 3.30, "away": 3.90},
}

# 隐含概率
odds = match_data["oddsportal"]
margin = 1/odds["avg_home"] + 1/odds["avg_draw"] + 1/odds["avg_away"]
prob_h = (1/odds["avg_home"]) / margin * 100
prob_d = (1/odds["avg_draw"]) / margin * 100
prob_a = (1/odds["avg_away"]) / margin * 100

up = match_data["user_pred"]

# 综合概率 (隐含35% + 用户25% + 主场20% + 状态15% + AI 5%)
adj_h = prob_h * 0.35 + up["home"] * 0.25 + 50 * 0.20 + 45 * 0.15 + 55 * 0.05
adj_d = prob_d * 0.35 + up["draw"] * 0.25 + 30 * 0.20 + 30 * 0.15 + 25 * 0.05
adj_a = prob_a * 0.35 + up["away"] * 0.25 + 20 * 0.20 + 25 * 0.15 + 20 * 0.05

total = adj_h + adj_d + adj_a
adj_h = adj_h / total * 100
adj_d = adj_d / total * 100
adj_a = adj_a / total * 100

print("【综合概率】")
print(f"  OddsPortal隐含: 主胜{prob_h:.1f}% | 平局{prob_d:.1f}% | 客胜{prob_a:.1f}%")
print(f"  用户预测:      主胜{up['home']}% | 平局{up['draw']}% | 客胜{up['away']}%")
print(f"  ★ 综合概率:    主胜{adj_h:.1f}% | 平局{adj_d:.1f}% | 客胜{adj_a:.1f}%")
print(f"    (隐含35% + 用户25% + 主场20% + 状态15% + AI 5%)")
print()

# 六维度预测
print("=" * 80)
print("                     六维度预测结果")
print("=" * 80)
print()

print("【维度1】胜平负 (1X2)")
print("-" * 80)
print(f"  推荐: 主胜 (美国胜) @OddsPortal平均2.07")
print(f"  信心: ★★★★☆")
print(f"  理由: 用户90%看好美国，SoFi Stadium主场，Pulisic/Reyna/Balogun欧洲球星")
print(f"  最佳赔率: Mozzartbet/Megapari 2.15 (返还率97.6-98.5%)")
print(f"  备选: 巴拉圭胜@4.00 (冷门价值，历史交锋美国曾0-1负)")
print()

print("【维度2】让球胜平负 (Asian Handicap)")
print("-" * 80)
print(f"  盘口: 美国-0.5 / 美国-0.75")
print(f"  推荐: 美国让胜 (-0.5) @1.75-1.80")
print(f"  信心: ★★★★☆")
print(f"  理由: 主场揭幕战，美国实力+深度优势，巴拉圭可能低位防守")
print()

print("【维度3】半全场 (HT/FT)")
print("-" * 80)
htft = {"主/主": 40, "平/主": 30, "平/平": 15, "主/平": 8, "平/客": 4, "客/客": 2, "客/主": 1}
for k, v in sorted(htft.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k}: {v:>3}% {'█' * int(v/2)}")
print(f"  ★ 推荐: 主/主 (40%) 或 平/主 (30%)")
print(f"  理由: 美国上半场可能进球，巴拉圭防守反击上半场谨慎")
print()

print("【维度4】比分 (Correct Score)")
print("-" * 80)
scores = {"1-0": 25, "2-0": 20, "1-1": 12, "2-1": 10, "0-0": 8, "0-1": 6, "1-2": 5, "2-2": 4, "0-2": 3, "其他": 7}
for i, (s, p) in enumerate(sorted(scores.items(), key=lambda x: x[1], reverse=True), 1):
    print(f"  {i}. {s}: {p:>3}% {'█' * int(p/2)}")
print(f"  ★ 推荐: 1-0, 2-0, 1-1")
print(f"  理由: OddsPortal AI预测'narrow 1-0 or 2-0'，历史近两次交锋美国1-0胜")
print()

print("【维度5】总进球数 (Total Goals)")
print("-" * 80)
goals = {"0球": 6, "1球": 22, "2球": 32, "3球": 22, "4球": 12, "5球+": 6}
for g, p in goals.items():
    print(f"  {g}: {p:>3}% {'█' * int(p/2)}")
over = goals["3球"] + goals["4球"] + goals["5球+"]
under = goals["0球"] + goals["1球"] + goals["2球"]
print(f"  大2.5: {over}% | 小2.5: {under}%")
print(f"  ★ 推荐: 2球最可能 | 小2.5球 @1.58")
print()

print("【维度6】大小球 (Over/Under)")
print("-" * 80)
print(f"  OddsPortal AI: 'World Cup openers between evenly matched sides are often cagey'")
print(f"  盘口: 2.5球 | 小2.5 @1.58 (GGBET最高) | 大2.5 @2.30+")
print(f"  ★ 推荐: 小2.5球 @1.58 | 信心: ★★★★☆")
print(f"  ★ 推荐: 双方进球-否 @1.78 | 信心: ★★★★☆")
print(f"  理由: AI预测巴拉圭低位防守，美国可能零封，1-0/2-0最可能")
print()

print("=" * 80)
print()

# Kelly注码
print("【Kelly注码建议】")
print("-" * 80)
print(f"  资金池: 10,000 EUR | 最大单注: 500 EUR (5%)")
print()

recommendations = [
    ("美国胜", adj_h/100, 2.07, "1X2"),
    ("小2.5球", 0.60, 1.58, "大小球"),
    ("双方进球-否", 0.65, 1.78, "BTTS"),
]

for i, (name, prob, odds, cat) in enumerate(recommendations, 1):
    b = odds - 1
    q = 1 - prob
    kelly = (b * prob - q) / b
    kelly_half = kelly / 2
    amount = min(10000 * kelly_half, 500)
    ev = (prob * odds - 1) * 100
    print(f"  {i}. {name} @ {odds}")
    print(f"     概率: {prob*100:.1f}% | Kelly: {kelly:.1%} | 半Kelly: {kelly_half:.1%}")
    print(f"     建议注码: {amount:,.0f} EUR | 期望值: {ev:+.1f}%")
    print()

print("=" * 80)
print("  ⚠️ 仅供研究学习，不构成投注建议")
print("  📊 数据源: OddsPortal + 500.com + Betfair Exchange")
print("  ⏱  数据抓取: 2026-06-12 19:05")
print("=" * 80)
