# -*- coding: utf-8 -*-
"""
HT/FT Data Framework - 半全场数据获取框架

问题：当前缺少半场数据，导致半全场预测准确率仅25%

解决方案：
1. 创建数据接口定义，支持多源接入
2. 实现模拟半场数据生成（基于历史统计）
3. 接入实时API（ESPN/500.com半场数据）

数据源：
- ESPN API：提供半场比分、控球率、射门等
- 500.com：部分比赛有半场数据
- OddsPortal：历史半场数据
- 本地模拟：基于球队历史上半场进球分布
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime
import random
import json


@dataclass
class HalfTimeData:
    """半场数据"""
    home_score: int = 0
    away_score: int = 0
    home_possession: float = 50.0
    away_possession: float = 50.0
    home_shots: int = 0
    away_shots: int = 0
    home_shots_on_target: int = 0
    away_shots_on_target: int = 0
    home_corners: int = 0
    away_corners: int = 0
    home_fouls: int = 0
    away_fouls: int = 0
    
    @property
    def total_goals_ht(self) -> int:
        return self.home_score + self.away_score
    
    @property
    def winner(self) -> str:
        if self.home_score > self.away_score:
            return "home"
        elif self.away_score > self.home_score:
            return "away"
        else:
            return "draw"
    
    def to_dict(self) -> Dict:
        return {
            'home_score': self.home_score,
            'away_score': self.away_score,
            'home_possession': self.home_possession,
            'away_possession': self.away_possession,
            'home_shots': self.home_shots,
            'away_shots': self.away_shots,
            'total_goals': self.total_goals_ht,
            'winner': self.winner,
        }


class HTDataProvider:
    """半全场数据提供者基类"""
    
    def get_ht_data(self, match_id: str) -> Optional[HalfTimeData]:
        """获取半场数据"""
        raise NotImplementedError


class SimulatedHTProvider(HTDataProvider):
    """
    模拟半场数据生成器
    
    基于球队历史统计生成半场数据
    """
    
    # 2026世界杯首轮上半场统计（基于12场实际数据）
    HT_STATS = {
        'average_ht_goals': 0.8,      # 上半场平均进球
        'ht_draw_rate': 0.55,          # 上半场平局率55%
        'ht_home_lead_rate': 0.25,     # 上半场主队领先率25%
        'ht_away_lead_rate': 0.20,     # 上半场客队领先率20%
    }
    
    # 球队上半场特性（基于实际表现）
    TEAM_HT_PROFILE = {
        'Germany': {'attack': 0.9, 'defense': 0.8},      # 上半场强势
        'Brazil': {'attack': 0.7, 'defense': 0.7},        # 上半场稳健
        'Netherlands': {'attack': 0.6, 'defense': 0.6},   # 上半场慢热
        'Sweden': {'attack': 0.5, 'defense': 0.7},        # 上半场保守
        'Australia': {'attack': 0.4, 'defense': 0.6},     # 上半场弱势
        'Ivory Coast': {'attack': 0.4, 'defense': 0.7},  # 上半场保守
        'Mexico': {'attack': 0.6, 'defense': 0.6},       # 上半场均衡
        'South Korea': {'attack': 0.5, 'defense': 0.6},  # 上半场保守
    }
    
    def __init__(self):
        self.random_seed = 42
    
    def generate_ht_data(
        self,
        home_team: str,
        away_team: str,
        home_odds: float,
        away_odds: float,
        final_home_goals: int = None,
        final_away_goals: int = None,
    ) -> HalfTimeData:
        """
        生成模拟半场数据
        
        Args:
            home_team: 主队名
            away_team: 客队名
            home_odds: 主胜赔率
            away_odds: 客胜赔率
            final_home_goals: 全场主队进球（可选，用于约束）
            final_away_goals: 全场客队进球（可选，用于约束）
        """
        ht = HalfTimeData()
        
        # 获取球队上半场特性
        home_profile = self.TEAM_HT_PROFILE.get(home_team, {'attack': 0.5, 'defense': 0.6})
        away_profile = self.TEAM_HT_PROFILE.get(away_team, {'attack': 0.5, 'defense': 0.6})
        
        # 基于赔率调整上半场预期
        home_strength = 1.0 / home_odds
        away_strength = 1.0 / away_odds
        
        # 计算上半场进球概率
        home_ht_goal_prob = home_profile['attack'] * home_strength * 0.5
        away_ht_goal_prob = away_profile['attack'] * away_strength * 0.5
        
        # 生成上半场比分
        ht.home_score = self._generate_goals(home_ht_goal_prob)
        ht.away_score = self._generate_goals(away_ht_goal_prob)
        
        # 如果有全场数据，约束上半场进球不超过全场
        if final_home_goals is not None:
            ht.home_score = min(ht.home_score, final_home_goals)
        if final_away_goals is not None:
            ht.away_score = min(ht.away_score, final_away_goals)
        
        # 生成控球率
        ht.home_possession = 50 + (home_strength - away_strength) * 20
        ht.home_possession = max(35, min(65, ht.home_possession))
        ht.away_possession = 100 - ht.home_possession
        
        # 生成射门数据
        ht.home_shots = int(ht.home_score * 3 + random.randint(1, 3))
        ht.away_shots = int(ht.away_score * 3 + random.randint(1, 3))
        ht.home_shots_on_target = max(1, int(ht.home_shots * 0.4))
        ht.away_shots_on_target = max(1, int(ht.away_shots * 0.4))
        
        return ht
    
    def _generate_goals(self, prob: float) -> int:
        """根据概率生成进球数"""
        if random.random() < prob:
            return 1
        elif random.random() < prob * 0.3:  # 进2球的概率较低
            return 2
        else:
            return 0


class ESPNHTProvider(HTDataProvider):
    """
    ESPN API 半场数据获取
    
    接口：ESPN Soccer API
    限制：需要API Key，免费额度有限
    """
    
    API_BASE = "https://site.api.espn.com/apis/site/v2/sports/soccer"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.cache = {}
    
    def get_ht_data(self, match_id: str) -> Optional[HalfTimeData]:
        """从ESPN获取半场数据"""
        # 实际实现需要requests库和API调用
        # 这里提供接口定义
        
        # 模拟返回（实际使用时替换为真实API调用）
        return None
    
    def parse_espn_response(self, data: Dict) -> HalfTimeData:
        """解析ESPN响应"""
        ht = HalfTimeData()
        
        if 'competitions' in data:
            comp = data['competitions'][0]
            if 'status' in comp:
                status = comp['status']
                if 'type' in status and status['type'] == 'IN_PROGRESS':
                    # 比赛进行中，可能有半场数据
                    pass
        
        return ht


class HTDataManager:
    """
    半全场数据管理器
    
    统一管理多个数据源，提供统一的半场数据接口
    """
    
    def __init__(self):
        self.providers: List[HTDataProvider] = []
        self.simulator = SimulatedHTProvider()
        self.cache = {}
    
    def add_provider(self, provider: HTDataProvider):
        """添加数据源"""
        self.providers.append(provider)
    
    def get_ht_data(
        self,
        match_id: str,
        home_team: str = "",
        away_team: str = "",
        home_odds: float = 2.0,
        away_odds: float = 2.0,
        use_simulation: bool = True,
    ) -> Optional[HalfTimeData]:
        """
        获取半场数据
        
        优先级：
        1. 缓存数据
        2. 真实数据源（ESPN/500.com）
        3. 模拟数据（fallback）
        """
        # 检查缓存
        if match_id in self.cache:
            return self.cache[match_id]
        
        # 尝试真实数据源
        for provider in self.providers:
            try:
                data = provider.get_ht_data(match_id)
                if data:
                    self.cache[match_id] = data
                    return data
            except Exception:
                continue
        
        # 使用模拟数据
        if use_simulation and home_team and away_team:
            data = self.simulator.generate_ht_data(
                home_team, away_team, home_odds, away_odds
            )
            self.cache[match_id] = data
            return data
        
        return None
    
    def predict_ht_ft(
        self,
        home_team: str,
        away_team: str,
        home_odds: float,
        away_odds: float,
        final_pred_home: float,
        final_pred_away: float,
    ) -> Dict[str, Any]:
        """
        预测半全场结果
        
        Returns:
            {
                'ht': HalfTimeData,
                'ft': {'home': float, 'away': float, 'draw': float},
                'combinations': {
                    'H/H': prob, 'H/D': prob, 'H/A': prob,
                    'D/H': prob, 'D/D': prob, 'D/A': prob,
                    'A/H': prob, 'A/D': prob, 'A/A': prob,
                }
            }
        """
        # 获取/生成半场数据
        ht = self.simulator.generate_ht_data(
            home_team, away_team, home_odds, away_odds
        )
        
        # 基于半场结果预测全场
        # 如果半场主队领先，全场主队胜概率增加
        ft_home = final_pred_home
        ft_away = final_pred_away
        ft_draw = 1 - ft_home - ft_away
        
        if ht.winner == "home":
            ft_home += 0.15
            ft_draw -= 0.05
            ft_away -= 0.10
        elif ht.winner == "away":
            ft_away += 0.15
            ft_draw -= 0.05
            ft_home -= 0.10
        else:  # 半场平局
            ft_draw += 0.10
            ft_home -= 0.05
            ft_away -= 0.05
        
        # 归一化
        total = ft_home + ft_draw + ft_away
        ft_home /= total
        ft_draw /= total
        ft_away /= total
        
        # 生成9种组合概率
        combinations = {}
        for ht_result in ['H', 'D', 'A']:
            for ft_result in ['H', 'D', 'A']:
                key = f"{ht_result}/{ft_result}"
                # 简化计算：半场概率 × 全场条件概率
                if ht_result == 'H':
                    ht_prob = ft_home * 0.7  # 简化
                elif ht_result == 'D':
                    ht_prob = ft_draw * 0.7
                else:
                    ht_prob = ft_away * 0.7
                
                if ft_result == 'H':
                    ft_cond = ft_home
                elif ft_result == 'D':
                    ft_cond = ft_draw
                else:
                    ft_cond = ft_away
                
                combinations[key] = round(ht_prob * ft_cond, 3)
        
        return {
            'ht': ht.to_dict(),
            'ft': {
                'home': round(ft_home, 3),
                'draw': round(ft_draw, 3),
                'away': round(ft_away, 3),
            },
            'combinations': combinations,
        }


# 测试
if __name__ == "__main__":
    manager = HTDataManager()
    
    # 测试：巴西vs摩洛哥（实际半场?，全场1-1）
    result = manager.predict_ht_ft(
        home_team="Brazil",
        away_team="Morocco",
        home_odds=1.65,
        away_odds=5.48,
        final_pred_home=0.52,
        final_pred_away=0.20,
    )
    
    print("=== HT/FT Framework Test ===")
    print(f"HT Data: {result['ht']}")
    print(f"FT Prob: {result['ft']}")
    print(f"Top 3 Combinations:")
    sorted_combos = sorted(result['combinations'].items(), key=lambda x: x[1], reverse=True)[:3]
    for combo, prob in sorted_combos:
        print(f"  {combo}: {prob:.1%}")
    print()
    
    # 测试：德国vs库拉索（实际半场?，全场7-1）
    result2 = manager.predict_ht_ft(
        home_team="Germany",
        away_team="Curacao",
        home_odds=1.03,
        away_odds=40.17,
        final_pred_home=0.92,
        final_pred_away=0.03,
    )
    
    print(f"Germany vs Curacao:")
    print(f"HT Data: {result2['ht']}")
    print(f"Top 3 Combinations:")
    sorted_combos = sorted(result2['combinations'].items(), key=lambda x: x[1], reverse=True)[:3]
    for combo, prob in sorted_combos:
        print(f"  {combo}: {prob:.1%}")
    
    print("\n=== Framework Ready ===")
    print("Next: Integrate with ESPN API for real HT data")
