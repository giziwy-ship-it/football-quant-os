#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
France vs Senegal - 2026 World Cup Prediction
Fixed encoding for Windows terminal
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import numpy as np
from scipy.stats import poisson
from v4.core.physical_ai import PhysicalAI, TeamState
from v4.scripts.validate_xg_hybrid import create_team_state

# Market odds (oddsportal composite)
ODDS_1X2 = {"home": 1.47, "draw": 4.55, "away": 7.10}
ODDS_OU = {"over_2.5": 2.15, "under_2.5": 1.70}

def implied_prob(odds):
    raw = {k: 1/v for k, v in odds.items()}
    total = sum(raw.values())
    return {k: v/total for k, v in raw.items()}

prob_1x2 = implied_prob(ODDS_1X2)

# v4 model prediction
france = create_team_state("FRA", is_home=True)
senegal = create_team_state("SEN", is_home=False)

ai = PhysicalAI()
ai.layer_weights = {"mechanics": 2.0, "field": 0.0, "entropy": 2.0, "coach": 0.0, "market": 0.0}
ai.draw_boost = 0.8

result = ai.predict(france, senegal)
model_probs = result["probabilities"]

# Bayesian fusion: model 60%, market 40%
MODEL_WEIGHT = 0.6
MARKET_WEIGHT = 0.4

fused = {
    "home": model_probs["home"] * MODEL_WEIGHT + prob_1x2["home"] * MARKET_WEIGHT,
    "draw": model_probs["draw"] * MODEL_WEIGHT + prob_1x2["draw"] * MARKET_WEIGHT,
    "away": model_probs["away"] * MODEL_WEIGHT + prob_1x2["away"] * MARKET_WEIGHT
}
total = sum(fused.values())
fused = {k: v/total for k, v in fused.items()}

# Expected goals
lambda_fra = france.attack * 2.5 * (1 - senegal.defense * 0.5)
lambda_sen = senegal.attack * 2.5 * (1 - france.defense * 0.5)
total_lambda = lambda_fra + lambda_sen

# Correct score probabilities
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

# Output with ASCII-safe formatting
print("=" * 60)
print("FRANCE vs SENEGAL - 2026 World Cup Prediction")
print("=" * 60)
print("Match: France vs Senegal | 2026-06-17 03:00")
print("")

print("[1. 1X2 / Sheng Ping Fu]")
print(f"  Model:     FRA {model_probs['home']:.1%} | Draw {model_probs['draw']:.1%} | SEN {model_probs['away']:.1%}")
print(f"  Market:    FRA {prob_1x2['home']:.1%} | Draw {prob_1x2['draw']:.1%} | SEN {prob_1x2['away']:.1%}")
print(f"  Fused:     FRA {fused['home']:.1%} | Draw {fused['draw']:.1%} | SEN {fused['away']:.1%}")
print(f"  PICK:      France Win ({fused['home']:.1%})")
print(f"  Confidence: {'HIGH' if fused['home'] > 0.55 else 'MEDIUM'}")
print("")

print("[2. Asian Handicap]")
print(f"  Expected xG: FRA {lambda_fra:.2f} | SEN {lambda_sen:.2f}")
print(f"  FRA -1.5:  Needs 2+ goal win (risky)")
print(f"  PICK:      FRA -1 (Asian) - safer, lose half if 1-goal win")
print("")

print("[3. HT/FT (Half/Full Time)]")
ht_fra = fused["home"] * 0.85
ht_draw = 0.35
print(f"  HT probs:  FRA {ht_fra:.1%} | Draw {ht_draw:.1%} | SEN {fused['away']*0.85:.1%}")
print(f"  PICK:      Draw/France (HT draw, FT France win) - {ht_draw*fused['home']:.1%}")
print(f"  ALT:       France/France - {ht_fra*fused['home']:.1%}")
print("")

print("[4. Correct Score]")
print(f"  Expected xG: FRA {lambda_fra:.2f} | SEN {lambda_sen:.2f}")
for f, s, p in scores[:6]:
    print(f"    {f}-{s}: {p:.1%}")
print(f"  PICK:      {scores[0][0]}-{scores[0][1]} or {scores[1][0]}-{scores[1][1]}")
print("")

print("[5. Total Goals]")
print(f"  Expected total: {total_lambda:.2f}")
for n in range(5):
    print(f"    {n} goals: {poisson.pmf(n, total_lambda):.1%}")
print(f"  PICK:      2-3 goals ({poisson.pmf(2,total_lambda)+poisson.pmf(3,total_lambda):.1%})")
print("")

print("[6. Over/Under 2.5]")
print(f"  Over 2.5:  {p_over_2_5:.1%} (odds {ODDS_OU['over_2.5']})")
print(f"  Under 2.5: {p_under_2_5:.1%} (odds {ODDS_OU['under_2.5']})")
print(f"  PICK:      Under 2.5 ({p_under_2_5:.1%})")
print("")

print("[7. BTTS (Both Teams To Score)]")
print(f"  FRA scores: {p_fra_scores:.1%}")
print(f"  SEN scores: {p_sen_scores:.1%}")
print(f"  BTTS Yes:   {p_btts:.1%}")
print(f"  PICK:      BTTS - No ({1-p_btts:.1%})")
print("")

print("=" * 60)
print("[FINAL PICKS]")
print("=" * 60)
print(f"  1X2:        France Win")
print(f"  Handicap:   France -1 (Asian)")
print(f"  HT/FT:      Draw/France")
print(f"  Score:      1-0 or 2-0")
print(f"  O/U:        Under 2.5")
print(f"  BTTS:       No")
print(f"  Total:      2 goals")
print("")
print(f"  Confidence: {'HIGH' if fused['home'] > 0.6 else 'MEDIUM'}")
print(f"  Risk:       Senegal AFCON champs, defends well, upset possible")
print("=" * 60)
