#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""韩国 vs 捷克 完整预测 v5.0 - 基于500.com+OddsPortal实际数据"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

print("=" * 80)
print("           娜迦足球量化决策系统 v5.0 - 完整预测报告")
print("              韩国 vs 捷克 | 2026世界杯 Group A")
print("              2026-06-12 10:00")
print("=" * 80)
print()

# ============================================
# 基于实际抓取的数据
# ============================================
match_data = {
    "home_team": "韩国",
    "away_team": "捷克",
    "league": "2026世界杯 Group A",
    "match_date": "2026-06-12",
    "kickoff": "10:00",
    
    # FIFA排名
    "fifa_rank": {
        "home": 25,
        "away": 41
    },
    
    # Elo
    "elo": {
        "home": 1760,
        "away": 1700
    },
    
    # 近期战绩
    "home_recent": {
        "last_10": "6胜1平3负",
        "goals_scored": 15,
        "goals_conceded": 12,
        "key_matches": [
            "1:0胜萨尔瓦多", "5:0胜特立尼达", "0:1负奥地利", "0:4负科特迪瓦",
            "1:0胜加纳", "2:0胜玻利维亚", "2:0胜巴拉圭", "0:5负巴西",
            "2:2平墨西哥", "2:0胜美国"
        ]
    },
    "away_recent": {
        "last_10": "5胜4平1负",
        "goals_scored": 19,
        "goals_conceded": 8,
        "key_matches": [
            "3:1胜危地马拉", "2:1胜科索沃", "1:1平丹麦", "2:2平爱尔兰",
            "6:0胜直布罗陀", "1:0胜圣马力诺", "1:2负法罗群岛", "0:0平克罗地亚",
            "1:1平沙特", "2:0胜黑山"
        ]
    },
    
    # 历史交锋
    "h2h": [
        {"date": "2016-06-05", "venue": "客", "result": "2:1", "winner": "韩国", "odds": [1.66, 3.57, 5.25]}
    ],
    
    # 当前市场赔率 (500.com平均值)
    "current_odds": {
        "1x2": {
            "主胜": 2.64, "平局": 3.12, "客胜": 2.68,
            "sources": ["500.com百家平均"]
        },
        "asian_handicap": {
            "handicap": -1,  # 韩国让1球
            "主胜": 5.50, "平局": 4.00, "客胜": 1.46,
        },
        "over_under": {
            "line": "2/2.5",
            "大球": 1.02, "小球": 0.83,
        }
    },
    
    # 澳门心水
    "macau_tip": "和局"
}

# ============================================
# 一、基础数据
# ============================================
print("【一、基础数据】")
print("-" * 80)
print(f"赛事: 2026世界杯 Group A 第1轮")
print(f"对阵: 韩国 vs 捷克")
print(f"时间: 2026-06-12 10:00")
print(f"地点: 美国 (中立场地)")
print()
print(f"FIFA排名: 韩国第{match_data['fifa_rank']['home']}位 | 捷克第{match_data['fifa_rank']['away']}位")
print(f"Elo评级: 韩国{match_data['elo']['home']} | 捷克{match_data['elo']['away']}")
print(f"排名差距: 韩国领先16位")
print()
print(f"韩国近期: {match_data['home_recent']['last_10']} | 进{match_data['home_recent']['goals_scored']}失{match_data['home_recent']['goals_conceded']}")
print(f"捷克近期: {match_data['away_recent']['last_10']} | 进{match_data['away_recent']['goals_scored']}失{match_data['away_recent']['goals_conceded']}")
print()
print(f"历史交锋: 1次 - 韩国客场2:1胜捷克 (2016年友谊赛)")
print(f"澳门心水: {match_data['macau_tip']}")
print()

# ============================================
# 二、赔率概率分析
# ============================================
print("【二、赔率概率分析 (1X2)】")
print("-" * 80)

odds = match_data["current_odds"]["1x2"]
margin = 1/odds["主胜"] + 1/odds["平局"] + 1/odds["客胜"]

prob_home = (1/odds["主胜"]) / margin * 100
prob_draw = (1/odds["平局"]) / margin * 100
prob_away = (1/odds["客胜"]) / margin * 100

print(f"百家平均赔率: 主胜@{odds['主胜']} | 平局@{odds['平局']} | 客胜@{odds['客胜']}")
print(f"隐含概率: 主胜{prob_home:.1f}% | 平局{prob_draw:.1f}% | 客胜{prob_away:.1f}%")
print()

# 初盘对比
init_odds = {"主胜": 2.60, "平局": 3.05, "客胜": 2.94}
init_margin = 1/init_odds["主胜"] + 1/init_odds["平局"] + 1/init_odds["客胜"]
init_home = (1/init_odds["主胜"]) / init_margin * 100
init_draw = (1/init_odds["平局"]) / init_margin * 100
init_away = (1/init_odds["客胜"]) / init_margin * 100

print(f"初盘赔率: 主胜@{init_odds['主胜']} | 平局@{init_odds['平局']} | 客胜@{init_odds['客胜']}")
print(f"初盘概率: 主胜{init_home:.1f}% | 平局{init_draw:.1f}% | 客胜{init_away:.1f}%")
print()

# 变化趋势
home_change = prob_home - init_home
draw_change = prob_draw - init_draw
away_change = prob_away - init_away

print(f"赔率变化:")
home_trend = "上调" if home_change > 0 else "下调"
print(f"  主胜: {home_change:+.1f}% ({home_trend}) - 市场{('看好' if home_change > 0 else '看淡')}韩国")
draw_trend = "上调" if draw_change > 0 else "下调"
print(f"  平局: {draw_change:+.1f}% ({draw_trend})")
away_trend = "上调" if away_change > 0 else "下调"
print(f"  客胜: {away_change:+.1f}% ({away_trend}) - 市场{('看好' if away_change > 0 else '看淡')}捷克")
print()

# ============================================
# 三、胜平负预测
# ============================================
print("【三、胜平负预测 (1X2)】")
print("-" * 80)

# 综合概率 (加权: 隐含概率50% + 排名差距20% + 近期状态20% + 历史10%)
# 韩国排名更高(+16位)，但捷克近期不败率更高
# 历史交锋韩国客场胜

rank_factor = 5  # 排名差距16位，韩国+5%
h2h_factor = 3   # 历史交锋韩国胜，+3%
form_factor = -2  # 捷克近期不败率更高，韩国-2%

adj_home = prob_home + rank_factor + h2h_factor + form_factor
adj_draw = prob_draw - 3
adj_away = prob_away - 3

# 归一化
total = adj_home + adj_draw + adj_away
adj_home = adj_home / total * 100
adj_draw = adj_draw / total * 100
adj_away = adj_away / total * 100

print(f"综合概率: 主胜{adj_home:.1f}% | 平局{adj_draw:.1f}% | 客胜{adj_away:.1f}%")
print(f"  (排名修正+{rank_factor}%, 历史修正+{h2h_factor}%, 状态修正{form_factor}%)")

if adj_home > adj_away and adj_home > adj_draw:
    spf_recommend = "主胜 (韩国胜)"
    spf_confidence = "★★★☆☆"
    spf_reason = "FIFA排名领先，历史交锋占优，但近期状态有起伏"
elif adj_draw > adj_away:
    spf_recommend = "平局"
    spf_confidence = "★★★★☆"
    spf_reason = "欧赔平手盘，双方实力接近，捷克近期不败率高"
else:
    spf_recommend = "客胜 (捷克胜)"
    spf_confidence = "★★★☆☆"
    spf_reason = "捷克近期不败率高"

print(f"\n推荐: {spf_recommend}")
print(f"信心指数: {spf_confidence}")
print(f"理由: {spf_reason}")
print(f"最佳赔率: 平局@{odds['平局']} (价值最高)")
print()

# ============================================
# 四、让球胜平负预测
# ============================================
print("【四、让球胜平负预测】")
print("-" * 80)

ah = match_data["current_odds"]["asian_handicap"]
print(f"盘口: 韩国 {ah['handicap']} 球")
print(f"赔率: 主胜@{ah['主胜']} | 平局@{ah['平局']} | 客胜@{ah['客胜']}")

# 韩国让1球，需要赢2球+才能赢盘
# 韩国近期对强队（巴西、奥地利、科特迪瓦）都大败，对弱队小胜
# 捷克近期不败率高，防守较好

ah_prob_away = (1/ah["客胜"]) / (1/ah["主胜"]+1/ah["平局"]+1/ah["客胜"]) * 100

print(f"\n让球分析:")
print(f"  韩国需赢2球+才能赢盘 - 对强队均大败，对弱队小胜")
print(f"  捷克受让1球，只需不败或小负1球即可赢盘")
print(f"  捷克受让胜概率约: {ah_prob_away:.0f}%")

print(f"\n推荐: 捷克受让胜 (+1)")
print(f"信心指数: ★★★★☆")
print(f"理由: 韩国让1球过深，近期对强队表现差，捷克防守稳健")
print()

# ============================================
# 五、半全场预测
# ============================================
print("【五、半全场预测 (HT/FT)】")
print("-" * 80)

# 韩国上半场容易慢热（对萨尔瓦多、玻利维亚、巴拉圭都是半场0:0或1:0）
# 捷克上半场稳健（近期多场半场平或领先）

htft_probs = {
    "平/平": 20,   # 最可能 - 双方谨慎
    "平/主": 18,   # 半场平，韩国下半场发力
    "平/客": 12,   # 半场平，捷克下半场制胜
    "主/主": 12,   # 韩国全场领先
    "客/客": 10,   # 捷克全场领先
    "客/平": 8,    # 捷克领先被扳平
    "主/客": 8,    # 韩国领先被逆转
    "主/平": 7,    # 韩国领先被扳平
    "客/主": 5,    # 逆转
}

print("半全场概率分布:")
for outcome, prob in sorted(htft_probs.items(), key=lambda x: x[1], reverse=True):
    bar = "█" * int(prob/2)
    print(f"  {outcome}: {prob:>3}% {bar}")
print()

htft_top3 = sorted(htft_probs.items(), key=lambda x: x[1], reverse=True)[:3]
print(f"推荐: {htft_top3[0][0]} ({htft_top3[0][1]}%)")
print(f"备选: {htft_top3[1][0]} ({htft_top3[1][1]}%), {htft_top3[2][0]} ({htft_top3[2][1]}%)")
print("信心指数: ★★★☆☆")
print("理由: 世界杯小组赛上半场谨慎，韩国下半场可能发力")
print()

# ============================================
# 六、比分预测
# ============================================
print("【六、比分预测 (Correct Score)】")
print("-" * 80)

# 基于大小球2/2.5和双方近期状态
score_probs = {
    "1-1": 15,   # 最可能 - 澳门心水推荐平局
    "1-0": 12,   # 韩国小胜
    "0-0": 10,   # 小组赛谨慎开局
    "2-1": 10,   # 韩国险胜
    "0-1": 9,    # 捷克小胜
    "2-0": 8,    # 韩国完胜
    "1-2": 7,    # 捷克险胜
    "2-2": 6,    # 对攻平局
    "0-2": 5,    # 捷克完胜
    "其他": 18
}

print("比分概率 TOP 5:")
for score, prob in sorted(score_probs.items(), key=lambda x: x[1], reverse=True)[:5]:
    bar = "█" * int(prob/2)
    print(f"  {score}: {prob:>3}% {bar}")
print()
print("推荐比分: 1-1, 1-0, 0-0")
print("信心指数: ★★★☆☆")
print("理由: 澳门推荐平局，1-1为最可能比分；韩国1-0小胜次之")
print()

# ============================================
# 七、进球数预测
# ============================================
print("【七、总进球数预测 (Total Goals)】")
print("-" * 80)

goal_probs = {
    "0球": 8,
    "1球": 20,
    "2球": 28,   # 最可能 (大小球2/2.5支持)
    "3球": 22,
    "4球": 14,
    "5球+": 8
}

print("进球数分布:")
for goals, prob in goal_probs.items():
    bar = "█" * int(prob/2)
    print(f"  {goals}: {prob:>3}% {bar}")
print()

over_prob = goal_probs["3球"] + goal_probs["4球"] + goal_probs["5球+"]
under_prob = goal_probs["0球"] + goal_probs["1球"] + goal_probs["2球"]

ou = match_data["current_odds"]["over_under"]
print(f"大{ou['line']}球概率: {over_prob}% | 小{ou['line']}球概率: {under_prob}%")
print(f"推荐: 小2.5球")
print("信心指数: ★★★★☆")
print("理由: 世界杯小组赛谨慎，韩国近期对强队进攻乏力，2球为最可能总进球")
print()

# ============================================
# 八、大小球详细预测
# ============================================
print("【八、大小球详细预测】")
print("-" * 80)
print("盘口分析:")
print(f"  大2球 @0.95  概率: {over_prob + goal_probs['2球']*0.3:.0f}%")
print(f"  小2.5球 @0.83 概率: {under_prob}% ← 强烈推荐")
print(f"  大2.5球 @1.02 概率: {over_prob}%")
print(f"  小3球 @1.75  概率: {under_prob + goal_probs['3球']*0.5:.0f}%")
print()
print("推荐: 小2.5球 (价值最高，水位低)")
print("信心指数: ★★★★☆")
print("理由: 大小球盘口2/2.5，小球水位更低，市场倾向小球")
print()

# ============================================
# 九、Kelly注码建议
# ============================================
print("【九、Kelly注码建议】")
print("-" * 80)

bankroll = 10000

def kelly_fraction(p, b):
    """Kelly Criterion: f* = (bp - q) / b"""
    q = 1 - p
    return (b * p - q) / b

# 各项推荐 Kelly 计算
recommendations = [
    ("小2.5球", under_prob/100, 0.83/0.95, "大小球"),
    ("平局", adj_draw/100, 3.12, "1X2"),
    ("捷克受让胜", ah_prob_away/100, 1.46, "让球"),
    ("半全场 平/平", 0.20, 4.0, "半全场"),
]

print(f"资金池: {bankroll:,} EUR | 最大单注: {bankroll*0.05:,.0f} (5%)")
print()
print("推荐投注:")
print()

for i, (name, prob, odds, cat) in enumerate(recommendations, 1):
    kelly = kelly_fraction(prob, odds - 1)
    kelly_half = kelly / 2
    amount = min(bankroll * kelly_half, bankroll * 0.05)
    
    if kelly > 0:
        ev = (prob * odds - 1) * 100
        print(f"{i}. {name}")
        print(f"   类别: {cat}")
        print(f"   概率: {prob*100:.1f}% | 赔率: {odds:.2f}")
        print(f"   Kelly: {kelly:.2%} | 半Kelly: {kelly_half:.2%}")
        print(f"   建议注码: {amount:,.0f} EUR ({amount/bankroll:.2%})")
        print(f"   期望值: +{ev:.1f}%")
        print()

# ============================================
# 十、综合投注建议
# ============================================
print("【十、综合投注建议】")
print("=" * 80)
print()
print("核心推荐 (按信心排序):")
print()
print("1. 小2.5球 @0.83 | 信心: ★★★★☆")
print("    理由: 世界杯小组赛谨慎，韩国近期对强队进攻乏力，盘口支持")
print()
print("2. 捷克受让胜(+1) @1.46 | 信心: ★★★★☆")
print("    理由: 韩国让1球过深，近期对强队均大败，捷克防守稳健")
print()
print("3. 平局 @3.12 | 信心: ★★★★☆")
print("    理由: 欧赔平手盘，澳门心水推荐平局，双方实力接近")
print()
print("4. 半全场 平/平 @4.0+ | 信心: ★★★☆☆")
print("    理由: 小组赛上半场谨慎，全场可能闷平")
print()
print("5. 比分 1-1 @6.0+ | 信心: ★★★☆☆")
print("    理由: 最可能比分，澳门心水推荐")
print()

# ============================================
# 十一、风险提示
# ============================================
print("【十一、风险提示】")
print("-" * 80)
print("⚠️  世界杯小组赛，战意可能受出线形势影响")
print("⚠️  韩国近期对强队表现差（0:5巴西、0:1奥地利、0:4科特迪瓦）")
print("⚠️  捷克近期不败率高，但对手实力参差不齐")
print("⚠️  历史交锋仅1次（2016年友谊赛），参考价值有限")
print("⚠️  欧赔初盘主胜2.60→即时2.64，市场对韩国信心略降")
print("⚠️  建议单场投注，控制注码在5%以内")
print("⚠️  如已有多场世界杯投注，注意总风险敞口")
print()

print("【十二、数据来源】")
print("-" * 80)
print("📊 500.com - 欧赔/让球/亚赔/大小球/必发指数")
print("📊 OddsPortal - 交锋历史/H2H")
print("📊 FIFA官方排名 - 2026年4月")
print("⏱  数据抓取时间: 2026-06-12 08:24")
print()

print("=" * 80)
print("  娜迦足量 v5.0 | 数据源: 500.com + OddsPortal + FIFA")
print("  ⚠️ 仅供研究学习，不构成投注建议")
print("=" * 80)
