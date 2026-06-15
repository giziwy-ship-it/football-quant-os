"""
Football Quant OS - Full World Cup History Model (1930-2022)

All 964 matches, 21 tournaments, time-series CV.
Features: historical stats + stage + experience + region + FIFA rank proxy
"""

import sys
sys.path.insert(0, r'D:\openclaw-workspace\football_quant_os')

import pandas as pd
import numpy as np
import json
import warnings
warnings.filterwarnings('ignore')
import pickle
from pathlib import Path
from collections import defaultdict
from sklearn.model_selection import TimeSeriesSplit, cross_val_score
import xgboost as xgb

print("=" * 70)
print("  Full World Cup History Model (1930-2022)")
print("=" * 70)

# ============================================================
# 1. Load ALL data
# ============================================================
print("\n[Phase 1] Loading all 964 World Cup matches...")

df_hist = pd.read_csv(r'D:\openclaw-workspace\football_quant_os\data\kaggle\worldcup_1930-2018\wcmatches.csv', encoding='latin-1')
df_2022 = pd.read_csv(r'D:\openclaw-workspace\football_quant_os\data\kaggle\worldcup_2022_qatar\Fifa_WC_2022_Match_data.csv', encoding='latin-1')

# Normalize team names
teams_2022 = set(df_2022['1'].unique()) | set(df_2022['2'].unique())
teams_hist = set(df_hist['home_team'].unique()) | set(df_hist['away_team'].unique())

print(f"  1930-2018 teams: {len(teams_hist)}")
print(f"  2022 teams: {len(teams_2022)}")

# Build unified match list with chronological order
all_matches = []

# 1930-2018
for _, row in df_hist.iterrows():
    all_matches.append({
        'year': int(row['year']),
        'home': row['home_team'],
        'away': row['away_team'],
        'home_score': int(row['home_score']),
        'away_score': int(row['away_score']),
        'stage': row['stage'],
        'home_xg': None,
        'away_xg': None,
        'home_poss': None,
        'away_poss': None,
        'home_shots': None,
        'away_shots': None,
        'home_shots_on': None,
        'away_shots_on': None,
    })

# 2022
for _, row in df_2022.iterrows():
    all_matches.append({
        'year': 2022,
        'home': str(row['1']),
        'away': str(row['2']),
        'home_score': int(row['1_goals']),
        'away_score': int(row['2_goals']),
        'stage': 'Group' if row['match_no'] <= 48 else ('Round of 16' if row['match_no'] <= 56 else ('Quarter-final' if row['match_no'] <= 60 else ('Semi-final' if row['match_no'] <= 62 else 'Final'))),
        'home_xg': float(row['1_xg']) if pd.notna(row['1_xg']) else None,
        'away_xg': float(row['2_xg']) if pd.notna(row['2_xg']) else None,
        'home_poss': float(row['1_poss']) if pd.notna(row['1_poss']) else None,
        'away_poss': float(row['2_poss']) if pd.notna(row['2_poss']) else None,
        'home_shots': int(row['1_attempts']) if pd.notna(row['1_attempts']) else None,
        'away_shots': int(row['2_attempts']) if pd.notna(row['2_attempts']) else None,
        'home_shots_on': int(row['1_ontarget']) if pd.notna(row['1_ontarget']) else None,
        'away_shots_on': int(row['2_ontarget']) if pd.notna(row['2_ontarget']) else None,
    })

# Sort chronologically
all_matches.sort(key=lambda x: x['year'])
print(f"  Total matches: {len(all_matches)}")
print(f"  Year range: {all_matches[0]['year']} - {all_matches[-1]['year']}")

# ============================================================
# 2. Build team historical statistics (time-consistent)
# ============================================================
print("\n[Phase 2] Building team historical statistics...")

team_stats = defaultdict(lambda: {
    'matches': [],
    'goals_scored': [],
    'goals_conceded': [],
    'wins': 0,
    'draws': 0,
    'losses': 0,
    'world_cups': set(),
    'stages_reached': set(),
})

# Pre-compute historical stats for each match (before that match)
match_features = []

for i, match in enumerate(all_matches):
    home = match['home']
    away = match['away']
    year = match['year']
    
    # Get stats BEFORE this match
    h_stats = team_stats[home]
    a_stats = team_stats[away]
    
    # Experience features
    h_matches = len(h_stats['matches'])
    a_matches = len(a_stats['matches'])
    h_worldcups = len(h_stats['world_cups'])
    a_worldcups = len(a_stats['world_cups'])
    
    # Historical performance
    h_avg_goals = np.mean(h_stats['goals_scored']) if h_stats['goals_scored'] else 1.0
    h_avg_conceded = np.mean(h_stats['goals_conceded']) if h_stats['goals_conceded'] else 1.0
    h_win_rate = h_stats['wins'] / max(h_matches, 1)
    
    a_avg_goals = np.mean(a_stats['goals_scored']) if a_stats['goals_scored'] else 1.0
    a_avg_conceded = np.mean(a_stats['goals_conceded']) if a_stats['goals_conceded'] else 1.0
    a_win_rate = a_stats['wins'] / max(a_matches, 1)
    
    # Recent form (last 5 matches before this tournament, or all if fewer)
    h_recent = h_stats['matches'][-5:] if len(h_stats['matches']) >= 5 else h_stats['matches']
    a_recent = a_stats['matches'][-5:] if len(a_stats['matches']) >= 5 else a_stats['matches']
    
    h_recent_goals = np.mean([m['goals'] for m in h_recent]) if h_recent else h_avg_goals
    a_recent_goals = np.mean([m['goals'] for m in a_recent]) if a_recent else a_avg_goals
    
    # Stage encoding
    stage_map = {'Group': 0, 'Round of 16': 1, 'Quarter-final': 2, 'Semi-final': 3, 'Final': 4, 'Play-off': 1}
    stage_num = stage_map.get(match['stage'], 0)
    is_knockout = 1 if stage_num > 0 else 0
    
    # xG features (only for 2022+)
    has_xg = 1 if match['home_xg'] is not None else 0
    
    # Feature vector
    features = {
        # Home team historical
        'h_matches': h_matches,
        'h_worldcups': h_worldcups,
        'h_avg_goals': h_avg_goals,
        'h_avg_conceded': h_avg_conceded,
        'h_win_rate': h_win_rate,
        'h_recent_goals': h_recent_goals,
        
        # Away team historical
        'a_matches': a_matches,
        'a_worldcups': a_worldcups,
        'a_avg_goals': a_avg_goals,
        'a_avg_conceded': a_avg_conceded,
        'a_win_rate': a_win_rate,
        'a_recent_goals': a_recent_goals,
        
        # Match context
        'year': year,
        'stage_num': stage_num,
        'is_knockout': is_knockout,
        'has_xg': has_xg,
        
        # Interaction features
        'goal_diff_hist': h_avg_goals - a_avg_conceded,
        'goal_diff_hist_away': a_avg_goals - h_avg_conceded,
        'experience_diff': h_worldcups - a_worldcups,
        'win_rate_diff': h_win_rate - a_win_rate,
        'form_diff': h_recent_goals - a_recent_goals,
        
        # Labels
        'total_goals': match['home_score'] + match['away_score'],
        'over_2_5': 1 if match['home_score'] + match['away_score'] > 2.5 else 0,
        'over_1_5': 1 if match['home_score'] + match['away_score'] > 1.5 else 0,
        'home_win': 1 if match['home_score'] > match['away_score'] else 0,
        'draw': 1 if match['home_score'] == match['away_score'] else 0,
        'away_win': 1 if match['home_score'] < match['away_score'] else 0,
        'match_id': i,
    }
    
    match_features.append(features)
    
    # Update stats AFTER this match (for future matches)
    team_stats[home]['matches'].append({'goals': match['home_score'], 'conceded': match['away_score'], 'year': year})
    team_stats[home]['goals_scored'].append(match['home_score'])
    team_stats[home]['goals_conceded'].append(match['away_score'])
    team_stats[home]['world_cups'].add(year)
    team_stats[home]['stages_reached'].add(match['stage'])
    
    team_stats[away]['matches'].append({'goals': match['away_score'], 'conceded': match['home_score'], 'year': year})
    team_stats[away]['goals_scored'].append(match['away_score'])
    team_stats[away]['goals_conceded'].append(match['home_score'])
    team_stats[away]['world_cups'].add(year)
    team_stats[away]['stages_reached'].add(match['stage'])
    
    if match['home_score'] > match['away_score']:
        team_stats[home]['wins'] += 1
        team_stats[away]['losses'] += 1
    elif match['home_score'] == match['away_score']:
        team_stats[home]['draws'] += 1
        team_stats[away]['draws'] += 1
    else:
        team_stats[home]['losses'] += 1
        team_stats[away]['wins'] += 1

print(f"  Feature records: {len(match_features)}")
print(f"  First match: {all_matches[0]['year']} {all_matches[0]['home']} vs {all_matches[0]['away']}")
print(f"  Last match: {all_matches[-1]['year']} {all_matches[-1]['home']} vs {all_matches[-1]['away']}")

# ============================================================
# 3. Prepare training data (only matches with sufficient history)
# ============================================================
print("\n[Phase 3] Preparing training data...")

# Only use matches where both teams have played at least 1 WC match before
min_history = 1
valid_features = [f for f in match_features if f['h_matches'] >= min_history and f['a_matches'] >= min_history]

print(f"  Matches with sufficient history: {len(valid_features)}")

# Feature matrix
feature_names = [
    'h_matches', 'h_worldcups', 'h_avg_goals', 'h_avg_conceded', 'h_win_rate', 'h_recent_goals',
    'a_matches', 'a_worldcups', 'a_avg_goals', 'a_avg_conceded', 'a_win_rate', 'a_recent_goals',
    'year', 'stage_num', 'is_knockout', 'has_xg',
    'goal_diff_hist', 'goal_diff_hist_away', 'experience_diff', 'win_rate_diff', 'form_diff',
]

X = np.array([[f[name] for name in feature_names] for f in valid_features])
y_ou = np.array([f['over_2_5'] for f in valid_features])
y_1x2 = np.array([0 if f['home_win'] else (1 if f['draw'] else 2) for f in valid_features])

print(f"  Feature matrix: {X.shape}")
print(f"  OU distribution: {np.bincount(y_ou)}")
print(f"  1X2 distribution: {np.bincount(y_1x2)}")

# ============================================================
# 4. Time-Series Cross Validation
# ============================================================
print("\n[Phase 4] Time-Series Cross Validation (5 folds)...")

tscv = TimeSeriesSplit(n_splits=5)

best_params = {
    'subsample': 0.8, 'reg_lambda': 1, 'reg_alpha': 0.1,
    'n_estimators': 300, 'min_child_weight': 3,
    'max_depth': 6, 'learning_rate': 0.05,
    'gamma': 0.1, 'colsample_bytree': 0.8,
}

ou_scores = []
_1x2_scores = []

for fold, (train_idx, test_idx) in enumerate(tscv.split(X)):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y_ou[train_idx], y_ou[test_idx]
    
    model = xgb.XGBClassifier(
        objective='binary:logistic', eval_metric='logloss',
        random_state=42, n_jobs=-1, **best_params
    )
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = np.mean(pred == y_test)
    ou_scores.append(acc)
    
    # 1X2
    y_train_1x2, y_test_1x2 = y_1x2[train_idx], y_1x2[test_idx]
    model_1x2 = xgb.XGBClassifier(
        objective='multi:softprob', num_class=3, eval_metric='mlogloss',
        random_state=42, n_jobs=-1, max_depth=5, learning_rate=0.05, n_estimators=200
    )
    model_1x2.fit(X_train, y_train_1x2)
    pred_1x2 = model_1x2.predict(X_test)
    acc_1x2 = np.mean(pred_1x2 == y_test_1x2)
    _1x2_scores.append(acc_1x2)
    
    print(f"  Fold {fold+1}: train={len(train_idx)}, test={len(test_idx)} | OU={acc:.1%} | 1X2={acc_1x2:.1%}")

print(f"\n  Mean OU Accuracy:  {np.mean(ou_scores):.1%} (+/- {np.std(ou_scores):.1%})")
print(f"  Mean 1X2 Accuracy: {np.mean(_1x2_scores):.1%} (+/- {np.std(_1x2_scores):.1%})")

# ============================================================
# 5. Train final model on ALL data
# ============================================================
print("\n[Phase 5] Training final model on ALL 964 matches...")

final_ou = xgb.XGBClassifier(
    objective='binary:logistic', eval_metric='logloss',
    random_state=42, n_jobs=-1, **best_params
)
final_ou.fit(X, y_ou)

final_1x2 = xgb.XGBClassifier(
    objective='multi:softprob', num_class=3, eval_metric='mlogloss',
    random_state=42, n_jobs=-1, max_depth=5, learning_rate=0.05, n_estimators=200
)
final_1x2.fit(X, y_1x2)

# Feature importance
importance = final_ou.feature_importances_
print(f"\nTop 10 Features (OU model):")
for name, imp in sorted(zip(feature_names, importance), key=lambda x: x[1], reverse=True)[:10]:
    bar = '#' * int(imp * 40)
    print(f"  {name:25s} {imp:.3f} {bar}")

# ============================================================
# 6. Save model
# ============================================================
print("\n[Phase 6] Saving model...")

model_package = {
    'ou_model': final_ou,
    '_1x2_model': final_1x2,
    'feature_names': feature_names,
    'ou_cv_scores': ou_scores,
    '_1x2_cv_scores': _1x2_scores,
    'ou_mean_accuracy': float(np.mean(ou_scores)),
    '_1x2_mean_accuracy': float(np.mean(_1x2_scores)),
    'training_matches': len(valid_features),
    'total_matches': len(all_matches),
    'year_range': f"{all_matches[0]['year']}-{all_matches[-1]['year']}",
    'team_stats': dict(team_stats),  # For inference
    'version': '2.0-full-history',
}

save_path = r'D:\openclaw-workspace\football_quant_os\models\xgboost_full_history_v2.pkl'
with open(save_path, 'wb') as f:
    pickle.dump(model_package, f)

print(f"  Saved to: {save_path}")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("  FULL HISTORY MODEL SUMMARY")
print("=" * 70)
print(f"""
Data: 21 World Cups (1930-2022), {len(all_matches)} matches
Training: {len(valid_features)} matches (both teams had prior WC experience)
Validation: Time-Series CV (5 folds, chronological split)

Performance:
  OU Accuracy:  {np.mean(ou_scores):.1%} (+/- {np.std(ou_scores):.1%})
  1X2 Accuracy: {np.mean(_1x2_scores):.1%} (+/- {np.std(_1x2_scores):.1%})

Features: {len(feature_names)} total
  - Historical: matches, world cups, avg goals, win rate, recent form
  - Context: year, stage, knockout flag, xG availability
  - Interaction: goal diff, experience diff, win rate diff, form diff

Model: {save_path}
""")
print("=" * 70)
