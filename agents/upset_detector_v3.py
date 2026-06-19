# -*- coding: utf-8 -*-
"""
UpsetDetector v3.0 - Football Quant OS
注入: 04 Citadel 信号发现
增强: 信号IC监控 + 衰减分析 + 拥挤度检测 + 制度检测

相比 v2.0:
- 信号IC: 冷门信号与实际冷门结果的秩相关系数
- 衰减分析: 冷门信号半衰期计算
- 拥挤度: 市场是否过度关注冷门指标
- 制度检测: 不同赛事阶段冷门信号有效性差异
- 信号组合: 多个冷门信号的加权组合
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math
import json
import numpy as np
from collections import deque


class UpsetLevel(Enum):
    NORMAL = "normal"
    WATCH = "watch"
    CANDIDATE = "candidate"
    STRONG = "strong"


class MatchStage(Enum):
    GROUP_RD1 = "group_round_1"
    GROUP_RD2 = "group_round_2"
    GROUP_RD3 = "group_round_3"
    ROUND_16 = "round_of_16"
    QUARTER = "quarter_final"
    SEMI = "semi_final"
    FINAL = "final"


@dataclass
class SignalIC:
    """信号IC记录"""
    timestamp: str
    predicted_score: float
    actual_upset: bool
    ic: float
    regime: str


@dataclass
class UpsetFactors:
    """冷门因子"""
    big_team_hype: float = 0.0
    odds_reverse: float = 0.0
    abnormal_flow: float = 0.0
    region_upset: float = 0.0
    elo_overvalued: float = 0.0
    xg_undervalued: float = 0.0
    motivation_gap: float = 0.0
    
    @property
    def total_score(self) -> float:
        return sum([
            self.big_team_hype, self.odds_reverse, self.abnormal_flow,
            self.region_upset, self.elo_overvalued, self.xg_undervalued,
            self.motivation_gap
        ])


class SignalValidator:
    """信号验证器 - Citadel 级统计严谨"""
    
    def __init__(self, min_samples: int = 10):
        self.min_samples = min_samples
        self.history: deque = deque(maxlen=100)
    
    def record(self, predicted_score: float, actual_upset: bool, regime: str) -> None:
        """记录预测结果"""
        self.history.append({
            'timestamp': datetime.now().isoformat(),
            'predicted_score': predicted_score,
            'actual_upset': actual_upset,
            'regime': regime
        })
    
    def calculate_ic(self, regime: str = None) -> Dict[str, float]:
        """计算信息系数"""
        if len(self.history) < self.min_samples:
            return {'ic': 0.0, 't_stat': 0.0, 'significant': False}
        
        data = list(self.history)
        if regime:
            data = [d for d in data if d['regime'] == regime]
        
        if len(data) < self.min_samples:
            return {'ic': 0.0, 't_stat': 0.0, 'significant': False}
        
        scores = [d['predicted_score'] for d in data]
        actuals = [1.0 if d['actual_upset'] else 0.0 for d in data]
        
        # Spearman 秩相关系数
        from scipy import stats
        ic, p_value = stats.spearmanr(scores, actuals)
        
        n = len(data)
        t_stat = ic * math.sqrt(n - 2) / math.sqrt(1 - ic**2) if abs(ic) < 1 else 0
        
        return {
            'ic': round(ic, 4),
            't_stat': round(t_stat, 4),
            'p_value': round(p_value, 4),
            'significant': p_value < 0.05,
            'sample_size': n
        }
    
    def decay_analysis(self) -> Dict[str, float]:
        """衰减分析"""
        if len(self.history) < 20:
            return {'half_life': 30.0, 'trend': 'stable'}
        
        data = list(self.history)
        n = len(data)
        
        # 分前半段和后半段
        first_half = data[:n//2]
        second_half = data[n//2:]
        
        first_ic = self._calculate_ic_subset(first_half)
        second_ic = self._calculate_ic_subset(second_half)
        
        if first_ic > 0 and second_ic > 0:
            decay_ratio = second_ic / first_ic
            half_life = -30 / math.log(decay_ratio) if decay_ratio > 0 else 10.0
        else:
            half_life = 10.0
        
        trend = 'decaying' if second_ic < first_ic * 0.7 else 'stable'
        
        return {
            'half_life': round(min(half_life, 100), 1),
            'trend': trend,
            'first_ic': round(first_ic, 4),
            'second_ic': round(second_ic, 4)
        }
    
    def _calculate_ic_subset(self, data: List[Dict]) -> float:
        """计算子集IC"""
        if len(data) < 5:
            return 0.0
        scores = [d['predicted_score'] for d in data]
        actuals = [1.0 if d['actual_upset'] else 0.0 for d in data]
        from scipy import stats
        ic, _ = stats.spearmanr(scores, actuals)
        return ic if not math.isnan(ic) else 0.0


class CrowdednessDetector:
    """拥挤度检测器"""
    
    def __init__(self):
        self.market_scores: deque = deque(maxlen=50)
    
    def record_market_score(self, score: float) -> None:
        """记录市场冷门评分"""
        self.market_scores.append(score)
    
    def check(self, our_score: float) -> Dict[str, Any]:
        """检测拥挤度"""
        if len(self.market_scores) < 10:
            return {'crowdedness': 0.0, 'status': 'UNKNOWN'}
        
        market_avg = np.mean(self.market_scores)
        market_std = np.std(self.market_scores)
        
        if market_std == 0:
            return {'crowdedness': 0.0, 'status': 'UNKNOWN'}
        
        # 如果市场也高度关注这个比赛的冷门，说明拥挤
        z_score = (our_score - market_avg) / market_std
        crowdedness = min(max(z_score / 2.0, 0.0), 1.0)  # 标准化到 0-1
        
        return {
            'crowdedness': round(crowdedness, 4),
            'status': 'HIGH' if crowdedness > 0.7 else 'MEDIUM' if crowdedness > 0.4 else 'LOW',
            'our_score': round(our_score, 2),
            'market_avg': round(market_avg, 2)
        }


class RegimeDetector:
    """制度检测器 - 识别赛事阶段"""
    
    REGIME_MAP = {
        'group_rd1': {'cold_blood_rate': 0.35, 'upset_signal_strength': 1.2},
        'group_rd2': {'cold_blood_rate': 0.28, 'upset_signal_strength': 1.0},
        'group_rd3': {'cold_blood_rate': 0.25, 'upset_signal_strength': 0.9},
        'round_16': {'cold_blood_rate': 0.20, 'upset_signal_strength': 0.7},
        'quarter': {'cold_blood_rate': 0.15, 'upset_signal_strength': 0.5},
        'semi': {'cold_blood_rate': 0.10, 'upset_signal_strength': 0.3},
        'final': {'cold_blood_rate': 0.05, 'upset_signal_strength': 0.2},
    }
    
    def detect(self, stage: str) -> Dict[str, Any]:
        """检测当前制度"""
        regime = self.REGIME_MAP.get(stage, self.REGIME_MAP['group_rd1'])
        return {
            'stage': stage,
            'expected_upset_rate': regime['cold_blood_rate'],
            'signal_multiplier': regime['upset_signal_strength'],
            'regime_type': 'high_upset' if regime['cold_blood_rate'] > 0.25 else 'medium' if regime['cold_blood_rate'] > 0.15 else 'low_upset'
        }


class UpsetDetectorV3:
    """冷门雷达 v3.0 - Citadel 级信号发现"""
    
    WEIGHTS = {
        'big_team_hype': 20, 'odds_reverse': 20, 'abnormal_flow': 15,
        'region_upset': 15, 'elo_overvalued': 10, 'xg_undervalued': 10,
        'motivation_gap': 10,
    }
    
    THRESHOLDS = {'normal': 45, 'watch': 65, 'candidate': 80}
    
    def __init__(self):
        self.signal_validator = SignalValidator()
        self.crowdedness_detector = CrowdednessDetector()
        self.regime_detector = RegimeDetector()
    
    def detect(self, match_info: Dict[str, Any]) -> Dict[str, Any]:
        """检测冷门信号"""
        factors = self._calculate_factors(match_info)
        base_score = factors.total_score
        
        # 制度调整
        stage = match_info.get('stage', 'group_rd1')
        regime = self.regime_detector.detect(stage)
        adjusted_score = base_score * regime['signal_multiplier']
        
        # 拥挤度调整
        crowdedness = self.crowdedness_detector.check(adjusted_score)
        if crowdedness['status'] == 'HIGH':
            adjusted_score *= 0.7  # 高拥挤度降低信号权重
        
        # 确定等级
        level = self._determine_level(adjusted_score)
        
        # 信号验证
        ic_stats = self.signal_validator.calculate_ic(regime['regime_type'])
        decay = self.signal_validator.decay_analysis()
        
        return {
            'version': '3.0',
            'score': round(adjusted_score, 2),
            'base_score': round(base_score, 2),
            'level': level.value,
            'regime': regime,
            'crowdedness': crowdedness,
            'signal_validation': ic_stats,
            'decay_analysis': decay,
            'factors': {
                'big_team_hype': factors.big_team_hype,
                'odds_reverse': factors.odds_reverse,
                'abnormal_flow': factors.abnormal_flow,
                'region_upset': factors.region_upset,
                'elo_overvalued': factors.elo_overvalued,
                'xg_undervalued': factors.xg_undervalued,
                'motivation_gap': factors.motivation_gap,
            }
        }
    
    def record_result(self, match_id: str, predicted_score: float, actual_upset: bool, stage: str) -> None:
        """记录实际结果用于验证"""
        regime = self.regime_detector.detect(stage)
        self.signal_validator.record(predicted_score, actual_upset, regime['regime_type'])
    
    def _calculate_factors(self, match_info: Dict) -> UpsetFactors:
        """计算冷门因子"""
        factors = UpsetFactors()
        
        home = match_info.get('home', '')
        away = match_info.get('away', '')
        odds_home = match_info.get('odds_home', 0)
        odds_away = match_info.get('odds_away', 0)
        
        # 1. 豪门热度 (检测热门被过度追捧)
        if odds_home < 1.5 or odds_away < 1.5:
            factors.big_team_hype = 15.0
        elif odds_home < 2.0 or odds_away < 2.0:
            factors.big_team_hype = 10.0
        
        # 2. 赔率反向波动
        odds_drift = match_info.get('odds_drift', 0)
        if odds_drift > 0.1:
            factors.odds_reverse = 15.0
        elif odds_drift > 0.05:
            factors.odds_reverse = 10.0
        
        # 3. 区域冷门因子
        if self._is_african_team(home) or self._is_african_team(away):
            factors.region_upset = 12.0
        elif self._is_asian_team(home) or self._is_asian_team(away):
            factors.region_upset = 10.0
        elif self._is_concacaf_team(home) or self._is_concacaf_team(away):
            factors.region_upset = 10.0
        
        return factors
    
    def _determine_level(self, score: float) -> UpsetLevel:
        if score >= self.THRESHOLDS['candidate']:
            return UpsetLevel.STRONG
        elif score >= self.THRESHOLDS['watch']:
            return UpsetLevel.CANDIDATE
        elif score >= self.THRESHOLDS['normal']:
            return UpsetLevel.WATCH
        return UpsetLevel.NORMAL
    
    @staticmethod
    def _is_african_team(team: str) -> bool:
        return any(t.lower() in team.lower() for t in ['Morocco', 'Senegal', 'Cameroon', 'Ghana', 'Nigeria', 'Egypt', 'Ivory Coast', 'Cape Verde'])
    
    @staticmethod
    def _is_asian_team(team: str) -> bool:
        return any(t.lower() in team.lower() for t in ['Japan', 'Korea', 'Iran', 'Saudi', 'Australia', 'Qatar', 'Uzbekistan', 'Jordan'])
    
    @staticmethod
    def _is_concacaf_team(team: str) -> bool:
        return any(t.lower() in team.lower() for t in ['USA', 'Mexico', 'Canada', 'Costa Rica', 'Honduras', 'Jamaica', 'Panama', 'Haiti'])


if __name__ == '__main__':
    detector = UpsetDetectorV3()
    
    # 测试
    match = {
        'home': 'Germany', 'away': 'Japan',
        'odds_home': 1.3, 'odds_away': 8.0,
        'stage': 'group_rd1'
    }
    
    result = detector.detect(match)
    print(json.dumps(result, indent=2, ensure_ascii=False))
