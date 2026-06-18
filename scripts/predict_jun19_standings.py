#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prediction with GROUP STANDINGS for 2026-06-19 matches
Compare: with vs without group context
"""

import sys, os, json

sys.stdout.reconfigure(encoding='utf-8')
os.chdir(r"D:\openclaw-workspace\football_quant_os")
sys.path.insert(0, r"D:\openclaw-workspace\football_quant_os\scripts")
sys.path.insert(0, r"D:\openclaw-workspace\football_quant_os")

from predict import run_prediction

# ===== REAL GROUP STANDINGS AFTER ROUND 1 =====
group_standings = {
    'A': {
        'Mexico': {'played': 1, 'won': 1, 'drawn': 0, 'lost': 0, 'gf': 2, 'ga': 0, 'points': 3, 'gd': 2},
        'Korea Republic': {'played': 1, 'won': 1, 'drawn': 0, 'lost': 0, 'gf': 2, 'ga': 1, 'points': 3, 'gd': 1},
        'Czechia': {'played': 1, 'won': 0, 'drawn': 0, 'lost': 1, 'gf': 1, 'ga': 2, 'points': 0, 'gd': -1},
        'South Africa': {'played': 1, 'won': 0, 'drawn': 0, 'lost': 1, 'gf': 0, 'ga': 2, 'points': 0, 'gd': -2},
    },
    'B': {
        'Switzerland': {'played': 1, 'won': 0, 'drawn': 1, 'lost': 0, 'gf': 1, 'ga': 1, 'points': 1, 'gd': 0},
        'Canada': {'played': 1, 'won': 0, 'drawn': 1, 'lost': 0, 'gf': 1, 'ga': 1, 'points': 1, 'gd': 0},
        'Bosnia & Herzegovina': {'played': 1, 'won': 0, 'drawn': 1, 'lost': 0, 'gf': 1, 'ga': 1, 'points': 1, 'gd': 0},
        'Qatar': {'played': 1, 'won': 0, 'drawn': 1, 'lost': 0, 'gf': 1, 'ga': 1, 'points': 1, 'gd': 0},
    }
}

matches = [
    {
        "home": "Czechia", "away": "South Africa", "group": "A",
        "home_cn": "捷克", "away_cn": "南非", "time": "00:00",
        "odds_home": 1.80, "odds_draw": 3.30, "odds_away": 4.10,
        "ou_line": 2.25, "odds_over": 1.00, "odds_under": 0.80,
        "home_xg": 1.60, "away_xg": 0.85,
        "home_poss": 54, "away_poss": 46,
    },
    {
        "home": "Canada", "away": "Qatar", "group": "B",
        "home_cn": "加拿大", "away_cn": "卡塔尔", "time": "03:00",
        "odds_home": 1.75, "odds_draw": 3.50, "odds_away": 5.00,
        "ou_line": 2.5, "odds_over": 1.80, "odds_under": 2.05,
        "home_xg": 1.50, "away_xg": 0.90,
        "home_poss": 52, "away_poss": 48,
    },
    {
        "home": "Switzerland", "away": "Bosnia & Herzegovina", "group": "B",
        "home_cn": "瑞士", "away_cn": "波黑", "time": "12:00",
        "odds_home": 1.65, "odds_draw": 3.60, "odds_away": 6.00,
        "ou_line": 2.5, "odds_over": 1.75, "odds_under": 2.10,
        "home_xg": 1.55, "away_xg": 0.85,
        "home_poss": 55, "away_poss": 45,
    },
    {
        "home": "Mexico", "away": "Korea Republic", "group": "A",
        "home_cn": "墨西哥", "away_cn": "韩国", "time": "12:00",
        "odds_home": 1.85, "odds_draw": 3.40, "odds_away": 4.20,
        "ou_line": 2.5, "odds_over": 1.80, "odds_under": 2.05,
        "home_xg": 1.50, "away_xg": 1.10,
        "home_poss": 50, "away_poss": 50,
    },
]

def get_pred(m, use_standings=False):
    kwargs = {
        'home': m['home'], 'away': m['away'],
        'odds_home': m['odds_home'], 'odds_draw': m['odds_draw'], 'odds_away': m['odds_away'],
        'stage': 'group', 'ou_line': m['ou_line'],
        'odds_over': m['odds_over'], 'odds_under': m['odds_under'],
        'home_xg': m['home_xg'], 'away_xg': m['away_xg'],
        'home_poss': m['home_poss'], 'away_poss': m['away_poss'],
        'is_first_match': False,
        'home_region': 'europe' if m['home'] in ['Czechia','Switzerland'] else 'north_america',
        'away_region': 'africa' if m['away'] == 'South Africa' else 'asia' if m['away'] in ['Qatar','Korea Republic'] else 'europe',
        'home_experience': 'experienced', 'away_experience': 'experienced',
    }
    if use_standings:
        kwargs['group_standings'] = group_standings
    return run_prediction(**kwargs)

def extract_probs(result):
    m1x2 = result.get('markets', {}).get('1x2', {})
    model = m1x2.get('model', {}) if isinstance(m1x2.get('model'), dict) else {}
    return model.get('home', 0), model.get('draw', 0), model.get('away', 0)

print("=" * 75)
print("🔮 2026世界杯预测 - 6月19日 (A组+B组 第二轮)")
print("=" * 75)
print("📊 对比: [无积分] vs [有积分 - 第一轮后]")
print()

for m in matches:
    print(f"📌 {m['home_cn']} vs {m['away_cn']} ({m['group']}组 · {m['time']})")
    
    # Without standings
    r1 = get_pred(m, False)
    h1, d1, a1 = extract_probs(r1)
    
    # With standings
    r2 = get_pred(m, True)
    h2, d2, a2 = extract_probs(r2)
    
    # Determine predictions
    pred1 = '主胜' if h1 >= d1 and h1 >= a1 else '客胜' if a1 >= h1 and a1 >= d1 else '平局'
    pred2 = '主胜' if h2 >= d2 and h2 >= a2 else '客胜' if a2 >= h2 and a2 >= d2 else '平局'
    
    # Show comparison
    print(f"   [无积分]  主{h1:.1%}/平{d1:.1%}/客{a1:.1%} → {pred1}")
    print(f"   [有积分]  主{h2:.1%}/平{d2:.1%}/客{a2:.1%} → {pred2}")
    
    if pred1 != pred2:
        print(f"   ⚠️ 方向变化! 积分因素导致预测反转")
    
    # Context info
    gs = group_standings.get(m['group'], {})
    home_stats = gs.get(m['home'], {})
    away_stats = gs.get(m['away'], {})
    print(f"   积分背景: {m['home_cn']} {home_stats.get('points',0)}分 | {m['away_cn']} {away_stats.get('points',0)}分")
    print()

print("=" * 75)
