"""
Football Quant OS - Feature Engineering Tests
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import numpy as np
from features.feature_engineer import FeatureEngineer, TeamFeatures, load_features_from_data_fetcher


class TestFeatureEngineer:
    """Test feature engineering"""
    
    def setup_method(self):
        self.mock_matches = [
            {'home': 'Germany', 'away': 'Japan', 'home_score': 1, 'away_score': 2, 'home_xg': 2.3, 'away_xg': 0.8},
            {'home': 'Spain', 'away': 'Costa Rica', 'home_score': 7, 'away_score': 0, 'home_xg': 4.5, 'away_xg': 0.3},
            {'home': 'Brazil', 'away': 'Serbia', 'home_score': 2, 'away_score': 0, 'home_xg': 2.8, 'away_xg': 0.5},
            {'home': 'Germany', 'away': 'Spain', 'home_score': 1, 'away_score': 1, 'home_xg': 1.2, 'away_xg': 1.8},
            {'home': 'Japan', 'away': 'Spain', 'home_score': 2, 'away_score': 1, 'home_xg': 1.5, 'away_xg': 2.0},
        ]
        self.engineer = FeatureEngineer(self.mock_matches)
    
    def test_team_features_basic(self):
        features = self.engineer.extract_team_features('Germany')
        assert features.team == 'Germany'
        assert features.avg_goals_scored > 0
        assert features.avg_goals_conceded > 0
    
    def test_team_features_default(self):
        features = self.engineer.extract_team_features('UnknownTeam')
        assert features.avg_goals_scored == 1.0  # Default value
    
    def test_team_features_vector(self):
        features = self.engineer.extract_team_features('Germany')
        vector = features.to_vector()
        assert len(vector) == 9
        assert isinstance(vector, np.ndarray)
    
    def test_match_features(self):
        mf = self.engineer.extract_match_features('Germany', 'Japan')
        assert 'home' in mf
        assert 'away' in mf
        assert 'interaction' in mf
        assert 'head_to_head' in mf
    
    def test_interaction_features(self):
        mf = self.engineer.extract_match_features('Germany', 'Japan')
        inter = mf['interaction']
        assert 'total_xg' in inter
        assert inter['total_xg'] > 0
    
    def test_head_to_head(self):
        h2h = self.engineer._get_head_to_head('Germany', 'Japan')
        assert h2h['matches'] >= 1
        assert h2h['avg_total_goals'] > 0
    
    def test_training_data(self):
        data = self.engineer.build_training_data(lookback=3)
        assert len(data) > 0
        
        sample = data[0]
        assert 'label' in sample
        assert 'total_goals' in sample['label']
        assert 'over_2_5' in sample['label']
    
    def test_feature_importance(self):
        importance = self.engineer.get_feature_importance([])
        assert len(importance) > 0
        assert 'avg_xg' in importance
        assert sum(importance.values()) > 0


class TestTeamFeatures:
    """Test TeamFeatures dataclass"""
    
    def test_creation(self):
        f = TeamFeatures(
            team='Test', avg_goals_scored=2.0, avg_goals_conceded=1.0,
            avg_xg=1.8, recent_form=2.0, attack_efficiency=1.1,
            defense_efficiency=0.9, home_advantage=1.2,
            away_disadvantage=0.8, consistency=0.6
        )
        assert f.team == 'Test'
    
    def test_to_dict(self):
        f = TeamFeatures(
            team='Test', avg_goals_scored=2.0, avg_goals_conceded=1.0,
            avg_xg=1.8, recent_form=2.0, attack_efficiency=1.1,
            defense_efficiency=0.9, home_advantage=1.2,
            away_disadvantage=0.8, consistency=0.6
        )
        d = f.to_dict()
        assert d['team'] == 'Test'
        assert d['avg_goals_scored'] == 2.0


class TestDataFetcherIntegration:
    """Test integration with data fetchers"""
    
    def test_load_from_fetcher(self):
        from data.data_fetcher import KaggleFetcher
        fetcher = KaggleFetcher()
        engineer = load_features_from_data_fetcher(fetcher, year=2022)
        assert isinstance(engineer, FeatureEngineer)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
