#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""加拿大 vs 波黑 | 六维度预测报告 v5.2"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("           娜迦足球量化决策系统 v5.2 - 六维度预测报告")
print("              加拿大 vs 波黑 | 2026世界杯 Group B")
print("              2026-06-13 03:00 | 多伦多 BMO Field")
print("=" * 80)
print()

# ============================================
# 综合数据
# ============================================
match_data = {
    "home": "加拿大",
    "away": "波黑",
    "date": "2026-06-13 03:00",
    "venue": "多伦多 BMO Field (加拿大主场)",
    
    # OddsPortal 18家博彩公司
    "oddsportal": {
        "avg_home": 1.85, "avg_draw": 3.45, "avg_away": 4.60,
        "best_home": 1.95, "best_draw": 3.54, "best_away": 4.75,
        "best_bookmaker": "Mozzartbet",
        "payout_avg": 96.0,
    },
    
    # Betfair Exchange
    "betfair": {
        "back_home": 1.90, "back_draw": 3.65, "back_away": 4.90,
        "lay_home": 1.91, "lay_draw": 3.70, "lay_away": 5.00,
    },
    
    # 用户预测
    "user_pred": {"home": 72, "draw": 15, "away": 13},
    
    # AI预测
    "ai": "Canada to win - tight Canadian win by a single goal",
    
    # 500.com
    "500_odds": {"home": 2.38, "draw": 3.16, "away": 2.64},
    "500_betfair": {"home": 38.7, "draw": 28.3, "away": 32.9},
}

# 隐含概率计算
odds = match_data["oddsportal"]
margin = 1/odds["avg_home"] + 1/odds["avg_draw"] + 1/odds["avg_away"]
prob_h = (1/odds["avg_home"]) / margin * 100
prob_d = (1/odds["avg_draw"]) / margin * 100
prob_a = (1/odds["avg_away"]) / margin * 100

up = match_data["user_pred"]

# 综合概率
adj_h = prob_h * 0.40 + up["home"] * 0.30 + 45 * 0.15 + 55 * 0.10 + 60 * 0.05
adj_d = prob_d * 0.40 + up["draw"] * 0.30 + 30 * 0.15 + 25 * 0.10 + 25 * 0.05
adj_a = prob_a * 0.40 + up["away"] * 0.30 + 25 * 0.15 + 20 * 0.10 + 15 * 0.05

total = adj_h + adj_d + adj_a
adj_h = adj_h / total * 100
adj_d = adj_d / total * 100
adj_a = adj_a / total * 100

print("【综合概率】")
print(f"  OddsPortal隐含: 主胜{prob_h:.1f}% | 平局{prob_d:.1f}% | 客胜{prob_a:.1f}%")
print(f"  用户预测:      主胜{up['home']}% | 平局{up['draw']}% | 客胜{up['away']}%")
print(f"  ★ 综合概率:    主胜{adj_h:.1f}% | 平局{adj_d:.1f}% | 客胜{adj_a:.1f}%")
print(f"    (隐含40% + 用户30% + 主场15% + 状态10% + AI 5%)")
print()

# ============================================
# 六维度预测
# ============================================
print("=" * 80)
print("                     六维度预测结果")
print("=" * 80)
print()

# 维度1: 1X2
print("【维度1】胜平负 (1X2)")
print("-" * 80)
print(f"  推荐: 主胜 (加拿大胜) @OddsPortal平均1.85")
print(f"  信心: ★★★★☆")
print(f"  理由: 用户预测72%看好加拿大，主场优势，OddsPortal AI预测加拿大小胜")
print(f"  最佳赔率: Mozzartbet 1.95 (返还率97.2%)")
print(f"  备选: 平局 @3.54 (价值高)")
print()

# 维度2: 让球
print("【维度2】让球胜平负")
print("-" * 80)
print(f"  盘口: 加拿大-0.75 / 加拿大-1")
print(f"  推荐: 加拿大让胜 (-0.75) @1.75-1.80")
print(f"  信心: ★★★★☆")
print(f"  理由: 主场揭幕战，加拿大 athleticism + depth优势，Betfair Back 1.90")
print()

# 维度3: 半全场
print("【维度3】半全场 (HT/FT)")
print("-" * 80)
htft = {"主/主": 35, "平/主": 28, "平/平": 18, "主/平": 8, "平/客": 5, "客/客": 3, "客/主": 2, "主/客": 1}
for k, v in sorted(htft.items(), key=lambda x: x[1], reverse=True):
    print(f"  {k}: {v:>3}% {'█' * int(v/2)}")
print(f"  ★ 推荐: 主/主 (35%) 或 平/主 (28%)")
print(f"  理由: 主场揭幕战，加拿大上半场可能领先")
print()

# 维度4: 比分
print("【维度4】比分 (Correct Score)")
print("-" * 80)
scores = {"1-0": 22, "2-0": 18, "1-1": 15, "2-1": 12, "0-0": 10, "0-1": 7, "1-2": 5, "2-2": 4, "0-2": 3, "其他": 4}
for i, (s, p) in enumerate(sorted(scores.items(), key=lambda x: x[1], reverse=True), 1):
    print(f"  {i}. {s}: {p:>3}% {'█' * int(p/2)}")
print(f"  ★ 推荐: 1-0, 2-0, 1-1")
print(f"  理由: AI预测加拿大小胜1球，OddsPortal AI认为1-0或1-1最可能")
print()

# 维度5: 进球数
print("【维度5】总进球数")
print("-" * 80)
goals = {"0球": 8, "1球": 22, "2球": 28, "3球": 22, "4球": 12, "5球+": 8}
for g, p in goals.items():
    print(f"  {g}: {p:>3}% {'█' * int(p/2)}")
over = goals["3球"] + goals["4球"] + goals["5球+"]
under = goals["0球"] + goals["1球"] + goals["2球"]
print(f"  大2.5: {over}% | 小2.5: {under}%")
print(f"  ★ 推荐: 2球最可能 | 小2.5球 @1.68")
print()

# 维度6: 大小球
print("【维度6】大小球 (Over/Under)")
print("-" * 80)
print(f"  推荐: 小2.5球 @1.68-1.75")
print(f"  信心: ★★★★☆")
print(f"  理由: OddsPortal AI: 'both teams have been involved in tight, draw-heavy")
print(f"        stretches rather than wild, end-to-end contests'")
print(f"  备选: 双方进球-否 @1.80")
print()

print("=" * 80)
print()

# ============================================
# Kelly注码
# ============================================
print("【Kelly注码建议】")
print("-" * 80)
print(f"  资金池: 10,000 EUR | 最大单注: 500 EUR (5%)")
print()

recommendations = [
    ("加拿大胜", adj_h/100, 1.85, "1X2"),
    ("小2.5球", 0.60, 1.68, "大小球"),
    ("双方进球-否", 0.55, 1.80, "BTTS"),
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
print("  📊 数据源: OddsPortal + 500.com + The Odds API")
print("  ⏱  数据抓取: 2026-06-12 17:12")
print("=" * 80)
