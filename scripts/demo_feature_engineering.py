#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - Feature Engineering Demo

Demonstrate how to extract features from historical data for Over/Under modeling
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from features.feature_engineer import FeatureEngineer


def demo():
    """Feature engineering demo"""
    print("=" * 60)
    print("Feature Engineering Demo - Historical Data for OU Modeling")
    print("=" * 60)
    
    # Mock data for demonstration
    matches = [
        {'home': 'Germany', 'away': 'Japan', 'home_score': 1, 'away_score': 2, 'home_xg': 2.3, 'away_xg': 0.8},
        {'home': 'Spain', 'away': 'Costa Rica', 'home_score': 7, 'away_score': 0, 'home_xg': 4.5, 'away_xg': 0.3},
        {'home': 'Brazil', 'away': 'Serbia', 'home_score': 2, 'away_score': 0, 'home_xg': 2.8, 'away_xg': 0.5},
        {'home': 'Germany', 'away': 'Spain', 'home_score': 1, 'away_score': 1, 'home_xg': 1.2, 'away_xg': 1.8},
        {'home': 'Japan', 'away': 'Spain', 'home_score': 2, 'away_score': 1, 'home_xg': 1.5, 'away_xg': 2.0},
        {'home': 'Germany', 'away': 'Costa Rica', 'home_score': 4, 'away_score': 2, 'home_xg': 3.5, 'away_xg': 1.0},
    ]
    
    print(f"\nLoaded {len(matches)} matches (mock data)")
    
    # Create feature engineer
    engineer = FeatureEngineer(matches)
    print("Feature engineer ready")
    
    # Extract team features
    print("\n" + "-" * 40)
    print("Team Features:")
    print("-" * 40)
    
    for team in ['Germany', 'Japan', 'Spain']:
        f = engineer.extract_team_features(team)
        print(f"\n{team}:")
        print(f"  Avg goals scored: {f.avg_goals_scored}")
        print(f"  Avg goals conceded: {f.avg_goals_conceded}")
        print(f"  Avg xG: {f.avg_xg}")
        print(f"  Recent form: {f.recent_form}")
        print(f"  Attack efficiency: {f.attack_efficiency}")
        print(f"  Defense efficiency: {f.defense_efficiency}")
    
    # Extract match features
    print("\n" + "-" * 40)
    print("Match Features (Germany vs Japan):")
    print("-" * 40)
    
    mf = engineer.extract_match_features('Germany', 'Japan')
    
    print("\nInteraction features:")
    for key, value in mf['interaction'].items():
        print(f"  {key}: {value}")
    
    print("\nHead-to-head:")
    h2h = mf['head_to_head']
    print(f"  Total matches: {h2h['matches']}")
    print(f"  Avg total goals: {h2h['avg_total_goals']}")
    
    # Build training data
    print("\n" + "-" * 40)
    print("Training Data:")
    print("-" * 40)
    
    training_data = engineer.build_training_data(lookback=3)
    print(f"Generated {len(training_data)} training samples")
    
    if training_data:
        sample = training_data[0]
        print(f"\nSample:")
        print(f"  Total goals: {sample['label']['total_goals']}")
        print(f"  Over 2.5: {sample['label']['over_2_5']}")
    
    # Feature importance
    print("\n" + "-" * 40)
    print("Feature Importance (reference):")
    print("-" * 40)
    
    importance = engineer.get_feature_importance([])
    for feature, score in sorted(importance.items(), key=lambda x: x[1], reverse=True):
        bar = "#" * int(score * 20)
        print(f"  {feature:20s}: {score:.2f} {bar}")
    
    print("\n" + "=" * 60)
    print("Feature engineering demo complete!")
    print("=" * 60)
    
    return engineer, training_data


if __name__ == '__main__':
    demo()
