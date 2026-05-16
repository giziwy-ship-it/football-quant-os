#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
历史赔率因素分析模块 v2.0 - Football Quant OS
整合到Naga Core Soccer Betting Intelligence v4.2

功能：
1. 历史同赔匹配：根据当前赔率匹配历史相似赔率比赛
2. 历史结果统计：分析历史同赔比赛的胜平负分布
3. 概率修正：基于历史数据修正当前预测概率
4. 与资金信号协同：当历史赔率与资金信号一致时提升置信度
"""

import json
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class OddsRange(Enum):
    """赔率区间分类"""
    LOW = "low"           # < 1.5
    MEDIUM_LOW = "med_low"  # 1.5 - 2.0
    MEDIUM = "medium"     # 2.0 - 3.0
    MEDIUM_HIGH = "med_high"  # 3.0 - 5.0
    HIGH = "high"         # > 5.0


@dataclass
class HistoricalMatch:
    """历史比赛数据模型"""
    match_id: str
    league: str
    home_team: str
    away_team: str
    home_odds: float
    draw_odds: float
    away_odds: float
    result: str  # "H", "D", "A"
    home_score: int
    away_score: int
    match_date: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class OddsPattern:
    """赔率模式分析结果"""
    pattern_id: str
    home_odds_range: str
    draw_odds_range: str
    away_odds_range: str
    total_matches: int
    home_wins: int
    draws: int
    away_wins: int
    home_win_pct: float
    draw_pct: float
    away_win_pct: float
    avg_home_goals: float
    avg_away_goals: float
    confidence: float  # 基于样本量的置信度
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class HistoricalOddsFactor:
    """历史赔率因素分析器 v2.0"""
    
    name = "HistoricalOddsFactor"
    version = "2.0"
    
    # 赔率相似度阈值（允许±10%的误差）
    ODDS_SIMILARITY_THRESHOLD = 0.10
    
    # 最小样本量（低于此数量认为不可靠）
    MIN_SAMPLE_SIZE = 3
    
    # 历史数据库（实际应用中应该从数据库加载）
    _historical_db: List[HistoricalMatch] = []
    
    def __init__(self):
        self.matched_matches: List[HistoricalMatch] = []
        self.pattern_analysis: Optional[OddsPattern] = None
        self.adjustment_applied = False
    
    @classmethod
    def load_historical_data(cls, data_source: str = "default"):
        """
        加载历史数据
        
        Args:
            data_source: 数据源标识（"default", "database", "file"）
        """
        # 这里应该从数据库或文件加载
        # 现在使用内置的示例数据
        cls._historical_db = cls._get_sample_data()
    
    @classmethod
    def _get_sample_data(cls) -> List[HistoricalMatch]:
        """获取示例历史数据（实际应用中替换为真实数据库）"""
        return [
            # 相似赔率模式示例：主胜2.0-2.5, 平局3.0-3.5, 客胜2.5-3.0
            HistoricalMatch("M001", "Premier League", "Team A", "Team B", 2.15, 3.25, 3.40, "D", 1, 1, "2025-01-15"),
            HistoricalMatch("M002", "Premier League", "Team C", "Team D", 2.35, 3.15, 3.10, "H", 2, 1, "2025-02-20"),
            HistoricalMatch("M003", "La Liga", "Team E", "Team F", 2.25, 3.35, 3.20, "D", 0, 0, "2025-03-10"),
            HistoricalMatch("M004", "Bundesliga", "Team G", "Team H", 2.45, 3.05, 3.00, "A", 1, 2, "2025-01-25"),
            HistoricalMatch("M005", "Serie A", "Team I", "Team J", 2.20, 3.40, 3.25, "H", 3, 1, "2025-04-05"),
            HistoricalMatch("M006", "Premier League", "Team K", "Team L", 2.30, 3.20, 3.15, "D", 2, 2, "2025-02-15"),
            HistoricalMatch("M007", "La Liga", "Team M", "Team N", 2.50, 3.10, 2.95, "H", 2, 0, "2025-03-20"),
            HistoricalMatch("M008", "Bundesliga", "Team O", "Team P", 2.10, 3.45, 3.30, "D", 1, 1, "2025-04-10"),
            HistoricalMatch("M009", "Premier League", "Team Q", "Team R", 2.40, 3.25, 3.05, "A", 0, 1, "2025-01-30"),
            HistoricalMatch("M010", "Serie A", "Team S", "Team T", 2.55, 3.00, 2.90, "H", 2, 1, "2025-02-28"),
            
            # 诱盘赔率模式示例：主胜1.2-1.5（低赔陷阱）
            HistoricalMatch("M011", "Premier League", "Strong Team", "Weak Team", 1.35, 4.50, 8.50, "D", 1, 1, "2025-01-10"),
            HistoricalMatch("M012", "La Liga", "Top Team", "Bottom Team", 1.25, 5.00, 10.00, "A", 0, 1, "2025-02-05"),
            HistoricalMatch("M013", "Bundesliga", "Champion", "Relegation", 1.30, 4.80, 9.00, "H", 3, 0, "2025-03-15"),
            HistoricalMatch("M014", "Premier League", "Big Club", "Small Club", 1.40, 4.30, 7.50, "D", 2, 2, "2025-04-01"),
            HistoricalMatch("M015", "Serie A", "Giant", "Minnow", 1.20, 5.50, 12.00, "H", 4, 1, "2025-01-20"),
        ]
    
    def find_similar_matches(self, home_odds: float, draw_odds: float, 
                            away_odds: float, league: Optional[str] = None) -> List[HistoricalMatch]:
        """
        查找历史相似赔率比赛
        
        Args:
            home_odds: 当前主胜赔率
            draw_odds: 当前平局赔率
            away_odds: 当前客胜赔率
            league: 联赛筛选（可选）
            
        Returns:
            匹配的历史比赛列表
        """
        if not self._historical_db:
            self.load_historical_data()
        
        matched = []
        
        for match in self._historical_db:
            # 联赛筛选
            if league and match.league != league:
                continue
            
            # 赔率相似度检查（±10%阈值）
            home_similar = self._is_odds_similar(home_odds, match.home_odds)
            draw_similar = self._is_odds_similar(draw_odds, match.draw_odds)
            away_similar = self._is_odds_similar(away_odds, match.away_odds)
            
            # 至少两个赔率维度相似才算匹配
            similarity_score = sum([home_similar, draw_similar, away_similar])
            if similarity_score >= 2:
                matched.append(match)
        
        self.matched_matches = matched
        return matched
    
    def analyze_pattern(self) -> Optional[OddsPattern]:
        """
        分析匹配到的历史赔率模式
        
        Returns:
            赔率模式分析结果
        """
        if not self.matched_matches:
            return None
        
        total = len(self.matched_matches)
        home_wins = sum(1 for m in self.matched_matches if m.result == "H")
        draws = sum(1 for m in self.matched_matches if m.result == "D")
        away_wins = sum(1 for m in self.matched_matches if m.result == "A")
        
        # 计算平均进球
        avg_home_goals = sum(m.home_score for m in self.matched_matches) / total
        avg_away_goals = sum(m.away_score for m in self.matched_matches) / total
        
        # 置信度计算（基于样本量）
        confidence = min(1.0, total / 10)  # 10场以上置信度为1.0
        
        # 赔率范围分类
        sample = self.matched_matches[0]
        pattern = OddsPattern(
            pattern_id=f"P_{sample.home_odds:.2f}_{sample.draw_odds:.2f}_{sample.away_odds:.2f}",
            home_odds_range=self._classify_odds_range(sample.home_odds),
            draw_odds_range=self._classify_odds_range(sample.draw_odds),
            away_odds_range=self._classify_odds_range(sample.away_odds),
            total_matches=total,
            home_wins=home_wins,
            draws=draws,
            away_wins=away_wins,
            home_win_pct=home_wins / total * 100,
            draw_pct=draws / total * 100,
            away_win_pct=away_wins / total * 100,
            avg_home_goals=avg_home_goals,
            avg_away_goals=avg_away_goals,
            confidence=round(confidence, 2)
        )
        
        self.pattern_analysis = pattern
        return pattern
    
    def adjust_probabilities(self, base_probs: Dict[str, float]) -> Dict[str, Any]:
        """
        基于历史赔率因素调整概率
        
        Args:
            base_probs: 基础概率 {"home_win": 45, "draw": 30, "away_win": 25}
            
        Returns:
            调整后的概率和分析结果
        """
        if not self.pattern_analysis or self.pattern_analysis.total_matches < self.MIN_SAMPLE_SIZE:
            return {
                "adjusted": False,
                "reason": "历史样本不足",
                "original_probs": base_probs,
                "adjusted_probs": base_probs
            }
        
        pattern = self.pattern_analysis
        
        # 计算调整权重（基于置信度和样本量）
        weight = pattern.confidence * 0.3  # 最大30%的调整权重
        
        # 历史概率
        hist_home = pattern.home_win_pct
        hist_draw = pattern.draw_pct
        hist_away = pattern.away_win_pct
        
        # 混合概率（基础概率 + 历史概率加权）
        adjusted = {
            "home_win": base_probs["home_win"] * (1 - weight) + hist_home * weight,
            "draw": base_probs["draw"] * (1 - weight) + hist_draw * weight,
            "away_win": base_probs["away_win"] * (1 - weight) + hist_away * weight
        }
        
        # 归一化
        total = sum(adjusted.values())
        adjusted = {k: round(v / total * 100, 2) for k, v in adjusted.items()}
        
        self.adjustment_applied = True
        
        return {
            "adjusted": True,
            "adjustment_weight": round(weight, 3),
            "original_probs": base_probs,
            "adjusted_probs": adjusted,
            "pattern": pattern.to_dict(),
            "key_insights": self._generate_insights(pattern, base_probs, adjusted)
        }
    
    def get_conflict_analysis(self, money_flow_signal: str) -> Dict[str, Any]:
        """
        分析历史赔率与资金信号的冲突/一致性
        
        Args:
            money_flow_signal: 资金信号方向 ("home", "draw", "away", "neutral")
            
        Returns:
            冲突分析结果
        """
        if not self.pattern_analysis:
            return {"analysis": "无历史赔率数据"}
        
        pattern = self.pattern_analysis
        
        # 确定历史赔率最看好的方向
        hist_directions = {
            "home": pattern.home_win_pct,
            "draw": pattern.draw_pct,
            "away": pattern.away_win_pct
        }
        hist_best = max(hist_directions, key=hist_directions.get)
        
        # 检查一致性
        if money_flow_signal == "neutral":
            consistency = "neutral"
            recommendation = "参考历史赔率倾向"
        elif money_flow_signal == hist_best:
            consistency = "aligned"
            recommendation = "历史赔率与资金信号一致，增强信心"
        else:
            consistency = "conflict"
            recommendation = "历史赔率与资金信号冲突，谨慎决策"
        
        return {
            "analysis": "历史赔率 vs 资金信号",
            "consistency": consistency,
            "historical_best": hist_best,
            "historical_best_pct": hist_directions[hist_best],
            "money_flow_signal": money_flow_signal,
            "recommendation": recommendation,
            "confidence_adjustment": 0.05 if consistency == "aligned" else (-0.05 if consistency == "conflict" else 0)
        }
    
    def _is_odds_similar(self, current: float, historical: float) -> bool:
        """检查两个赔率是否相似（±10%阈值）"""
        if current == 0 or historical == 0:
            return False
        diff = abs(current - historical) / historical
        return diff <= self.ODDS_SIMILARITY_THRESHOLD
    
    def _classify_odds_range(self, odds: float) -> str:
        """分类赔率区间"""
        if odds < 1.5:
            return OddsRange.LOW.value
        elif odds < 2.0:
            return OddsRange.MEDIUM_LOW.value
        elif odds < 3.0:
            return OddsRange.MEDIUM.value
        elif odds < 5.0:
            return OddsRange.MEDIUM_HIGH.value
        else:
            return OddsRange.HIGH.value
    
    def _generate_insights(self, pattern: OddsPattern, original: Dict[str, float], 
                          adjusted: Dict[str, float]) -> List[str]:
        """生成关键洞察"""
        insights = []
        
        # 样本量说明
        if pattern.total_matches >= 10:
            insights.append(f"历史同赔样本充足({pattern.total_matches}场)，可信度高")
        elif pattern.total_matches >= 5:
            insights.append(f"历史同赔样本{pattern.total_matches}场，参考价值中等")
        else:
            insights.append(f"历史同赔样本较少({pattern.total_matches}场)，谨慎参考")
        
        # 历史结果分布
        insights.append(f"历史同赔结果: 主胜{pattern.home_win_pct:.1f}% | 平局{pattern.draw_pct:.1f}% | 客胜{pattern.away_win_pct:.1f}%")
        
        # 调整幅度
        for key in ["home_win", "draw", "away_win"]:
            diff = adjusted[key] - original[key]
            if abs(diff) > 2:
                direction = "提升" if diff > 0 else "降低"
                insights.append(f"{key}概率{direction}{abs(diff):.1f}%（历史因素）")
        
        # 特殊模式识别
        if pattern.home_win_pct > 50 and pattern.home_odds_range in ["med_low", "medium"]:
            insights.append("历史数据显示该赔率区间主队胜率较高")
        elif pattern.draw_pct > 35:
            insights.append("历史数据显示该赔率区间平局概率较高，注意防范")
        
        return insights
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        主运行方法
        
        Args:
            match_data: 比赛数据字典
                - market_odds: {"home_win": 2.15, "draw": 3.25, "away_win": 3.40}
                - league: 联赛名称（可选）
                - base_probs: 基础概率（可选）
                - money_flow_signal: 资金信号方向（可选）
        
        Returns:
            完整的历史赔率分析结果
        """
        odds = match_data.get('market_odds', {})
        home_odds = odds.get('home_win', 2.0)
        draw_odds = odds.get('draw', 3.5)
        away_odds = odds.get('away_win', 2.0)
        league = match_data.get('league')
        
        # 1. 查找相似历史比赛
        matched = self.find_similar_matches(home_odds, draw_odds, away_odds, league)
        
        # 2. 分析赔率模式
        pattern = self.analyze_pattern()
        
        # 3. 调整概率（如果有基础概率）
        base_probs = match_data.get('base_probs', {
            "home_win": 33.3, "draw": 33.3, "away_win": 33.3
        })
        adjustment = self.adjust_probabilities(base_probs)
        
        # 4. 与资金信号协同分析
        money_flow_signal = match_data.get('money_flow_signal', 'neutral')
        conflict_analysis = self.get_conflict_analysis(money_flow_signal)
        
        return {
            "agent": self.name,
            "version": self.version,
            "matched_count": len(matched),
            "pattern": pattern.to_dict() if pattern else None,
            "probability_adjustment": adjustment,
            "conflict_analysis": conflict_analysis,
            "key_factors": adjustment.get("key_insights", []) if adjustment else []
        }


# ============ 测试代码 ============

if __name__ == "__main__":
    import json
    
    print("=== HistoricalOddsFactor v2.0 测试 ===\n")
    
    # 测试1：基础功能
    print("测试1: 基础功能测试")
    factor = HistoricalOddsFactor()
    
    result = factor.run({
        "home_team": "水晶宫",
        "away_team": "西汉姆联",
        "market_odds": {"home_win": 2.25, "draw": 3.35, "away_win": 3.20},
        "league": "Premier League",
        "base_probs": {"home_win": 40, "draw": 30, "away_win": 30},
        "money_flow_signal": "home"
    })
    
    print(f"匹配历史比赛: {result['matched_count']}场")
    if result['pattern']:
        print(f"历史胜率分布: 主{result['pattern']['home_win_pct']:.1f}% | 平{result['pattern']['draw_pct']:.1f}% | 客{result['pattern']['away_win_pct']:.1f}%")
    
    if result['probability_adjustment']['adjusted']:
        adj = result['probability_adjustment']
        print(f"原始概率: {adj['original_probs']}")
        print(f"调整后: {adj['adjusted_probs']}")
        print(f"调整权重: {adj['adjustment_weight']}")
    
    print(f"资金信号协同: {result['conflict_analysis']['consistency']}")
    print(f"建议: {result['conflict_analysis']['recommendation']}")
    
    # 测试2：诱盘识别
    print("\n测试2: 诱盘识别测试")
    factor2 = HistoricalOddsFactor()
    
    result2 = factor2.run({
        "home_team": "强队",
        "away_team": "弱队",
        "market_odds": {"home_win": 1.30, "draw": 4.80, "away_win": 9.00},
        "base_probs": {"home_win": 70, "draw": 20, "away_win": 10},
        "money_flow_signal": "away"
    })
    
    print(f"匹配历史比赛: {result2['matched_count']}场")
    if result2['pattern']:
        print(f"历史低赔陷阱结果: 主{result2['pattern']['home_win_pct']:.1f}% | 平{result2['pattern']['draw_pct']:.1f}% | 客{result2['pattern']['away_win_pct']:.1f}%")
    
    print("\nHistoricalOddsFactor v2.0 测试完成!")
