"""
Football Quant OS - XGBoost Prediction Model

Integrate trained XGBoost models into the prediction pipeline
"""

import numpy as np
import pickle
from typing import Dict, Any, List, Optional
from pathlib import Path

from models.base_model import BaseModel


class XGBoostPredictor(BaseModel):
    """
    XGBoost-based prediction model
    
    Loads trained models from disk and makes predictions
    """
    
    def __init__(self, model_dir: str = None):
        if model_dir is None:
            model_dir = Path(__file__).parent.parent / 'models' / 'xgboost_multi_market'
        
        self.model_dir = Path(model_dir)
        self.models = {}
        self._load_models()
        
        self._version = "2.0"
        self._name = "XGBoostPredictor"
    
    def _load_models(self):
        """Load all trained models from disk"""
        model_files = {
            '1x2': '1x2_xgb_model.pkl',
            'over_under_25': 'over_under_25_xgb_model.pkl',
            'over_under_15': 'over_under_15_xgb_model.pkl',
            'asian_handicap': 'asian_handicap_xgb_model.pkl',
            'total_goals': 'total_goals_xgb_model.pkl',
            'correct_score': 'correct_score_xgb_model.pkl'
        }
        
        for market, filename in model_files.items():
            model_path = self.model_dir / filename
            if model_path.exists():
                try:
                    with open(model_path, 'rb') as f:
                        self.models[market] = pickle.load(f)
                    print(f"  Loaded {market} model")
                except Exception as e:
                    print(f"  Failed to load {market}: {e}")
            else:
                print(f"  Model not found: {model_path}")
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def version(self) -> str:
        return self._version
    
    @property
    def supported_markets(self) -> List[str]:
        return list(self.models.keys())
    
    def _extract_features(self, match_info: Dict) -> np.ndarray:
        """
        Extract features from match_info for XGBoost prediction
        
        Features must match the training feature order:
        [home_goals_scored, home_goals_conceded, home_xg, home_poss, home_form,
         away_goals_scored, away_goals_conceded, away_xg, away_poss, away_form,
         home_home_goals, home_away_goals, away_home_goals, away_away_goals,
         home_advantage, away_disadvantage,
         xg_total, xg_diff, form_diff, goals_diff,
         home_attack_vs_away_def, away_attack_vs_home_def,
         cross_1, cross_2, cross_3, cross_4, cross_5, cross_6]
        """
        home = match_info.get('home', '')
        away = match_info.get('away', '')
        
        # Get values from match_info or use defaults
        home_goals_scored = match_info.get('home_avg_scored', 1.0)
        home_goals_conceded = match_info.get('home_avg_conceded', 1.0)
        home_xg = match_info.get('home_xg', 1.0)
        home_poss = match_info.get('home_poss', 50)
        home_form = match_info.get('home_form', 1.5)
        
        away_goals_scored = match_info.get('away_avg_scored', 1.0)
        away_goals_conceded = match_info.get('away_avg_conceded', 1.0)
        away_xg = match_info.get('away_xg', 1.0)
        away_poss = match_info.get('away_poss', 50)
        away_form = match_info.get('away_form', 1.5)
        
        # Home/away advantage (defaults)
        home_home_goals = match_info.get('home_home_goals', home_goals_scored)
        home_away_goals = match_info.get('home_away_goals', home_goals_scored * 0.8)
        away_home_goals = match_info.get('away_home_goals', away_goals_scored * 0.8)
        away_away_goals = match_info.get('away_away_goals', away_goals_scored)
        
        # Differences
        home_advantage = home_home_goals / max(home_away_goals, 0.1)
        away_disadvantage = away_away_goals / max(away_home_goals, 0.1)
        xg_total = home_xg + away_xg
        xg_diff = home_xg - away_xg
        form_diff = home_form - away_form
        goals_diff = home_goals_scored - away_goals_conceded
        
        # Cross features
        home_attack_vs_away_def = home_goals_scored / max(away_goals_conceded, 0.1)
        away_attack_vs_home_def = away_goals_scored / max(home_goals_conceded, 0.1)
        cross_1 = home_xg * home_poss / 100
        cross_2 = away_xg * away_poss / 100
        cross_3 = home_form * home_goals_scored
        cross_4 = away_form * away_goals_scored
        cross_5 = (home_goals_scored + away_goals_conceded) / 2
        cross_6 = (away_goals_scored + home_goals_conceded) / 2
        
        features = [
            home_goals_scored, home_goals_conceded, home_xg, home_poss, home_form,
            away_goals_scored, away_goals_conceded, away_xg, away_poss, away_form,
            home_home_goals, home_away_goals, away_home_goals, away_away_goals,
            home_advantage, away_disadvantage,
            xg_total, xg_diff, form_diff, goals_diff,
            home_attack_vs_away_def, away_attack_vs_home_def,
            cross_1, cross_2, cross_3, cross_4, cross_5, cross_6
        ]
        
        return np.array(features).reshape(1, -1)
    
    def predict(self, match_info: Dict, **kwargs) -> Dict[str, Any]:
        """
        Make predictions using XGBoost models
        
        Returns predictions for all available markets
        """
        features = self._extract_features(match_info)
        
        predictions = {
            'model_name': self.name,
            'version': self.version,
            'markets': {}
        }
        
        # 1X2 Prediction
        if '1x2' in self.models:
            model = self.models['1x2']
            proba = model.predict_proba(features)[0]
            classes = ['away', 'draw', 'home']  # Based on LabelEncoder classes
            
            predictions['markets']['1x2'] = {
                'home': round(proba[classes.index('home')], 3),
                'draw': round(proba[classes.index('draw')], 3),
                'away': round(proba[classes.index('away')], 3),
                'prediction': classes[np.argmax(proba)],
                'confidence': round(float(np.max(proba)), 3)
            }
        
        # Over/Under 2.5 Prediction
        if 'over_under_25' in self.models:
            model = self.models['over_under_25']
            proba = model.predict_proba(features)[0]
            
            predictions['markets']['over_under'] = {
                'over_prob': round(proba[1], 3),
                'under_prob': round(proba[0], 3),
                'recommendation': 'Over 2.5' if proba[1] > proba[0] else 'Under 2.5',
                'confidence': round(abs(proba[1] - proba[0]), 3),
                'line': 2.5
            }
        
        # Over/Under 1.5 Prediction
        if 'over_under_15' in self.models:
            model = self.models['over_under_15']
            proba = model.predict_proba(features)[0]
            
            predictions['markets']['over_under_15'] = {
                'over_1_5': round(proba[1], 3),
                'under_1_5': round(proba[0], 3),
                'prediction': 'Over 1.5' if proba[1] > proba[0] else 'Under 1.5',
                'confidence': round(abs(proba[1] - proba[0]), 3),
                'line': 1.5
            }
        
        # Asian Handicap Prediction
        if 'asian_handicap' in self.models:
            model = self.models['asian_handicap']
            proba = model.predict_proba(features)[0]
            
            predictions['markets']['asian_handicap'] = {
                'prediction': 'home_win' if proba[0] > 0.5 else 'away_win',
                'confidence': round(float(np.max(proba)), 3)
            }
        
        # Total Goals Prediction
        if 'total_goals' in self.models:
            model = self.models['total_goals']
            pred = model.predict(features)[0]
            
            predictions['markets']['total_goals'] = {
                'prediction': int(pred),
                'most_likely': int(pred)
            }
        
        # Correct Score Prediction
        if 'correct_score' in self.models:
            model = self.models['correct_score']
            proba = model.predict_proba(features)[0]
            classes = model.classes_ if hasattr(model, 'classes_') else []
            
            predictions['markets']['correct_score'] = {
                'prediction': str(classes[np.argmax(proba)]) if len(classes) > 0 else 'unknown',
                'confidence': round(float(np.max(proba)), 3)
            }
        
        # Calculate overall confidence
        if predictions['markets']:
            confidences = [m.get('confidence', 0) for m in predictions['markets'].values()]
            predictions['confidence'] = round(np.mean(confidences), 3)
        else:
            predictions['confidence'] = 0.0
        
        return predictions
    
    def calibrate(self, historical_data: List[Dict]) -> None:
        """Placeholder for calibration - not needed for XGBoost"""
        pass


if __name__ == '__main__':
    # Test loading
    print("Loading XGBoost models...")
    predictor = XGBoostPredictor()
    
    print(f"\nLoaded markets: {predictor.supported_markets}")
    
    # Test prediction
    test_match = {
        'home': 'Germany',
        'away': 'Japan',
        'home_avg_scored': 2.0,
        'home_avg_conceded': 1.0,
        'home_xg': 2.3,
        'home_poss': 60,
        'home_form': 2.0,
        'away_avg_scored': 1.0,
        'away_avg_conceded': 2.0,
        'away_xg': 0.8,
        'away_poss': 40,
        'away_form': 1.0
    }
    
    result = predictor.predict(test_match)
    print(f"\nTest prediction:")
    print(json.dumps(result, indent=2))
