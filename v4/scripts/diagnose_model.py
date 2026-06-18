#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V4 Model Diagnostics - 诊断训练问题
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
val_df = df[df['year'] == 2018].copy()

# 准备特征
trainer = V4Trainer()
trainer.prepare_data(df[df['year'] <= 2014])

# 检查几场具体比赛
print("=== 2018 World Cup Predictions ===\n")

test_matches = [
    ("Russia", "Saudi Arabia", 5, 0, "home"),
    ("Germany", "Mexico", 0, 1, "away"),
    ("Argentina", "Iceland", 1, 1, "draw"),
    ("Brazil", "Switzerland", 1, 1, "draw"),
    ("France", "Argentina", 4, 3, "home"),
]

for home_name, away_name, h_score, a_score, actual in test_matches:
    home, away = trainer.match_to_features(home_name, away_name)
    result = ai.predict(home, away)
    probs = result["probabilities"]
    
    pred = max(probs, key=probs.get)
    correct = "OK" if pred == actual else "WRONG"
    
    print(f"{correct} {home_name} vs {away_name}")
    print(f"   Actual: {actual} | Predicted: {pred}")
    print(f"   Probs:  H={probs['home']:.2f} D={probs['draw']:.2f} A={probs['away']:.2f}")
    print(f"   Signals: mech={result['signals']['mechanics']['home']:+.2f}/{result['signals']['mechanics']['away']:+.2f}")
    print()

# 检查特征提取
print("\n=== Team Feature Check ===")
for team in ["Germany", "Brazil", "Russia", "Saudi Arabia", "Mexico"]:
    f = trainer.extractor.get_team_features(team)
    print(f"{team}: attack={f['attack']:.2f} defense={f['defense']:.2f} gene={f['tournament_gene']:.2f}")

# 分析为什么准确率低
print("\n=== Analysis ===")
print(f"Total 2018 matches: {len(val_df)}")

# 统计预测分布
pred_counts = {"home": 0, "draw": 0, "away": 0}
actual_counts = {"home": 0, "draw": 0, "away": 0}

for _, row in val_df.iterrows():
    home_name = row['home_team']
    away_name = row['away_team']
    h_score = row['home_score']
    a_score = row['away_score']
    
    if h_score > a_score:
        actual = "home"
    elif h_score < a_score:
        actual = "away"
    else:
        actual = "draw"
    
    actual_counts[actual] += 1
    
    try:
        home, away = trainer.match_to_features(home_name, away_name)
        result = ai.predict(home, away)
        pred = max(result["probabilities"], key=result["probabilities"].get)
        pred_counts[pred] += 1
    except:
        pass

print(f"\nPrediction distribution: {pred_counts}")
print(f"Actual distribution:     {actual_counts}")

# 如果总是预测home，说明主场优势权重过高
home_bias = pred_counts["home"] / sum(pred_counts.values())
print(f"\nHome prediction bias: {home_bias:.1%}")
if home_bias > 0.5:
    print("WARNING: Model heavily biased toward home predictions!")
    print("Suggestion: Reduce home_advantage or mechanics weight")
