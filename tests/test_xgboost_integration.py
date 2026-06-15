"""
Test XGBoost Model Integration

pytest tests/test_xgboost_integration.py -v
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import json

from models.xgboost_model import XGBoostPredictor
from models.heuristic_model import HeuristicModel
from models.poisson_model import PoissonModel
from models.ensemble import ModelEnsemble
from features.feature_engineer import FeatureEngineer


@pytest.fixture
def trained_xgb():
    """加载已训练的 XGBoost 模型"""
    path = Path(__file__).parent.parent / 'models' / 'xgboost_v1.pkl'
    if not path.exists():
        pytest.skip("XGBoost model not trained yet. Run: python scripts/train_xgboost.py")
    return XGBoostPredictor(model_path=str(path))


@pytest.fixture
def sample_features():
    """模拟 feature_engineer 输出格式"""
    return {
        'home': {
            'team': 'Germany', 'avg_goals_scored': 2.0, 'avg_goals_conceded': 0.8,
            'avg_xg': 2.3, 'recent_form': 2.5, 'attack_efficiency': 1.2,
            'defense_efficiency': 1.1, 'home_advantage': 1.3, 'consistency': 0.7
        },
        'away': {
            'team': 'Japan', 'avg_goals_scored': 1.5, 'avg_goals_conceded': 1.2,
            'avg_xg': 1.3, 'recent_form': 1.8, 'attack_efficiency': 1.0,
            'defense_efficiency': 0.9, 'away_disadvantage': 0.8, 'consistency': 0.6
        },
        'interaction': {
            'home_xg_diff': 1.1, 'away_xg_diff': -0.3, 'total_xg': 3.6,
            'home_attack_vs_away_defense': 1.3, 'away_attack_vs_home_defense': 0.9
        },
        'head_to_head': {'matches': 2, 'team1_wins': 1, 'team2_wins': 1, 'draws': 0, 'avg_total_goals': 2.5},
        'odds_home': 1.8, 'odds_draw': 3.4, 'odds_away': 4.5, 'odds_over_2_5': 1.9
    }


class TestXGBoostPredictor:
    def test_model_loaded(self, trained_xgb):
        assert trained_xgb.is_trained
        assert trained_xgb._ou_accuracy > 0.4
        assert trained_xgb._1x2_accuracy > 0.3

    def test_predict_feature_format(self, trained_xgb, sample_features):
        pred = trained_xgb.predict(sample_features)
        assert 'error' not in pred
        assert 'markets' in pred
        assert 'over_under' in pred['markets']
        assert '1x2' in pred['markets']

    def test_predict_simple_format_returns_error(self, trained_xgb):
        """简单格式应返回 error，由 ensemble 跳过"""
        simple = {'home': 'Germany', 'away': 'Japan', 'odds_home': 1.8, 'odds_draw': 3.4, 'odds_away': 4.5}
        pred = trained_xgb.predict(simple)
        assert 'error' in pred

    def test_feature_importance(self, trained_xgb):
        imp = trained_xgb.get_feature_importance('over_under')
        assert len(imp) == len(XGBoostPredictor.FEATURE_NAMES)
        assert sum(imp.values()) > 0.99  # 归一化后接近1

    def test_save_load_roundtrip(self, trained_xgb, tmp_path):
        path = tmp_path / 'test_xgb.pkl'
        trained_xgb.save(str(path))
        assert path.exists()

        xgb2 = XGBoostPredictor(model_path=str(path))
        assert xgb2.is_trained
        assert xgb2._ou_accuracy == trained_xgb._ou_accuracy


class TestEnsembleIntegration:
    def test_ensemble_with_xgboost(self, trained_xgb, sample_features):
        ensemble = ModelEnsemble()
        ensemble.add_model(HeuristicModel(), weight=0.3)
        ensemble.add_model(PoissonModel(), weight=0.5)
        ensemble.add_model(trained_xgb, weight=0.3)

        pred = ensemble.predict(sample_features)
        assert 'error' not in pred
        assert 'XGBoostPredictor' in pred['metadata']['models_used']
        assert 'over_under' in pred['markets']
        assert '1x2' in pred['markets']

    def test_ensemble_skips_xgboost_for_simple_input(self, trained_xgb):
        """简单输入时 XGBoost 被跳过，其他模型正常工作"""
        ensemble = ModelEnsemble()
        ensemble.add_model(HeuristicModel(), weight=0.3)
        ensemble.add_model(PoissonModel(), weight=0.5)
        ensemble.add_model(trained_xgb, weight=0.3)

        simple = {'home': 'Germany', 'away': 'Japan', 'odds_home': 1.8, 'odds_draw': 3.4, 'odds_away': 4.5}
        pred = ensemble.predict(simple)

        assert 'error' not in pred
        models_used = pred['metadata']['models_used']
        assert 'HeuristicModel' in models_used
        assert 'PoissonModel' in models_used
        assert 'XGBoostPredictor' not in models_used  # 被跳过

    def test_fusion_probabilities_sum_to_one(self, trained_xgb, sample_features):
        ensemble = ModelEnsemble()
        ensemble.add_model(HeuristicModel(), weight=0.3)
        ensemble.add_model(PoissonModel(), weight=0.5)
        ensemble.add_model(trained_xgb, weight=0.3)

        pred = ensemble.predict(sample_features)
        m1x2 = pred['markets']['1x2']['model']
        total = m1x2['home'] + m1x2['draw'] + m1x2['away']
        assert 0.99 <= total <= 1.01
