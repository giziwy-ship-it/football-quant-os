#!/usr/bin/env python3
"""
Football Quant OS - XGBoost Model Training Pipeline

Usage:
    python scripts/train_xgboost.py
    python scripts/train_xgboost.py --sources kaggle football_data --years 2022 2018 2014
    python scripts/train_xgboost.py --output models/xgboost_v1.pkl
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
from typing import List, Dict, Any

from features.feature_engineer import FeatureEngineer
from models.xgboost_model import XGBoostPredictor
from scripts.generate_training_data import generate_training_dataset


def train_xgboost_pipeline(
    sources: List[str] = None,
    years: List[int] = None,
    output_path: str = None,
    test_size: float = 0.2,
    compare: bool = True
) -> Dict[str, Any]:
    """
    完整训练管道

    1. 获取训练数据 (generate_training_data)
    2. 训练 XGBoost 模型
    3. (可选) 与现有模型 A/B 对比
    4. 保存模型
    """
    print("=" * 70)
    print("  XGBoost Model Training Pipeline")
    print("=" * 70)

    # ---- Step 1: 数据准备 ----
    print("\n[Step 1] Generating training data...")
    training_samples = generate_training_dataset(
        sources=sources or ['kaggle'],
        years=years or [2022],
        output_file=None  # 不保存中间JSON，直接内存处理
    )

    if len(training_samples) < 50:
        print(f"\nERROR: Only {len(training_samples)} samples. Need at least 50.")
        print("Try: --sources kaggle --years 2022 2018 2014")
        return {'success': False, 'error': 'Not enough data'}

    print(f"  Total samples: {len(training_samples)}")

    # ---- Step 2: 训练 XGBoost ----
    print("\n[Step 2] Training XGBoost models...")
    predictor = XGBoostPredictor()
    result = predictor.train(training_samples, test_size=test_size, verbose=True)

    # ---- Step 3: 特征重要性分析 ----
    print("\n[Step 3] Feature Importance (Over/Under):")
    ou_imp = result['feature_importance_ou']
    sorted_imp = sorted(ou_imp.items(), key=lambda x: x[1], reverse=True)
    for name, imp in sorted_imp[:10]:
        bar = '█' * int(imp * 50)
        print(f"  {name:30s} {imp:.3f} {bar}")

    # ---- Step 4: 与现有模型对比 (可选) ----
    if compare:
        print("\n[Step 4] A/B Comparison with existing models...")
        _compare_with_existing(training_samples, predictor)

    # ---- Step 5: 保存模型 ----
    if output_path:
        predictor.save(output_path)
        print(f"\n[Step 5] Model saved to: {output_path}")

    print("\n" + "=" * 70)
    print("  Training Complete!")
    print("=" * 70)

    return {
        'success': True,
        'samples': result['samples'],
        'ou_accuracy': result['ou_accuracy'],
        '_1x2_accuracy': result['_1x2_accuracy'],
        'model_path': output_path,
    }


def _compare_with_existing(samples: List[Dict], xgb_predictor: XGBoostPredictor):
    """与 HeuristicModel + PoissonModel 做简单对比"""
    from models.heuristic_model import HeuristicModel
    from models.poisson_model import PoissonModel

    hm = HeuristicModel()
    pm = PoissonModel()

    # 使用最后 20% 做对比
    n_test = max(1, len(samples) // 5)
    test_samples = samples[-n_test:]

    xgb_ou_correct = 0
    hm_1x2_correct = 0
    pm_ou_correct = 0

    for sample in test_samples:
        actual_over = sample['label']['over_2_5']
        actual_result = 0 if sample.get('home_score', 0) > sample.get('away_score', 0) else (
            1 if sample.get('home_score', 0) == sample.get('away_score', 0) else 2
        )

        # XGBoost OU
        xgb_pred = xgb_predictor.predict(sample)
        if 'over_under' in xgb_pred.get('markets', {}):
            pred_over = xgb_pred['markets']['over_under']['over_2_5'] > 0.5
            if int(pred_over) == actual_over:
                xgb_ou_correct += 1

        # Heuristic 1X2 (简化对比)
        try:
            hm_pred = hm.predict({
                'home': sample.get('home', {}).get('team', 'Home'),
                'away': sample.get('away', {}).get('team', 'Away'),
                'odds_home': 2.5, 'odds_draw': 3.2, 'odds_away': 2.8,
            })
            hm_result = max(hm_pred['markets']['1x2']['model'],
                          key=hm_pred['markets']['1x2']['model'].get)
            # 简化: heuristic 返回的是概率 dict，取最大
            # 这里只做 OU 对比
        except Exception:
            pass

        # Poisson OU
        try:
            pm_pred = pm.predict({
                'home': sample.get('home', {}).get('team', 'Home'),
                'away': sample.get('away', {}).get('team', 'Away'),
                'odds_home': 2.5, 'odds_draw': 3.2, 'odds_away': 2.8,
                'home_xg': sample.get('home', {}).get('avg_xg', 1.5),
                'away_xg': sample.get('away', {}).get('avg_xg', 1.2),
            })
            if 'over_under' in pm_pred.get('markets', {}):
                pred_over = pm_pred['markets']['over_under']['over_prob'] > 0.5
                if int(pred_over) == actual_over:
                    pm_ou_correct += 1
        except Exception:
            pass

    n = len(test_samples)
    print(f"  Sample size: {n}")
    print(f"  XGBoost OU Accuracy:  {xgb_ou_correct}/{n} = {xgb_ou_correct/n:.1%}")
    print(f"  Poisson OU Accuracy:  {pm_ou_correct}/{n} = {pm_ou_correct/n:.1%}")
    print(f"  Baseline (always Over): {sum(s['label']['over_2_5'] for s in test_samples)/n:.1%}")


def main():
    parser = argparse.ArgumentParser(description='Train XGBoost model for Football Quant OS')
    parser.add_argument('--sources', nargs='+', default=['kaggle'],
                        help='Data sources: kaggle, football_data, api_football')
    parser.add_argument('--years', nargs='+', type=int, default=[2022],
                        help='Years to include')
    parser.add_argument('--output', default='models/xgboost_v1.pkl',
                        help='Output model path')
    parser.add_argument('--test-size', type=float, default=0.2,
                        help='Test set ratio')
    parser.add_argument('--no-compare', action='store_true',
                        help='Skip comparison with existing models')

    args = parser.parse_args()

    result = train_xgboost_pipeline(
        sources=args.sources,
        years=args.years,
        output_path=args.output,
        test_size=args.test_size,
        compare=not args.no_compare
    )

    if result['success']:
        print(f"\nFinal Report:")
        print(f"  Samples:     {result['samples']}")
        print(f"  OU Accuracy: {result['ou_accuracy']:.1%}")
        print(f"  1X2 Accuracy: {result['_1x2_accuracy']:.1%}")
        print(f"  Model:       {result['model_path']}")
    else:
        print(f"\nTraining failed: {result.get('error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()
