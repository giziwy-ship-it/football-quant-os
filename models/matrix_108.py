#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
108组合概率矩阵 - Naga Core v4.1
通过多维度组合精准定位比赛走向：
• 3种实力对比 × 2种先进球方 × 6个时间段 = 108种组合
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum


class StrengthGap(Enum):
    STRONG_VS_WEAK = "strong_vs_weak"
    MEDIUM_GAP = "medium_gap"
    EVEN = "even"


class FirstScorer(Enum):
    HOME = "home"
    AWAY = "away"


class TimeSegment(Enum):
    T_0_15 = "0-15"
    T_16_30 = "16-30"
    T_31_45 = "31-45"
    T_46_60 = "46-60"
    T_61_75 = "61-75"
    T_76_90 = "76-90"


@dataclass
class MatrixCell:
    strength_gap: StrengthGap
    first_scorer: FirstScorer
    time_segment: TimeSegment
    home_win_prob: float = 0.0
    draw_prob: float = 0.0
    away_win_prob: float = 0.0
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "combination": f"{self.strength_gap.value}_{self.first_scorer.value}_{self.time_segment.value}",
            "strength_gap": self.strength_gap.value,
            "first_scorer": self.first_scorer.value,
            "time_segment": self.time_segment.value,
            "probabilities": {
                "home_win": round(self.home_win_prob, 2),
                "draw": round(self.draw_prob, 2),
                "away_win": round(self.away_win_prob, 2)
            },
            "tags": self.tags
        }


class ProbabilityMatrix108:
    """108组合概率矩阵"""
    
    def __init__(self):
        self.matrix: Dict[str, MatrixCell] = {}
        self._init_matrix()
    
    def _init_matrix(self):
        for gap in StrengthGap:
            for scorer in FirstScorer:
                for segment in TimeSegment:
                    cell = self._create_cell(gap, scorer, segment)
                    key = self._make_key(gap, scorer, segment)
                    self.matrix[key] = cell
    
    def _make_key(self, gap: StrengthGap, scorer: FirstScorer, segment: TimeSegment) -> str:
        return f"{gap.value}_{scorer.value}_{segment.value}"
    
    def _create_cell(self, gap: StrengthGap, scorer: FirstScorer, segment: TimeSegment) -> MatrixCell:
        if gap == StrengthGap.STRONG_VS_WEAK:
            base = {"home_win": 78, "draw": 15, "away_win": 7} if scorer == FirstScorer.HOME else {"home_win": 45, "draw": 30, "away_win": 25}
        elif gap == StrengthGap.MEDIUM_GAP:
            base = {"home_win": 65, "draw": 22, "away_win": 13} if scorer == FirstScorer.HOME else {"home_win": 32, "draw": 35, "away_win": 33}
        else:
            base = {"home_win": 58, "draw": 25, "away_win": 17} if scorer == FirstScorer.HOME else {"home_win": 22, "draw": 32, "away_win": 46}
        
        time_modifier = self._get_time_modifier(segment, scorer)
        
        home_win = max(5, base["home_win"] + time_modifier["home_win"])
        draw = max(5, base["draw"] + time_modifier["draw"])
        away_win = max(5, base["away_win"] + time_modifier["away_win"])
        
        total = home_win + draw + away_win
        
        return MatrixCell(
            strength_gap=gap,
            first_scorer=scorer,
            time_segment=segment,
            home_win_prob=home_win / total * 100,
            draw_prob=draw / total * 100,
            away_win_prob=away_win / total * 100,
            tags=self._generate_tags(gap, scorer, segment)
        )
    
    def _get_time_modifier(self, segment: TimeSegment, scorer: FirstScorer) -> Dict[str, float]:
        modifiers = {
            TimeSegment.T_0_15: {"home_win": 2 if scorer == FirstScorer.HOME else -3, "draw": -2, "away_win": 0 if scorer == FirstScorer.HOME else 5},
            TimeSegment.T_16_30: {"home_win": 1 if scorer == FirstScorer.HOME else -1, "draw": 0, "away_win": -1 if scorer == FirstScorer.HOME else 1},
            TimeSegment.T_31_45: {"home_win": 0 if scorer == FirstScorer.HOME else 2, "draw": 3, "away_win": 3 if scorer == FirstScorer.HOME else -1},
            TimeSegment.T_46_60: {"home_win": 1 if scorer == FirstScorer.HOME else -2, "draw": -1, "away_win": 0 if scorer == FirstScorer.HOME else 3},
            TimeSegment.T_61_75: {"home_win": 2 if scorer == FirstScorer.HOME else -1, "draw": -2, "away_win": 0 if scorer == FirstScorer.HOME else 3},
            TimeSegment.T_76_90: {"home_win": 5 if scorer == FirstScorer.HOME else -5, "draw": -5, "away_win": 0 if scorer == FirstScorer.HOME else 10},
        }
        return modifiers[segment]
    
    def _generate_tags(self, gap: StrengthGap, scorer: FirstScorer, segment: TimeSegment) -> List[str]:
        tags = []
        if gap == StrengthGap.STRONG_VS_WEAK:
            tags.append("强队主导")
        elif gap == StrengthGap.EVEN:
            tags.append("势均力敌")
        
        tags.append("主队先进球" if scorer == FirstScorer.HOME else "客队先进球")
        
        if segment in [TimeSegment.T_0_15, TimeSegment.T_46_60]:
            tags.append("早进球-空间大")
        elif segment in [TimeSegment.T_31_45, TimeSegment.T_76_90]:
            tags.append("时间紧迫")
        
        if gap == StrengthGap.STRONG_VS_WEAK and scorer == FirstScorer.AWAY:
            tags.append("冷门预警")
        if segment == TimeSegment.T_76_90:
            tags.append("绝杀概率高")
        
        return tags
    
    def get_probability(self, strength_gap: str, first_scorer: str, time_segment: str) -> Optional[MatrixCell]:
        key = f"{strength_gap}_{first_scorer}_{time_segment}"
        return self.matrix.get(key)
    
    def apply_to_match(self, strength_gap: str, first_scorer: str = None, current_minute: int = None) -> Optional[Dict[str, Any]]:
        if first_scorer is None:
            return self._get_pre_match_probs(strength_gap)
        
        segment = self._minute_to_segment(current_minute or 0)
        cell = self.get_probability(strength_gap, first_scorer, segment.value)
        return cell.to_dict() if cell else None
    
    def _get_pre_match_probs(self, strength_gap: str) -> Dict[str, Any]:
        home_total = {"home_win": 0, "draw": 0, "away_win": 0}
        away_total = {"home_win": 0, "draw": 0, "away_win": 0}
        count = 0
        
        for segment in TimeSegment:
            home_cell = self.get_probability(strength_gap, "home", segment.value)
            away_cell = self.get_probability(strength_gap, "away", segment.value)
            
            if home_cell and away_cell:
                home_total["home_win"] += home_cell.home_win_prob
                home_total["draw"] += home_cell.draw_prob
                home_total["away_win"] += home_cell.away_win_prob
                
                away_total["home_win"] += away_cell.home_win_prob
                away_total["draw"] += away_cell.draw_prob
                away_total["away_win"] += away_cell.away_win_prob
                count += 1
        
        if count == 0:
            return {"error": "No data"}
        
        avg_home = {k: v / count for k, v in home_total.items()}
        avg_away = {k: v / count for k, v in away_total.items()}
        
        return {
            "strength_gap": strength_gap,
            "scenario": "pre_match",
            "probabilities": {
                "home_win": round(avg_home["home_win"] * 0.55 + avg_away["home_win"] * 0.45, 2),
                "draw": round(avg_home["draw"] * 0.55 + avg_away["draw"] * 0.45, 2),
                "away_win": round(avg_home["away_win"] * 0.55 + avg_away["away_win"] * 0.45, 2)
            },
            "tags": ["赛前综合预测", "108矩阵加权"]
        }
    
    def _minute_to_segment(self, minute: int) -> TimeSegment:
        if minute <= 15: return TimeSegment.T_0_15
        elif minute <= 30: return TimeSegment.T_16_30
        elif minute <= 45: return TimeSegment.T_31_45
        elif minute <= 60: return TimeSegment.T_46_60
        elif minute <= 75: return TimeSegment.T_61_75
        else: return TimeSegment.T_76_90
