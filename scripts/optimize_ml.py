"""
Football Quant OS - ML Model Optimization Pipeline

突破准确率天花板的系统优化：
1. Hyperparameter Tuning (RandomizedSearchCV)
2. Feature Engineering Expansion
3. LightGBM comparison
4. Stacking Ensemble
"""

import sys
sys.path.insert(0, r'D:\openclaw-workspace\football_quant_os')

import json
import numpy as np
from collections import Counter
from sklearn.model_selection import RandomizedSearchCV, cross_val_score, StratifiedKFold
from sklearn.ensemble import StackingClassifier
from sklearn.linear_model import LogisticRegression
import warnings
warnings.filterwarnings('ignore')

from models.xgboost_model import XGBoostPredictor
from features.feature_engineer import FeatureEngineer

# Try LightGBM
try:
    import lightgbm as lgb
    LIGHTGBM_AVAILABLE = True
except ImportError:
    LIGHTGBM_AVAILABLE = False
    print("LightGBM not installed. Run: pip install lightgbm")


# ============================================================
# 1. 加载数据
# ============================================================
print("=" * 70)
print("  ML Model Optimization Pipeline")
print("=" * 70)

with open(r'D:\openclaw-workspace\football_quant_os\data\training\football_data_training.json', 'r', encoding='utf-8') as f:
    all_samples = json.load(f)

print(f"\nLoaded {len(all_samples)} samples")

# 构建特征矩阵
X = XGBoostPredictor.build_feature_matrix(all_samples)
y_ou, y_1x2 = XGBoostPredictor.extract_labels(all_samples)

print(f"Feature matrix: {X.shape}")
print(f"OU distribution: {dict(Counter(y_ou))}")
print(f"1X2 distribution: {dict(Counter(y_1x2))}")

# ============================================================
# 2. Hyperparameter Tuning — XGBoost OU
# ============================================================
print("\n" + "-" * 70)
print("Phase 1: XGBoost Hyperparameter Tuning (OU)")
print("-" * 70)

import xgboost as xgb

param_dist = {
    'n_estimators': [100, 200, 300, 500],
    'max_depth': [3, 4, 5, 6, 7, 8],
    'learning_rate': [0.01, 0.05, 0.1, 0.15, 0.2],
    'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
    'colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
    'min_child_weight': [1, 3, 5, 7],
    'gamma': [0, 0.1, 0.2, 0.3],
    'reg_alpha': [0, 0.01, 0.1, 1],
    'reg_lambda': [0.1, 1, 10],
}

xgb_clf = xgb.XGBClassifier(
    objective='binary:logistic',
    eval_metric='logloss',
    random_state=42,
    n_jobs=-1,
    use_label_encoder=False,
)

random_search = RandomizedSearchCV(
    xgb_clf, param_dist,
    n_iter=30,
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    scoring='accuracy',
    n_jobs=-1,
    random_state=42,
    verbose=1,
)

random_search.fit(X, y_ou)

print(f"\nBest OU Accuracy (CV): {random_search.best_score_:.1%}")
print(f"Best Params:")
for k, v in random_search.best_params_.items():
    print(f"  {k}: {v}")

best_xgb_ou = random_search.best_estimator_

# ============================================================
# 3. Hyperparameter Tuning — XGBoost 1X2
# ============================================================
print("\n" + "-" * 70)
print("Phase 2: XGBoost Hyperparameter Tuning (1X2)")
print("-" * 70)

xgb_1x2 = xgb.XGBClassifier(
    objective='multi:softprob',
    num_class=3,
    eval_metric='mlogloss',
    random_state=42,
    n_jobs=-1,
    use_label_encoder=False,
)

random_search_1x2 = RandomizedSearchCV(
    xgb_1x2, param_dist,
    n_iter=30,
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    scoring='accuracy',
    n_jobs=-1,
    random_state=42,
    verbose=1,
)

random_search_1x2.fit(X, y_1x2)

print(f"\nBest 1X2 Accuracy (CV): {random_search_1x2.best_score_:.1%}")
print(f"Best Params:")
for k, v in random_search_1x2.best_params_.items():
    print(f"  {k}: {v}")

best_xgb_1x2 = random_search_1x2.best_estimator_

# ============================================================
# 4. LightGBM Comparison
# ============================================================
if LIGHTGBM_AVAILABLE:
    print("\n" + "-" * 70)
    print("Phase 3: LightGBM Comparison")
    print("-" * 70)

    lgb_param_dist = {
        'n_estimators': [100, 200, 300, 500],
        'max_depth': [3, 4, 5, 6, 7, -1],
        'learning_rate': [0.01, 0.05, 0.1, 0.15, 0.2],
        'num_leaves': [15, 31, 63, 127],
        'subsample': [0.6, 0.7, 0.8, 0.9, 1.0],
        'colsample_bytree': [0.6, 0.7, 0.8, 0.9, 1.0],
        'min_child_samples': [5, 10, 20, 30],
        'reg_alpha': [0, 0.01, 0.1, 1],
        'reg_lambda': [0.1, 1, 10],
    }

    lgb_clf = lgb.LGBMClassifier(
        objective='binary',
        random_state=42,
        n_jobs=-1,
        verbose=-1,
    )

    lgb_search = RandomizedSearchCV(
        lgb_clf, lgb_param_dist,
        n_iter=30,
        cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
        scoring='accuracy',
        n_jobs=-1,
        random_state=42,
        verbose=1,
    )

    lgb_search.fit(X, y_ou)

    print(f"\nLightGBM OU Accuracy (CV): {lgb_search.best_score_:.1%}")
    print(f"Best Params:")
    for k, v in lgb_search.best_params_.items():
        print(f"  {k}: {v}")

# ============================================================
# 5. Stacking Ensemble
# ============================================================
print("\n" + "-" * 70)
print("Phase 4: Stacking Ensemble")
print("-" * 70)

estimators = [
    ('xgb', best_xgb_ou),
]

if LIGHTGBM_AVAILABLE:
    estimators.append(('lgb', lgb_search.best_estimator_))

stacking = StackingClassifier(
    estimators=estimators,
    final_estimator=LogisticRegression(random_state=42, max_iter=1000),
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    n_jobs=-1,
)

stack_scores = cross_val_score(stacking, X, y_ou, cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42), scoring='accuracy')
print(f"\nStacking Ensemble OU Accuracy (CV): {stack_scores.mean():.1%} (+/- {stack_scores.std():.1%})")

# ============================================================
# 6. Save Optimized Models
# ============================================================
print("\n" + "-" * 70)
print("Phase 5: Saving Optimized Models")
print("-" * 70)

import pickle

optimized = {
    'ou_model': best_xgb_ou,
    '_1x2_model': best_xgb_1x2,
    'ou_params': random_search.best_params_,
    '_1x2_params': random_search_1x2.best_params_,
    'ou_cv_accuracy': random_search.best_score_,
    '_1x2_cv_accuracy': random_search_1x2.best_score_,
}

if LIGHTGBM_AVAILABLE:
    optimized['lgb_ou_model'] = lgb_search.best_estimator_
    optimized['lgb_ou_params'] = lgb_search.best_params_
    optimized['lgb_ou_cv_accuracy'] = lgb_search.best_score_

path = r'D:\openclaw-workspace\football_quant_os\models\xgboost_v2_optimized.pkl'
with open(path, 'wb') as f:
    pickle.dump(optimized, f)

print(f"Saved optimized models to: {path}")

# ============================================================
# 7. Summary Report
# ============================================================
print("\n" + "=" * 70)
print("  OPTIMIZATION SUMMARY")
print("=" * 70)
print(f"\nOriginal XGBoost (default params):")
print(f"  OU Accuracy:  52.1%")
print(f"  1X2 Accuracy: 43.1%")
print(f"\nOptimized XGBoost (tuned params):")
print(f"  OU Accuracy:  {random_search.best_score_:.1%}  (+{random_search.best_score_-0.521:+.1%})")
print(f"  1X2 Accuracy: {random_search_1x2.best_score_:.1%}  (+{random_search_1x2.best_score_-0.431:+.1%})")
if LIGHTGBM_AVAILABLE:
    print(f"\nLightGBM:")
    print(f"  OU Accuracy:  {lgb_search.best_score_:.1%}")
print(f"\nStacking Ensemble:")
print(f"  OU Accuracy:  {stack_scores.mean():.1%}  (+/- {stack_scores.std():.1%})")

print("\n" + "=" * 70)
print("  Optimization Complete!")
print("=" * 70)
