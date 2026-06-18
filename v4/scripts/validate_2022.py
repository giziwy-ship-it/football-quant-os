#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V4 Model Validation - 2022 World Cup Detailed Analysis
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import pandas as pd
from pathlib import Path

from v4.core.physical_ai import PhysicalAI, TeamState, MarketState
from v4.scripts.train_v4 import V4Trainer, load_historical_data

# 加载训练好的权重
with open("D:/openclaw-workspace/football_quant_os/v4/data/trained_weights.json", 'r') as f:
    weights = json.load(f)["layer_weights"]

# 创建AI
ai = PhysicalAI()
ai.layer_weights = weights

# 加载数据
df = load_historical_data()

# 准备特征（使用所有历史数据）
trainer = V4Trainer()
trainer.prepare_data(df)

# 加载2022数据
with open("D:/openclaw-workspace/football_quant_os/data/worldcup2022_data.json", 'r') as f:
    wc2022 = json.load(f)

matches = wc2022.get("group_stage", []) + wc2022.get("knockout_stage", [])

# 分析预测
correct = 0
total = 0
pred_dist = {"home": 0, "draw": 0, "away": 0}
actual_dist = {"home": 0, "draw": 0, "away": 0}
brier_scores = []

print("=== 2022 World Cup - Match by Match Analysis ===\n")

for m in matches:
    home_name = m['home']
    away_name = m['away']
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
        home, away = trainer.match_to_features(home_name, away_name)
        result = ai.predict(home, away)
        probs = result["probabilities"]
        
        pred = max(probs, key=probs.get)
        pred_dist[pred] += 1
        
        is_correct = pred == actual
        if is_correct:
            correct += 1
        total += 1
        
        # Brier
        actual_vec = {"home": 0, "draw": 0, "away": 0}
        actual_vec[actual] = 1
        brier = sum((probs[k] - actual_vec[k]) ** 2 for k in probs) / 3
        brier_scores.append(brier)
        
        marker = "OK" if is_correct else "XX"
        print(f"{marker} {home_name} {h_score}-{a_score} {away_name}")
        print(f"   Pred: {pred} | Actual: {actual}")
        print(f"   Probs: H={probs['home']:.2f} D={probs['draw']:.2f} A={probs['away']:.2f} | Brier={brier:.3f}")
        
    except Exception as e:
        print(f"SKIP {home_name} vs {away_name}: {e}")

print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print(f"Total matches analyzed: {total}")
print(f"Correct predictions: {correct}")
print(f"Accuracy: {correct/total:.1%}" if total > 0 else "N/A")
print(f"Avg Brier: {sum(brier_scores)/len(brier_scores):.4f}" if brier_scores else "N/A")
print(f"\nPrediction distribution: {pred_dist}")
print(f"Actual distribution: {actual_dist}")

# 按阶段分析
print("\n=== By Stage ===")
for stage_name, stage_matches in [("Group", wc2022.get("group_stage", [])), 
                                   ("Knockout", wc2022.get("knockout_stage", []))]:
    stage_correct = 0
    stage_total = 0
    for m in stage_matches:
        h_score = m.get('home_score', 0)
        a_score = m.get('away_score', 0)
        if h_score > a_score:
            actual = "home"
        elif h_score < a_score:
            actual = "away"
        else:
            actual = "draw"
        
        try:
            home, away = trainer.match_to_features(m['home'], m['away'])
            result = ai.predict(home, away)
            pred = max(result["probabilities"], key=result["probabilities"].get)
            if pred == actual:
                stage_correct += 1
            stage_total += 1
        except:
            pass
    
    if stage_total > 0:
        print(f"{stage_name}: {stage_correct}/{stage_total} = {stage_correct/stage_total:.1%}")
