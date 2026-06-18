#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prediction for 2026-06-19 World Cup matches (Beijing Time)
A组+B组 第二轮
"""

import sys
import os

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"D:\openclaw-workspace\football_quant_os")
sys.path.insert(0, r"D:\openclaw-workspace\football_quant_os\scripts")
sys.path.insert(0, r"D:\openclaw-workspace\football_quant_os")

from predict import run_prediction

matches = [
    {
        "match_id": "WC2026-A2-003", "group": "A",
        "home": "Czechia", "away": "South Africa",
        "home_cn": "捷克", "away_cn": "南非",
        "time": "2026-06-19 00:00",
        "odds_home": 1.55, "odds_draw": 3.80, "odds_away": 6.50,
        "ou_line": 2.5, "odds_over": 1.85, "odds_under": 2.00,
        "home_xg": 1.70, "away_xg": 0.90,
        "home_poss": 55, "away_poss": 45,
        "stage": "group", "first_match": False,
        "home_region": "europe", "away_region": "africa",
        "home_exp": "experienced", "away_exp": "experienced"
    },
    {
        "match_id": "WC2026-B2-009", "group": "B",
        "home": "Canada", "away": "Qatar",
        "home_cn": "加拿大", "away_cn": "卡塔尔",
        "time": "2026-06-19 03:00",
        "odds_home": 1.75, "odds_draw": 3.50, "odds_away": 5.00,
        "ou_line": 2.5, "odds_over": 1.80, "odds_under": 2.05,
        "home_xg": 1.50, "away_xg": 1.00,
        "home_poss": 52, "away_poss": 48,
        "stage": "group", "first_match": False,
        "home_region": "north_america", "away_region": "asia",
        "home_exp": "experienced", "away_exp": "experienced"
    },
    {
        "match_id": "WC2026-B2-010", "group": "B",
        "home": "Switzerland", "away": "Bosnia & Herzegovina",
        "home_cn": "瑞士", "away_cn": "波黑",
        "time": "2026-06-19 12:00",
        "odds_home": 1.65, "odds_draw": 3.60, "odds_away": 6.00,
        "ou_line": 2.5, "odds_over": 1.75, "odds_under": 2.10,
        "home_xg": 1.60, "away_xg": 0.95,
        "home_poss": 54, "away_poss": 46,
        "stage": "group", "first_match": False,
        "home_region": "europe", "away_region": "europe",
        "home_exp": "experienced", "away_exp": "experienced"
    },
    {
        "match_id": "WC2026-A2-004", "group": "A",
        "home": "Mexico", "away": "Korea Republic",
        "home_cn": "墨西哥", "away_cn": "韩国",
        "time": "2026-06-19 12:00",
        "odds_home": 1.85, "odds_draw": 3.40, "odds_away": 4.20,
        "ou_line": 2.5, "odds_over": 1.80, "odds_under": 2.05,
        "home_xg": 1.55, "away_xg": 1.15,
        "home_poss": 50, "away_poss": 50,
        "stage": "group", "first_match": False,
        "home_region": "north_america", "away_region": "asia",
        "home_exp": "experienced", "away_exp": "experienced"
    }
]

print("=" * 70)
print("🔮 2026世界杯预测报告 - 6月19日 (A组+B组 第二轮)")
print("=" * 70)
print()

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

        kelly = result.get("kelly", {})
        kelly_bets = kelly.get("recommendations", [])

        print(f"📌 {m['home_cn']} vs {m['away_cn']} ({m['group']}组)")
        print(f"   时间: {m['time']} (北京时间)")
        print(f"   模型概率: 主{home_prob:.1%}/平{draw_prob:.1%}/客{away_prob:.1%}")
        print(f"   预测1X2: {pred_1x2}")
        print(f"   预测OU:  {pred_ou} (λ={ou.get('lambda', 'N/A')})")
        print(f"   冷门评分: {result.get('upset_score', 0)}")
        print(f"   置信度: {result.get('confidence', 0)}")
        
        if kelly_bets:
            print(f"   Kelly推荐:")
            for rec in kelly_bets:
                opp = rec.get('opportunity', {})
                stake = rec.get('stake', {})
                if stake.get('action') == 'bet':
                    print(f"     [BET] {opp.get('selection', 'N/A')}: ${stake.get('stake', 0):.2f} (Kelly: {stake.get('kelly_pct', 0)}%, EV: {stake.get('expected_value', 0):.1f}%)")
        print()
    except Exception as e:
        import traceback
        print(f"📌 {m['home_cn']} vs {m['away_cn']} - 错误: {e}")
        print()

print("=" * 70)
