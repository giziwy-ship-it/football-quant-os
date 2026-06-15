#!/usr/bin/env python3
"""
Football Quant OS - Multi-Market Model Training

Train models for:
1. 1X2 (Win/Draw/Loss)
2. Asian Handicap (让球胜平负)
3. Half-Time/Full-Time (半全场)
4. Correct Score (比分)
5. Total Goals (进球数)
6. Over/Under (大小球) - already done
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import numpy as np
from typing import Dict, List, Any, Tuple
from collections import defaultdict

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import accuracy_score, classification_report
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn not available")


def load_training_data() -> List[Dict]:
    """Load training data"""
    data_file = 'D:/openclaw-workspace/football_quant_os/data/training/football_data_training.json'
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []


def extract_features(sample: Dict) -> np.ndarray:
    """Extract feature vector"""
    home = sample.get('home', {})
    away = sample.get('away', {})
    inter = sample.get('interaction', {})
    
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


class MultiMarketModel:
    """Multi-market prediction model"""
    
    def __init__(self):
        self.models = {}
        self.metrics = {}
    
    def train_1x2(self, training_data: List[Dict]) -> Dict:
        """Train 1X2 (Win/Draw/Loss) model"""
        print("\n  [1X2] Training Win/Draw/Loss model...")
        
        X, y = [], []
        for sample in training_data:
            try:
                features = extract_features(sample)
                home_score = sample.get('home_score', 0)
                away_score = sample.get('away_score', 0)
                
                if home_score > away_score:
                    label = 'home'
                elif home_score == away_score:
                    label = 'draw'
                else:
                    label = 'away'
                
                X.append(features)
                y.append(label)
            except:
                continue
        
        X = np.array(X)
        y = np.array(y)
        
        if len(X) < 50 or not SKLEARN_AVAILABLE:
            return {'error': 'Not enough data or sklearn not available'}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.models['1x2'] = model
        self.metrics['1x2'] = {
            'accuracy': round(accuracy, 3),
            'samples': len(X),
            'distribution': {
                'home': round(np.sum(y == 'home') / len(y), 3),
                'draw': round(np.sum(y == 'draw') / len(y), 3),
                'away': round(np.sum(y == 'away') / len(y), 3)
            }
        }
        
        print(f"    Accuracy: {accuracy:.3f}")
        print(f"    Distribution: H={self.metrics['1x2']['distribution']['home']:.1%}, D={self.metrics['1x2']['distribution']['draw']:.1%}, A={self.metrics['1x2']['distribution']['away']:.1%}")
        
        return self.metrics['1x2']
    
    def train_asian_handicap(self, training_data: List[Dict]) -> Dict:
        """Train Asian Handicap model (simplified: -1, 0, +1)"""
        print("\n  [Asian Handicap] Training AH model...")
        
        X, y = [], []
        for sample in training_data:
            try:
                features = extract_features(sample)
                home_score = sample.get('home_score', 0)
                away_score = sample.get('away_score', 0)
                goal_diff = home_score - away_score
                
                if goal_diff > 1:
                    label = 'home_win_ah'  # Home wins AH -1
                elif goal_diff == 1:
                    label = 'home_push'    # Home push AH -1
                elif goal_diff == 0:
                    label = 'draw'         # Draw
                elif goal_diff == -1:
                    label = 'away_push'    # Away push AH +1
                else:
                    label = 'away_win_ah'  # Away wins AH +1
                
                X.append(features)
                y.append(label)
            except:
                continue
        
        X = np.array(X)
        y = np.array(y)
        
        if len(X) < 50 or not SKLEARN_AVAILABLE:
            return {'error': 'Not enough data'}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.models['asian_handicap'] = model
        self.metrics['asian_handicap'] = {
            'accuracy': round(accuracy, 3),
            'samples': len(X)
        }
        
        print(f"    Accuracy: {accuracy:.3f}")
        return self.metrics['asian_handicap']
    
    def train_halftime_fulltime(self, training_data: List[Dict]) -> Dict:
        """Train Half-Time/Full-Time model (simplified)"""
        print("\n  [HT/FT] Training Half-Time/Full-Time model...")
        
        X, y = [], []
        for sample in training_data:
            try:
                features = extract_features(sample)
                home_score = sample.get('home_score', 0)
                away_score = sample.get('away_score', 0)
                
                # Simplified: HT result = FT result (no half-time data available)
                if home_score > away_score:
                    label = 'HH'  # Home/Home
                elif home_score == away_score:
                    label = 'DD'  # Draw/Draw
                else:
                    label = 'AA'  # Away/Away
                
                X.append(features)
                y.append(label)
            except:
                continue
        
        X = np.array(X)
        y = np.array(y)
        
        if len(X) < 50 or not SKLEARN_AVAILABLE:
            return {'error': 'Not enough data'}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.models['ht_ft'] = model
        self.metrics['ht_ft'] = {
            'accuracy': round(accuracy, 3),
            'samples': len(X)
        }
        
        print(f"    Accuracy: {accuracy:.3f}")
        return self.metrics['ht_ft']
    
    def train_correct_score(self, training_data: List[Dict]) -> Dict:
        """Train Correct Score model (grouped by score ranges)"""
        print("\n  [Correct Score] Training score prediction model...")
        
        X, y = [], []
        for sample in training_data:
            try:
                features = extract_features(sample)
                home_score = sample.get('home_score', 0)
                away_score = sample.get('away_score', 0)
                
                # Group into categories
                total = home_score + away_score
                if home_score > away_score:
                    if total <= 2:
                        label = 'home_low'
                    elif total <= 4:
                        label = 'home_mid'
                    else:
                        label = 'home_high'
                elif home_score == away_score:
                    if total <= 2:
                        label = 'draw_low'
                    else:
                        label = 'draw_high'
                else:
                    if total <= 2:
                        label = 'away_low'
                    elif total <= 4:
                        label = 'away_mid'
                    else:
                        label = 'away_high'
                
                X.append(features)
                y.append(label)
            except:
                continue
        
        X = np.array(X)
        y = np.array(y)
        
        if len(X) < 50 or not SKLEARN_AVAILABLE:
            return {'error': 'Not enough data'}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.models['correct_score'] = model
        self.metrics['correct_score'] = {
            'accuracy': round(accuracy, 3),
            'samples': len(X)
        }
        
        print(f"    Accuracy: {accuracy:.3f}")
        return self.metrics['correct_score']
    
    def train_total_goals(self, training_data: List[Dict]) -> Dict:
        """Train Total Goals model (exact number)"""
        print("\n  [Total Goals] Training exact goals model...")
        
        X, y = [], []
        for sample in training_data:
            try:
                features = extract_features(sample)
                home_score = sample.get('home_score', 0)
                away_score = sample.get('away_score', 0)
                total = home_score + away_score
                
                # Cap at 5+ goals
                label = min(total, 5)
                
                X.append(features)
                y.append(label)
            except:
                continue
        
        X = np.array(X)
        y = np.array(y)
        
        if len(X) < 50 or not SKLEARN_AVAILABLE:
            return {'error': 'Not enough data'}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.models['total_goals'] = model
        self.metrics['total_goals'] = {
            'accuracy': round(accuracy, 3),
            'samples': len(X)
        }
        
        print(f"    Accuracy: {accuracy:.3f}")
        return self.metrics['total_goals']
    
    def train_over_under(self, training_data: List[Dict]) -> Dict:
        """Train Over/Under 2.5 model"""
        print("\n  [Over/Under] Training OU 2.5 model...")
        
        X, y = [], []
        for sample in training_data:
            try:
                features = extract_features(sample)
                home_score = sample.get('home_score', 0)
                away_score = sample.get('away_score', 0)
                total = home_score + away_score
                
                label = 1 if total > 2.5 else 0
                
                X.append(features)
                y.append(label)
            except:
                continue
        
        X = np.array(X)
        y = np.array(y)
        
        if len(X) < 50 or not SKLEARN_AVAILABLE:
            return {'error': 'Not enough data'}
        
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        model = RandomForestClassifier(n_estimators=100, random_state=42)
        model.fit(X_train, y_train)
        
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        self.models['over_under'] = model
        self.metrics['over_under'] = {
            'accuracy': round(accuracy, 3),
            'samples': len(X)
        }
        
        print(f"    Accuracy: {accuracy:.3f}")
        return self.metrics['over_under']
    
    def train_all(self, training_data: List[Dict]) -> Dict:
        """Train all models"""
        print("Training 6 market models...")
        
        self.train_1x2(training_data)
        self.train_asian_handicap(training_data)
        self.train_halftime_fulltime(training_data)
        self.train_correct_score(training_data)
        self.train_total_goals(training_data)
        self.train_over_under(training_data)
        
        return self.metrics
    
    def save(self, output_dir: str):
        """Save all models"""
        import pickle
        
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Save models
        for name, model in self.models.items():
            model_path = Path(output_dir) / f'{name}_model.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
        
        # Save metrics
        metrics_path = Path(output_dir) / 'multi_market_metrics.json'
        with open(metrics_path, 'w', encoding='utf-8') as f:
            json.dump(self.metrics, f, indent=2, ensure_ascii=False)
        
        print(f"\nAll models saved to {output_dir}")
        return output_dir


def main():
    """Main training pipeline"""
    print("=" * 60)
    print("Football Quant OS - Multi-Market Model Training")
    print("=" * 60)
    
    # Load data
    print("\n1. Loading training data...")
    training_data = load_training_data()
    print(f"   Loaded {len(training_data)} samples")
    
    if len(training_data) < 100:
        print("   Not enough training data!")
        return
    
    # Train all models
    print("\n2. Training all market models...")
    multi_model = MultiMarketModel()
    metrics = multi_model.train_all(training_data)
    
    # Summary
    print("\n" + "=" * 60)
    print("Training Summary:")
    print("=" * 60)
    for market, metric in metrics.items():
        acc = metric.get('accuracy', 'N/A')
        print(f"  {market:20s}: Accuracy = {acc}")
    
    # Save
    print("\n3. Saving models...")
    output_dir = 'D:/openclaw-workspace/football_quant_os/models/multi_market'
    multi_model.save(output_dir)
    
    print("\n" + "=" * 60)
    print("Multi-market training complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
