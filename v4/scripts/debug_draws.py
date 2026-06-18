#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug: Analyze why draws are not predicted in 2022
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
from v4.core.physical_ai import PhysicalAI
from v4.scripts.train_full_v4 import create_team_state

# Load 2022 data
with open("D:/openclaw-workspace/football_quant_os/data/worldcup2022_data.json", 'r') as f:
    wc2022 = json.load(f)

matches = wc2022.get("group_stage", []) + wc2022.get("knockout_stage", [])

# Set optimal weights
ai = PhysicalAI()
ai.layer_weights = {"mechanics": 1.5, "field": 0.0, "entropy": 2.0, "coach": 0.0, "market": 0.0}
ai.draw_boost = 1.5

print("=== 2022 Draw Matches - Signal Analysis ===\n")

for m in matches:
    h_score = m.get('home_score', 0)
    a_score = m.get('away_score', 0)
    
    if h_score != a_score:
        continue
    
    home = create_team_state(m['home'], is_home=True)
    away = create_team_state(m['away'], is_home=False)
    
    result = ai.predict(home, away)
    probs = result["probabilities"]
    pred = max(probs, key=probs.get)
    
    s = result["signals"]["combined"]
    gap = abs(s["home"] - s["away"])
    
    print(f"{m['home']} {h_score}-{a_score} {m['away']} -> Pred: {pred}")
    print(f"   Probs: H={probs['home']:.3f} D={probs['draw']:.3f} A={probs['away']:.3f}")
    print(f"   Signals: home={s['home']:+.3f} away={s['away']:+.3f} gap={gap:.3f}")
    print(f"   Entropy: {result['signals']['entropy']['system']:.3f}")
    print()
