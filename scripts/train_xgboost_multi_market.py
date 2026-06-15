#!/usr/bin/env python3
"""
Football Quant OS - XGBoost Multi-Market Model Training v2.0

Improvements:
1. Kaggle World Cup data (real xG, possession)
2. XGBoost + LightGBM
3. Feature crossing (interaction features)
4. Combined with Football-Data.org data
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any
from collections import defaultdict

from xgboost import XGBClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score


def load_kaggle_worldcup_data():
    """Load Kaggle 2022 World Cup data with real xG and possession"""
    file_path = 'D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_2022_qatar/Fifa_WC_2022_Match_data.csv'
    
    try:
        df = pd.read_csv(file_path, encoding='latin-1')
        print(f"Loaded Kaggle 2022 WC: {len(df)} matches, {len(df.columns)} columns")
        
        matches = []
        for _, row in df.iterrows():
            match = {
                'home': row.get('1', ''),
                'away': row.get('2', ''),
                'home_score': row.get('1_goals', 0),
                'away_score': row.get('2_goals', 0),
                'home_xg': row.get('1_xg', 0),
                'away_xg': row.get('2_xg', 0),
                'home_poss': row.get('1_poss', 50),
                'away_poss': row.get('2_poss', 50),
                'home_attempts': row.get('1_attempts', 0),
                'away_attempts': row.get('2_attempts', 0),
                'home_conceded': row.get('1_conceded', 0),
                'away_conceded': row.get('2_conceded', 0),
                'stage': 'group' if 'Group' in str(row.get('group', '')) else 'knockout',
                'competition': 'World Cup 2022'
            }
            matches.append(match)
        
        return matches
    except Exception as e:
        print(f"Error loading Kaggle data: {e}")
        return []


def load_football_data():
    """Load Football-Data.org training data"""
    try:
        with open('D:/openclaw-workspace/football_quant_os/data/training/football_data_training.json', 'r') as f:
            data = json.load(f)
        
        # Convert back to match format
        matches = []
        for d in data:
            match = {
                'home': d['home']['team'],
                'away': d['away']['team'],
                'home_score': d.get('home_score', 0),
                'away_score': d.get('away_score', 0),
                'home_xg': d['home'].get('avg_xg', 1.0),
                'away_xg': d['away'].get('avg_xg', 1.0),
                'competition': 'Football-Data'
            }
            matches.append(match)
        
        return matches
    except Exception as e:
        print(f"Error loading football-data: {e}")
        return []


def build_team_stats(matches):
    """Build comprehensive team statistics"""
    stats = defaultdict(lambda: {
        'goals_scored': [], 'goals_conceded': [],
        'xg': [], 'possession': [],
        'attempts': [], 'matches': [],
        'home_matches': [], 'away_matches': [],
        'points': [], 'recent_form': []
    })
    
    for match in matches:
        home = match['home']
        away = match['away']
        
        home_score = match.get('home_score', 0)
        away_score = match.get('away_score', 0)
        home_xg = match.get('home_xg', 0)
        away_xg = match.get('away_xg', 0)
        home_poss = match.get('home_poss', 50)
        away_poss = match.get('away_poss', 50)
        
        # Points
        home_points = 3 if home_score > away_score else (1 if home_score == away_score else 0)
        away_points = 3 if away_score > home_score else (1 if home_score == away_score else 0)
        
        # Home team stats
        stats[home]['goals_scored'].append(home_score)
        stats[home]['goals_conceded'].append(away_score)
        stats[home]['xg'].append(home_xg)
        stats[home]['possession'].append(home_poss)
        stats[home]['points'].append(home_points)
        stats[home]['matches'].append(match)
        stats[home]['home_matches'].append(match)
        
        # Away team stats
        stats[away]['goals_scored'].append(away_score)
        stats[away]['goals_conceded'].append(home_score)
        stats[away]['xg'].append(away_xg)
        stats[away]['possession'].append(away_poss)
        stats[away]['points'].append(away_points)
        stats[away]['matches'].append(match)
        stats[away]['away_matches'].append(match)
    
    return stats


def extract_features_v2(match, team_stats, is_kaggle=True):
    """Extract enhanced features with crossing"""
    home = match['home']
    away = match['away']
    
    home_stat = team_stats[home]
    away_stat = team_stats[away]
    
    # Basic stats
    home_goals_scored = np.mean(home_stat['goals_scored']) if home_stat['goals_scored'] else 1.0
    home_goals_conceded = np.mean(home_stat['goals_conceded']) if home_stat['goals_conceded'] else 1.0
    away_goals_scored = np.mean(away_stat['goals_scored']) if away_stat['goals_scored'] else 1.0
    away_goals_conceded = np.mean(away_stat['goals_conceded']) if away_stat['goals_conceded'] else 1.0
    
    # xG stats (if available)
    home_xg = np.mean(home_stat['xg']) if home_stat['xg'] and is_kaggle else 1.0
    away_xg = np.mean(away_stat['xg']) if away_stat['xg'] and is_kaggle else 1.0
    
    # Possession (if available)
    home_poss = np.mean(home_stat['possession']) if home_stat['possession'] and is_kaggle else 50
    away_poss = np.mean(away_stat['possession']) if away_stat['possession'] and is_kaggle else 50
    
    # Recent form (last 5 matches)
    home_form = np.mean(home_stat['points'][-5:]) if len(home_stat['points']) >= 5 else np.mean(home_stat['points']) if home_stat['points'] else 1.5
    away_form = np.mean(away_stat['points'][-5:]) if len(away_stat['points']) >= 5 else np.mean(away_stat['points']) if away_stat['points'] else 1.5
    
    # Home/away advantage
    home_home_goals = np.mean([m['home_score'] for m in home_stat['home_matches']]) if home_stat['home_matches'] else 1.0
    home_away_goals = np.mean([m['away_score'] for m in home_stat['away_matches']]) if home_stat['away_matches'] else 1.0
    away_home_goals = np.mean([m['home_score'] for m in away_stat['home_matches']]) if away_stat['home_matches'] else 1.0
    away_away_goals = np.mean([m['away_score'] for m in away_stat['away_matches']]) if away_stat['away_matches'] else 1.0
    
    # Feature crossing (interactions)
    home_attack_vs_away_def = home_goals_scored / max(away_goals_conceded, 0.1)
    away_attack_vs_home_def = away_goals_scored / max(home_goals_conceded, 0.1)
    xg_total = home_xg + away_xg
    xg_diff = home_xg - away_xg
    form_diff = home_form - away_form
    goals_diff = home_goals_scored - away_goals_conceded
    home_advantage = home_home_goals / max(home_away_goals, 0.1)
    away_disadvantage = away_away_goals / max(away_home_goals, 0.1)
    
    # Cross features
    cross_1 = home_xg * home_poss / 100
    cross_2 = away_xg * away_poss / 100
    cross_3 = home_form * home_goals_scored
    cross_4 = away_form * away_goals_scored
    cross_5 = (home_goals_scored + away_goals_conceded) / 2
    cross_6 = (away_goals_scored + home_goals_conceded) / 2
    
    features = [
        # Basic features
        home_goals_scored, home_goals_conceded, home_xg, home_poss, home_form,
        away_goals_scored, away_goals_conceded, away_xg, away_poss, away_form,
        
        # Home/away specific
        home_home_goals, home_away_goals, away_home_goals, away_away_goals,
        home_advantage, away_disadvantage,
        
        # Differences
        xg_total, xg_diff, form_diff, goals_diff,
        
        # Cross features
        home_attack_vs_away_def, away_attack_vs_home_def,
        cross_1, cross_2, cross_3, cross_4, cross_5, cross_6
    ]
    
    return np.array(features)


def train_xgboost_model(X, y, market_name):
    """Train XGBoost model"""
    print(f"\n  Training XGBoost for {market_name}...")
    
    if len(X) < 50:
        return None, {'error': 'Not enough data'}
    
    # Encode labels if string
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)
    
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded if len(np.unique(y_encoded)) > 1 else None
    )
    
    # XGBoost with optimized parameters
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        learning_rate=0.1,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='mlogloss' if len(np.unique(y_encoded)) > 2 else 'logloss',
        use_label_encoder=False
    )
    
    model.fit(X_train, y_train)
    
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    
    # Cross-validation
    cv_scores = cross_val_score(model, X, y_encoded, cv=5, scoring='accuracy')
    
    metrics = {
        'accuracy': round(accuracy, 3),
        'cv_mean': round(cv_scores.mean(), 3),
        'cv_std': round(cv_scores.std(), 3),
        'samples': len(X),
        'classes': list(le.classes_)
    }
    
    print(f"    Accuracy: {accuracy:.3f}")
    print(f"    CV Score: {cv_scores.mean():.3f} (+/- {cv_scores.std()*2:.3f})")
    
    return model, metrics


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("Football Quant OS - XGBoost Multi-Market Training v2.0")
    print("=" * 60)
    
    # 1. Load Kaggle World Cup data
    print("\n1. Loading Kaggle 2022 World Cup data (with xG/possession)...")
    kaggle_matches = load_kaggle_worldcup_data()
    
    # 2. Load Football-Data.org data
    print("\n2. Loading Football-Data.org data...")
    football_data_matches = load_football_data()
    
    # 3. Combine datasets
    print(f"\n3. Combined dataset: {len(kaggle_matches)} (Kaggle) + {len(football_data_matches)} (Football-Data)")
    all_matches = kaggle_matches + football_data_matches
    
    if len(all_matches) < 100:
        print("Not enough data!")
        return
    
    # 4. Build team stats
    print("\n4. Building team statistics...")
    team_stats = build_team_stats(all_matches)
    print(f"   Teams: {len(team_stats)}")
    
    # 5. Prepare training data for each market
    print("\n5. Extracting features with crossing...")
    
    markets = {
        '1x2': {'X': [], 'y': []},
        'over_under_25': {'X': [], 'y': []},
        'over_under_15': {'X': [], 'y': []},
        'asian_handicap': {'X': [], 'y': []},
        'total_goals': {'X': [], 'y': []},
        'correct_score': {'X': [], 'y': []}
    }
    
    for match in all_matches:
        try:
            is_kaggle = match.get('competition') == 'World Cup 2022'
            features = extract_features_v2(match, team_stats, is_kaggle)
            
            home_score = match.get('home_score', 0)
            away_score = match.get('away_score', 0)
            total = home_score + away_score
            
            # 1X2
            if home_score > away_score:
                label_1x2 = 'home'
            elif home_score == away_score:
                label_1x2 = 'draw'
            else:
                label_1x2 = 'away'
            markets['1x2']['X'].append(features)
            markets['1x2']['y'].append(label_1x2)
            
            # Over/Under 2.5
            markets['over_under_25']['X'].append(features)
            markets['over_under_25']['y'].append(1 if total > 2.5 else 0)
            
            # Over/Under 1.5
            markets['over_under_15']['X'].append(features)
            markets['over_under_15']['y'].append(1 if total > 1.5 else 0)
            
            # Asian Handicap (simplified)
            diff = home_score - away_score
            if diff > 1:
                label_ah = 'home_win'
            elif diff == 1:
                label_ah = 'push'
            elif diff == 0:
                label_ah = 'draw'
            elif diff == -1:
                label_ah = 'away_push'
            else:
                label_ah = 'away_win'
            markets['asian_handicap']['X'].append(features)
            markets['asian_handicap']['y'].append(label_ah)
            
            # Total goals (capped at 5)
            markets['total_goals']['X'].append(features)
            markets['total_goals']['y'].append(min(total, 5))
            
            # Correct score (grouped)
            if home_score > away_score:
                if total <= 2:
                    label_cs = 'home_low'
                elif total <= 4:
                    label_cs = 'home_mid'
                else:
                    label_cs = 'home_high'
            elif home_score == away_score:
                if total <= 2:
                    label_cs = 'draw_low'
                else:
                    label_cs = 'draw_high'
            else:
                if total <= 2:
                    label_cs = 'away_low'
                elif total <= 4:
                    label_cs = 'away_mid'
                else:
                    label_cs = 'away_high'
            markets['correct_score']['X'].append(features)
            markets['correct_score']['y'].append(label_cs)
            
        except Exception as e:
            continue
    
    # 6. Train models
    print("\n6. Training XGBoost models...")
    print("=" * 60)
    
    results = {}
    for market_name, data in markets.items():
        X = np.array(data['X'])
        y = np.array(data['y'])
        
        print(f"\n  Market: {market_name}")
        print(f"  Samples: {len(X)}")
        
        model, metrics = train_xgboost_model(X, y, market_name)
        if model:
            results[market_name] = {'model': model, 'metrics': metrics}
    
    # 7. Summary
    print("\n" + "=" * 60)
    print("XGBoost Training Summary:")
    print("=" * 60)
    for market_name, result in results.items():
        acc = result['metrics'].get('accuracy', 'N/A')
        cv = result['metrics'].get('cv_mean', 'N/A')
        print(f"  {market_name:20s}: Accuracy={acc}, CV={cv}")
    
    # 8. Save models
    print("\n7. Saving models...")
    import pickle
    output_dir = Path('D:/openclaw-workspace/football_quant_os/models/xgboost_multi_market')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for market_name, result in results.items():
        model_path = output_dir / f'{market_name}_xgb_model.pkl'
        with open(model_path, 'wb') as f:
            pickle.dump(result['model'], f)
    
    # Save metrics
    metrics_dict = {}
    for k, v in results.items():
        metrics_dict[k] = {
            'accuracy': float(v['metrics']['accuracy']),
            'cv_mean': float(v['metrics']['cv_mean']),
            'cv_std': float(v['metrics']['cv_std']),
            'samples': int(v['metrics']['samples'])
        }
    
    with open(output_dir / 'xgboost_metrics.json', 'w') as f:
        json.dump(metrics_dict, f, indent=2)
    
    print(f"   Saved to: {output_dir}")
    
    print("\n" + "=" * 60)
    print("XGBoost training complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
