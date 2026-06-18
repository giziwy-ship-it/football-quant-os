#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V4 xG-enhanced Training
Use 2022 xG data to create more accurate team power mapping
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json, numpy as np
from pathlib import Path
from v4.core.physical_ai import PhysicalAI, TeamState

# Load xG stats
with open("D:/openclaw-workspace/football_quant_os/v4/data/wc2022_xg_stats.json", 'r') as f:
    xg_stats = json.load(f)

# Team name mapping
TEAM_MAP = {
    "GERMANY": "GER", "BRAZIL": "BRA", "ECUADOR": "ECU", "ARGENTINA": "ARG",
    "MEXICO": "MEX", "ENGLAND": "ENG", "SPAIN": "ESP", "FRANCE": "FRA",
    "MOROCCO": "MAR", "PORTUGAL": "POR", "QATAR": "QAT", "SWITZERLAND": "SUI",
    "URUGUAY": "URU", "UNITED STATES": "USA", "CROATIA": "CRO", "JAPAN": "JPN",
    "TUNISIA": "TUN", "POLAND": "POL", "IRAN": "IRN", "SENEGAL": "SEN",
    "DENMARK": "DEN", "GHANA": "GHA", "KOREA REPUBLIC": "KOR", "WALES": "WAL",
    "CAMEROON": "CMR", "NETHERLANDS": "NED", "CANADA": "CAN", "BELGIUM": "BEL",
    "AUSTRALIA": "AUS", "SERBIA": "SRB", "SAUDI ARABIA": "KSA", "COSTA RICA": "CRC",
}

# xG-based power mapping (attack from xG, defense from xGA)
def get_xg_power(team_code):
    """Get team power based on 2022 xG data"""
    # Find team in xg_stats
    for full_name, code in TEAM_MAP.items():
        if code == team_code or full_name == team_code:
            if full_name in xg_stats:
                stats = xg_stats[full_name]
                
                # Attack: xG per match (0.47 to 3.37)
                xg = stats['xg']
                # Normalize to 0.3-0.95
                attack = 0.3 + (xg - 0.47) / (3.37 - 0.47) * 0.65
                
                # Defense: 1 - xGA per match (inverse, higher=better defense)
                xga = stats['xga']
                # Normalize xGA (0.17 to 3.37), lower is better
                defense = 0.95 - (xga - 0.17) / (3.37 - 0.17) * 0.65
                
                # Tournament gene: based on xG difference
                xg_diff = stats['xg_diff']
                # Top 8: >0.5, 8-16: 0 to 0.5, bottom: <0
                if xg_diff > 0.5:
                    tournament_gene = 0.85
                elif xg_diff > 0:
                    tournament_gene = 0.65
                else:
                    tournament_gene = 0.40
                
                # Elo: from FIFA ranking (approximate)
                # Top 10 avg ~1700, bottom ~1400
                elo = 1400 + (xg_diff + 2.9) / 5.14 * 450
                
                return {
                    "attack": max(0.30, min(0.95, attack)),
                    "defense": max(0.30, min(0.95, defense)),
                    "elo": elo,
                    "tournament_gene": tournament_gene,
                    "xg": xg,
                    "xga": xga
                }
    
    # Fallback: FIFA ranking based (from train_full_v4)
    return None


def create_team_state_xg(team_code, is_home=False):
    """Create team state using xG-based power"""
    power = get_xg_power(team_code)
    
    if power is None:
        # Fallback to FIFA ranking
        from v4.scripts.train_full_v4 import get_team_power
        power = get_team_power(team_code)
    
    return TeamState(
        attack=power["attack"],
        defense=power["defense"],
        form=0.5,
        fatigue=0.0,
        morale=0.5,
        home_advantage=0.05 if is_home else 0.0,
        elo=power["elo"],
        xg_for=power.get("xg", power["attack"] * 2.5),
        xg_against=power.get("xga", (1 - power["defense"]) * 2.0),
        coach_factor=0.0,
        tournament_gene=power["tournament_gene"]
    )


def run_2022_validation():
    """Validate on 2022 using xG-based power"""
    with open("D:/openclaw-workspace/football_quant_os/data/worldcup2022_data.json", 'r') as f:
        wc2022 = json.load(f)
    
    matches = wc2022.get("group_stage", []) + wc2022.get("knockout_stage", [])
    
    ai = PhysicalAI()
    ai.layer_weights = {"mechanics": 2.0, "field": 0.0, "entropy": 2.0, "coach": 0.0, "market": 0.0}
    ai.draw_boost = 0.8
    
    correct = 0
    total = 0
    pred_dist = {"home": 0, "draw": 0, "away": 0}
    actual_dist = {"home": 0, "draw": 0, "away": 0}
    brier_scores = []
    
    for m in matches:
        h_score = m.get('home_score', 0)
        a_score = m.get('away_score', 0)
        
        if h_score > a_score:
            actual = "home"
        elif h_score < a_score:
            actual = "away"
        else:
            actual = "draw"
        
        actual_dist[actual] += 1
        
        try:
            home = create_team_state_xg(m['home'], is_home=True)
            away = create_team_state_xg(m['away'], is_home=False)
            
            result = ai.predict(home, away)
            probs = result["probabilities"]
            pred = max(probs, key=probs.get)
            
            pred_dist[pred] += 1
            
            if pred == actual:
                correct += 1
            total += 1
            
            actual_vec = {"home": 0, "draw": 0, "away": 0}
            actual_vec[actual] = 1
            brier = sum((probs[k] - actual_vec[k]) ** 2 for k in probs) / 3
            brier_scores.append(brier)
            
            # Debug interesting matches
            if probs['draw'] > 0.35 and actual != 'draw':
                print(f"DRAW_MISS: {m['home']} {h_score}-{a_score} {m['away']} -> Pred:draw Actual:{actual}")
            
        except Exception as e:
            print(f"ERROR: {m['home']} vs {m['away']}: {e}")
    
    acc = correct / total if total > 0 else 0
    avg_brier = sum(brier_scores) / len(brier_scores) if brier_scores else 1.0
    
    print(f"\n{'='*50}")
    print(f"2022 xG-based Validation")
    print(f"{'='*50}")
    print(f"Accuracy: {acc:.1%}")
    print(f"Brier:    {avg_brier:.4f}")
    print(f"Pred:     {pred_dist}")
    print(f"Actual:   {actual_dist}")
    
    return {"accuracy": acc, "brier": avg_brier, "pred_dist": pred_dist, "actual_dist": actual_dist}


if __name__ == "__main__":
    run_2022_validation()
