"""
Football Quant OS - 特征工程模块

从历史数据中提取特征用于大小球建模
支持: 历史统计/近期状态/攻防效率/主客场优势
"""

from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import numpy as np


@dataclass
class TeamFeatures:
    """球队特征向量"""
    team: str
    avg_goals_scored: float      # 场均进球
    avg_goals_conceded: float     # 场均失球
    avg_xg: float                 # 场均xG
    recent_form: float            # 最近5场场均积分 (0-3)
    attack_efficiency: float      # 进攻效率 (实际进球/xG)
    defense_efficiency: float     # 防守效率 (xG/实际失球)
    home_advantage: float         # 主场优势系数
    away_disadvantage: float      # 客场劣势系数
    consistency: float            # 稳定性 (标准差倒数)
    
    def to_vector(self) -> np.ndarray:
        """转换为特征向量"""
        return np.array([
            self.avg_goals_scored,
            self.avg_goals_conceded,
            self.avg_xg,
            self.recent_form,
            self.attack_efficiency,
            self.defense_efficiency,
            self.home_advantage,
            self.away_disadvantage,
            self.consistency
        ])


class FeatureEngineer:
    """
    特征工程器
    
    从历史比赛数据中提取特征用于预测
    """
    
    def __init__(self, matches: List[Dict[str, Any]] = None):
        self.matches = matches or []
        self.team_stats = defaultdict(lambda: {
            'goals_scored': [],
            'goals_conceded': [],
            'xg': [],
            'points': [],
            'home_matches': [],
            'away_matches': []
        })
        
        if matches:
            self._build_stats()
    
    def _build_stats(self):
        """构建球队统计数据库"""
        for match in self.matches:
            home = match.get('home')
            away = match.get('away')
            home_score = match.get('home_score', 0)
            away_score = match.get('away_score', 0)
            home_xg = match.get('home_xg', 0)
            away_xg = match.get('away_xg', 0)
            
            if not home or not away:
                continue
            
            # 积分计算
            home_points = 3 if home_score > away_score else (1 if home_score == away_score else 0)
            away_points = 3 if away_score > home_score else (1 if away_score == home_score else 0)
            
            # 主队统计
            self.team_stats[home]['goals_scored'].append(home_score)
            self.team_stats[home]['goals_conceded'].append(away_score)
            self.team_stats[home]['xg'].append(home_xg)
            self.team_stats[home]['points'].append(home_points)
            self.team_stats[home]['home_matches'].append(match)
            
            # 客队统计
            self.team_stats[away]['goals_scored'].append(away_score)
            self.team_stats[away]['goals_conceded'].append(home_score)
            self.team_stats[away]['xg'].append(away_xg)
            self.team_stats[away]['points'].append(away_points)
            self.team_stats[away]['away_matches'].append(match)
    
    def extract_team_features(self, team: str, venue: str = 'neutral') -> TeamFeatures:
        """
        提取球队特征
        
        Args:
            team: 球队名称
            venue: 'home'/'away'/'neutral'
        
        Returns:
            TeamFeatures: 特征向量
        """
        stats = self.team_stats[team]
        
        if not stats['goals_scored']:
            return TeamFeatures(
                team=team, avg_goals_scored=1.0, avg_goals_conceded=1.0,
                avg_xg=1.0, recent_form=1.5, attack_efficiency=1.0,
                defense_efficiency=1.0, home_advantage=1.0,
                away_disadvantage=1.0, consistency=0.5
            )
        
        # 基础统计
        avg_scored = np.mean(stats['goals_scored'])
        avg_conceded = np.mean(stats['goals_conceded'])
        avg_xg = np.mean(stats['xg']) if stats['xg'] else avg_scored
        
        # 近期状态 (最近5场)
        recent_points = stats['points'][-5:] if len(stats['points']) >= 5 else stats['points']
        recent_form = np.mean(recent_points) if recent_points else 1.5
        
        # 进攻效率 (实际进球 / xG)
        total_xg = sum(stats['xg']) if stats['xg'] else 1
        attack_efficiency = sum(stats['goals_scored']) / max(total_xg, 0.1)
        attack_efficiency = min(2.0, max(0.5, attack_efficiency))
        
        # 防守效率 (xG / 实际失球)
        total_xg_against = sum(stats['goals_conceded']) * 0.8  # 简化估算
        defense_efficiency = max(total_xg_against, 0.1) / sum(stats['goals_conceded']) if sum(stats['goals_conceded']) > 0 else 1.0
        defense_efficiency = min(2.0, max(0.5, defense_efficiency))
        
        # 主客场优势
        home_matches = stats['home_matches']
        away_matches = stats['away_matches']
        
        if home_matches and away_matches:
            home_scored = np.mean([m.get('home_score', 0) for m in home_matches])
            away_scored = np.mean([m.get('away_score', 0) for m in away_matches])
            home_advantage = home_scored / max(away_scored, 0.1)
            away_disadvantage = away_scored / max(home_scored, 0.1)
        else:
            home_advantage = 1.0
            away_disadvantage = 1.0
        
        # 稳定性 (进球数标准差的倒数)
        if len(stats['goals_scored']) > 1:
            std = np.std(stats['goals_scored'])
            consistency = 1.0 / (1.0 + std)
        else:
            consistency = 0.5
        
        return TeamFeatures(
            team=team,
            avg_goals_scored=round(avg_scored, 2),
            avg_goals_conceded=round(avg_conceded, 2),
            avg_xg=round(avg_xg, 2),
            recent_form=round(recent_form, 2),
            attack_efficiency=round(attack_efficiency, 2),
            defense_efficiency=round(defense_efficiency, 2),
            home_advantage=round(home_advantage, 2),
            away_disadvantage=round(away_disadvantage, 2),
            consistency=round(consistency, 2)
        )
    
    def extract_match_features(self, home: str, away: str) -> Dict[str, Any]:
        """
        提取比赛级特征
        
        Args:
            home: 主队
            away: 客队
        
        Returns:
            Dict: 包含两队特征和交互特征
        """
        home_features = self.extract_team_features(home, 'home')
        away_features = self.extract_team_features(away, 'away')
        
        # 交互特征
        home_xg_diff = home_features.avg_xg - away_features.avg_goals_conceded
        away_xg_diff = away_features.avg_xg - home_features.avg_goals_conceded
        
        total_xg = home_features.avg_xg + away_features.avg_xg
        
        # 历史对战
        h2h = self._get_head_to_head(home, away)
        
        return {
            'home': home_features.to_dict(),
            'away': away_features.to_dict(),
            'interaction': {
                'home_xg_diff': round(home_xg_diff, 2),
                'away_xg_diff': round(away_xg_diff, 2),
                'total_xg': round(total_xg, 2),
                'home_attack_vs_away_defense': round(home_features.attack_efficiency / max(away_features.defense_efficiency, 0.1), 2),
                'away_attack_vs_home_defense': round(away_features.attack_efficiency / max(home_features.defense_efficiency, 0.1), 2)
            },
            'head_to_head': h2h
        }
    
    def _get_head_to_head(self, team1: str, team2: str) -> Dict[str, Any]:
        """获取历史对战记录"""
        matches = []
        for match in self.matches:
            home = match.get('home')
            away = match.get('away')
            if (home == team1 and away == team2) or (home == team2 and away == team1):
                matches.append(match)
        
        if not matches:
            return {'matches': 0, 'team1_wins': 0, 'team2_wins': 0, 'draws': 0, 'avg_total_goals': 0}
        
        team1_wins = sum(1 for m in matches if (m['home'] == team1 and m['home_score'] > m['away_score']) or (m['away'] == team1 and m['away_score'] > m['home_score']))
        team2_wins = sum(1 for m in matches if (m['home'] == team2 and m['home_score'] > m['away_score']) or (m['away'] == team2 and m['away_score'] > m['home_score']))
        draws = len(matches) - team1_wins - team2_wins
        avg_goals = np.mean([m['home_score'] + m['away_score'] for m in matches])
        
        return {
            'matches': len(matches),
            'team1_wins': team1_wins,
            'team2_wins': team2_wins,
            'draws': draws,
            'avg_total_goals': round(avg_goals, 2)
        }
    
    def build_training_data(self, lookback: int = 10) -> List[Dict[str, Any]]:
        """
        构建训练数据集
        
        用于训练大小球预测模型 (XGBoost/泊松)
        
        Returns:
            List[Dict]: 每条记录包含特征和标签 (total_goals, over_under)
        """
        training_data = []
        
        for i, match in enumerate(self.matches):
            if i < lookback:
                continue  # 前面几场没有足够历史
            
            home = match.get('home')
            away = match.get('away')
            total_goals = match.get('home_score', 0) + match.get('away_score', 0)
            
            # 使用之前的数据构建特征
            historical = self.matches[:i]
            temp_engineer = FeatureEngineer(historical)
            
            try:
                features = temp_engineer.extract_match_features(home, away)
                
                # Add score data if available
                if 'home_score' in match:
                    features['home_score'] = match['home_score']
                if 'away_score' in match:
                    features['away_score'] = match['away_score']
                
                # 添加标签
                features['label'] = {
                    'total_goals': total_goals,
                    'over_2_5': 1 if total_goals > 2.5 else 0,
                    'over_1_5': 1 if total_goals > 1.5 else 0,
                    'over_3_5': 1 if total_goals > 3.5 else 0
                }
                
                training_data.append(features)
            except Exception as e:
                # 跳过无法提取特征的比赛
                continue
        
        return training_data
    
    def get_feature_importance(self, model_predictions: List[Dict]) -> Dict[str, float]:
        """
        计算特征重要性 (简化版，基于预测差异)
        
        实际使用时应结合 SHAP 或 XGBoost 的 feature_importances_
        """
        # 简化实现，返回特征名称
        return {
            'avg_xg': 0.25,
            'attack_efficiency': 0.20,
            'defense_efficiency': 0.15,
            'recent_form': 0.15,
            'home_advantage': 0.10,
            'consistency': 0.10,
            'head_to_head': 0.05
        }


def load_features_from_data_fetcher(fetcher, tournament: str = 'worldcup', year: int = 2022) -> FeatureEngineer:
    """
    从数据获取器加载特征工程器
    
    Args:
        fetcher: DataFetcher 实例
        tournament: 赛事
        year: 年份
    
    Returns:
        FeatureEngineer: 特征工程器
    """
    matches = fetcher.fetch_matches(tournament=tournament, year=year)
    
    if matches and 'error' in matches[0]:
        print(f"Warning: {matches[0]['error']}")
        return FeatureEngineer([])
    
    return FeatureEngineer(matches)


# 扩展 TeamFeatures 添加 to_dict 方法
TeamFeatures.to_dict = lambda self: {
    'team': self.team,
    'avg_goals_scored': self.avg_goals_scored,
    'avg_goals_conceded': self.avg_goals_conceded,
    'avg_xg': self.avg_xg,
    'recent_form': self.recent_form,
    'attack_efficiency': self.attack_efficiency,
    'defense_efficiency': self.defense_efficiency,
    'home_advantage': self.home_advantage,
    'away_disadvantage': self.away_disadvantage,
    'consistency': self.consistency
}
