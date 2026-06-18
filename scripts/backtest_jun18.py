#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest script for 2026-06-18 World Cup matches (Beijing Time)
Matches: K组 + L组 首轮
"""

import sys
import json
import os

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"D:\openclaw-workspace\football_quant_os")
sys.path.insert(0, r"D:\openclaw-workspace\football_quant_os\scripts")
sys.path.insert(0, r"D:\openclaw-workspace\football_quant_os")

from predict import run_prediction

# Match data (confirmed from LiveScore)
matches = [
    {
        "match_id": "WC2026-K1-061",
        "group": "K",
        "home": "Portugal", "away": "Congo DR",
        "home_cn": "葡萄牙", "away_cn": "刚果(金)",
        "actual": "1-1", "actual_home": 1, "actual_away": 1,
        "odds_home": 1.35, "odds_draw": 4.80, "odds_away": 9.00,
        "ou_line": 2.5, "odds_over": 1.75, "odds_under": 2.10,
        "home_xg": 1.80, "away_xg": 0.70,
        "home_poss": 60, "away_poss": 40,
        "stage": "group", "first_match": True,
        "home_region": "europe", "away_region": "africa",
        "home_exp": "experienced", "away_exp": "newbie"
    },
    {
        "match_id": "WC2026-L1-067",
        "group": "L",
        "home": "England", "away": "Croatia",
        "home_cn": "英格兰", "away_cn": "克罗地亚",
        "actual": "4-2", "actual_home": 4, "actual_away": 2,
        "odds_home": 1.65, "odds_draw": 3.80, "odds_away": 5.50,
        "ou_line": 2.5, "odds_over": 1.70, "odds_under": 2.15,
        "home_xg": 1.75, "away_xg": 1.10,
        "home_poss": 55, "away_poss": 45,
        "stage": "group", "first_match": True,
        "home_region": "europe", "away_region": "europe",
        "home_exp": "experienced", "away_exp": "experienced"
    },
    {
        "match_id": "WC2026-L1-068",
        "group": "L",
        "home": "Ghana", "away": "Panama",
        "home_cn": "加纳", "away_cn": "巴拿马",
        "actual": "1-0", "actual_home": 1, "actual_away": 0,
        "odds_home": 1.75, "odds_draw": 3.50, "odds_away": 5.00,
        "ou_line": 2.5, "odds_over": 1.80, "odds_under": 2.05,
        "home_xg": 1.50, "away_xg": 0.90,
        "home_poss": 52, "away_poss": 48,
        "stage": "group", "first_match": True,
        "home_region": "africa", "away_region": "north_america",
        "home_exp": "experienced", "away_exp": "newbie"
    },
    {
        "match_id": "WC2026-K1-062",
        "group": "K",
        "home": "Uzbekistan", "away": "Colombia",
        "home_cn": "乌兹别克斯坦", "away_cn": "哥伦比亚",
        "actual": "1-3", "actual_home": 1, "actual_away": 3,
        "odds_home": 5.50, "odds_draw": 3.80, "odds_away": 1.65,
        "ou_line": 2.5, "odds_over": 1.75, "odds_under": 2.10,
        "home_xg": 0.80, "away_xg": 1.70,
        "home_poss": 42, "away_poss": 58,
        "stage": "group", "first_match": True,
        "home_region": "asia", "away_region": "south_america",
        "home_exp": "newbie", "away_exp": "experienced"
    }
]

results = []

for m in matches:
    try:
        result = run_prediction(
            home=m["home"], away=m["away"],
            odds_home=m["odds_home"], odds_draw=m["odds_draw"], odds_away=m["odds_away"],
            stage=m["stage"], ou_line=m["ou_line"],
            odds_over=m["odds_over"], odds_under=m["odds_under"],
            home_xg=m["home_xg"], away_xg=m["away_xg"],
            home_poss=m["home_poss"], away_poss=m["away_poss"],
            is_first_match=m["first_match"],
            home_region=m["home_region"], away_region=m["away_region"],
            home_experience=m["home_exp"], away_experience=m["away_exp"],
            bankroll=100000, kelly_fraction=0.25
        )

        if m["actual_home"] > m["actual_away"]:
            actual_1x2 = "主胜"
        elif m["actual_home"] < m["actual_away"]:
            actual_1x2 = "客胜"
        else:
            actual_1x2 = "平局"

        total_goals = m["actual_home"] + m["actual_away"]
        actual_ou = "Over" if total_goals > m["ou_line"] else "Under"

        markets = result.get("markets", {})
        m1x2 = markets.get("1x2", {})
        ou = markets.get("over_under", {})

        model_probs = m1x2.get("model", {}) if isinstance(m1x2.get("model"), dict) else {}
        home_prob = model_probs.get("home", 0)
        draw_prob = model_probs.get("draw", 0)
        away_prob = model_probs.get("away", 0)

        if home_prob >= draw_prob and home_prob >= away_prob:
            pred_1x2 = "主胜"
        elif away_prob >= home_prob and away_prob >= draw_prob:
            pred_1x2 = "客胜"
        else:
            pred_1x2 = "平局"

        ou_rec = ou.get("recommendation", "")
        if "Over" in str(ou_rec):
            pred_ou = "Over"
        elif "Under" in str(ou_rec):
            pred_ou = "Under"
        else:
            over_prob = ou.get("over_prob", 0.5)
            pred_ou = "Over" if over_prob > 0.5 else "Under"

        correct_1x2 = pred_1x2 == actual_1x2
        correct_ou = pred_ou == actual_ou

        results.append({
            **m,
            "prediction": {
                "probabilities_1x2": {"home": home_prob, "draw": draw_prob, "away": away_prob},
                "predicted_1x2": pred_1x2,
                "predicted_ou": pred_ou,
                "ou_recommendation": ou_rec,
                "lambda": ou.get("lambda", None),
                "upset_score": result.get("upset_score", 0),
                "confidence": result.get("confidence", 0),
                "recommendations": result.get("recommendations", [])
            },
            "actual_1x2": actual_1x2,
            "actual_ou": actual_ou,
            "total_goals": total_goals,
            "correct_1x2": correct_1x2,
            "correct_ou": correct_ou
        })
    except Exception as e:
        import traceback
        results.append({**m, "error": str(e), "traceback": traceback.format_exc()})

print("=" * 70)
print("🏆 2026世界杯回测报告 - 2026年6月18日 (北京时间 K组+L组)")
print("=" * 70)
print()

correct_1x2_count = sum(1 for r in results if r.get("correct_1x2"))
correct_ou_count = sum(1 for r in results if r.get("correct_ou"))

for r in results:
    print(f"📌 {r['home_cn']} vs {r['away_cn']} ({r['group']}组)")
    print(f"   实际比分: {r['actual']} → {r['actual_1x2']} / {r['actual_ou']} {r['ou_line']} ({r['total_goals']}球)")
    if "prediction" in r:
        pred = r["prediction"]
        probs = pred.get("probabilities_1x2", {})
        print(f"   模型概率: 主{probs.get('home',0):.1%}/平{probs.get('draw',0):.1%}/客{probs.get('away',0):.1%}")
        print(f"   预测1X2: {pred['predicted_1x2']}")
        print(f"   预测OU:  {pred['predicted_ou']} (λ={pred.get('lambda','N/A')})")
        print(f"   冷门评分: {pred['upset_score']}")
        print(f"   1X2 {'✅ 命中' if r['correct_1x2'] else '❌ 未中'} | OU {'✅ 命中' if r['correct_ou'] else '❌ 未中'}")
    else:
        print(f"   错误: {r.get('error', 'Unknown')}")
    print()

print("-" * 70)
print(f"📊 回测汇总:")
print(f"  1X2 准确率: {correct_1x2_count}/4 = {correct_1x2_count/4*100:.1f}%")
print(f"  OU  准确率: {correct_ou_count}/4 = {correct_ou_count/4*100:.1f}%")
print("=" * 70)

report_path = r"D:\openclaw-workspace\football_quant_os\reports\backtest_2026-06-18.json"
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n💾 报告已保存: {report_path}")
