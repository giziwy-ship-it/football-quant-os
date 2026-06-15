#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoachFactor - 教练因子模块 v1.0
基于用户研究框架：教练是冷门发动机 + 大比分放大器

核心洞察：
- "70%的冷门不是数据错，而是教练决策放大了随机性"
- 教练因子在世界杯/欧洲杯/淘汰赛权重：15% → 35%

Coach Impact Score (CIS) 6维度：
1. 战术稳定性 (25%) - 阵型变化频率
2. 临场决策风险 (20%) - 换人/策略调整
3. 大赛经验 (10%) - 世界杯/欧洲杯履历
4. 心理控制能力 (15%) - 情绪化/崩盘倾向
5. 轮换策略 (20%) - 小组赛轮换概率
6. 对强队/弱队策略差异 (10%) - 极端策略

Coach Risk Index (CRI) = 加权6维度
Coach Behavior Model (CBM) 输出：
- 冷门放大系数 (Upset Amplifier)
- 大比分倾向 (Big Score Tendency)
- 保守指数 (Conservative Index)
- 赌性指数 (Gambler Index)
"""

import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math

from agents.coach_types import CoachProfile, CoachType, TacticalStyle


class CoachFactorAnalyzer:
    """
    教练因子分析器
    
    角色：教练行为解码器 + 冷门放大器探测器
    
    核心问题：这个教练是"稳定器"还是"波动放大器"？
    """
    """
    教练因子分析器
    
    角色：教练行为解码器 + 冷门放大器探测器
    
    核心问题：这个教练是"稳定器"还是"波动放大器"？
    """
    
    # CRI 权重配置
    CRI_WEIGHTS = {
        'tactical_stability': 0.25,      # 战术不稳定性
        'in_game_volatility': 0.20,       # 临场波动
        'rotation_policy': 0.20,          # 轮换概率
        'emotional_control': 0.15,        # 情绪控制弱点
        'tournament_experience': 0.10,    # 大赛经验不足
        'strategy_extremity': 0.10,       # 战术极端性
    }
    
    # 教练类型阈值
    COACH_TYPE_THRESHOLDS = {
        'stable': 3.0,      # CRI < 3.0
        'moderate': 5.5,    # 3.0 <= CRI < 5.5
        'volatile': 10.0,   # CRI >= 5.5
    }
    
    def __init__(self):
        self.coach_database: Dict[str, CoachProfile] = {}
        self.analysis_history: List[Dict] = []
    
    def calculate_cri(self, coach: CoachProfile, match_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        计算 Coach Risk Index (CRI)
        
        CRI 越高 = 教练越容易产生冷门/大比分
        """
        # 1. 战术不稳定性 (25%)
        tactical_stability = coach.get_tactical_stability_score()
        tactical_instability = 10 - tactical_stability  # 翻转：不稳定 = 高风险
        tactical_risk = tactical_instability * self.CRI_WEIGHTS['tactical_stability']
        
        # 2. 临场决策风险 (20%)
        in_game_volatility = self._calculate_in_game_volatility(coach)
        in_game_risk = in_game_volatility * self.CRI_WEIGHTS['in_game_volatility']
        
        # 3. 轮换策略 (20%)
        rotation_risk = self._calculate_rotation_risk(coach, match_context)
        rotation_risk = rotation_risk * self.CRI_WEIGHTS['rotation_policy']
        
        # 4. 心理控制弱点 (15%)
        emotional_risk = self._calculate_emotional_risk(coach)
        emotional_risk = emotional_risk * self.CRI_WEIGHTS['emotional_control']
        
        # 5. 大赛经验不足 (10%)
        experience_risk = self._calculate_experience_risk(coach)
        experience_risk = experience_risk * self.CRI_WEIGHTS['tournament_experience']
        
        # 6. 战术极端性 (10%)
        extremity_risk = coach.strategy_extremity * self.CRI_WEIGHTS['strategy_extremity']
        
        # 总 CRI
        total_cri = (tactical_risk + in_game_risk + rotation_risk + 
                     emotional_risk + experience_risk + extremity_risk)
        
        # 归一化到 0-10
        normalized_cri = min(10, total_cri)
        
        # 教练类型判断
        coach_type = self._classify_coach_type(normalized_cri)
        
        # 冷门放大系数
        upset_amplifier = self._calculate_upset_amplifier(normalized_cri, coach_type)
        
        # 大比分倾向
        big_score_tendency = self._calculate_big_score_tendency(coach, normalized_cri)
        
        # 保守指数
        conservative_index = self._calculate_conservative_index(coach, normalized_cri)
        
        # 赌性指数
        gambler_index = self._calculate_gambler_index(coach, normalized_cri)
        
        return {
            'coach_name': coach.name,
            'coach_nationality': coach.nationality,
            'total_cri': round(normalized_cri, 2),
            'coach_type': coach_type.value,
            'coach_type_chinese': self._coach_type_to_chinese(coach_type),
            
            # 6维度分解
            'factor_breakdown': {
                'tactical_instability': round(tactical_risk, 2),
                'in_game_volatility': round(in_game_risk, 2),
                'rotation_risk': round(rotation_risk, 2),
                'emotional_risk': round(emotional_risk, 2),
                'experience_risk': round(experience_risk, 2),
                'extremity_risk': round(extremity_risk, 2),
            },
            
            # CBM 输出
            'cbm_outputs': {
                'upset_amplifier': round(upset_amplifier, 2),      # 冷门放大系数
                'big_score_tendency': round(big_score_tendency, 2), # 大比分倾向
                'conservative_index': round(conservative_index, 2),  # 保守指数
                'gambler_index': round(gambler_index, 2),         # 赌性指数
            },
            
            'interpretation': self._generate_interpretation(coach, normalized_cri, coach_type),
            'timestamp': datetime.now().isoformat(),
        }
    
    def _calculate_in_game_volatility(self, coach: CoachProfile) -> float:
        """计算临场决策风险 0-10"""
        score = 5.0  # 基准
        
        # 换人激进程度
        if coach.avg_substitutions_per_match > 4.5:
            score += 2.0
        elif coach.avg_substitutions_per_match > 3.5:
            score += 1.0
        
        # 早换人比例
        score += coach.early_substitution_rate * 2
        
        # 进攻型换人
        score += coach.aggressive_substitution_rate * 1.5
        
        #  comeback rate（高逆转率 = 敢于冒险）
        score += coach.comeback_rate * 2
        
        return min(10, score)
    
    def _calculate_rotation_risk(self, coach: CoachProfile, 
                                match_context: Dict[str, Any] = None) -> float:
        """计算轮换风险 0-10"""
        if match_context is None:
            match_context = {}
        
        score = coach.rotation_tendency  # 基础轮换倾向
        
        # 小组赛第三轮已出线情况（最大冷门来源）
        stage = match_context.get('stage', 'group')
        position = match_context.get('group_position', 0)
        points = match_context.get('points', 0)
        
        if stage == 'group_round_3' and points >= 4:  # 已大概率出线
            score += 3.0  # 轮换概率大增
        
        # 世界杯淘汰赛经验不足的教练更爱轮换
        if coach.world_cup_experience == 0:
            score += 1.0
        
        return min(10, score)
    
    def _calculate_emotional_risk(self, coach: CoachProfile) -> float:
        """计算心理控制风险 0-10"""
        # 情绪稳定性越低 = 风险越高
        stability_risk = 10 - coach.emotional_stability
        
        # 媒体影响
        media_risk = coach.media_influence_susceptibility * 0.5
        
        # 崩盘事件
        meltdown_risk = coach.team_meltdown_incidents * 1.5
        
        return min(10, stability_risk + media_risk + meltdown_risk)
    
    def _calculate_experience_risk(self, coach: CoachProfile) -> float:
        """计算大赛经验不足风险 0-10"""
        tournament_iq = coach.get_tournament_iq()
        
        # 经验越不足 = 风险越高
        experience_risk = 10 - tournament_iq
        
        return max(0, experience_risk)
    
    def _classify_coach_type(self, cri: float) -> CoachType:
        """根据CRI分类教练类型"""
        if cri < self.COACH_TYPE_THRESHOLDS['stable']:
            return CoachType.STABLE
        elif cri < self.COACH_TYPE_THRESHOLDS['moderate']:
            return CoachType.MODERATE
        else:
            return CoachType.VOLATILE
    
    def _coach_type_to_chinese(self, coach_type: CoachType) -> str:
        """教练类型中文"""
        mapping = {
            CoachType.STABLE: '稳定型（低冷门）',
            CoachType.MODERATE: '中风险型（中冷门）',
            CoachType.VOLATILE: '高爆炸型（冷门发动机）',
            CoachType.UNKNOWN: '未知',
        }
        return mapping.get(coach_type, '未知')
    
    def _calculate_upset_amplifier(self, cri: float, coach_type: CoachType) -> float:
        """
        冷门放大系数
        
        范围：0.5 - 2.0
        - 稳定型教练 = 0.5-0.8（抑制冷门）
        - 中风险教练 = 0.8-1.2（正常波动）
        - 高爆炸教练 = 1.2-2.0（放大冷门）
        """
        base = 0.5 + cri * 0.15  # 0.5 + 10*0.15 = 2.0
        
        # 类型修正
        adjustment = {
            CoachType.STABLE: 0.8,
            CoachType.MODERATE: 1.0,
            CoachType.VOLATILE: 1.2,
        }.get(coach_type, 1.0)
        
        return base * adjustment
    
    def _calculate_big_score_tendency(self, coach: CoachProfile, cri: float) -> float:
        """
        大比分倾向
        
        范围：0-10
        高压/极端战术 = 高倾向
        """
        score = 5.0
        
        # 战术风格影响
        style_effect = {
            TacticalStyle.CONTROL: -2,
            TacticalStyle.PRESS: 1,
            TacticalStyle.COUNTER: -1,
            TacticalStyle.EXTREME: 3,
            TacticalStyle.EXPERIMENTAL: 2,
        }.get(coach.tactical_style, 0)
        score += style_effect
        
        # 高CRI = 高波动 = 高比分
        score += cri * 0.3
        
        # 进攻数据
        if coach.avg_goals_per_match > 2.0:
            score += 1.0
        if coach.avg_conceded_per_match > 1.5:
            score += 1.0
        
        return min(10, max(0, score))
    
    def _calculate_conservative_index(self, coach: CoachProfile, cri: float) -> float:
        """
        保守指数
        
        范围：0-10
        越高 = 越保守（不容易出冷门）
        """
        score = 10 - cri  # 与CRI反向
        
        # 战术风格修正
        style_effect = {
            TacticalStyle.CONTROL: 2,
            TacticalStyle.PRESS: 0,
            TacticalStyle.COUNTER: 1,
            TacticalStyle.EXTREME: -3,
            TacticalStyle.EXPERIMENTAL: -2,
        }.get(coach.tactical_style, 0)
        score += style_effect
        
        # 打强队策略
        if coach.vs_strong_team_strategy == 'defensive':
            score += 1
        elif coach.vs_strong_team_strategy == 'aggressive':
            score -= 1
        
        return min(10, max(0, score))
    
    def _calculate_gambler_index(self, coach: CoachProfile, cri: float) -> float:
        """
        赌性指数
        
        范围：0-10
        越高 = 教练越容易做出"赌博式"决策
        """
        score = cri * 0.7  # 基础来自CRI
        
        # 极端战术
        if coach.tactical_style in [TacticalStyle.EXTREME, TacticalStyle.EXPERIMENTAL]:
            score += 2
        
        # 高换人
        if coach.avg_substitutions_per_match > 4.5:
            score += 1
        
        # 低情绪稳定性
        score += (10 - coach.emotional_stability) * 0.3
        
        return min(10, score)
    
    def _generate_interpretation(self, coach: CoachProfile, cri: float, 
                                  coach_type: CoachType) -> str:
        """生成解读文本"""
        interpretations = {
            CoachType.STABLE: (
                f"{coach.name}是稳定型教练（CRI={cri:.1f}），"
                "战术体系成熟，临场决策保守，"
                "冷门概率低，比赛倾向于「控制型」低比分。"
            ),
            CoachType.MODERATE: (
                f"{coach.name}是中风险教练（CRI={cri:.1f}），"
                "高压逼抢风格带来中等波动，"
                "可能产生大比分，但冷门概率适中。"
            ),
            CoachType.VOLATILE: (
                f"{coach.name}是高爆炸教练（CRI={cri:.1f}）！"
                "战术不稳定/临场激进/轮换大胆，"
                "是冷门发动机和大比分放大器。"
                "建议：关注冷门信号 + 大比分盘口。"
            ),
        }
        return interpretations.get(coach_type, "教练类型未知，数据不足。")
    
    def get_coach_type_risk_profile(self, coach_type: CoachType) -> Dict[str, Any]:
        """获取教练类型的风险画像"""
        profiles = {
            CoachType.STABLE: {
                'name': '稳定型',
                'emoji': '[STABLE]',
                'description': '瓜迪奥拉系/德尚系/西蒙尼系',
                'characteristics': [
                    '控制节奏',
                    '数据依赖',
                    '极低随机性',
                ],
                'upset_probability': '10-15%',
                'big_score_probability': '15-25%',
                'typical_scores': '1-0, 2-0, 1-1',
                'betting_strategy': '适合小比分/平局',
            },
            CoachType.MODERATE: {
                'name': '中风险型',
                'emoji': '[MODERATE]',
                'description': '克洛普系/斯卡洛尼系',
                'characteristics': [
                    '高压逼抢',
                    '情绪驱动',
                    '比赛开放',
                ],
                'upset_probability': '15-25%',
                'big_score_probability': '25-40%',
                'typical_scores': '2-1, 3-2, 2-2',
                'betting_strategy': '适合大比分/双方进球',
            },
            CoachType.VOLATILE: {
                'name': '高爆炸型',
                'emoji': '[VOLATILE]',
                'description': '新帅/实验型/极端战术派',
                'characteristics': [
                    '战术未稳定',
                    '临场赌性强',
                    '轮换大胆',
                ],
                'upset_probability': '25-40%',
                'big_score_probability': '35-55%',
                'typical_scores': '0-1, 1-2, 3-2, 4-1',
                'betting_strategy': '冷门候选 + 大比分',
            },
        }
        return profiles.get(coach_type, {})


if __name__ == "__main__":
    import sys
    sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')
    from agents.worldcup_2026_full_coaches import WORLD_CUP_2026_FULL_COACHES as WORLD_CUP_2026_COACHES
    
    print("=" * 60)
    print("CoachFactor v1.0 - 教练因子分析器")
    print("=" * 60)
    print()
    
    analyzer = CoachFactorAnalyzer()
    
    # 测试所有教练
    print("[All 48 Teams CRI Analysis]")
    print("-" * 60)
    
    results = []
    for team, coach in WORLD_CUP_2026_COACHES.items():
        result = analyzer.calculate_cri(coach)
        results.append((team, result['total_cri'], result['coach_name'], result['coach_type_chinese']))
    
    results.sort(key=lambda x: x[1], reverse=True)
    
    print("Top 10 HIGHEST CRI (Most Volatile):")
    for i, (team, cri, name, ctype) in enumerate(results[:10], 1):
        marker = '!!!' if cri > 6.0 else '!' if cri > 5.0 else ''
        print(f"  {i:2}. {team:20} {cri:5.2f} {marker}")
    
    print()
    print("Top 10 LOWEST CRI (Most Stable):")
    for i, (team, cri, name, ctype) in enumerate(results[-10:], 1):
        print(f"  {i:2}. {team:20} {cri:5.2f}")
    
    print()
    print(f"Total: {len(results)} teams")
    print(f"CRI range: {min(r[1] for r in results):.2f} - {max(r[1] for r in results):.2f}")
    print()
    print("VOLATILE (>5.5):", sum(1 for r in results if r[1] > 5.5))
    print("MODERATE (3.5-5.5):", sum(1 for r in results if 3.5 <= r[1] <= 5.5))
    print("STABLE (<3.5):", sum(1 for r in results if r[1] < 3.5))
    
    print()
    print("=" * 60)
    print("CoachFactor v1.0 - 48 Teams Complete")
    print("=" * 60)
