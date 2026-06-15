#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Core Tests - Football Quant OS v4.2.1-naga
Priority: Kelly (capital management) > Matrix 108 (probability) > Predictor (engine)
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from models.kelly import Kelly
from models.matrix_108 import ProbabilityMatrix108
from agents.multi_market_predictor import MultiMarketPredictor, Match


class TestKelly:
    """Test Kelly criterion - capital management (CRITICAL for money safety)"""
    
    def test_kelly_basic(self):
        k = Kelly(bankroll=10000)
        result = k.calculate(probability=0.55, odds=2.0)
        assert result['stake'] > 0
        assert result['stake'] <= 1000  # max 10% bankroll per config
        assert result['risk_level'] in ['LOW', 'MEDIUM', 'HIGH']
    
    def test_kelly_negative_edge(self):
        k = Kelly(bankroll=10000)
        # No edge - should not bet or minimal
        result = k.calculate(probability=0.5, odds=2.0)
        assert result['kelly_fraction'] <= 0.01  # Near zero or zero
    
    def test_kelly_max_cap(self):
        k = Kelly(bankroll=10000)
        # Even with huge edge, max is capped by config
        result = k.calculate(probability=0.9, odds=10.0)
        assert result['safe_fraction'] <= 0.05  # 5% max per config
        assert result['stake'] <= 1000  # 10% max bet


class TestMatrix108:
    """Test 108 probability matrix"""
    
    def test_probabilities_sum_to_100(self):
        m = ProbabilityMatrix108()
        result = m.apply_to_match(strength_gap='strong_vs_weak')
        probs = result['probabilities']
        total = probs['home_win'] + probs['draw'] + probs['away_win']
        assert abs(total - 100.0) < 2.0  # Allow small rounding error
    
    def test_home_advantage_effect(self):
        m = ProbabilityMatrix108()
        # Test different strength gaps produce different results
        result_strong = m.apply_to_match(strength_gap='strong_vs_weak')
        result_even = m.apply_to_match(strength_gap='even')
        assert result_strong['probabilities']['home_win'] != result_even['probabilities']['home_win']


class TestMultiMarketPredictor:
    """Test prediction engine with CoachFactor integration"""
    
    def test_qatar_vs_switzerland(self):
        match = Match(
            home='Qatar', away='Switzerland', competition='World Cup', date='2026-06-14',
            home_fifa_rank=50, away_fifa_rank=15,
            home_recent_form=['D','L','D','L'], away_recent_form=['D','W','D','L','D'],
            home_goals_scored=1, home_goals_conceded=7,
            away_goals_scored=9, away_goals_conceded=7,
            odds_1x2=(16.00, 7.36, 1.24),
            odds_ah={'+2.0': (1.67, 3.70)},
            odds_ou={'2.5': (1.61, 1.00)},
            coach_home_cri=3.1, coach_away_cri=4.8,
            venue_type='neutral'
        )
        
        predictor = MultiMarketPredictor(match)
        result = predictor.predict_1x2()
        
        # Prediction should be away win (Switzerland is stronger)
        assert result.prediction == '客胜'
        # But value bet might be on home (high odds)
        assert result.edge != 0
    
    def test_venue_type_affects_probability(self):
        # Neutral venue
        match_neutral = Match(
            home='Qatar', away='Switzerland', competition='World Cup', date='2026-06-14',
            home_fifa_rank=50, away_fifa_rank=15,
            home_recent_form=['D','L','D','L'], away_recent_form=['D','W','D','L','D'],
            home_goals_scored=1, home_goals_conceded=7,
            away_goals_scored=9, away_goals_conceded=7,
            odds_1x2=(16.00, 7.36, 1.24),
            odds_ah={'+2.0': (1.67, 3.70)},
            odds_ou={'2.5': (1.61, 1.00)},
            coach_home_cri=3.1, coach_away_cri=4.8,
            venue_type='neutral'
        )
        
        # Home venue
        match_home = Match(
            home='Qatar', away='Switzerland', competition='World Cup', date='2026-06-14',
            home_fifa_rank=50, away_fifa_rank=15,
            home_recent_form=['D','L','D','L'], away_recent_form=['D','W','D','L','D'],
            home_goals_scored=1, home_goals_conceded=7,
            away_goals_scored=9, away_goals_conceded=7,
            odds_1x2=(16.00, 7.36, 1.24),
            odds_ah={'+2.0': (1.67, 3.70)},
            odds_ou={'2.5': (1.61, 1.00)},
            coach_home_cri=3.1, coach_away_cri=4.8,
            venue_type='home'
        )
        
        p_neutral = MultiMarketPredictor(match_neutral).predict_1x2()
        p_home = MultiMarketPredictor(match_home).predict_1x2()
        
        # Home venue should give higher probability to home team
        assert p_home.confidence >= p_neutral.confidence


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
