#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Physical AI Model Engine (PAME) v4.0
物理AI模型引擎 - 世界杯量化交易核心

整合四大物理维度：
- Mechanics: 力学层 (进攻×状态 - 防守)
- Field: 场域层 (情绪 + 资金流)
- Thermo/Entropy: 熵层 (状态不确定性)
- Quantum: 量子层 (概率坍缩)

Author: Naga Core Team
Version: 4.0.0
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TeamState:
    """球队状态向量"""
    attack: float = 0.5          # 进攻力 0-1
    defense: float = 0.5         # 防守力 0-1
    form: float = 0.5            # 近期状态 0-1
    fatigue: float = 0.0         # 疲劳度 0-1
    morale: float = 0.5          # 士气 0-1
    home_advantage: float = 0.0  # 主场优势系数
    
    # 扩展维度
    elo: float = 1500.0          # ELO评分
    xg_for: float = 1.0          # 预期进球
    xg_against: float = 1.0      # 预期失球
    coach_factor: float = 0.0    # 教练因子 -1~1
    tournament_gene: float = 0.5 # 大赛基因 0-1
    
    def to_vector(self) -> np.ndarray:
        """转换为特征向量"""
        return np.array([
            self.attack, self.defense, self.form, self.fatigue,
            self.morale, self.home_advantage, self.elo / 2000,
            self.xg_for / 3, self.xg_against / 3, self.coach_factor,
            self.tournament_gene
        ])


@dataclass
class MarketState:
    """市场状态"""
    home_odds: float = 2.0
    draw_odds: float = 3.5
    away_odds: float = 2.0
    home_prob: float = 0.33
    draw_prob: float = 0.33
    away_prob: float = 0.33
    volume: float = 0.0          # 交易量
    odds_history: List[float] = field(default_factory=list)
    
    def implied_probs(self) -> Tuple[float, float, float]:
        """计算市场隐含概率（去水）"""
        inv_h = 1.0 / self.home_odds if self.home_odds > 0 else 0
        inv_d = 1.0 / self.draw_odds if self.draw_odds > 0 else 0
        inv_a = 1.0 / self.away_odds if self.away_odds > 0 else 0
        total = inv_h + inv_d + inv_a
        if total == 0:
            return 0.33, 0.33, 0.33
        return inv_h / total, inv_d / total, inv_a / total


@dataclass
class UpsetSignal:
    """冷门信号"""
    score: float = 0.0           # 0-1, >0.7 高冷门风险
    factors: Dict[str, float] = field(default_factory=dict)
    
    def is_high_risk(self) -> bool:
        return self.score > 0.7
    
    def is_moderate_risk(self) -> bool:
        return 0.4 < self.score <= 0.7


@dataclass
class GoalExplosionSignal:
    """大比分信号"""
    score: float = 0.0
    expected_goals: float = 2.5
    factors: Dict[str, float] = field(default_factory=dict)
    
    def is_likely(self) -> bool:
        return self.score > 0.6


class MechanicsLayer:
    """
    力学层 - 球队基本面实力计算
    S = attack × form - defense + coach_bonus + gene_bonus
    """
    
    def compute(self, team: TeamState) -> float:
        """计算球队力学得分"""
        # 基础力学
        base = team.attack * team.form - team.defense * 0.8
        
        # ELO 标准化贡献
        elo_contrib = (team.elo - 1500) / 500 * 0.15
        
        # xG 差异贡献
        xg_diff = (team.xg_for - team.xg_against) * 0.1
        
        # 教练因子
        coach_contrib = team.coach_factor * 0.1
        
        # 大赛基因
        gene_contrib = (team.tournament_gene - 0.5) * 0.05
        
        # 疲劳惩罚
        fatigue_penalty = -team.fatigue * 0.2
        
        score = base + elo_contrib + xg_diff + coach_contrib + gene_contrib + fatigue_penalty
        return np.tanh(score)  # 压缩到 -1~1


class FieldLayer:
    """
    场域层 - 市场情绪与资金流向
    F = tanh(sentiment + money_flow + home_field)
    """
    
    def compute(
        self,
        sentiment: float = 0.0,      # 情绪得分 -1~1
        money_flow: float = 0.0,     # 资金流向 -1~1 (正=看好主)
        home_field: float = 0.0,     # 主场加成 0~1
        weather_factor: float = 0.0  # 天气影响 -0.5~0.5
    ) -> float:
        """计算场域影响因子"""
        raw = sentiment + money_flow * 0.5 + home_field * 0.3 + weather_factor * 0.1
        return np.tanh(raw)


class EntropyLayer:
    """
    熵层 - 状态不确定性度量
    E = (1 - form) × 0.6 + fatigue × 0.4 + coach_volatility × 0.3
    
    熵越高，结果越不可预测（冷门概率越高）
    """
    
    def compute(
        self,
        team: TeamState,
        coach_volatility: float = 0.0,  # 教练风格波动 0-1
        missing_key_players: int = 0,    # 关键球员缺阵数
        historical_upset_rate: float = 0.1  # 历史冷门率
    ) -> float:
        """计算熵值 0-1"""
        form_entropy = (1 - team.form) * 0.6
        fatigue_entropy = team.fatigue * 0.4
        coach_entropy = coach_volatility * 0.3
        injury_entropy = min(missing_key_players * 0.15, 0.5)
        history_entropy = historical_upset_rate * 0.2
        
        entropy = form_entropy + fatigue_entropy + coach_entropy + injury_entropy + history_entropy
        return min(entropy, 1.0)
    
    def upset_probability(self, home_entropy: float, away_entropy: float, 
                          elo_gap: float) -> float:
        """
        冷门概率计算
        高熵 + 小ELO差距 = 高冷门概率
        """
        avg_entropy = (home_entropy + away_entropy) / 2
        # ELO差距越小，冷门越容易发生
        elo_factor = max(0, 1 - elo_gap / 400)
        
        upset = avg_entropy * 0.5 + elo_factor * 0.5
        return min(upset, 1.0)


class QuantumLayer:
    """
    量子层 - 概率坍缩 v3
    
    v3 改进：
    - 降低 gap 阈值，让更多比赛触发平局增强
    - 增加 entropy 对平局的正面影响
    - 引入独立平局基线（不依赖 gap）
    """
    
    # 世界杯历史平局率基线
    DRAW_BASELINE = 0.28
    
    def collapse(
        self,
        s_home: float,
        s_away: float,
        entropy: float,
        temperature: float = 1.0,
        draw_boost: float = 1.0
    ) -> Tuple[float, float, float]:
        """
        量子坍缩 - 生成胜平负概率
        """
        # 信号差距
        gap = abs(s_home - s_away)
        
        # 温度
        effective_temp = max(0.3, temperature * (1 + entropy * 0.3))
        
        # ===== 平局强度计算 v3 =====
        # 1. 基线：始终存在的平局概率
        base_draw = self.DRAW_BASELINE
        
        # 2. 实力接近加成：gap 越小，平局概率越高
        # 降低阈值：gap < 0.6 就开始有加成
        closeness = max(0, 1 - gap * 1.5)  # 原来 gap*3，现在 gap*1.5，范围翻倍
        close_bonus = closeness * 0.4
        
        # 3. 高熵加成：混乱的比赛更容易平局
        entropy_bonus = entropy * 0.2
        
        # 4. 综合
        draw_strength = (base_draw + close_bonus + entropy_bonus) * draw_boost
        draw_strength = min(0.6, draw_strength)  # 上限 60%
        
        # ===== 构建 logits =====
        sharpness = 2.5
        
        home_logit = s_home * sharpness / effective_temp
        away_logit = s_away * sharpness / effective_temp
        
        # 平局 logit：draw_strength 映射到 logit 空间
        # 使用更大倍数让平局在实力接近时更有竞争力
        draw_logit = (draw_strength - 0.25) * 6.0 / effective_temp
        
        logits = np.array([home_logit, draw_logit, away_logit])
        
        # Softmax
        exp_logits = np.exp(logits - np.max(logits))
        probs = exp_logits / np.sum(exp_logits)
        
        return float(probs[0]), float(probs[1]), float(probs[2])


class PhysicalAI:
    """
    物理AI引擎 - v4.0 核心
    整合四大物理层，输出比赛概率估计
    """
    
    VERSION = "4.0.0"
    
    def __init__(self, weights_path: Optional[str] = None):
        self.mechanics = MechanicsLayer()
        self.field = FieldLayer()
        self.entropy = EntropyLayer()
        self.quantum = QuantumLayer()
        
        # 可学习的层权重 (由 Evolution 引擎更新)
        self.layer_weights = {
            "mechanics": 1.0,
            "field": 0.6,
            "entropy": 0.8,
            "coach": 0.7,
            "market": 0.5
        }
        
        # 平局增强因子
        self.draw_boost = 1.0
        
        # 加载已保存的权重
        if weights_path and Path(weights_path).exists():
            with open(weights_path, 'r') as f:
                saved = json.load(f)
                self.layer_weights.update(saved.get('layer_weights', {}))
                self.draw_boost = saved.get('draw_boost', 1.0)
    
    def predict(
        self,
        home: TeamState,
        away: TeamState,
        market: Optional[MarketState] = None,
        sentiment: float = 0.0,
        money_flow: float = 0.0,
        weather: float = 0.0,
        draw_boost: float = None
    ) -> Dict[str, Any]:
        """
        主预测方法
        
        Returns:
            {
                "probabilities": {"home": p, "draw": p, "away": p},
                "upset": UpsetSignal,
                "goal_explosion": GoalExplosionSignal,
                "signals": {"mechanics": ..., "field": ..., "entropy": ...},
                "confidence": float
            }
        """
        # 使用实例的 draw_boost 或传入的参数
        effective_draw_boost = draw_boost if draw_boost is not None else self.draw_boost
        # === 力学层 ===
        s_home_mech = self.mechanics.compute(home)
        s_away_mech = self.mechanics.compute(away)
        
        # === 场域层 ===
        field_home = self.field.compute(
            sentiment=sentiment,
            money_flow=money_flow,
            home_field=home.home_advantage,
            weather_factor=weather
        )
        field_away = self.field.compute(
            sentiment=-sentiment,
            money_flow=-money_flow,
            home_field=0.0,
            weather_factor=weather
        )
        
        # === 熵层 ===
        home_entropy = self.entropy.compute(home)
        away_entropy = self.entropy.compute(away)
        system_entropy = (home_entropy + away_entropy) / 2
        
        elo_gap = abs(home.elo - away.elo)
        upset_prob = self.entropy.upset_probability(home_entropy, away_entropy, elo_gap)
        
        # === 综合信号 ===
        s_home = (
            s_home_mech * self.layer_weights["mechanics"] +
            field_home * self.layer_weights["field"] +
            (1 - home_entropy) * self.layer_weights["entropy"] * 0.5 +
            home.coach_factor * self.layer_weights["coach"] * 0.5
        )
        
        s_away = (
            s_away_mech * self.layer_weights["mechanics"] +
            field_away * self.layer_weights["field"] +
            (1 - away_entropy) * self.layer_weights["entropy"] * 0.5 +
            away.coach_factor * self.layer_weights["coach"] * 0.5
        )
        
        # 如果有市场概率，做贝叶斯融合
        if market:
            m_home, m_draw, m_away = market.implied_probs()
            # 简单贝叶斯融合: 模型概率 × 市场概率 ^ weight
            w = self.layer_weights["market"]
            s_home = s_home * (1 - w) + (m_home * 2 - 1) * w
            s_away = s_away * (1 - w) + (m_away * 2 - 1) * w
        
        # === 量子坍缩 ===
        home_prob, draw_prob, away_prob = self.quantum.collapse(
            s_home, s_away, system_entropy,
            draw_boost=effective_draw_boost
        )
        
        # === 冷门信号 ===
        upset_signal = UpsetSignal(
            score=upset_prob,
            factors={
                "home_entropy": home_entropy,
                "away_entropy": away_entropy,
                "elo_gap": elo_gap / 400,
                "form_volatility": abs(home.form - away.form)
            }
        )
        
        # === 大比分信号 ===
        combined_attack = (home.attack + away.attack) / 2
        combined_defense = (home.defense + away.defense) / 2
        goal_explosion = GoalExplosionSignal(
            score=(combined_attack * 0.5 + (1 - combined_defense) * 0.5),
            expected_goals=home.xg_for + away.xg_for,
            factors={
                "attack_strength": combined_attack,
                "defense_weakness": 1 - combined_defense,
                "tempo_mismatch": abs(home.attack - away.defense),
                "entropy": system_entropy
            }
        )
        
        # === 置信度 ===
        confidence = 1 - system_entropy * 0.5
        if market:
            # 模型与市场一致度高则置信度提升
            model_best = max([(home_prob, 'home'), (draw_prob, 'draw'), (away_prob, 'away')])
            market_best = max([(m_home, 'home'), (m_draw, 'draw'), (m_away, 'away')])
            if model_best[1] == market_best[1]:
                confidence = min(0.95, confidence + 0.1)
        
        return {
            "probabilities": {
                "home": round(home_prob, 4),
                "draw": round(draw_prob, 4),
                "away": round(away_prob, 4)
            },
            "upset": {
                "score": round(upset_signal.score, 4),
                "is_high_risk": upset_signal.is_high_risk(),
                "factors": upset_signal.factors
            },
            "goal_explosion": {
                "score": round(goal_explosion.score, 4),
                "expected_goals": round(goal_explosion.expected_goals, 2),
                "is_likely": goal_explosion.is_likely(),
                "factors": goal_explosion.factors
            },
            "signals": {
                "mechanics": {"home": round(s_home_mech, 4), "away": round(s_away_mech, 4)},
                "field": {"home": round(field_home, 4), "away": round(field_away, 4)},
                "entropy": {"home": round(home_entropy, 4), "away": round(away_entropy, 4), "system": round(system_entropy, 4)},
                "combined": {"home": round(s_home, 4), "away": round(s_away, 4)}
            },
            "confidence": round(confidence, 4),
            "version": self.VERSION
        }
    
    def save_weights(self, path: str, draw_boost: float = None):
        """保存当前权重"""
        data = {
            "layer_weights": self.layer_weights,
            "draw_boost": draw_boost if draw_boost is not None else self.draw_boost
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)


# ============ 快速测试 ============
if __name__ == "__main__":
    ai = PhysicalAI()
    
    # 模拟一场强弱对话
    home = TeamState(
        attack=0.8, defense=0.3, form=0.85, fatigue=0.1,
        morale=0.9, elo=1850, xg_for=2.2, xg_against=0.8,
        coach_factor=0.3, tournament_gene=0.8
    )
    
    away = TeamState(
        attack=0.4, defense=0.6, form=0.5, fatigue=0.3,
        morale=0.5, elo=1600, xg_for=1.0, xg_against=1.5,
        coach_factor=-0.1, tournament_gene=0.4
    )
    
    market = MarketState(home_odds=1.55, draw_odds=4.2, away_odds=5.8)
    
    result = ai.predict(home, away, market, sentiment=0.2, money_flow=0.3)
    
    print("=== Physical AI v4.0 测试 ===")
    print(f"主胜概率: {result['probabilities']['home']:.1%}")
    print(f"平局概率: {result['probabilities']['draw']:.1%}")
    print(f"客胜概率: {result['probabilities']['away']:.1%}")
    print(f"冷门风险: {result['upset']['score']:.2f} {'⚠️ 高' if result['upset']['is_high_risk'] else ''}")
    print(f"大比分可能: {result['goal_explosion']['score']:.2f} {'🔥 可能' if result['goal_explosion']['is_likely'] else ''}")
    print(f"置信度: {result['confidence']:.1%}")
