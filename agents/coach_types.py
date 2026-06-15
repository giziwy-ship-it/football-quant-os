#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Coach Types - Base types for CoachFactor system
Separated to avoid circular imports
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math


class CoachType(Enum):
    """教练类型分类"""
    STABLE = "stable"           # 稳定型：低冷门（瓜迪奥拉系/德尚系/西蒙尼系）
    MODERATE = "moderate"       # 中风险：中冷门（克洛普系/斯卡洛尼系）
    VOLATILE = "volatile"       # 高爆炸：高冷门（新帅/实验型/极端战术派）
    UNKNOWN = "unknown"         # 未知/数据不足


class TacticalStyle(Enum):
    """战术风格"""
    CONTROL = "control"         # 控球主导（低波动）
    PRESS = "press"             # 高压逼抢（中波动）
    COUNTER = "counter"         # 反击型（低波动）
    EXTREME = "extreme"         # 极端战术（高波动）
    EXPERIMENTAL = "experimental" # 实验型（最高波动）


@dataclass
class CoachProfile:
    """
    教练档案
    
    包含所有可量化的教练特征
    """
    name: str
    nationality: str
    age: int = 0
    
    # 战术特征
    tactical_style: TacticalStyle = TacticalStyle.CONTROL
    formation_flexibility: float = 0.0  # 0-10, 越高越不稳定
    avg_formations_per_tournament: float = 1.0
    
    # 临场决策
    avg_substitutions_per_match: float = 3.0
    early_substitution_rate: float = 0.0  # 60分钟前换人比例
    aggressive_substitution_rate: float = 0.0  # 进攻型换人比例
    
    # 大赛经验
    world_cup_experience: int = 0  # 参加世界杯次数
    euro_experience: int = 0     # 参加欧洲杯次数
    knockout_stage_wins: int = 0
    total_major_tournaments: int = 0
    
    # 心理控制
    emotional_stability: float = 5.0  # 0-10, 越高越稳定
    media_influence_susceptibility: float = 5.0  # 0-10, 越高越易受媒体影响
    team_meltdown_incidents: int = 0  # 崩盘事件数
    
    # 轮换策略
    rotation_tendency: float = 0.0  # 0-10, 越高越爱轮换
    squad_depth_utilization: float = 0.0  # 0-1, 使用球员比例
    
    # 策略差异
    vs_strong_team_strategy: str = "defensive"  # defensive/balanced/aggressive
    vs_weak_team_strategy: str = "aggressive"   # defensive/balanced/aggressive
    strategy_extremity: float = 0.0  # 0-10, 策略极端程度
    
    # 历史数据
    avg_goals_per_match: float = 0.0  # 执教该队场均进球
    avg_conceded_per_match: float = 0.0  # 执教该队场均失球
    clean_sheet_rate: float = 0.0
    comeback_rate: float = 0.0  # 落后逆转率
    
    def get_tournament_iq(self) -> float:
        """计算大赛经验评分 0-10"""
        base = min(10, self.world_cup_experience * 2 + self.euro_experience * 1.5)
        bonus = min(5, self.knockout_stage_wins * 0.5)
        return min(10, base + bonus)
    
    def get_tactical_stability_score(self) -> float:
        """战术稳定性评分 0-10（越高越稳定）"""
        # 阵型变化少 = 稳定
        formation_penalty = max(0, 10 - self.formation_flexibility * 2)
        style_penalty = {
            TacticalStyle.CONTROL: 2,
            TacticalStyle.PRESS: 1,
            TacticalStyle.COUNTER: 2,
            TacticalStyle.EXTREME: -2,
            TacticalStyle.EXPERIMENTAL: -3,
        }.get(self.tactical_style, 0)
        return max(0, min(10, formation_penalty + style_penalty))
