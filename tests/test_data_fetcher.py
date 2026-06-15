"""
Football Quant OS - DataFetcher 单元测试
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from data.data_fetcher import (
    DataFetcherFactory, KaggleFetcher, FootballDataFetcher, 
    APIFootballFetcher, FootballDataOrgFetcher, MultiSourceFetcher
)


class TestDataFetcherFactory:
    """测试数据获取工厂"""
    
    def test_available_sources(self):
        sources = DataFetcherFactory.available_sources()
        assert 'kaggle' in sources
        assert 'football_data' in sources
        assert 'api_football' in sources
    
    def test_create_kaggle(self):
        fetcher = DataFetcherFactory.create('kaggle')
        assert isinstance(fetcher, KaggleFetcher)
        assert fetcher.name == 'KaggleFetcher'
    
    def test_create_football_data(self):
        fetcher = DataFetcherFactory.create('football_data')
        assert isinstance(fetcher, FootballDataFetcher)
        assert fetcher.name == 'FootballDataFetcher'
    
    def test_create_api_football(self):
        fetcher = DataFetcherFactory.create('api_football')
        assert isinstance(fetcher, APIFootballFetcher)
        assert fetcher.name == 'APIFootballFetcher'
    
    def test_create_unknown(self):
        with pytest.raises(ValueError):
            DataFetcherFactory.create('unknown')
    
    def test_register_new_fetcher(self):
        class MockFetcher:
            @property
            def name(self): return 'Mock'
        
        DataFetcherFactory.register('mock', MockFetcher)
        assert 'mock' in DataFetcherFactory.available_sources()


class TestKaggleFetcher:
    """测试Kaggle数据源"""
    
    def setup_method(self):
        self.fetcher = KaggleFetcher()
    
    def test_properties(self):
        assert self.fetcher.supports_historical == True
        assert self.fetcher.supports_live == False
    
    def test_fetch_matches_2022(self):
        matches = self.fetcher.fetch_matches(year=2022)
        # 可能为空(文件不存在)，但不报错
        assert isinstance(matches, list)
    
    def test_fetch_teams(self):
        teams = self.fetcher.fetch_teams(year=2022)
        assert isinstance(teams, list)
    
    def test_validate_data_empty(self):
        valid, errors = self.fetcher.validate_data([])
        assert valid == False
        assert 'Empty data' in errors[0]
    
    def test_validate_data_good(self):
        data = [{'home': 'A', 'away': 'B', 'stage': 'group'}]
        valid, errors = self.fetcher.validate_data(data)
        assert valid == True
        assert len(errors) == 0
    
    def test_validate_data_missing_field(self):
        data = [{'home': 'A', 'away': 'B'}]  # 缺少 stage
        valid, errors = self.fetcher.validate_data(data)
        assert valid == False
        assert any('stage' in e for e in errors)


class TestFootballDataOrgFetcher:
    """测试 Football-Data.org 数据源"""
    
    def test_properties(self):
        fetcher = FootballDataOrgFetcher()
        assert fetcher.supports_historical == True
        assert fetcher.supports_live == True
    
    def test_no_api_key(self):
        fetcher = FootballDataOrgFetcher()
        matches = fetcher.fetch_matches()
        assert len(matches) == 1
        assert 'error' in matches[0]
    
    def test_get_request_stats(self):
        fetcher = FootballDataOrgFetcher()
        stats = fetcher.get_request_stats()
        assert 'requests_made' in stats
        assert 'rate_limit' in stats


class TestAPIFootballFetcher:
    """测试API-Football数据源"""
    
    def test_properties(self):
        fetcher = APIFootballFetcher()
        assert fetcher.supports_historical == True
        assert fetcher.supports_live == True
    
    def test_no_api_key(self):
        fetcher = APIFootballFetcher()
        matches = fetcher.fetch_matches()
        assert len(matches) == 1
        assert 'error' in matches[0]
    
    def test_with_api_key(self):
        fetcher = APIFootballFetcher(api_key='test_key')
        # 有 API key 时尝试真实请求，但 test_key 无效
        # 应该返回错误而不是 mock 数据
        matches = fetcher.fetch_matches()
        assert len(matches) == 1
        assert 'error' in matches[0]  # test_key 是无效的，会返回错误


class TestMultiSourceFetcher:
    """测试多数据源聚合器"""
    
    def test_init(self):
        fetcher = MultiSourceFetcher(['kaggle', 'football_data'])
        assert 'kaggle' in fetcher.fetchers
        assert 'football_data' in fetcher.fetchers
    
    def test_fetch_matches(self):
        fetcher = MultiSourceFetcher(['kaggle'])
        matches = fetcher.fetch_matches(year=2022)
        assert isinstance(matches, list)
    
    def test_fetch_odds_fallback(self):
        fetcher = MultiSourceFetcher(['kaggle'])
        odds = fetcher.fetch_odds('test_match')
        assert isinstance(odds, dict)


class TestKellyIntegration:
    """测试Kelly集成模块"""
    
    def test_kelly_import(self):
        from models.kelly_integration import BettingOpportunity, calculate_kelly_stake
        opp = BettingOpportunity(
            match='A vs B', market='1x2', selection='home',
            odds=2.0, model_probability=0.55, model_confidence=0.7, edge=0.05
        )
        result = calculate_kelly_stake(opp, bankroll=100000)
        assert result['action'] == 'bet'
        assert result['stake'] > 0
    
    def test_kelly_negative(self):
        from models.kelly_integration import BettingOpportunity, calculate_kelly_stake
        opp = BettingOpportunity(
            match='A vs B', market='1x2', selection='home',
            odds=1.5, model_probability=0.3, model_confidence=0.7, edge=-0.1
        )
        result = calculate_kelly_stake(opp, bankroll=100000)
        assert result['action'] == 'skip'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
