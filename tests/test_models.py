"""
Football Quant OS - 模型单元测试
覆盖: BaseModel, HeuristicModel, PoissonModel, ModelEnsemble
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from models import HeuristicModel, PoissonModel, ModelEnsemble


# ============================================================
# 测试数据
# ============================================================

MATCH_INFO_BASE = {
    'home': 'TEST_HOME',
    'away': 'TEST_AWAY',
    'odds_home': 2.0,
    'odds_draw': 3.2,
    'odds_away': 3.8,
    'stage': 'group'
}

MATCH_INFO_WITH_XG = {
    **MATCH_INFO_BASE,
    'home_xg': 1.5,
    'away_xg': 1.2,
    'home_poss': 55,
    'away_poss': 45
}

MATCH_INFO_UPSET = {
    'home': 'ARGENTINA',
    'away': 'SAUDI ARABIA',
    'odds_home': 1.25,
    'odds_draw': 5.5,
    'odds_away': 12.0,
    'stage': 'group'
}


# ============================================================
# HeuristicModel 测试
# ============================================================

class TestHeuristicModel:
    
    def setup_method(self):
        self.model = HeuristicModel()
    
    def test_name_and_version(self):
        assert self.model.name == "HeuristicModel"
        assert self.model.version == "4.3.6"
    
    def test_supported_markets(self):
        markets = self.model.supported_markets
        assert '1x2' in markets
        assert 'over_under' in markets
        assert 'upset_score' in markets
    
    def test_predict_basic(self):
        result = self.model.predict(MATCH_INFO_BASE)
        assert 'error' not in result
        assert result['model_name'] == 'HeuristicModel'
        assert 'markets' in result
        assert '1x2' in result['markets']
        assert 'over_under' in result['markets']
        assert 'upset_score' in result['markets']
    
    def test_predict_missing_required_field(self):
        bad_info = {'home': 'A', 'away': 'B'}  # 缺少赔率
        result = self.model.predict(bad_info)
        assert 'error' in result
    
    def test_predict_invalid_odds(self):
        bad_info = {**MATCH_INFO_BASE, 'odds_home': 0.5}  # 赔率<1
        result = self.model.predict(bad_info)
        assert 'error' in result
    
    def test_1x2_probability_sum(self):
        result = self.model.predict(MATCH_INFO_BASE)
        m1x2 = result['markets']['1x2']
        model_probs = m1x2['model']
        total = model_probs['home'] + model_probs['draw'] + model_probs['away']
        assert 0.99 <= total <= 1.01  # 允许浮点误差
    
    def test_1x2_edge_calculation(self):
        result = self.model.predict(MATCH_INFO_BASE)
        m1x2 = result['markets']['1x2']
        # Edge = model_prob - implied_prob
        home_edge = m1x2['edge']['home']
        implied_home = m1x2['implied']['home']
        model_home = m1x2['model']['home']
        assert abs(home_edge - (model_home - implied_home)) < 0.001
    
    def test_upset_score_range(self):
        result = self.model.predict(MATCH_INFO_BASE)
        score = result['markets']['upset_score']
        assert 0 <= score <= 65
    
    def test_upset_score_higher_for_favorite(self):
        # 强队vs弱队应该有更高的冷门评分
        result_upset = self.model.predict(MATCH_INFO_UPSET)
        result_base = self.model.predict(MATCH_INFO_BASE)
        assert result_upset['markets']['upset_score'] > result_base['markets']['upset_score']
    
    def test_stage_calibration(self):
        # 小组赛和淘汰赛的校准系数不同
        group_result = self.model.predict({**MATCH_INFO_BASE, 'stage': 'group'})
        knockout_result = self.model.predict({**MATCH_INFO_BASE, 'stage': 'knockout'})
        
        group_home = group_result['markets']['1x2']['model']['home']
        knockout_home = knockout_result['markets']['1x2']['model']['home']
        # 淘汰赛强队概率应该更高(上调20%)
        assert knockout_home > group_home
    
    def test_calibrate_empty_data(self):
        result = self.model.calibrate([])
        assert result['calibration_success'] == False
    
    def test_calibrate_with_data(self):
        historical = [
            {'stage': 'group', 'is_upset': True},
            {'stage': 'group', 'is_upset': False},
            {'stage': 'knockout', 'is_upset': True},
            {'stage': 'knockout', 'is_upset': False}
        ]
        result = self.model.calibrate(historical)
        assert result['calibration_success'] == True
        assert 'metrics' in result
        assert 'parameters' in result


# ============================================================
# PoissonModel 测试
# ============================================================

class TestPoissonModel:
    
    def setup_method(self):
        self.model = PoissonModel()
    
    def test_name_and_version(self):
        assert self.model.name == "PoissonModel"
        assert self.model.version == "2.1"
    
    def test_supported_markets(self):
        markets = self.model.supported_markets
        assert 'over_under' in markets
        assert '1x2' not in markets  # 泊松模型只支持大小球
    
    def test_predict_basic(self):
        result = self.model.predict(MATCH_INFO_BASE)
        assert 'error' not in result
        assert result['model_name'] == 'PoissonModel'
        assert 'over_under' in result['markets']
    
    def test_predict_with_xg(self):
        result = self.model.predict(MATCH_INFO_WITH_XG)
        ou = result['markets']['over_under']
        # 有xG时lambda应该基于xG
        expected_lambda = 1.5 + 1.2  # home_xg + away_xg
        assert abs(ou['lambda'] - expected_lambda * 0.95) < 0.5  # 允许阶段因子影响
    
    def test_lambda_range(self):
        result = self.model.predict(MATCH_INFO_BASE)
        lambda_val = result['markets']['over_under']['lambda']
        assert 1.2 <= lambda_val <= 4.5
    
    def test_probability_sum(self):
        result = self.model.predict(MATCH_INFO_BASE)
        ou = result['markets']['over_under']
        total = ou['over_prob'] + ou['under_prob']
        assert 0.99 <= total <= 1.01
    
    def test_first_match_factor(self):
        # 首战因子
        base = self.model.predict(MATCH_INFO_BASE)
        first_match = self.model.predict({**MATCH_INFO_BASE, 'is_first_match': True})
        # 首战后lambda应该变化
        base_lambda = base['markets']['over_under']['lambda']
        first_lambda = first_match['markets']['over_under']['lambda']
        assert base_lambda != first_lambda
    
    def test_motivation_factor(self):
        # 战意因子
        neutral = self.model.predict({**MATCH_INFO_BASE, 'motivation': 'neutral'})
        must_win = self.model.predict({**MATCH_INFO_BASE, 'motivation': 'must_win'})
        # must_win应该提高lambda
        assert must_win['markets']['over_under']['lambda'] > neutral['markets']['over_under']['lambda']
    
    def test_regional_factor(self):
        # 区域因子
        neutral = self.model.predict({**MATCH_INFO_BASE, 'home_region': 'neutral', 'away_region': 'neutral'})
        asia_europe = self.model.predict({**MATCH_INFO_BASE, 'home_region': 'asia', 'away_region': 'europe'})
        # 亚洲vs欧洲有特定因子
        assert asia_europe['markets']['over_under']['lambda'] != neutral['markets']['over_under']['lambda']
    
    def test_newbie_factor(self):
        # 新军因子
        experienced = self.model.predict({**MATCH_INFO_BASE, 'home_experience': 'experienced'})
        newbie = self.model.predict({**MATCH_INFO_BASE, 'home_experience': 'newbie'})
        # 新军应该降低lambda
        assert newbie['markets']['over_under']['lambda'] < experienced['markets']['over_under']['lambda']
    
    def test_most_likely_goals(self):
        result = self.model.predict(MATCH_INFO_BASE)
        most_likely = result['markets']['over_under']['most_likely']
        assert isinstance(most_likely, int)
        assert 0 <= most_likely <= 7
    
    def test_edge_calculation(self):
        result = self.model.predict({
            **MATCH_INFO_BASE,
            'odds_over': 1.9,
            'odds_under': 1.9
        })
        ou = result['markets']['over_under']
        # 有赔率时应该有edge计算
        assert 'edge' in ou


# ============================================================
# ModelEnsemble 测试
# ============================================================

class TestModelEnsemble:
    
    def setup_method(self):
        self.ensemble = ModelEnsemble()
        self.heuristic = HeuristicModel()
        self.poisson = PoissonModel()
        self.ensemble.add_model(self.heuristic, weight=0.3)
        self.ensemble.add_model(self.poisson, weight=0.7)
    
    def test_name_and_version(self):
        assert self.ensemble.name == "ModelEnsemble"
        assert self.ensemble.version == "1.0"
    
    def test_supported_markets(self):
        markets = self.ensemble.supported_markets
        # 应该包含两个子模型的并集
        assert '1x2' in markets
        assert 'over_under' in markets
        assert 'upset_score' in markets
    
    def test_predict_basic(self):
        result = self.ensemble.predict(MATCH_INFO_BASE)
        assert 'error' not in result
        assert 'markets' in result
        assert 'confidence' in result
        assert 'metadata' in result
        # 检查包含子模型信息
        assert 'models_used' in result['metadata']
        assert 'HeuristicModel' in result['metadata']['models_used']
        assert 'PoissonModel' in result['metadata']['models_used']
    
    def test_predict_with_kwargs(self):
        result = self.ensemble.predict(MATCH_INFO_WITH_XG)
        assert 'error' not in result
        assert 'over_under' in result['markets']
    
    def test_empty_ensemble(self):
        empty = ModelEnsemble()
        result = empty.predict(MATCH_INFO_BASE)
        assert 'error' in result
    
    def test_weight_normalization(self):
        # 权重应该归一化
        raw_weights = self.ensemble._weights
        total = sum(raw_weights)
        assert abs(total - 1.0) < 0.001
    
    def test_1x2_fusion(self):
        result = self.ensemble.predict(MATCH_INFO_BASE)
        m1x2 = result['markets']['1x2']
        # 融合后的概率和应该接近1
        total = m1x2['model']['home'] + m1x2['model']['draw'] + m1x2['model']['away']
        assert 0.99 <= total <= 1.01
    
    def test_calibrate(self):
        historical = [
            {'stage': 'group', 'is_upset': True, 'home_xg': 1.5, 'away_xg': 1.0, 'total_goals': 2},
            {'stage': 'group', 'is_upset': False, 'home_xg': 2.0, 'away_xg': 0.5, 'total_goals': 3}
        ]
        result = self.ensemble.calibrate(historical)
        assert result['calibration_success'] == True
        assert 'individual_results' in result
        assert 'adjusted_weights' in result


# ============================================================
# 集成测试
# ============================================================

class TestIntegration:
    """集成测试 - 模拟完整预测流程"""
    
    def test_full_prediction_pipeline(self):
        """完整预测流程"""
        ensemble = ModelEnsemble()
        ensemble.add_model(HeuristicModel(), weight=0.3)
        ensemble.add_model(PoissonModel(), weight=0.7)
        
        match_info = {
            'home': 'GERMANY',
            'away': 'JAPAN',
            'odds_home': 1.30,
            'odds_draw': 4.50,
            'odds_away': 8.50,
            'stage': 'group',
            'home_xg': 2.3,
            'away_xg': 0.8,
            'home_region': 'europe',
            'away_region': 'asia',
            'is_first_match': True
        }
        
        result = ensemble.predict(match_info)
        
        assert 'error' not in result
        assert 'markets' in result
        assert result['confidence'] > 0
        assert result['confidence'] <= 1
    
    def test_multiple_predictions_consistency(self):
        """多次预测结果一致性"""
        model = HeuristicModel()
        
        result1 = model.predict(MATCH_INFO_BASE)
        result2 = model.predict(MATCH_INFO_BASE)
        
        # 相同输入应该产生相同输出
        assert result1['markets']['1x2']['model'] == result2['markets']['1x2']['model']


# ============================================================
# 性能测试
# ============================================================

class TestPerformance:
    """简单性能测试"""
    
    def test_prediction_speed(self):
        """预测速度测试"""
        import time
        
        ensemble = ModelEnsemble()
        ensemble.add_model(HeuristicModel(), weight=0.5)
        ensemble.add_model(PoissonModel(), weight=0.5)
        
        start = time.time()
        for _ in range(100):
            ensemble.predict(MATCH_INFO_BASE)
        elapsed = time.time() - start
        
        # 100次预测应该<1秒
        assert elapsed < 1.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
