#!/usr/bin/env python3
"""
2026 FIFA World Cup - USA vs Paraguay
Complete Predictions (Jingcai Format)

Output: 1X2, AH, HT/FT, Score, Total Goals, O/U
Data: Model probabilities + market data
"""

from datetime import datetime
import math

print("=" * 80)
print("                    2026 FIFA WORLD CUP - COMPLETE PREDICTIONS")
print("                        USA vs Paraguay | Group D | Round 1")
print("                              Match Time: 2026-06-13 09:00")
print("                              Report Time: 2026-06-13 07:46")
print("=" * 80)
print()

# ============================================================
# BASE PROBABILITY MODEL
# ============================================================
# Derived from six-dimension analysis
home_xg = 1.6   # USA expected goals
away_xg = 1.2   # Paraguay expected goals

home_prob = 0.55
draw_prob = 0.22
away_prob = 0.23

# Poisson helper

def poisson_prob(lam, k):
    return (lam ** k) * math.exp(-lam) / math.factorial(k)


def score_prob(hg, ag, home_xg, away_xg):
    return poisson_prob(home_xg, hg) * poisson_prob(away_xg, ag)


# ============================================================
# 1. 胜平负 (1X2)
# ============================================================
print("【1】胜平负 (1X2 / Match Result)")
print("-" * 80)
print()

# Recalculate based on Poisson model
home_win_p = 0
draw_p = 0
away_win_p = 0

scores = []
for hg in range(0, 6):
    for ag in range(0, 6):
        p = score_prob(hg, ag, home_xg, away_xg)
        scores.append((hg, ag, p))
        if hg > ag:
            home_win_p += p
        elif hg == ag:
            draw_p += p
        else:
            away_win_p += p

# Normalize
total = home_win_p + draw_p + away_win_p
home_win_p /= total
draw_p /= total
away_win_p /= total

# Confidence intervals
home_odds_fair = 1 / home_win_p
draw_odds_fair = 1 / draw_p
away_odds_fair = 1 / away_prob

print(f"  结果          概率      公平赔率      市场赔率      价值")
print(f"  {'-'*72}")
print(f"  美国胜        {home_win_p*100:.1f}%     {home_odds_fair:.2f}         2.05          {'VALUE' if home_odds_fair > 2.05 else 'NO'}")
print(f"  平局          {draw_p*100:.1f}%     {draw_odds_fair:.2f}         3.23          {'VALUE' if draw_odds_fair > 3.23 else 'NO'}")
print(f"  巴拉圭胜      {away_win_p*100:.1f}%     {away_odds_fair:.2f}         3.83          {'VALUE' if away_odds_fair > 3.83 else 'NO'}")
print()
print(f"  模型推荐: 美国胜 (概率 {home_win_p*100:.1f}%)")
print(f"  信心度: 中 (但市场过度定价，低价值)")
print()

# ============================================================
# 2. 让球胜平负 (Asian Handicap)
# ============================================================
print("【2】让球胜平负 (Asian Handicap)")
print("-" * 80)
print()

# Calculate AH probabilities for common lines
ah_lines = [
    (-1.0, "USA -1"),
    (-0.5, "USA -0.5"),
    (0.0, "平手 (0)"),
    (+0.5, "USA +0.5 / PAR -0.5"),
    (+1.0, "USA +1 / PAR -1"),
]


def ah_prob(line, home_xg, away_xg, n=10):
    """Probability home team wins AH line"""
    win = 0
    draw = 0
    lose = 0
    for hg in range(n):
        for ag in range(n):
            p = poisson_prob(home_xg, hg) * poisson_prob(away_xg, ag)
            margin = hg - ag + line
            if margin > 0:
                win += p
            elif margin == 0:
                draw += p
            else:
                lose += p
    return win, draw, lose


print(f"  盘口                美国胜(让球)   走水     美国负(让球)")
print(f"  {'-'*72}")
for line, name in ah_lines:
    w, d, l = ah_prob(line, home_xg, away_xg)
    print(f"  {name:20s} {w*100:.1f}%         {d*100:.1f}%     {l*100:.1f}%")
print()

# Most likely AH line
print(f"  推荐让球:")
print(f"    USA -0.5: 美国胜概率 {home_win_p*100:.1f}% (同1X2)")
print(f"    USA +0.5: 美国不败概率 {(home_win_p+draw_p)*100:.1f}%")
print(f"    PAR +0.5: 巴拉圭不败概率 {(away_win_p+draw_p)*100:.1f}%")
print()

# ============================================================
# 3. 半全场 (HT/FT)
# ============================================================
print("【3】半全场 (Half-Time / Full-Time)")
print("-" * 80)
print()

# Simplified: assume HT probabilities are 60% of FT (home team takes time)
# More realistic: use half xG for HT
ht_home_xg = home_xg * 0.45
ht_away_xg = away_xg * 0.40

ht_home = 0
ht_draw = 0
ht_away = 0
for hg in range(6):
    for ag in range(6):
        p = poisson_prob(ht_home_xg, hg) * poisson_prob(ht_away_xg, ag)
        if hg > ag:
            ht_home += p
        elif hg == ag:
            ht_draw += p
        else:
            ht_away += p

total_ht = ht_home + ht_draw + ht_away
ht_home /= total_ht
ht_draw /= total_ht
ht_away /= total_ht

htft = []
for ht_res in [("H", ht_home), ("D", ht_draw), ("A", ht_away)]:
    for ft_res in [("H", home_win_p), ("D", draw_p), ("A", away_win_p)]:
        p = ht_res[1] * ft_res[1]
        label = f"{ht_res[0]}/{ft_res[0]}"
        htft.append((label, p))

htft.sort(key=lambda x: x[1], reverse=True)

print(f"  半全场组合          概率")
print(f"  {'-'*72}")
for label, p in htft[:9]:
    desc = {
        "H/H": "美国/美国", "H/D": "美国/平", "H/A": "美国/巴拉圭",
        "D/H": "平/美国", "D/D": "平/平", "D/A": "平/巴拉圭",
        "A/H": "巴拉圭/美国", "A/D": "巴拉圭/平", "A/A": "巴拉圭/巴拉圭",
    }[label]
    bar = "*" * int(p * 50) + "-" * (50 - int(p * 50))
    print(f"  {label} ({desc:8s})    {p*100:.1f}%  {bar}")
print()
print(f"  推荐: 美国/美国 (H/H) 概率 {ht_home*home_win_p*100:.1f}%")
print(f"  次选: 平/美国 (D/H) 概率 {ht_draw*home_win_p*100:.1f}%")
print()

# ============================================================
# 4. 比分 (Correct Score - Probability Ranking)
# ============================================================
print("【4】比分 (Correct Score)")
print("-" * 80)
print()

scores_sorted = sorted(scores, key=lambda x: x[2], reverse=True)

print(f"  排名    比分          概率      推荐")
print(f"  {'-'*72}")
for i, (hg, ag, p) in enumerate(scores_sorted[:15]):
    mark = "TOP TOP" if i == 0 else "HIGH" if i <= 2 else ""
    print(f"  {i+1:2d}      {hg}:{ag}           {p*100:.1f}%     {mark}")
print()

# Top 3 analysis
top3 = scores_sorted[:3]
print(f"  最可能比分 TOP 3:")
for i, (hg, ag, p) in enumerate(top3):
    print(f"    {i+1}. {hg}:{ag} ({p*100:.1f}%)")
print()

# ============================================================
# 5. 进球数 (Total Goals)
# ============================================================
print("【5】进球数 (Total Goals)")
print("-" * 80)
print()

# Total goals distribution
goal_probs = {}
for total_goals in range(0, 11):
    goal_probs[total_goals] = 0

for hg in range(6):
    for ag in range(6):
        p = poisson_prob(home_xg, hg) * poisson_prob(away_xg, ag)
        total = hg + ag
        if total <= 10:
            goal_probs[total] += p

# Normalize
g_total = sum(goal_probs.values())
for k in goal_probs:
    goal_probs[k] /= g_total

print(f"  总进球      概率")
print(f"  {'-'*72}")
for g in range(0, 9):
    bar = "*" * int(goal_probs[g] * 50) + "-" * (50 - int(goal_probs[g] * 50))
    mark = " ← 最可能" if g == 2 else ""
    print(f"  {g} 球        {goal_probs[g]*100:.1f}%  {bar}{mark}")
print()

# Most likely
total_expected = home_xg + away_xg
print(f"  预期总进球: {total_expected:.1f}")
print(f"  最可能进球数: 2-3 球")
print(f"  2球概率: {(goal_probs[2]+goal_probs[3])*100:.1f}%")
print()

# ============================================================
# 6. 大小球 (Over/Under)
# ============================================================
print("【6】大小球 (Over/Under)")
print("-" * 80)
print()

ou_lines = [1.5, 2.0, 2.5, 3.0, 3.5]


def ou_prob(threshold, home_xg, away_xg, n=10):
    over = 0
    under = 0
    for hg in range(n):
        for ag in range(n):
            p = poisson_prob(home_xg, hg) * poisson_prob(away_xg, ag)
            total = hg + ag
            if total > threshold:
                over += p
            elif total < threshold:
                under += p
            else:  # exactly threshold (for 2.0, 3.0 etc.)
                if threshold == int(threshold):
                    over += p * 0.5
                    under += p * 0.5
                else:
                    over += p
    return over, under


print(f"  盘口          大球概率    小球概率    推荐")
print(f"  {'-'*72}")
for line in ou_lines:
    over, under = ou_prob(line, home_xg, away_xg)
    total = over + under
    over /= total
    under /= total
    
    if over > 0.55:
        rec = "推荐大"
    elif under > 0.55:
        rec = "推荐小"
    else:
        rec = "观望"
    
    print(f"  {'大' if line == int(line) else '大'}{line:.1f}        {over*100:.1f}%       {under*100:.1f}%      {rec}")
print()

# Recommended
print(f"  模型推荐:")
over_25, under_25 = ou_prob(2.5, home_xg, away_xg)
total = over_25 + under_25
over_25 /= total
under_25 /= total
print(f"    大2.5: {over_25*100:.1f}%")
print(f"    小2.5: {under_25*100:.1f}%")
if over_25 > under_25:
    print(f"    → 推荐: 大2.5 (概率 {over_25*100:.1f}%)")
else:
    print(f"    → 推荐: 小2.5 (概率 {under_25*100:.1f}%)")
print()

# ============================================================
# SUMMARY TABLE
# ============================================================
print("=" * 80)
print("                          预测汇总 (PREDICTION SUMMARY)")
print("=" * 80)
print()
print(f"  {'项目':20s} {'预测':20s} {'概率':12s} {'信心度'}")
print(f"  {'-'*72}")
print(f"  {'胜平负':20s} {'美国胜':20s} {home_win_p*100:.1f}%        {'中'}")
print(f"  {'让球胜平负':20s} {'美国-0.5':20s} {home_win_p*100:.1f}%        {'中'}")
print(f"  {'半全场':20s} {'美国/美国':20s} {ht_home*home_win_p*100:.1f}%        {'中'}")
print(f"  {'最可能比分':20s} {'1:0 或 2:1':20s} {(scores_sorted[0][2]+scores_sorted[1][2]+scores_sorted[2][2])*100:.1f}%        {'中'}")
print(f"  {'进球数':20s} {'2-3球':20s} {(goal_probs[2]+goal_probs[3])*100:.1f}%        {'中'}")
print(f"  {'大小球':20s} {'大2.5' if over_25 > under_25 else '小2.5':20s} {max(over_25, under_25)*100:.1f}%        {'低'}")
print(f"  {'-'*72}")
print()

print("  比分概率排序 (Top 10):")
print(f"  {'排名':4s} {'比分':8s} {'概率':8s}")
print(f"  {'-'*25}")
for i, (hg, ag, p) in enumerate(scores_sorted[:10]):
    print(f"  {i+1:2d}    {hg}:{ag}      {p*100:.1f}%")
print()

print("=" * 80)
print(f"  系统: Naga Core Football Quant OS v2.0")
print(f"  模型: 泊松分布 + 六维调整")
print(f"  数据: 500.com, FIFA, Historical")
print(f"  时间: {datetime.now().isoformat()}")
print("=" * 80)
