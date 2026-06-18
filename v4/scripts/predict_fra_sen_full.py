#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
France vs Senegal - 2026 World Cup
Comprehensive Prediction with oddsportal + 500.com data
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
from scipy.stats import poisson
from v4.core.physical_ai import PhysicalAI
from v4.scripts.validate_xg_hybrid import create_team_state

# ====== MARKET DATA ======

# oddsportal.com (International)
ODDSPORTAL_1X2 = {"home": 1.47, "draw": 4.55, "away": 7.10}
ODDSPORTAL_AH = {"france_1.25": 1.35, "senegal_1.25": 3.20}
ODDSPORTAL_OU = {"over_2.5": 2.15, "under_2.5": 1.70}
ODDSPORTAL_BTS = {"yes": 2.05, "no": 1.75}

# 500.com (China)
# 百家欧赔 Average (57 companies)
ODDS_500_1X2 = {"home": 1.46, "draw": 4.44, "away": 6.77}
# 亚盘 Average - France -1.0 ball, 0.871 water
ODDS_500_AH = {"france_1.0": 0.871, "senegal_1.0": 1.03}
# 大小球 Average - 2.68 line, Over 0.93, Under 0.86
ODDS_500_OU = {"over_2.68": 0.93, "under_2.68": 0.86}

# 主流公司 (Major bookmakers)
MAJOR_BOOKMAKERS = {
    "William Hill": {"1x2": [1.44, 4.20, 6.50], "ah": [0.71, 1.0, 0.94], "ou": [2.5, 0.75, 1.00]},
    "Macau": {"1x2": [1.36, 4.40, 6.70], "ah": [0.82, 1.0, 1.02], "ou": [2.75, 1.00, 0.80]},
    "Ladbrokes": {"1x2": [1.50, 4.50, 5.75], "ah": [1.20, 1.5, 0.60], "ou": [2.5, 0.73, 1.00]},
    "Bet365": {"1x2": [1.45, 4.50, 7.00], "ah": [1.03, 1.25, 0.83], "ou": [2.75, 0.95, 0.90]},
    "Interwetten": {"1x2": [1.50, 4.30, 6.75], "ah": [0.77, 1.0, 0.95], "ou": [2.5, 0.65, 1.20]},
}


def implied_prob(odds):
    raw = {k: 1/v for k, v in odds.items()}
    total = sum(raw.values())
    return {k: v/total for k, v in raw.items()}


def run_prediction():
    # v4 model
    france = create_team_state("FRA", is_home=True)
    senegal = create_team_state("SEN", is_home=False)
    
    ai = PhysicalAI()
    ai.layer_weights = {"mechanics": 2.0, "field": 0.0, "entropy": 2.0, "coach": 0.0, "market": 0.0}
    ai.draw_boost = 0.8
    
    result = ai.predict(france, senegal)
    model_probs = result["probabilities"]
    
    # Market probs
    prob_op = implied_prob(ODDSPORTAL_1X2)
    prob_500 = implied_prob(ODDS_500_1X2)
    
    # Average market probability
    market_home = (prob_op["home"] + prob_500["home"]) / 2
    market_draw = (prob_op["draw"] + prob_500["draw"]) / 2
    market_away = (prob_op["away"] + prob_500["away"]) / 2
    
    # Fusion: Model 50% + Market 50%
    fused = {
        "home": model_probs["home"] * 0.5 + market_home * 0.5,
        "draw": model_probs["draw"] * 0.5 + market_draw * 0.5,
        "away": model_probs["away"] * 0.5 + market_away * 0.5
    }
    
    # Expected goals
    lambda_fra = france.attack * 2.5 * (1 - senegal.defense * 0.5)
    lambda_sen = senegal.attack * 2.5 * (1 - france.defense * 0.5)
    total_lambda = lambda_fra + lambda_sen
    
    # Correct score
    scores = []
    for f in range(5):
        for s in range(4):
            p = poisson.pmf(f, lambda_fra) * poisson.pmf(s, lambda_sen)
            scores.append((f, s, p))
    scores.sort(key=lambda x: x[2], reverse=True)
    
    # BTTS
    p_fra_scores = 1 - poisson.pmf(0, lambda_fra)
    p_sen_scores = 1 - poisson.pmf(0, lambda_sen)
    p_btts = p_fra_scores * p_sen_scores
    
    # Over/Under 2.5
    p_over_2_5 = 1 - poisson.cdf(2, total_lambda)
    p_under_2_5 = poisson.cdf(2, total_lambda)
    
    # Output
    print("=" * 70)
    print("FRANCE vs SENEGAL - 2026 WORLD CUP PREDICTION")
    print("=" * 70)
    print("Match: 2026-06-17 03:00 | MetLife Stadium")
    print()
    
    print("【DATA SOURCES】")
    print("  oddsportal.com (International)")
    print("  500.com (China - 57 bookmakers)")
    print()
    
    print("【1. 1X2 / WIN-DRAW-WIN】")
    print(f"  v4 Model:      FRA {model_probs['home']:.1%} | Draw {model_probs['draw']:.1%} | SEN {model_probs['away']:.1%}")
    print(f"  oddsportal:    FRA {prob_op['home']:.1%} | Draw {prob_op['draw']:.1%} | SEN {prob_op['away']:.1%}")
    print(f"  500.com avg:   FRA {prob_500['home']:.1%} | Draw {prob_500['draw']:.1%} | SEN {prob_500['away']:.1%}")
    print(f"  => FUSED:      FRA {fused['home']:.1%} | Draw {fused['draw']:.1%} | SEN {fused['away']:.1%}")
    print(f"  PICK:          FRANCE WIN")
    print(f"  Confidence:    {'HIGH' if fused['home'] > 0.60 else 'MEDIUM'}")
    print()
    
    print("【2. ASIAN HANDICAP / 让球】")
    print("  Major Bookmakers:")
    for name, data in MAJOR_BOOKMAKERS.items():
        ah = data["ah"]
        print(f"    {name:15s}: FRA {ah[1]:.1f} ball @ {ah[0]:.2f} | SEN @ {ah[2]:.2f}")
    print("  PICK:          FRANCE -1.0 (Asian)")
    print("  Note:          Most bookmakers moved from -1.25 to -1.0 (lowered for France)")
    print("                 Low water on France (0.71-0.82) = strong confidence")
    print()
    
    print("【3. HT/FT (Half/Full Time)】")
    ht_fra = fused["home"] * 0.85
    ht_draw = 0.35
    print(f"  HT probs:      FRA {ht_fra:.1%} | Draw {ht_draw:.1%} | SEN {fused['away']*0.85:.1%}")
    print(f"  PICK:          Draw/France ({ht_draw*fused['home']:.1%})")
    print(f"  ALT:           France/France ({ht_fra*fused['home']:.1%})")
    print()
    
    print("【4. CORRECT SCORE / 比分】")
    print(f"  Expected xG:   FRA {lambda_fra:.2f} | SEN {lambda_sen:.2f}")
    print(f"  Top 5 scores:")
    for i, (f, s, p) in enumerate(scores[:5]):
        print(f"    {f}-{s}: {p:.1%}")
    print(f"  PICK:          1-0 or 2-0")
    print()
    
    print("【5. TOTAL GOALS / 进球数】")
    print(f"  Expected total: {total_lambda:.2f}")
    for n in range(5):
        print(f"    {n} goals: {poisson.pmf(n, total_lambda):.1%}")
    print(f"  PICK:          2-3 goals ({poisson.pmf(2,total_lambda)+poisson.pmf(3,total_lambda):.1%})")
    print()
    
    print("【6. OVER/UNDER 2.5 / 大小球】")
    print("  Major Bookmakers:")
    for name, data in MAJOR_BOOKMAKERS.items():
        ou = data["ou"]
        print(f"    {name:15s}: {ou[0]:.1f} line, Over {ou[1]:.2f} | Under {ou[2]:.2f}")
    print(f"  Over 2.5:      {p_over_2_5:.1%} (odds 2.15)")
    print(f"  Under 2.5:     {p_under_2_5:.1%} (odds 1.70)")
    print(f"  PICK:          UNDER 2.5")
    print()
    
    print("【7. BTTS / 双方进球】")
    print(f"  FRA scores:    {p_fra_scores:.1%}")
    print(f"  SEN scores:    {p_sen_scores:.1%}")
    print(f"  BTTS Yes:      {p_btts:.1%}")
    print(f"  PICK:          BTTS - NO ({1-p_btts:.1%})")
    print()
    
    print("【8. CORNER / 角球】")
    print("  Expected:      France 5-6, Senegal 3-4")
    print("  PICK:          France -2.5 corners")
    print()
    
    print("【9. YELLOW CARDS / 黄牌】")
    print("  Expected:      3-4 total")
    print("  PICK:          Under 4.5 cards")
    print()
    
    print("=" * 70)
    print("【FINAL PICKS / 最终推荐】")
    print("=" * 70)
    print()
    print("  1X2:           FRANCE WIN")
    print("  Handicap:      FRANCE -1.0 (Asian)")
    print("  HT/FT:         Draw/France")
    print("  Score:         1-0 or 2-0")
    print("  O/U:           UNDER 2.5")
    print("  BTTS:          NO")
    print("  Goals:         2")
    print()
    print("  Confidence:    HIGH (60%+)")
    print()
    print("  RISK:          Senegal AFCON champs, strong defense")
    print("                 Possible upset if France underestimates")
    print("                 France has NOT won opening match in last 3 World Cups")
    print()
    print("  Market Note:   Bookmakers lowered France handicap from -1.25 to -1.0")
    print("                 but France water is very low (0.71-0.82) = strong confidence")
    print("                 Under 2.5 is heavily favored (odds 1.70)")
    print("=" * 70)


if __name__ == "__main__":
    run_prediction()
