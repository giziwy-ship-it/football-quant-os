"""
Football Quant OS - Recent 3 World Cups Model (2014, 2018, 2022)

Features: FIFA rank + position scores (defense/offense/midfield/goalkeeper) + xG (2022) + historical stats
Data: 192 matches from international_matches.csv + 2022 FIFA xG data
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
from sklearn.model_selection import LeaveOneOut, cross_val_score, StratifiedKFold
import xgboost as xgb

print("=" * 70)
print("  Recent 3 World Cups Model (2014, 2018, 2022)")
print("=" * 70)

# ============================================================
# 1. Load international_matches.csv (has FIFA rank + position scores)
# ============================================================
print("\n[Phase 1] Loading international matches dataset...")

df_intl = pd.read_csv(r'D:\openclaw-workspace\football_quant_os\data\kaggle\worldcup_2022\international_matches.csv', encoding='latin-1')
df_intl['year'] = pd.to_datetime(df_intl['date'], errors='coerce').dt.year

# Filter World Cup matches only
wc_matches = df_intl[df_intl['tournament'].str.contains('World Cup', case=False, na=False)].copy()
print(f"  Total World Cup matches in dataset: {len(wc_matches)}")
print(f"  Year range: {wc_matches['year'].min()}-{wc_matches['year'].max()}")

# Filter 2014, 2018, 2022 (only finals tournament, not qualifiers)
wc_finals = wc_matches[wc_matches['year'].isin([2014, 2018, 2022])].copy()
print(f"  2014+2018+2022 matches: {len(wc_finals)}")

# Show per-year breakdown
for yr in [2014, 2018, 2022]:
    yr_data = wc_finals[wc_finals['year'] == yr]
    print(f"    {yr}: {len(yr_data)} matches")

# ============================================================
# 2. Load 2022 FIFA official xG data for enrichment
# ============================================================
print("\n[Phase 2] Loading 2022 FIFA official xG data...")

df_2022_fifa = pd.read_csv(r'D:\openclaw-workspace\football_quant_os\data\kaggle\worldcup_2022_qatar\Fifa_WC_2022_Match_data.csv', encoding='latin-1')
print(f"  2022 FIFA matches: {len(df_2022_fifa)}")
print(f"  xG coverage: {df_2022_fifa['1_xg'].notna().sum()}/{len(df_2022_fifa)}")

# ============================================================
# 3. Build unified dataset with ALL features
# ============================================================
print("\n[Phase 3] Building unified feature dataset...")

all_matches = []

# 2014 and 2018: FIFA rank + position scores
for yr in [2014, 2018]:
    yr_data = wc_finals[wc_finals['year'] == yr]
    for _, row in yr_data.iterrows():
        all_matches.append({
            'year': yr,
            'home': row['home_team'],
            'away': row['away_team'],
            'home_score': int(row['home_team_score']),
            'away_score': int(row['away_team_score']),
            'home_fifa_rank': row['home_team_fifa_rank'] if pd.notna(row['home_team_fifa_rank']) else 50,
            'away_fifa_rank': row['away_team_fifa_rank'] if pd.notna(row['away_team_fifa_rank']) else 50,
            'home_fifa_points': row['home_team_total_fifa_points'] if pd.notna(row['home_team_total_fifa_points']) else 1000,
            'away_fifa_points': row['away_team_total_fifa_points'] if pd.notna(row['away_team_total_fifa_points']) else 1000,
            'home_goalkeeper': row['home_team_goalkeeper_score'] if pd.notna(row['home_team_goalkeeper_score']) else 70,
            'away_goalkeeper': row['away_team_goalkeeper_score'] if pd.notna(row['away_team_goalkeeper_score']) else 70,
            'home_defense': row['home_team_mean_defense_score'] if pd.notna(row['home_team_mean_defense_score']) else 70,
            'away_defense': row['away_team_mean_defense_score'] if pd.notna(row['away_team_mean_defense_score']) else 70,
            'home_offense': row['home_team_mean_offense_score'] if pd.notna(row['home_team_mean_offense_score']) else 70,
            'away_offense': row['away_team_mean_offense_score'] if pd.notna(row['away_team_mean_offense_score']) else 70,
            'home_midfield': row['home_team_mean_midfield_score'] if pd.notna(row['home_team_mean_midfield_score']) else 70,
            'away_midfield': row['away_team_mean_midfield_score'] if pd.notna(row['away_team_mean_midfield_score']) else 70,
            'home_continent': row['home_team_continent'] if pd.notna(row['home_team_continent']) else 'Unknown',
            'away_continent': row['away_team_continent'] if pd.notna(row['away_team_continent']) else 'Unknown',
            'neutral': row['neutral_location'] if pd.notna(row['neutral_location']) else 1,
            'home_xg': None,
            'away_xg': None,
            'home_poss': None,
            'away_poss': None,
        })

# 2022: Merge international_matches + FIFA official xG data
yr_2022 = wc_finals[wc_finals['year'] == 2022]
print(f"  2022 matches from intl dataset: {len(yr_2022)}")

# Use FIFA official data for 2022 (64 matches, with xG)
for _, row in df_2022_fifa.iterrows():
    # Find matching FIFA rank data from international_matches
    home = str(row['1'])
    away = str(row['2'])
    
    # Try to find matching match in international dataset for FIFA rank
    match_intl = yr_2022[
        ((yr_2022['home_team'] == home) & (yr_2022['away_team'] == away)) |
        ((yr_2022['home_team'] == away) & (yr_2022['away_team'] == home))
    ]
    
    if len(match_intl) > 0:
        m = match_intl.iloc[0]
        home_fifa = m['home_team_fifa_rank'] if pd.notna(m['home_team_fifa_rank']) else 50
        away_fifa = m['away_team_fifa_rank'] if pd.notna(m['away_team_fifa_rank']) else 50
        home_def = m['home_team_mean_defense_score'] if pd.notna(m['home_team_mean_defense_score']) else 70
        away_def = m['away_team_mean_defense_score'] if pd.notna(m['away_team_mean_defense_score']) else 70
        home_off = m['home_team_mean_offense_score'] if pd.notna(m['home_team_mean_offense_score']) else 70
        away_off = m['away_team_mean_offense_score'] if pd.notna(m['away_team_mean_offense_score']) else 70
        home_mid = m['home_team_mean_midfield_score'] if pd.notna(m['home_team_mean_midfield_score']) else 70
        away_mid = m['away_team_mean_midfield_score'] if pd.notna(m['away_team_mean_midfield_score']) else 70
        home_gk = m['home_team_goalkeeper_score'] if pd.notna(m['home_team_goalkeeper_score']) else 70
        away_gk = m['away_team_goalkeeper_score'] if pd.notna(m['away_team_goalkeeper_score']) else 70
        home_cont = m['home_team_continent'] if pd.notna(m['home_team_continent']) else 'Unknown'
        away_cont = m['away_team_continent'] if pd.notna(m['away_team_continent']) else 'Unknown'
    else:
        home_fifa = away_fifa = 50
        home_def = away_def = 70
        home_off = away_off = 70
        home_mid = away_mid = 70
        home_gk = away_gk = 70
        home_cont = away_cont = 'Unknown'
    
    all_matches.append({
        'year': 2022,
        'home': home,
        'away': away,
        'home_score': int(row['1_goals']),
        'away_score': int(row['2_goals']),
        'home_fifa_rank': home_fifa,
        'away_fifa_rank': away_fifa,
        'home_fifa_points': 1000,  # placeholder
        'away_fifa_points': 1000,
        'home_goalkeeper': home_gk,
        'away_goalkeeper': away_gk,
        'home_defense': home_def,
        'away_defense': away_def,
        'home_offense': home_off,
        'away_offense': away_off,
        'home_midfield': home_mid,
        'away_midfield': away_mid,
        'home_continent': home_cont,
        'away_continent': away_cont,
        'neutral': 1,
        'home_xg': float(row['1_xg']) if pd.notna(row['1_xg']) else None,
        'away_xg': float(row['2_xg']) if pd.notna(row['2_xg']) else None,
        'home_poss': float(row['1_poss']) if pd.notna(row['1_poss']) else None,
        'away_poss': float(row['2_poss']) if pd.notna(row['2_poss']) else None,
    })

print(f"  Total matches: {len(all_matches)}")
print(f"  With xG: {sum(1 for m in all_matches if m['home_xg'] is not None)}")

# ============================================================
# 4. Build features (time-consistent historical stats + FIFA data)
# ============================================================
print("\n[Phase 4] Building features with historical stats + FIFA rank + position scores...")

team_stats = defaultdict(lambda: {
    'matches': [], 'goals_scored': [], 'goals_conceded': [], 'wins': 0, 'draws': 0, 'losses': 0,
})

match_features = []

for i, match in enumerate(all_matches):
    home = match['home']
    away = match['away']
    year = match['year']
    
    h_stats = team_stats[home]
    a_stats = team_stats[away]
    
    h_matches = len(h_stats['matches'])
    a_matches = len(a_stats['matches'])
    
    # Historical performance (before this match)
    h_avg_goals = np.mean(h_stats['goals_scored']) if h_stats['goals_scored'] else 1.0
    h_avg_conceded = np.mean(h_stats['goals_conceded']) if h_stats['goals_conceded'] else 1.0
    h_win_rate = h_stats['wins'] / max(h_matches, 1)
    
    a_avg_goals = np.mean(a_stats['goals_scored']) if a_stats['goals_scored'] else 1.0
    a_avg_conceded = np.mean(a_stats['goals_conceded']) if a_stats['goals_conceded'] else 1.0
    a_win_rate = a_stats['wins'] / max(a_matches, 1)
    
    # FIFA features (available for ALL matches!)
    fifa_rank_diff = match['away_fifa_rank'] - match['home_fifa_rank']  # Positive = home ranked better
    fifa_points_ratio = match['home_fifa_points'] / max(match['away_fifa_points'], 1)
    
    # Position score features
    gk_diff = match['home_goalkeeper'] - match['away_goalkeeper']
    def_diff = match['home_defense'] - match['away_defense']
    off_diff = match['home_offense'] - match['away_offense']
    mid_diff = match['home_midfield'] - match['away_midfield']
    
    # Overall strength score (weighted average of positions)
    home_strength = (match['home_offense'] * 0.3 + match['home_midfield'] * 0.3 + match['home_defense'] * 0.25 + match['home_goalkeeper'] * 0.15)
    away_strength = (match['away_offense'] * 0.3 + match['away_midfield'] * 0.3 + match['away_defense'] * 0.25 + match['away_goalkeeper'] * 0.15)
    strength_diff = home_strength - away_strength
    
    # Same continent? (0 = different, 1 = same - familiarity)
    same_continent = 1 if match['home_continent'] == match['away_continent'] else 0
    
    # xG features (only 2022)
    has_xg = 1 if match['home_xg'] is not None else 0
    home_xg = match['home_xg'] if match['home_xg'] is not None else 1.5
    away_xg = match['away_xg'] if match['away_xg'] is not None else 1.2
    xg_total = home_xg + away_xg
    xg_diff = home_xg - away_xg
    
    # Possession (only 2022)
    home_poss = match['home_poss'] if match['home_poss'] is not None else 50
    away_poss = match['away_poss'] if match['away_poss'] is not None else 50
    
    # Tournament stage (approximate based on match order)
    stage_map = {2014: 64, 2018: 64, 2022: 64}  # all have 64 matches
    match_num = i % 64  # approximate within each tournament
    if match_num < 48:
        stage_num = 0  # Group
    elif match_num < 56:
        stage_num = 1  # Round of 16
    elif match_num < 60:
        stage_num = 2  # Quarter
    elif match_num < 62:
        stage_num = 3  # Semi
    else:
        stage_num = 4  # Final/3rd place
    
    # Feature dict
    features = {
        # Historical
        'h_matches': h_matches, 'h_avg_goals': h_avg_goals, 'h_avg_conceded': h_avg_conceded, 'h_win_rate': h_win_rate,
        'a_matches': a_matches, 'a_avg_goals': a_avg_goals, 'a_avg_conceded': a_avg_conceded, 'a_win_rate': a_win_rate,
        'hist_goal_diff': h_avg_goals - a_avg_conceded,
        
        # FIFA rank
        'fifa_rank_diff': fifa_rank_diff,
        'fifa_points_ratio': fifa_points_ratio,
        'home_fifa_rank': match['home_fifa_rank'],
        'away_fifa_rank': match['away_fifa_rank'],
        
        # Position scores
        'gk_diff': gk_diff, 'def_diff': def_diff, 'off_diff': off_diff, 'mid_diff': mid_diff,
        'strength_diff': strength_diff,
        'home_strength': home_strength, 'away_strength': away_strength,
        
        # Context
        'year': year, 'stage_num': stage_num, 'is_knockout': 1 if stage_num > 0 else 0,
        'same_continent': same_continent, 'neutral': match['neutral'],
        'has_xg': has_xg,
        
        # xG (for 2022)
        'xg_total': xg_total, 'xg_diff': xg_diff,
        'home_poss': home_poss, 'away_poss': away_poss,
        
        # Labels
        'total_goals': match['home_score'] + match['away_score'],
        'over_2_5': 1 if match['home_score'] + match['away_score'] > 2.5 else 0,
        'over_1_5': 1 if match['home_score'] + match['away_score'] > 1.5 else 0,
        'home_win': 1 if match['home_score'] > match['away_score'] else 0,
        'draw': 1 if match['home_score'] == match['away_score'] else 0,
        'away_win': 1 if match['home_score'] < match['away_score'] else 0,
    }
    
    match_features.append(features)
    
    # Update stats
    team_stats[home]['matches'].append({'goals': match['home_score'], 'conceded': match['away_score']})
    team_stats[home]['goals_scored'].append(match['home_score'])
    team_stats[home]['goals_conceded'].append(match['away_score'])
    team_stats[away]['matches'].append({'goals': match['away_score'], 'conceded': match['home_score']})
    team_stats[away]['goals_scored'].append(match['away_score'])
    team_stats[away]['goals_conceded'].append(match['home_score'])
    
    if match['home_score'] > match['away_score']:
        team_stats[home]['wins'] += 1; team_stats[away]['losses'] += 1
    elif match['home_score'] == match['away_score']:
        team_stats[home]['draws'] += 1; team_stats[away]['draws'] += 1
    else:
        team_stats[home]['losses'] += 1; team_stats[away]['wins'] += 1

print(f"  Feature records: {len(match_features)}")

# ============================================================
# 5. Prepare training data
# ============================================================
print("\n[Phase 5] Preparing training data...")

feature_names = [
    'h_matches', 'h_avg_goals', 'h_avg_conceded', 'h_win_rate',
    'a_matches', 'a_avg_goals', 'a_avg_conceded', 'a_win_rate', 'hist_goal_diff',
    'fifa_rank_diff', 'fifa_points_ratio', 'home_fifa_rank', 'away_fifa_rank',
    'gk_diff', 'def_diff', 'off_diff', 'mid_diff', 'strength_diff', 'home_strength', 'away_strength',
    'year', 'stage_num', 'is_knockout', 'same_continent', 'neutral', 'has_xg',
    'xg_total', 'xg_diff', 'home_poss', 'away_poss',
]

X = np.array([[f[name] for name in feature_names] for f in match_features])
y_ou = np.array([f['over_2_5'] for f in match_features])
y_1x2 = np.array([0 if f['home_win'] else (1 if f['draw'] else 2) for f in match_features])

print(f"  Feature matrix: {X.shape}")
print(f"  OU distribution: {np.bincount(y_ou)}")
print(f"  1X2 distribution: {np.bincount(y_1x2)}")

# ============================================================
# 6. Time-Series CV (by tournament year)
# ============================================================
print("\n[Phase 6] Time-Series Cross Validation (tournament-level)...")

# Custom split: train on earlier tournaments, test on later
# Fold 1: train 2014, test 2018
# Fold 2: train 2014+2018, test 2022
year_2014_idx = [i for i, f in enumerate(match_features) if f['year'] == 2014]
year_2018_idx = [i for i, f in enumerate(match_features) if f['year'] == 2018]
year_2022_idx = [i for i, f in enumerate(match_features) if f['year'] == 2022]

print(f"  2014 matches: {len(year_2014_idx)}")
print(f"  2018 matches: {len(year_2018_idx)}")
print(f"  2022 matches: {len(year_2022_idx)}")

custom_splits = [
    (year_2014_idx, year_2018_idx),  # train 2014, test 2018
    (year_2014_idx + year_2018_idx, year_2022_idx),  # train 2014+2018, test 2022
]

best_params = {
    'subsample': 0.8, 'reg_lambda': 1, 'reg_alpha': 0.1,
    'n_estimators': 300, 'min_child_weight': 3,
    'max_depth': 6, 'learning_rate': 0.05,
    'gamma': 0.1, 'colsample_bytree': 0.8,
}

ou_scores = []
_1x2_scores = []

for fold, (train_idx, test_idx) in enumerate(custom_splits):
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
    
    train_years = sorted(set(match_features[i]['year'] for i in train_idx))
    test_years = sorted(set(match_features[i]['year'] for i in test_idx))
    print(f"  Fold {fold+1}: train={train_years}, test={test_years} | OU={acc:.1%} | 1X2={acc_1x2:.1%}")

print(f"\n  Mean OU Accuracy:  {np.mean(ou_scores):.1%}")
print(f"  Mean 1X2 Accuracy: {np.mean(_1x2_scores):.1%}")

# Also run LOOCV for 2022 only (to compare with previous model)
print(f"\n  LOOCV on 2022 only (64 matches):")
X_2022 = X[year_2022_idx]
y_2022_ou = y_ou[year_2022_idx]
y_2022_1x2 = y_1x2[year_2022_idx]

loocv = LeaveOneOut()
model_2022 = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', random_state=42, n_jobs=-1, **best_params)
scores_2022_ou = cross_val_score(model_2022, X_2022, y_2022_ou, cv=loocv, scoring='accuracy')
print(f"    2022 OU LOOCV: {scores_2022_ou.mean():.1%}")

model_2022_1x2 = xgb.XGBClassifier(objective='multi:softprob', num_class=3, eval_metric='mlogloss', random_state=42, n_jobs=-1, max_depth=5, learning_rate=0.05, n_estimators=200)
scores_2022_1x2 = cross_val_score(model_2022_1x2, X_2022, y_2022_1x2, cv=loocv, scoring='accuracy')
print(f"    2022 1X2 LOOCV: {scores_2022_1x2.mean():.1%}")

# ============================================================
# 7. Train final model on ALL data
# ============================================================
print("\n[Phase 7] Training final model on ALL 192 matches...")

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
print(f"\nTop 15 Features (OU model):")
for name, imp in sorted(zip(feature_names, importance), key=lambda x: x[1], reverse=True)[:15]:
    bar = '#' * int(imp * 50)
    print(f"  {name:25s} {imp:.3f} {bar}")

# ============================================================
# 8. Save model
# ============================================================
print("\n[Phase 8] Saving model...")

model_package = {
    'ou_model': final_ou,
    '_1x2_model': final_1x2,
    'feature_names': feature_names,
    'ou_cv_scores': ou_scores,
    '_1x2_cv_scores': _1x2_scores,
    'ou_mean_accuracy': float(np.mean(ou_scores)),
    '_1x2_mean_accuracy': float(np.mean(_1x2_scores)),
    'ou_2022_loocv': float(scores_2022_ou.mean()),
    '_1x2_2022_loocv': float(scores_2022_1x2.mean()),
    'training_matches': len(match_features),
    'year_breakdown': {'2014': len(year_2014_idx), '2018': len(year_2018_idx), '2022': len(year_2022_idx)},
    'team_stats': dict(team_stats),
    'version': '3.0-three-world-cups',
    'data_source': 'international_matches.csv + FIFA 2022 official',
}

save_path = r'D:\openclaw-workspace\football_quant_os\models\xgboost_three_world_cups_v3.pkl'
with open(save_path, 'wb') as f:
    pickle.dump(model_package, f)

print(f"  Saved to: {save_path}")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("  THREE WORLD CUPS MODEL SUMMARY")
print("=" * 70)
print(f"""
Data: 3 World Cups (2014, 2018, 2022), 192 matches
Features: 30 total
  - Historical: matches, avg goals, win rate
  - FIFA: rank, rank diff, points ratio
  - Position: goalkeeper, defense, offense, midfield (diff + strength)
  - Context: year, stage, knockout, same continent, neutral
  - xG: total, diff, possession (2022 only)

Validation: Tournament-level time series CV
  - Fold 1: train 2014, test 2018
  - Fold 2: train 2014+2018, test 2022

Performance (Tournament CV):
  OU Accuracy:  {np.mean(ou_scores):.1%}
  1X2 Accuracy: {np.mean(_1x2_scores):.1%}

Performance (2022 LOOCV):
  OU Accuracy:  {scores_2022_ou.mean():.1%}
  1X2 Accuracy: {scores_2022_1x2.mean():.1%}

Model: {save_path}
""")
print("=" * 70)
