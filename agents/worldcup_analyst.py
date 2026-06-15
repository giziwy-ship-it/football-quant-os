#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorldCupAnalyst - 世界杯专家 Agent
作为 9 Agent 流水线中的 Phase 1 专家，输出六维预测概率

职责：
- 接收比赛数据
- 输出六维概率预测（1X2/让球/半全场/比分/进球数/大小球）
- 不计算 Kelly，不风控，只输出概率分析
- 输出格式与其他 Agent 统一，供 Committee 加权综合
"""

import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime


class WorldCupAnalyst:
    """
    世界杯专家 Agent - 兼容 9 Agent 流水线
    
    在 Pipeline 中作为 Phase 1 的独立 Agent 运行，
    与其他 Agent（DataScout, GeneEngine, Analyst）并行，
    最终由 Committee 加权综合。
    """
    
    name = "WorldCupAnalyst"
    version = "1.0.0"
    
    def __init__(self):
        self._team_db = self._load_team_db()
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行六维预测分析
        
        输入: match_data 包含:
            - home_team, away_team
            - home_elo, away_elo (可选)
            - market_odds: {home, draw, away}
        
        输出: 统一的 Agent 格式
            {
                "agent": "WorldCupAnalyst",
                "prediction": {"home_win": xx, "draw": xx, "away_win": xx},
                "confidence": 0.85,
                "key_factors": [...],
                "six_dimensions": {...}  # 六维详细预测
            }
        """
        home = match_data.get('home_team', '')
        away = match_data.get('away_team', '')
        
        # 获取球队信息
        home_info = self._get_team_info(home)
        away_info = self._get_team_info(away)
        
        # 计算基础概率
        base_probs = self._calculate_base_probs(home_info, away_info, match_data)
        
        # 六维预测
        dimensions = self._predict_dimensions(base_probs, home, away, match_data)
        
        # 生成关键因子
        key_factors = self._generate_factors(home, away, home_info, away_info, dimensions)
        
        return {
            "agent": self.name,
            "version": self.version,
            "prediction": {
                "home_win": round(base_probs['home'] * 100, 2),
                "draw": round(base_probs['draw'] * 100, 2),
                "away_win": round(base_probs['away'] * 100, 2)
            },
            "confidence": self._calculate_confidence(dimensions),
            "key_factors": key_factors,
            "six_dimensions": dimensions,
            "home_team_info": home_info,
            "away_team_info": away_info,
            "analysis_method": "Elo + Poisson + Market Odds Fusion"
        }
    
    def _calculate_base_probs(self, home_info: Dict, away_info: Dict, 
                              match_data: Dict) -> Dict[str, float]:
        """计算基础概率（Elo + 市场赔率融合）"""
        
        # 1. Elo 概率
        home_elo = home_info.get('elo', 1700)
        away_elo = away_info.get('elo', 1700)
        elo_diff = home_elo - away_elo
        elo_prob = 1 / (1 + 10 ** (-elo_diff / 400))
        
        # 2. 市场赔率概率（去水）
        odds = match_data.get('market_odds', {})
        home_odds = odds.get('home', 1.5)
        draw_odds = odds.get('draw', 4.0)
        away_odds = odds.get('away', 6.0)
        
        total_prob = 1/home_odds + 1/draw_odds + 1/away_odds
        market_home = (1/home_odds / total_prob) if total_prob > 0 else 0.65
        market_draw = (1/draw_odds / total_prob) if total_prob > 0 else 0.20
        market_away = (1/away_odds / total_prob) if total_prob > 0 else 0.15
        
        # 3. 融合（Elo 40% + Market 60%）
        home = elo_prob * 0.4 + market_home * 0.6
        draw = 0.25 * 0.4 + market_draw * 0.6  # 平局权重较低
        away = 1 - home - draw
        
        # 确保概率和为 1
        total = home + draw + away
        
        return {
            'home': home / total,
            'draw': draw / total,
            'away': away / total
        }
    
    def _predict_dimensions(self, probs: Dict[str, float], home: str, away: str,
                           match_data: Dict) -> Dict[str, Any]:
        """六维预测"""
        
        home_prob = probs['home']
        draw_prob = probs['draw']
        away_prob = probs['away']
        
        home_info = self._get_team_info(home)
        away_info = self._get_team_info(away)
        
        odds = match_data.get('market_odds', {})
        home_odds = odds.get('home', 1.5)
        draw_odds = odds.get('draw', 4.0)
        away_odds = odds.get('away', 6.0)
        
        # 1. 1X2
        dim_1x2 = {
            'prediction': f"{home} 胜" if home_prob > 0.5 else "平局" if draw_prob > 0.33 else f"{away} 胜",
            'probability': round(home_prob, 3),
            'probability_draw': round(draw_prob, 3),
            'probability_away': round(away_prob, 3),
            'odds': home_odds,
            'confidence': 4 if max(home_prob, draw_prob, away_prob) > 0.6 else 3
        }
        
        # 2. 让球 (-1)
        handicap_prob = max(0, home_prob - 0.15)
        dim_handicap = {
            'prediction': f"{home} -1 胜" if home_prob > 0.55 else "走水/负",
            'probability': round(handicap_prob, 3),
            'odds': 2.0,
            'confidence': 3 if handicap_prob > 0.45 else 2
        }
        
        # 3. 半全场
        ht_home_prob = home_prob * 0.85  # 上半场主队优势略低
        dim_htft = {
            'prediction': "胜-胜" if home_prob > 0.6 else "平-胜" if home_prob > 0.5 else "平/负-平",
            'probability': round(0.45 if home_prob > 0.6 else 0.25, 3),
            'confidence': 3
        }
        
        # 4. 精确比分 (Poisson 简化)
        score = self._poisson_score(home_prob, away_prob, home_info, away_info)
        dim_score = {
            'prediction': score['score'],
            'probability': round(score['probability'], 3),
            'top5_scores': score['top5'],
            'confidence': 4 if score['probability'] > 0.15 else 3
        }
        
        # 5. 进球数
        expected_goals = home_prob * 2.5 + away_prob * 1.0
        dim_goals = {
            'prediction': "2-3球" if expected_goals > 2.0 else "0-1球",
            'probability': round(0.55 if expected_goals > 2.0 else 0.30, 3),
            'expected_goals': round(expected_goals, 2),
            'confidence': 3
        }
        
        # 6. 大小球
        dim_overunder = {
            'prediction': "大球 2.25" if expected_goals > 2.0 else "小球 2.25",
            'probability': round(0.55 if expected_goals > 2.0 else 0.45, 3),
            'odds': 0.91,
            'confidence': 3
        }
        
        return {
            '1x2': dim_1x2,
            'handicap': dim_handicap,
            'htft': dim_htft,
            'correct_score': dim_score,
            'goals': dim_goals,
            'over_under': dim_overunder
        }
    
    def _poisson_score(self, home_prob: float, away_prob: float,
                       home_info: Dict, away_info: Dict) -> Dict:
        """简化 Poisson 比分预测"""
        
        # 预期进球
        home_xg = home_prob * 2.5 + 0.3  # 基础 + 主场优势
        away_xg = away_prob * 1.5 + 0.1
        
        # 生成比分概率
        scores = {}
        for h in range(5):
            for a in range(5):
                prob = self._poisson_prob(h, home_xg) * self._poisson_prob(a, away_xg)
                scores[f"{h}-{a}"] = prob
        
        # 排序
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top5 = [{"score": s, "probability": round(p, 4)} for s, p in sorted_scores[:5]]
        
        return {
            'score': top5[0]['score'],
            'probability': top5[0]['probability'],
            'top5': top5,
            'home_xg': round(home_xg, 2),
            'away_xg': round(away_xg, 2)
        }
    
    def _poisson_prob(self, k: int, lam: float) -> float:
        """Poisson 概率"""
        import math
        return (lam ** k) * math.exp(-lam) / math.factorial(k)
    
    def _generate_factors(self, home: str, away: str, 
                         home_info: Dict, away_info: Dict,
                         dimensions: Dict) -> List[str]:
        """生成关键因子"""
        factors = []
        
        # Elo 差距
        elo_diff = home_info.get('elo', 1700) - away_info.get('elo', 1700)
        if elo_diff > 200:
            factors.append(f"Elo差距显著: {home} +{elo_diff}")
        elif elo_diff < -200:
            factors.append(f"Elo差距显著: {away} 优势{abs(elo_diff)}")
        
        # FIFA 排名
        rank_diff = home_info.get('fifa_rank', 50) - away_info.get('fifa_rank', 50)
        if abs(rank_diff) > 30:
            leader = home if rank_diff < 0 else away
            factors.append(f"排名差距: {leader}领先{abs(rank_diff)}位")
        
        # 世界杯东道主/战意
        if home_info.get('host', False):
            factors.append(f"{home} 东道主主场优势")
        
        # 首选比分
        score = dimensions['correct_score']['prediction']
        prob = dimensions['correct_score']['probability']
        factors.append(f"首选比分: {score} ({prob*100:.1f}%)")
        
        # 预期进球
        xg = dimensions['goals']['expected_goals']
        factors.append(f"预期总进球: {xg}")
        
        return factors
    
    def _calculate_confidence(self, dimensions: Dict) -> float:
        """计算置信度"""
        base = 0.85
        
        # 1X2 集中度
        probs = [dimensions['1x2']['probability'], 
                dimensions['1x2']['probability_draw'],
                dimensions['1x2']['probability_away']]
        max_prob = max(probs)
        
        if max_prob > 0.65:
            base += 0.05
        elif max_prob < 0.45:
            base -= 0.05
        
        return min(0.95, max(0.6, base))
    
    def _get_team_info(self, team: str) -> Dict:
        """从世界杯数据库获取球队信息"""
        return self._team_db.get(team, {
            'fifa_rank': 50,
            'elo': 1700,
            'group': 'Unknown',
            'host': False
        })
    
    def _load_team_db(self) -> Dict:
        """加载 48 队数据库"""
        return {
            'Mexico': {'fifa_rank': 19, 'elo': 1920, 'group': 'A', 'host': True},
            'South Africa': {'fifa_rank': 60, 'elo': 1650, 'group': 'A', 'host': False},
            'Argentina': {'fifa_rank': 1, 'elo': 2100, 'group': 'A', 'host': False},
            'Brazil': {'fifa_rank': 3, 'elo': 2050, 'group': 'B', 'host': False},
            'Germany': {'fifa_rank': 10, 'elo': 1950, 'group': 'B', 'host': False},
            'France': {'fifa_rank': 2, 'elo': 2080, 'group': 'C', 'host': False},
            'Spain': {'fifa_rank': 8, 'elo': 2000, 'group': 'C', 'host': False},
            'Portugal': {'fifa_rank': 6, 'elo': 2020, 'group': 'D', 'host': False},
            'England': {'fifa_rank': 4, 'elo': 2040, 'group': 'D', 'host': False},
            'Netherlands': {'fifa_rank': 7, 'elo': 2010, 'group': 'E', 'host': False},
            'Italy': {'fifa_rank': 9, 'elo': 1980, 'group': 'E', 'host': False},
            'Belgium': {'fifa_rank': 5, 'elo': 2030, 'group': 'F', 'host': False},
            'USA': {'fifa_rank': 15, 'elo': 1900, 'group': 'F', 'host': True},
            'Canada': {'fifa_rank': 45, 'elo': 1750, 'group': 'F', 'host': True},
        }
