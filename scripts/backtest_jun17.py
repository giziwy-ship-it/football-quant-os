#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest script for 2026-06-17 World Cup matches (Beijing Time)
Matches: I组 + J组 首轮
"""

import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

# Match data: home, away, actual_result, typical_odds
matches = [
    {
        "match_id": "WC2026-I1-049",
        "group": "I",
        "home": "France", "away": "Senegal",
        "home_cn": "法国", "away_cn": "塞内加尔",
        "actual": "3-1", "actual_home": 3, "actual_away": 1,
        # France strong favorite vs solid African team
        "odds_home": 1.55, "odds_draw": 4.20, "odds_away": 6.50,
        "ou_line": 2.5, "odds_over": 1.85, "odds_under": 2.00,
        "home_xg": 1.85, "away_xg": 0.95,
        "home_poss": 58, "away_poss": 42,
        "stage": "group", "first_match": True,
        "home_region": "europe", "away_region": "africa",
        "home_exp": "experienced", "away_exp": "experienced"
    },
    {
        "match_id": "WC2026-I1-050",
        "group": "I",
        "home": "Iraq", "away": "Norway",
        "home_cn": "伊拉克", "away_cn": "挪威",
        "actual": "1-4", "actual_home": 1, "actual_away": 4,
        # Norway favorite, Iraq underdog
        "odds_home": 5.50, "odds_draw": 3.80, "odds_away": 1.65,
        "ou_line": 2.5, "odds_over": 1.75, "odds_under": 2.10,
        "home_xg": 0.85, "away_xg": 1.75,
        "home_poss": 40, "away_poss": 60,
        "stage": "group", "first_match": True,
        "home_region": "asia", "away_region": "europe",
        "home_exp": "experienced", "away_exp": "newbie"
    },
    {
        "match_id": "WC2026-J1-055",
        "group": "J",
        "home": "Argentina", "away": "Algeria",
        "home_cn": "阿根廷", "away_cn": "阿尔及利亚",
        "actual": "3-0", "actual_home": 3, "actual_away": 0,
        # Argentina heavy favorite
        "odds_home": 1.25, "odds_draw": 5.50, "odds_away": 12.00,
        "ou_line": 2.5, "odds_over": 1.65, "odds_under": 2.25,
        "home_xg": 2.10, "away_xg": 0.70,
        "home_poss": 62, "away_poss": 38,
        "stage": "group", "first_match": True,
        "home_region": "south_america", "away_region": "africa",
        "home_exp": "experienced", "away_exp": "experienced"
    },
    {
        "match_id": "WC2026-J1-056",
        "group": "J",
        "home": "Austria", "away": "Jordan",
        "home_cn": "奥地利", "away_cn": "约旦",
        "actual": "3-1", "actual_home": 3, "actual_away": 1,
        # Austria moderate favorite vs debutant
        "odds_home": 1.45, "odds_draw": 4.50, "odds_away": 7.50,
        "ou_line": 2.5, "odds_over": 1.80, "odds_under": 2.05,
        "home_xg": 1.65, "away_xg": 0.80,
        "home_poss": 55, "away_poss": 45,
        "stage": "group", "first_match": True,
        "home_region": "europe", "away_region": "asia",
        "home_exp": "experienced", "away_exp": "newbie"
    }
]

results = []

for m in matches:
    cmd = [
        "python", "scripts/predict.py",
        "--home", m["home"],
        "--away", m["away"],
        "--odds-home", str(m["odds_home"]),
        "--odds-draw", str(m["odds_draw"]),
        "--odds-away", str(m["odds_away"]),
        "--stage", m["stage"],
        "--ou-line", str(m["ou_line"]),
        "--odds-over", str(m["odds_over"]),
        "--odds-under", str(m["odds_under"]),
        "--home-xg", str(m["home_xg"]),
        "--away-xg", str(m["away_xg"]),
        "--home-poss", str(m["home_poss"]),
        "--away-poss", str(m["away_poss"]),
        "--home-region", m["home_region"],
        "--away-region", m["away_region"],
        "--home-exp", m["home_exp"],
        "--away-exp", m["away_exp"],
        "--format", "json"
    ]
    if m["first_match"]:
        cmd.append("--first-match")

    try:
        proc = subprocess.run(
            cmd,
            capture_output=True, text=True,
            encoding='utf-8', errors='ignore',
            cwd=r"D:\openclaw-workspace\football_quant_os",
            timeout=30
        )
        output = proc.stdout
        # Try to parse JSON from output
        try:
            pred = json.loads(output)
        except:
            # Extract JSON if wrapped in other text
            import re
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                pred = json.loads(json_match.group())
            else:
                pred = {"error": "Failed to parse", "raw": output[:200]}

        # Determine prediction correctness
        pred_1x2 = pred.get("prediction", {}).get("recommendation_1x2", "")
        pred_ou = pred.get("prediction", {}).get("recommendation_ou", "")

        # 1X2 result
        if m["actual_home"] > m["actual_away"]:
            actual_1x2 = "主胜"
        elif m["actual_home"] < m["actual_away"]:
            actual_1x2 = "客胜"
        else:
            actual_1x2 = "平局"

        # OU result
        total_goals = m["actual_home"] + m["actual_away"]
        actual_ou = "Over" if total_goals > m["ou_line"] else "Under"

        # Check correctness
        correct_1x2 = pred_1x2 == actual_1x2 if pred_1x2 else False
        correct_ou = pred_ou == actual_ou if pred_ou else False

        results.append({
            **m,
            "prediction": pred,
            "actual_1x2": actual_1x2,
            "actual_ou": actual_ou,
            "total_goals": total_goals,
            "correct_1x2": correct_1x2,
            "correct_ou": correct_ou
        })

    except Exception as e:
        results.append({**m, "error": str(e)})

# Print summary
print("=" * 70)
print("2026世界杯回测报告 - 2026年6月17日 (北京时间 I组+J组)")
print("=" * 70)
print()

correct_1x2_count = sum(1 for r in results if r.get("correct_1x2"))
correct_ou_count = sum(1 for r in results if r.get("correct_ou"))

for r in results:
    print(f"📌 {r['home_cn']} vs {r['away_cn']} ({r['group']}组)")
    print(f"   实际比分: {r['actual']} → {r['actual_1x2']} / {r['actual_ou']} {r['ou_line']} ({r['total_goals']}球)")
    if "prediction" in r:
        pred = r["prediction"]
        rec_1x2 = pred.get("prediction", {}).get("recommendation_1x2", "N/A")
        rec_ou = pred.get("prediction", {}).get("recommendation_ou", "N/A")
        probs = pred.get("prediction", {}).get("probabilities_1x2", {})
        print(f"   预测1X2: {rec_1x2} (主{probs.get('home',0):.1%}/平{probs.get('draw',0):.1%}/客{probs.get('away',0):.1%})")
        print(f"   预测OU: {rec_ou}")
        print(f"   1X2 {'✅ 命中' if r['correct_1x2'] else '❌ 未中'} | OU {'✅ 命中' if r['correct_ou'] else '❌ 未中'}")
    else:
        print(f"   错误: {r.get('error', 'Unknown')}")
    print()

print("-" * 70)
print(f"回测汇总:")
print(f"  1X2 准确率: {correct_1x2_count}/4 = {correct_1x2_count/4*100:.1f}%")
print(f"  OU  准确率: {correct_ou_count}/4 = {correct_ou_count/4*100:.1f}%")
print("=" * 70)

# Save report
report_path = r"D:\openclaw-workspace\football_quant_os\reports\backtest_2026-06-17.json"
with open(report_path, 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)
print(f"\n报告已保存: {report_path}")
