"""
Football Quant OS - World Cup 2026 Model with CRI + FIFA Ranking + Position Scores

Full feature set: historical stats + FIFA rank + position scores + coach CRI
Training: 2014/2018/2022 (192 matches)
2026 prediction: load CRI from cri_2026.json
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
from sklearn.model_selection import LeaveOneOut, cross_val_score
import xgboost as xgb

print("=" * 70)
print("  World Cup 2026 Model with CRI + FIFA + Position Scores")
print("=" * 70)

# ============================================================
# 1. Load CRI data
# ============================================================
print("\n[Phase 1] Loading CRI data...")
with open(r'D:\openclaw-workspace\football_quant_os\data\coaching\cri_2026.json', 'r', encoding='utf-8') as f:
    cri_2026 = json.load(f)
print(f"  CRI data: {len(cri_2026)} teams")

# ============================================================
# 2. Load international matches (with FIFA rank + position scores)
# ============================================================
print("\n[Phase 2] Loading international matches...")

df_intl = pd.read_csv(r'D:\openclaw-workspace\football_quant_os\data\kaggle\worldcup_2022\international_matches.csv', encoding='latin-1')
df_intl['year'] = pd.to_datetime(df_intl['date'], errors='coerce').dt.year

wc_finals = df_intl[df_intl['tournament'].str.contains('World Cup', case=False, na=False)]
wc_finals = wc_finals[wc_finals['year'].isin([2014, 2018, 2022])].copy()

print(f"  WC finals: {len(wc_finals)} matches")

# Load 2022 FIFA xG data
df_2022_fifa = pd.read_csv(r'D:\openclaw-workspace\football_quant_os\data\kaggle\worldcup_2022_qatar\Fifa_WC_2022_Match_data.csv', encoding='latin-1')

# ============================================================
# 3. Build unified dataset
# ============================================================
print("\n[Phase 3] Building unified dataset...")

all_matches = []

for yr in [2014, 2018]:
    yr_data = wc_finals[wc_finals['year'] == yr]
    for _, row in yr_data.iterrows():
        all_matches.append({
            'year': yr, 'home': row['home_team'], 'away': row['away_team'],
            'home_score': int(row['home_team_score']), 'away_score': int(row['away_team_score']),
            'home_fifa_rank': row['home_team_fifa_rank'] if pd.notna(row['home_team_fifa_rank']) else 50,
            'away_fifa_rank': row['away_team_fifa_rank'] if pd.notna(row['away_team_fifa_rank']) else 50,
            'home_fifa_points': row['home_team_total_fifa_points'] if pd.notna(row['home_team_total_fifa_points']) else 1000,
            'away_fifa_points': row['away_team_total_fifa_points'] if pd.notna(row['away_team_total_fifa_points']) else 1000,
            'home_gk': row['home_team_goalkeeper_score'] if pd.notna(row['home_team_goalkeeper_score']) else 70,
            'away_gk': row['away_team_goalkeeper_score'] if pd.notna(row['away_team_goalkeeper_score']) else 70,
            'home_def': row['home_team_mean_defense_score'] if pd.notna(row['home_team_mean_defense_score']) else 70,
            'away_def': row['away_team_mean_defense_score'] if pd.notna(row['away_team_mean_defense_score']) else 70,
            'home_off': row['home_team_mean_offense_score'] if pd.notna(row['home_team_mean_offense_score']) else 70,
            'away_off': row['away_team_mean_offense_score'] if pd.notna(row['away_team_mean_offense_score']) else 70,
            'home_mid': row['home_team_mean_midfield_score'] if pd.notna(row['home_team_mean_midfield_score']) else 70,
            'away_mid': row['away_team_mean_midfield_score'] if pd.notna(row['away_team_mean_midfield_score']) else 70,
            'home_cont': row['home_team_continent'] if pd.notna(row['home_team_continent']) else 'Unknown',
            'away_cont': row['away_team_continent'] if pd.notna(row['away_team_continent']) else 'Unknown',
            'neutral': row['neutral_location'] if pd.notna(row['neutral_location']) else 1,
            'home_xg': None, 'away_xg': None, 'home_poss': None, 'away_poss': None,
            # Historical CRI: default 5.0 (moderate, no data)
            'home_cri': 5.0, 'away_cri': 5.0,
            'home_upset_amp': 1.3, 'away_upset_amp': 1.3,
            'home_big_score': 1.0, 'away_big_score': 1.0,
        })

# 2022: merge international + FIFA official
for _, row in df_2022_fifa.iterrows():
    home = str(row['1'])
    away = str(row['2'])
    
    # Find matching FIFA rank data
    match_intl = wc_finals[
        ((wc_finals['home_team'] == home) & (wc_finals['away_team'] == away)) |
        ((wc_finals['home_team'] == away) & (wc_finals['away_team'] == home))
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
    else:
        home_fifa = away_fifa = 50
        home_def = away_def = 70
        home_off = away_off = 70
        home_mid = away_mid = 70
        home_gk = away_gk = 70
    
    all_matches.append({
        'year': 2022, 'home': home, 'away': away,
        'home_score': int(row['1_goals']), 'away_score': int(row['2_goals']),
        'home_fifa_rank': home_fifa, 'away_fifa_rank': away_fifa,
        'home_fifa_points': 1000, 'away_fifa_points': 1000,
        'home_gk': home_gk, 'away_gk': away_gk,
        'home_def': home_def, 'away_def': away_def,
        'home_off': home_off, 'away_off': away_off,
        'home_mid': home_mid, 'away_mid': away_mid,
        'home_cont': 'Unknown', 'away_cont': 'Unknown',
        'neutral': 1,
        'home_xg': float(row['1_xg']) if pd.notna(row['1_xg']) else None,
        'away_xg': float(row['2_xg']) if pd.notna(row['2_xg']) else None,
        'home_poss': float(row['1_poss']) if pd.notna(row['1_poss']) else None,
        'away_poss': float(row['2_poss']) if pd.notna(row['2_poss']) else None,
        'home_cri': 5.0, 'away_cri': 5.0,  # Default for historical
        'home_upset_amp': 1.3, 'away_upset_amp': 1.3,
        'home_big_score': 1.0, 'away_big_score': 1.0,
    })

print(f"  Total matches: {len(all_matches)}")

# ============================================================
# 4. Build features with CRI + FIFA + Position + Historical
# ============================================================
print("\n[Phase 4] Building features with CRI + FIFA + Position + Historical...")

team_stats = defaultdict(lambda: {'matches': [], 'goals_scored': [], 'goals_conceded': [], 'wins': 0, 'draws': 0, 'losses': 0})

match_features = []

for i, match in enumerate(all_matches):
    home = match['home']
    away = match['away']
    h_stats = team_stats[home]
    a_stats = team_stats[away]
    
    h_matches = len(h_stats['matches'])
    a_matches = len(a_stats['matches'])
    
    h_avg_goals = np.mean(h_stats['goals_scored']) if h_stats['goals_scored'] else 1.0
    h_avg_conceded = np.mean(h_stats['goals_conceded']) if h_stats['goals_conceded'] else 1.0
    h_win_rate = h_stats['wins'] / max(h_matches, 1)
    
    a_avg_goals = np.mean(a_stats['goals_scored']) if a_stats['goals_scored'] else 1.0
    a_avg_conceded = np.mean(a_stats['goals_conceded']) if a_stats['goals_conceded'] else 1.0
    a_win_rate = a_stats['wins'] / max(a_matches, 1)
    
    # FIFA features
    fifa_rank_diff = match['away_fifa_rank'] - match['home_fifa_rank']
    fifa_points_ratio = match['home_fifa_points'] / max(match['away_fifa_points'], 1)
    
    # Position scores
    home_strength = (match['home_off'] * 0.3 + match['home_mid'] * 0.3 + match['home_def'] * 0.25 + match['home_gk'] * 0.15)
    away_strength = (match['away_off'] * 0.3 + match['away_mid'] * 0.3 + match['away_def'] * 0.25 + match['away_gk'] * 0.15)
    strength_diff = home_strength - away_strength
    gk_diff = match['home_gk'] - match['away_gk']
    def_diff = match['home_def'] - match['away_def']
    off_diff = match['home_off'] - match['away_off']
    mid_diff = match['home_mid'] - match['away_mid']
    
    # CRI features
    cri_diff = match['home_cri'] - match['away_cri']  # Positive = home coach more volatile
    upset_diff = match['home_upset_amp'] - match['away_upset_amp']
    big_score_diff = match['home_big_score'] - match['away_big_score']
    
    # Context
    stage_num = 0 if i % 64 < 48 else (1 if i % 64 < 56 else (2 if i % 64 < 60 else (3 if i % 64 < 62 else 4)))
    has_xg = 1 if match['home_xg'] is not None else 0
    same_continent = 1 if match['home_cont'] == match['away_cont'] else 0
    
    # xG
    home_xg = match['home_xg'] if match['home_xg'] is not None else 1.5
    away_xg = match['away_xg'] if match['away_xg'] is not None else 1.2
    xg_total = home_xg + away_xg
    xg_diff = home_xg - away_xg
    
    features = {
        # Historical
        'h_matches': h_matches, 'h_avg_goals': h_avg_goals, 'h_avg_conceded': h_avg_conceded, 'h_win_rate': h_win_rate,
        'a_matches': a_matches, 'a_avg_goals': a_avg_goals, 'a_avg_conceded': a_avg_conceded, 'a_win_rate': a_win_rate,
        'hist_goal_diff': h_avg_goals - a_avg_conceded,
        
        # FIFA
        'fifa_rank_diff': fifa_rank_diff, 'fifa_points_ratio': fifa_points_ratio,
        'home_fifa_rank': match['home_fifa_rank'], 'away_fifa_rank': match['away_fifa_rank'],
        
        # Position scores
        'gk_diff': gk_diff, 'def_diff': def_diff, 'off_diff': off_diff, 'mid_diff': mid_diff,
        'strength_diff': strength_diff, 'home_strength': home_strength, 'away_strength': away_strength,
        
        # CRI (Coach Risk Index) - NEW!
        'cri_diff': cri_diff, 'upset_diff': upset_diff, 'big_score_diff': big_score_diff,
        'home_cri': match['home_cri'], 'away_cri': match['away_cri'],
        'home_upset_amp': match['home_upset_amp'], 'away_upset_amp': match['away_upset_amp'],
        
        # Context
        'year': match['year'], 'stage_num': stage_num, 'is_knockout': 1 if stage_num > 0 else 0,
        'same_continent': same_continent, 'neutral': match['neutral'], 'has_xg': has_xg,
        
        # xG
        'xg_total': xg_total, 'xg_diff': xg_diff,
        
        # Labels
        'total_goals': match['home_score'] + match['away_score'],
        'over_2_5': 1 if match['home_score'] + match['away_score'] > 2.5 else 0,
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
    'cri_diff', 'upset_diff', 'big_score_diff', 'home_cri', 'away_cri', 'home_upset_amp', 'away_upset_amp',
    'year', 'stage_num', 'is_knockout', 'same_continent', 'neutral', 'has_xg',
    'xg_total', 'xg_diff',
]

X = np.array([[f[name] for name in feature_names] for f in match_features])
y_ou = np.array([f['over_2_5'] for f in match_features])
y_1x2 = np.array([0 if f['home_win'] else (1 if f['draw'] else 2) for f in match_features])

print(f"  Feature matrix: {X.shape}")
print(f"  OU distribution: {np.bincount(y_ou)}")
print(f"  1X2 distribution: {np.bincount(y_1x2)}")

# ============================================================
# 6. LOOCV on 2022 only
# ============================================================
print("\n[Phase 6] LOOCV on 2022 (64 matches, with xG + CRI features)...")

year_2022_idx = [i for i, f in enumerate(match_features) if f['year'] == 2022]
X_2022 = X[year_2022_idx]
y_2022_ou = y_ou[year_2022_idx]
y_2022_1x2 = y_1x2[year_2022_idx]

best_params = {
    'subsample': 0.8, 'reg_lambda': 1, 'reg_alpha': 0.1,
    'n_estimators': 300, 'min_child_weight': 3,
    'max_depth': 6, 'learning_rate': 0.05,
    'gamma': 0.1, 'colsample_bytree': 0.8,
}

loocv = LeaveOneOut()
model_2022 = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', random_state=42, n_jobs=-1, **best_params)
scores_2022_ou = cross_val_score(model_2022, X_2022, y_2022_ou, cv=loocv, scoring='accuracy')
print(f"  2022 OU LOOCV:  {scores_2022_ou.mean():.1%}")

model_2022_1x2 = xgb.XGBClassifier(objective='multi:softprob', num_class=3, eval_metric='mlogloss', random_state=42, n_jobs=-1, max_depth=5, learning_rate=0.05, n_estimators=200)
scores_2022_1x2 = cross_val_score(model_2022_1x2, X_2022, y_2022_1x2, cv=loocv, scoring='accuracy')
print(f"  2022 1X2 LOOCV: {scores_2022_1x2.mean():.1%}")

# Tournament-level CV
custom_splits = [
    ([i for i, f in enumerate(match_features) if f['year'] == 2014], [i for i, f in enumerate(match_features) if f['year'] == 2018]),
    ([i for i, f in enumerate(match_features) if f['year'] in [2014, 2018]], [i for i, f in enumerate(match_features) if f['year'] == 2022]),
]

ou_scores = []
_1x2_scores = []
for fold, (train_idx, test_idx) in enumerate(custom_splits):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y_ou[train_idx], y_ou[test_idx]
    
    model = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', random_state=42, n_jobs=-1, **best_params)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)
    acc = np.mean(pred == y_test)
    ou_scores.append(acc)
    
    y_train_1x2, y_test_1x2 = y_1x2[train_idx], y_1x2[test_idx]
    model_1x2 = xgb.XGBClassifier(objective='multi:softprob', num_class=3, eval_metric='mlogloss', random_state=42, n_jobs=-1, max_depth=5, learning_rate=0.05, n_estimators=200)
    model_1x2.fit(X_train, y_train_1x2)
    pred_1x2 = model_1x2.predict(X_test)
    acc_1x2 = np.mean(pred_1x2 == y_test_1x2)
    _1x2_scores.append(acc_1x2)
    
    train_years = sorted(set(match_features[i]['year'] for i in train_idx))
    test_years = sorted(set(match_features[i]['year'] for i in test_idx))
    print(f"  Fold {fold+1}: train={train_years}, test={test_years} | OU={acc:.1%} | 1X2={acc_1x2:.1%}")

print(f"\n  Mean Tournament CV OU:  {np.mean(ou_scores):.1%}")
print(f"  Mean Tournament CV 1X2: {np.mean(_1x2_scores):.1%}")

# ============================================================
# 7. Train final model on ALL data
# ============================================================
print("\n[Phase 7] Training final model on ALL 192 matches...")

final_ou = xgb.XGBClassifier(objective='binary:logistic', eval_metric='logloss', random_state=42, n_jobs=-1, **best_params)
final_ou.fit(X, y_ou)

final_1x2 = xgb.XGBClassifier(objective='multi:softprob', num_class=3, eval_metric='mlogloss', random_state=42, n_jobs=-1, max_depth=5, learning_rate=0.05, n_estimators=200)
final_1x2.fit(X, y_1x2)

# Feature importance
importance = final_ou.feature_importances_
print(f"\nTop 15 Features (OU model with CRI):")
for name, imp in sorted(zip(feature_names, importance), key=lambda x: x[1], reverse=True)[:15]:
    bar = '#' * int(imp * 50)
    print(f"  {name:25s} {imp:.3f} {bar}")

# ============================================================
# 8. Save model with CRI support
# ============================================================
print("\n[Phase 8] Saving model with CRI support...")

model_package = {
    'ou_model': final_ou,
    '_1x2_model': final_1x2,
    'feature_names': feature_names,
    'ou_cv_scores': ou_scores,
    '_1x2_cv_scores': _1x2_scores,
    'ou_2022_loocv': float(scores_2022_ou.mean()),
    '_1x2_2022_loocv': float(scores_2022_1x2.mean()),
    'ou_tournament_cv': float(np.mean(ou_scores)),
    '_1x2_tournament_cv': float(np.mean(_1x2_scores)),
    'training_matches': len(match_features),
    'team_stats': dict(team_stats),
    'cri_2026': cri_2026,  # Embed CRI data for 2026 prediction
    'version': '4.0-cri-fifa-position',
    'feature_set': 'historical + FIFA rank + position scores + CRI',
}

save_path = r'D:\openclaw-workspace\football_quant_os\models\xgboost_2026_cri_fifa_v4.pkl'
with open(save_path, 'wb') as f:
    pickle.dump(model_package, f)

print(f"  Saved to: {save_path}")

# ============================================================
# Summary
# ============================================================
print("\n" + "=" * 70)
print("  WORLD CUP 2026 MODEL WITH CRI + FIFA + POSITION SCORES")
print("=" * 70)
print(f"""
Data: 3 World Cups (2014, 2018, 2022), 192 matches
Features: 34 total
  - Historical:     matches, avg goals, win rate, goal diff
  - FIFA:           rank, rank diff, points ratio
  - Position:       GK, DF, OF, MF diff + strength scores
  - CRI (NEW):      coach risk diff, upset amplifier diff, big score diff
  - Context:        year, stage, knockout, same continent, neutral, xG

Validation:
  2022 LOOCV:        OU {scores_2022_ou.mean():.1%} | 1X2 {scores_2022_1x2.mean():.1%}
  Tournament CV:     OU {np.mean(ou_scores):.1%} | 1X2 {np.mean(_1x2_scores):.1%}

Model: {save_path}
""")
print("=" * 70)
