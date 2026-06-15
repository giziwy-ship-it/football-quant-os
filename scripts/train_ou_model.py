#!/usr/bin/env python3
"""
Football Quant OS - Model Training

Train a simple Over/Under prediction model using scikit-learn
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from typing import Dict, List, Any, Tuple

# Try to import sklearn, fallback to simple model if not available
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available, using simple heuristic model")


def load_training_data(file_path: str) -> List[Dict[str, Any]]:
    """Load training data from JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def extract_features(sample: Dict) -> np.ndarray:
    """Extract feature vector from training sample"""
    home = sample['home']
    away = sample['away']
    inter = sample['interaction']
    
    features = [
        home.get('avg_goals_scored', 1.0),
        home.get('avg_goals_conceded', 1.0),
        home.get('avg_xg', 1.0),
        home.get('attack_efficiency', 1.0),
        home.get('defense_efficiency', 1.0),
        home.get('recent_form', 1.5),
        home.get('home_advantage', 1.0),
        
        away.get('avg_goals_scored', 1.0),
        away.get('avg_goals_conceded', 1.0),
        away.get('avg_xg', 1.0),
        away.get('attack_efficiency', 1.0),
        away.get('defense_efficiency', 1.0),
        away.get('recent_form', 1.5),
        away.get('away_disadvantage', 1.0),
        
        inter.get('total_xg', 2.0),
        inter.get('home_xg_diff', 0.0),
        inter.get('away_xg_diff', 0.0),
        inter.get('home_attack_vs_away_defense', 1.0),
        inter.get('away_attack_vs_home_defense', 1.0),
    ]
    
    return np.array(features)


def train_ou_model(training_data: List[Dict]) -> Tuple[Any, Dict]:
    """
    Train Over/Under 2.5 prediction model
    
    Returns:
        (model, metrics)
    """
    # Prepare features and labels
    X = []
    y = []
    
    for sample in training_data:
        try:
            features = extract_features(sample)
            label = sample['label']['over_2_5']
            X.append(features)
            y.append(label)
        except Exception as e:
            continue
    
    X = np.array(X)
    y = np.array(y)
    
    print(f"Training data: {len(X)} samples")
    print(f"Features: {X.shape[1]} dimensions")
    print(f"Over 2.5 rate: {np.mean(y):.1%}")
    
    if len(X) < 50:
        return None, {'error': 'Not enough training data'}
    
    if SKLEARN_AVAILABLE and len(X) >= 100:
        # Split train/test
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train Random Forest
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            n_jobs=-1
        )
        model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        metrics = {
            'accuracy': round(accuracy, 3),
            'samples': len(X),
            'features': X.shape[1],
            'over_rate': round(np.mean(y), 3),
        }
        
        # Feature importance
        feature_names = [
            'home_avg_scored', 'home_avg_conceded', 'home_xg',
            'home_attack_eff', 'home_defense_eff', 'home_form', 'home_advantage',
            'away_avg_scored', 'away_avg_conceded', 'away_xg',
            'away_attack_eff', 'away_defense_eff', 'away_form', 'away_disadvantage',
            'total_xg', 'home_xg_diff', 'away_xg_diff',
            'home_attack_vs_away_def', 'away_attack_vs_home_def'
        ]
        
        importances = model.feature_importances_
        feature_importance = dict(zip(feature_names, importances))
        metrics['feature_importance'] = {
            k: round(v, 3) for k, v in sorted(
                feature_importance.items(), key=lambda x: x[1], reverse=True
            )[:10]
        }
        
    else:
        # Simple heuristic: predict over if total_xg > 2.5
        class SimpleModel:
            def predict(self, X):
                return (X[:, 14] > 2.5).astype(int)  # total_xg column
            
            def predict_proba(self, X):
                preds = self.predict(X)
                return np.column_stack([1 - preds, preds])
        
        model = SimpleModel()
        metrics = {
            'accuracy': 'N/A (heuristic model)',
            'samples': len(X),
            'features': X.shape[1],
            'over_rate': round(np.mean(y), 3),
        }
    
    return model, metrics


def predict_match(model, home_features: Dict, away_features: Dict) -> Dict:
    """Predict Over/Under for a match"""
    # Build interaction features
    inter = {
        'total_xg': home_features.get('avg_xg', 1.0) + away_features.get('avg_xg', 1.0),
        'home_xg_diff': home_features.get('avg_xg', 1.0) - away_features.get('avg_goals_conceded', 1.0),
        'away_xg_diff': away_features.get('avg_xg', 1.0) - home_features.get('avg_goals_conceded', 1.0),
        'home_attack_vs_away_defense': home_features.get('attack_efficiency', 1.0) / max(away_features.get('defense_efficiency', 0.1), 0.1),
        'away_attack_vs_home_defense': away_features.get('attack_efficiency', 1.0) / max(home_features.get('defense_efficiency', 0.1), 0.1),
    }
    
    sample = {
        'home': home_features,
        'away': away_features,
        'interaction': inter
    }
    
    features = extract_features(sample)
    features = features.reshape(1, -1)
    
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(features)[0]
        over_prob = proba[1]
    else:
        pred = model.predict(features)[0]
        over_prob = float(pred)
    
    return {
        'over_prob': round(over_prob, 3),
        'under_prob': round(1 - over_prob, 3),
        'prediction': 'Over 2.5' if over_prob > 0.5 else 'Under 2.5',
        'confidence': round(abs(over_prob - 0.5) * 2, 3)
    }


def save_model(model, metrics: Dict, output_path: str):
    """Save model and metrics"""
    import pickle
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save model
    model_path = output_path.replace('.json', '.pkl')
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    
    # Save metrics
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)
    
    return model_path


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("Football Quant OS - Model Training")
    print("=" * 60)
    
    # Load training data
    data_file = 'D:/openclaw-workspace/football_quant_os/data/training/football_data_training.json'
    
    print(f"\n1. Loading training data from {data_file}...")
    try:
        training_data = load_training_data(data_file)
        print(f"   Loaded {len(training_data)} samples")
    except FileNotFoundError:
        print("   Training data not found. Run collect_training_data first.")
        return
    
    # Train model
    print("\n2. Training Over/Under 2.5 prediction model...")
    model, metrics = train_ou_model(training_data)
    
    if model is None:
        print(f"   Error: {metrics['error']}")
        return
    
    print(f"\n   Training complete!")
    print(f"   Accuracy: {metrics.get('accuracy', 'N/A')}")
    print(f"   Samples: {metrics['samples']}")
    print(f"   Features: {metrics['features']}")
    print(f"   Over 2.5 rate: {metrics['over_rate']:.1%}")
    
    if 'feature_importance' in metrics:
        print(f"\n   Top features:")
        for feat, imp in metrics['feature_importance'].items():
            bar = "#" * int(imp * 20)
            print(f"     {feat:25s}: {imp:.3f} {bar}")
    
    # Save model
    print("\n3. Saving model...")
    model_path = save_model(model, metrics, 
        'D:/openclaw-workspace/football_quant_os/models/ou_model.json')
    print(f"   Saved to: {model_path}")
    
    # Test prediction
    print("\n4. Testing prediction...")
    test_home = {
        'avg_goals_scored': 2.5,
        'avg_goals_conceded': 1.0,
        'avg_xg': 2.3,
        'attack_efficiency': 1.1,
        'defense_efficiency': 0.9,
        'recent_form': 2.0,
        'home_advantage': 1.2
    }
    test_away = {
        'avg_goals_scored': 1.0,
        'avg_goals_conceded': 2.0,
        'avg_xg': 0.9,
        'attack_efficiency': 0.9,
        'defense_efficiency': 1.1,
        'recent_form': 1.0,
        'away_disadvantage': 0.8
    }
    
    result = predict_match(model, test_home, test_away)
    print(f"\n   Test prediction (strong home vs weak away):")
    print(f"   Over 2.5: {result['over_prob']:.1%}")
    print(f"   Under 2.5: {result['under_prob']:.1%}")
    print(f"   Prediction: {result['prediction']}")
    print(f"   Confidence: {result['confidence']:.1%}")
    
    print("\n" + "=" * 60)
    print("Training complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
