#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorldCupDataEngineer - 世界杯数据采集与特征工程系统 v1.0
Naga Core Football Quant OS 升级组件

核心功能：
1. 2014/2018/2022 三届世界杯结构化数据采集
2. 特征工程流水线（ELO差、进攻差、防守指数、压力因子）
3. 模型训练数据集生成
4. 跨届对比分析

数据来源：FIFA官方、Transfermarkt、WorldFootball.net（免费官方）
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import math


# ============================================================
# 数据模型定义
# ============================================================

class WorldCupYear(Enum):
    WC_2014 = 2014
    WC_2018 = 2018
    WC_2022 = 2022


class MatchStage(Enum):
    GROUP = "group"
    ROUND_16 = "round_of_16"
    QUARTER = "quarter_final"
    SEMI = "semi_final"
    THIRD_PLACE = "third_place"
    FINAL = "final"


@dataclass
class TeamPerformance:
    """球队表现数据"""
    name: str
    fifa_rank: int = 0
    elo: float = 1500.0
    
    # 进攻指标
    goals_scored: int = 0
    goals_avg: float = 0.0
    shots_per_game: float = 0.0
    shot_accuracy: float = 0.0
    
    # 防守指标
    goals_conceded: int = 0
    defense_strength: float = 0.0  # 越低越好
    clean_sheets: int = 0
    
    # 状态指标
    recent_form: str = ""  # e.g., "WWDLW"
    win_streak: int = 0
    
    # 世界杯特定
    group_points: int = 0
    group_position: int = 0
    advanced: bool = False
    
    def to_features(self) -> Dict[str, float]:
        """转换为特征向量"""
        return {
            'fifa_rank': self.fifa_rank,
            'elo': self.elo,
            'goals_avg': self.goals_avg,
            'defense_strength': self.defense_strength,
            'clean_sheets': self.clean_sheets,
            'win_streak': self.win_streak,
            'group_points': self.group_points,
        }


@dataclass
class MatchResult:
    """比赛结果"""
    team_a: str
    team_b: str
    score_a: int
    score_b: int
    stage: MatchStage
    
    # 附加信息
    extra_time: bool = False
    penalties: bool = False
    penalty_a: int = 0
    penalty_b: int = 0
    
    # 市场数据（如有）
    odds_a: float = 0.0
    odds_draw: float = 0.0
    odds_b: float = 0.0
    
    @property
    def winner(self) -> Optional[str]:
        if self.score_a > self.score_b:
            return self.team_a
        elif self.score_b > self.score_a:
            return self.team_b
        elif self.penalties:
            return self.team_a if self.penalty_a > self.penalty_b else self.team_b
        return None  # Draw in group stage
    
    @property
    def goal_diff(self) -> int:
        return self.score_a - self.score_b


@dataclass
class WorldCupData:
    """单届世界杯完整数据"""
    year: int
    host: str
    champion: str = ""
    runner_up: str = ""
    third_place: str = ""
    fourth_place: str = ""
    
    total_matches: int = 0
    total_goals: int = 0
    avg_goals_per_match: float = 0.0
    teams_count: int = 32
    
    groups: Dict[str, List[TeamPerformance]] = field(default_factory=dict)
    knockout_matches: List[MatchResult] = field(default_factory=list)
    all_matches: List[MatchResult] = field(default_factory=list)
    top_players: List[Dict[str, Any]] = field(default_factory=list)
    
    # 统计特征
    biggest_win: Optional[MatchResult] = None
    dark_horses: List[str] = field(default_factory=list)
    
    def calculate_stats(self):
        """计算统计指标"""
        if self.all_matches:
            self.total_matches = len(self.all_matches)
            self.total_goals = sum(m.score_a + m.score_b for m in self.all_matches)
            self.avg_goals_per_match = self.total_goals / self.total_matches if self.total_matches > 0 else 0
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            'year': self.year,
            'host': self.host,
            'champion': self.champion,
            'runner_up': self.runner_up,
            'third_place': self.third_place,
            'fourth_place': self.fourth_place,
            'total_matches': self.total_matches,
            'total_goals': self.total_goals,
            'avg_goals_per_match': round(self.avg_goals_per_match, 2),
            'teams_count': self.teams_count,
        }


# ============================================================
# 特征工程引擎
# ============================================================

class FeatureEngineer:
    """
    特征工程引擎
    
    核心特征：
    1. ELO差值 → 实力差距
    2. 进攻效率差 → AttackDiff
    3. 防守稳定性指数 → DefenseIndex
    4. 压力修正因子 → PressureFactor
    5. 赛程疲劳效应 → FatigueIndex
    6. 历史交锋修正 → H2HFactor
    """
    
    # 权重配置（可训练）
    WEIGHTS = {
        'strength': 0.45,
        'attack': 0.25,
        'defense': 0.15,
        'pressure': 0.15,
    }
    
    @staticmethod
    def elo_probability(elo_a: float, elo_b: float) -> float:
        """ELO模型胜率概率"""
        return 1.0 / (1.0 + math.pow(10, (elo_b - elo_a) / 400))
    
    @staticmethod
    def attack_diff(team_a: TeamPerformance, team_b: TeamPerformance) -> float:
        """进攻能力差异"""
        return team_a.goals_avg - team_b.goals_avg
    
    @staticmethod
    def defense_index(team_a: TeamPerformance, team_b: TeamPerformance) -> float:
        """防守稳定性指数（越低越好，所以A-B正值表示A防守更好）"""
        return team_b.defense_strength - team_a.defense_strength
    
    @staticmethod
    def pressure_factor(stage: MatchStage, is_knockout: bool) -> float:
        """
        压力修正因子
        淘汰赛压力 > 小组赛
        决赛 > 半决赛 > 1/4 > 1/8
        """
        if not is_knockout:
            return 1.0
        
        pressure_map = {
            MatchStage.ROUND_16: 1.1,
            MatchStage.QUARTER: 1.15,
            MatchStage.SEMI: 1.25,
            MatchStage.THIRD_PLACE: 1.1,
            MatchStage.FINAL: 1.35,
        }
        return pressure_map.get(stage, 1.0)
    
    @staticmethod
    def fatigue_index(days_rest: int) -> float:
        """
        疲劳指数
        休息天数影响表现
        """
        if days_rest >= 5:
            return 1.0  # 充分休息
        elif days_rest >= 3:
            return 0.95
        elif days_rest >= 2:
            return 0.88
        else:
            return 0.80  # 极度疲劳
    
    @classmethod
    def generate_features(
        cls,
        team_a: TeamPerformance,
        team_b: TeamPerformance,
        stage: MatchStage = MatchStage.GROUP,
        days_rest_a: int = 3,
        days_rest_b: int = 3,
    ) -> Dict[str, float]:
        """
        生成完整特征向量
        
        Returns:
            特征字典，可直接用于模型训练
        """
        is_knockout = stage != MatchStage.GROUP
        
        # 核心特征
        strength = cls.elo_probability(team_a.elo, team_b.elo)
        attack = cls.attack_diff(team_a, team_b)
        defense = cls.defense_index(team_a, team_b)
        pressure = cls.pressure_factor(stage, is_knockout)
        fatigue_a = cls.fatigue_index(days_rest_a)
        fatigue_b = cls.fatigue_index(days_rest_b)
        
        # 综合评分（加权）
        # 归一化攻击和防守差异到[-1, 1]
        attack_norm = max(-1, min(1, attack / 2.0))
        defense_norm = max(-1, min(1, defense / 2.0))
        
        final_score = (
            cls.WEIGHTS['strength'] * strength +
            cls.WEIGHTS['attack'] * (0.5 + 0.5 * attack_norm) +
            cls.WEIGHTS['defense'] * (0.5 + 0.5 * defense_norm) +
            cls.WEIGHTS['pressure'] * (1.0 / pressure)  # 压力越大，表现可能下降
        )
        
        # Softmax前的logits
        home_logit = math.log(final_score / (1 - final_score)) if 0 < final_score < 1 else 0
        
        return {
            # 原始特征
            'elo_a': team_a.elo,
            'elo_b': team_b.elo,
            'elo_diff': team_a.elo - team_b.elo,
            'fifa_rank_a': team_a.fifa_rank,
            'fifa_rank_b': team_b.fifa_rank,
            'rank_diff': team_a.fifa_rank - team_b.fifa_rank,
            'goals_avg_a': team_a.goals_avg,
            'goals_avg_b': team_b.goals_avg,
            'attack_diff': attack,
            'defense_a': team_a.defense_strength,
            'defense_b': team_b.defense_strength,
            'defense_diff': defense,
            'pressure_factor': pressure,
            'fatigue_a': fatigue_a,
            'fatigue_b': fatigue_b,
            'is_knockout': 1 if is_knockout else 0,
            
            # 衍生特征
            'strength_prob': strength,
            'final_score': final_score,
            'home_logit': home_logit,
        }
    
    @classmethod
    def generate_training_sample(
        cls,
        match: MatchResult,
        team_a_perf: TeamPerformance,
        team_b_perf: TeamPerformance,
        days_rest_a: int = 3,
        days_rest_b: int = 3,
    ) -> Dict[str, Any]:
        """
        生成单个训练样本
        
        Returns:
            包含特征和标签的完整训练样本
        """
        features = cls.generate_features(
            team_a_perf, team_b_perf,
            match.stage, days_rest_a, days_rest_b
        )
        
        # 标签
        label = 0  # 0=home win, 1=draw, 2=away win
        if match.score_a > match.score_b:
            label = 0
        elif match.score_a == match.score_b:
            label = 1
        else:
            label = 2
        
        return {
            'match_id': f"{match.team_a}_vs_{match.team_b}_{match.stage.value}",
            'features': features,
            'label': label,
            'actual_score': [match.score_a, match.score_b],
            'odds': {
                'home': match.odds_a,
                'draw': match.odds_draw,
                'away': match.odds_b,
            }
        }


# ============================================================
# 预测模型
# ============================================================

class WorldCupPredictor:
    """
    世界杯预测模型
    
    基于特征工程引擎，输出：
    1. 胜平负概率
    2. 价值投注判断
    3. 冷门指数
    4. 风险等级
    """
    
    def __init__(self, feature_engineer: FeatureEngineer = None):
        self.fe = feature_engineer or FeatureEngineer()
    
    def predict(self, team_a: TeamPerformance, team_b: TeamPerformance,
                stage: MatchStage = MatchStage.GROUP,
                odds: Dict[str, float] = None) -> Dict[str, Any]:
        """
        预测单场比赛
        """
        features = self.fe.generate_features(team_a, team_b, stage)
        
        # 基础概率（基于ELO + 特征加权）
        base_prob_home = features['final_score']
        
        # 加入平局概率（历史约25%）
        draw_prob = 0.25 * (1 - abs(base_prob_home - 0.5) * 2)
        
        # 归一化
        remaining = 1 - draw_prob
        prob_home = base_prob_home * remaining
        prob_away = (1 - base_prob_home) * remaining
        
        # 确保和为1
        total = prob_home + draw_prob + prob_away
        prob_home /= total
        prob_draw = draw_prob / total
        prob_away /= total
        
        # 价值投注分析
        value_bets = []
        if odds:
            implied_home = 1.0 / odds.get('home', 2.0)
            implied_draw = 1.0 / odds.get('draw', 3.0)
            implied_away = 1.0 / odds.get('away', 3.0)
            
            for label, prob, implied, name in [
                (0, prob_home, implied_home, 'home'),
                (1, prob_draw, implied_draw, 'draw'),
                (2, prob_away, implied_away, 'away'),
            ]:
                value = prob - implied
                if value > 0.02:
                    value_bets.append({
                        'selection': name,
                        'value': round(value, 3),
                        'recommendation': 'BET' if value > 0.05 else 'WATCH',
                    })
        
        # 冷门指数
        upset_index = self._calculate_upset_index(team_a, team_b, features)
        
        # 风险等级
        risk_level = self._assess_risk(upset_index, len(value_bets))
        
        # 建议投注比例（Kelly简化版）
        bet_size = 0
        if value_bets:
            best_value = max(v['value'] for v in value_bets)
            if best_value > 0:
                bet_size = min(0.03, best_value * 0.5)  # 最大3%，Kelly半仓
        
        return {
            'match': f"{team_a.name} vs {team_b.name}",
            'probabilities': {
                'home_win': round(prob_home, 3),
                'draw': round(prob_draw, 3),
                'away_win': round(prob_away, 3),
            },
            'value_bets': value_bets,
            'upset_index': round(upset_index, 3),
            'risk_level': risk_level,
            'bet_sizing': round(bet_size, 4),
            'features': features,
        }
    
    def _calculate_upset_index(self, team_a: TeamPerformance, 
                               team_b: TeamPerformance,
                               features: Dict[str, float]) -> float:
        """计算冷门指数"""
        # 弱队实力 / 强队实力 * 波动性
        favorite = team_a if team_a.elo > team_b.elo else team_b
        underdog = team_b if team_a.elo > team_b.elo else team_a
        
        strength_ratio = underdog.elo / favorite.elo
        
        # 波动性：排名差距大但ELO接近 = 高波动
        rank_gap = abs(team_a.fifa_rank - team_b.fifa_rank)
        elo_gap = abs(team_a.elo - team_b.elo)
        volatility = rank_gap / (elo_gap / 10 + 1)
        
        upset_index = strength_ratio * (1 + volatility * 0.1)
        return min(1.0, upset_index)
    
    def _assess_risk(self, upset_index: float, value_bet_count: int) -> str:
        """评估风险等级"""
        if upset_index > 0.85:
            return "HIGH"
        elif upset_index > 0.6 or value_bet_count > 0:
            return "MEDIUM"
        return "LOW"


# ============================================================
# 数据采集提示词模板（Prompt Engineering）
# ============================================================

WORLD_CUP_DATA_COLLECTION_PROMPT = """
你是一名专业体育数据分析师 + 足球数据工程师 + FIFA数据库研究员。

任务：系统性整理 {year} FIFA世界杯结构化数据。

## 必须采集的数据维度：

### 1. 基础赛事信息
- 年份、举办国家
- 冠军/亚军/季军/殿军
- 总场次、总进球数、场均进球
- 参赛队伍数量

### 2. 小组赛数据（每组输出）
- 小组名称
- 每支球队：积分、进球/失球/净胜球、胜平负、是否晋级

### 3. 淘汰赛路径
- 16强/8强/半决赛/三四名/决赛对阵与比分
- 格式：阶段 | 比赛 | 比分 | 晋级球队

### 4. 冠军路径
- 冠军球队每场比赛：比分、对手、是否加时/点球

### 5. 球员核心数据（Top 10）
- 姓名、国家、进球、助攻、出场、关键事件

### 6. 数据对比分析
- 场均进球趋势
- 冠军球队风格
- 黑马球队列表
- 最大比分比赛

## 输出格式：
先输出JSON结构化数据，再输出Markdown表格展示关键统计。

## 约束：
- 不允许编造数据
- 必须数字，不允许模糊描述
- 数据缺失标记为null
"""


# ============================================================
# 示例数据（2022世界杯 - 用于测试）
# ============================================================

WC_2022_SAMPLE = {
    "year": 2022,
    "host": "Qatar",
    "champion": "Argentina",
    "runner_up": "France",
    "third_place": "Croatia",
    "fourth_place": "Morocco",
    "total_matches": 64,
    "total_goals": 172,
    "avg_goals_per_match": 2.69,
    "teams_count": 32,
}


# ============================================================
# 快速测试
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("WorldCupDataEngineer v1.0 - Feature Engineering Test")
    print("=" * 60)
    print()
    
    # 创建示例球队
    argentina = TeamPerformance(
        name="Argentina",
        fifa_rank=3,
        elo=1840,
        goals_avg=2.2,
        defense_strength=0.8,
        group_points=6,
    )
    
    france = TeamPerformance(
        name="France",
        fifa_rank=4,
        elo=1820,
        goals_avg=2.1,
        defense_strength=0.9,
        group_points=6,
    )
    
    # 特征工程
    fe = FeatureEngineer()
    features = fe.generate_features(argentina, france, MatchStage.FINAL)
    
    print("[Feature Engineering Test]")
    print(f"  Argentina ELO: {features['elo_a']}")
    print(f"  France ELO: {features['elo_b']}")
    print(f"  ELO Diff: {features['elo_diff']}")
    print(f"  Strength Prob: {features['strength_prob']:.3f}")
    print(f"  Attack Diff: {features['attack_diff']:.3f}")
    print(f"  Defense Diff: {features['defense_diff']:.3f}")
    print(f"  Final Score: {features['final_score']:.3f}")
    print()
    
    # 预测模型
    predictor = WorldCupPredictor()
    odds = {'home': 2.5, 'draw': 3.2, 'away': 2.8}
    result = predictor.predict(argentina, france, MatchStage.FINAL, odds)
    
    print("[Prediction Result]")
    print(f"  Match: {result['match']}")
    print(f"  Home Win: {result['probabilities']['home_win']:.1%}")
    print(f"  Draw: {result['probabilities']['draw']:.1%}")
    print(f"  Away Win: {result['probabilities']['away_win']:.1%}")
    print(f"  Upset Index: {result['upset_index']}")
    print(f"  Risk Level: {result['risk_level']}")
    print(f"  Value Bets: {len(result['value_bets'])}")
    for vb in result['value_bets']:
        print(f"    {vb['selection'].upper()}: +{vb['value']:.1%} edge -> {vb['recommendation']}")
    print()
    
    print("=" * 60)
    print("WorldCupDataEngineer - Ready for Integration")
    print("=" * 60)
