#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoachFactor 整合到 UpsetDetector
UpsetDetector v1.1 - 增加教练因子模块

核心升级：
- 原 Upset Score + Coach Risk Index (CRI)
- 教练因子权重：小组赛 15% → 淘汰赛 35%
"""

import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.upset_detector import UpsetDetector, MatchStage
from agents.coach_factor import CoachFactorAnalyzer, CoachProfile, WORLD_CUP_2026_COACHES
from datetime import datetime

class UpsetDetectorWithCoach(UpsetDetector):
    """
    UpsetDetector v1.1 - 教练因子增强版
    
    升级点：
    - 原100分模型 + 教练因子（权重动态15-35%）
    - Coach Risk Index (CRI) 直接加成到冷门评分
    - 大比分预测 + 教练大比分倾向
    """
    
    def __init__(self):
        super().__init__()
        self.coach_analyzer = CoachFactorAnalyzer()
    
    def calculate_upset_score_with_coach(
        self,
        coach_home: CoachProfile,
        coach_away: CoachProfile,
        market_prob: dict,
        model_prob: dict,
        market_odds: dict,
        **kwargs
    ) -> dict:
        """
        计算带教练因子的冷门评分
        """
        # 1. 先计算基础冷门评分
        base_result = self.calculate_upset_score(
            market_prob=market_prob,
            model_prob=model_prob,
            market_odds=market_odds,
            **kwargs
        )
        
        # 2. 计算教练CRI
        stage = kwargs.get('stage', MatchStage.GROUP_RD1)
        match_context = kwargs.get('match_context', {})
        
        home_cri_result = self.coach_analyzer.calculate_cri(coach_home, match_context)
        away_cri_result = self.coach_analyzer.calculate_cri(coach_away, match_context)
        
        # 3. 确定教练因子权重
        # 小组赛：15%，淘汰赛：35%
        if stage in [MatchStage.GROUP_RD1, MatchStage.GROUP_RD2, MatchStage.GROUP_RD3]:
            coach_weight = 0.15
        else:
            coach_weight = 0.35
        
        # 4. 计算教练加成
        # 取两队CRI的平均值作为比赛的整体教练因子
        avg_cri = (home_cri_result['total_cri'] + away_cri_result['total_cri']) / 2
        
        # 冷门放大系数（取两队中较高的）
        upset_amp = max(
            home_cri_result['cbm_outputs']['upset_amplifier'],
            away_cri_result['cbm_outputs']['upset_amplifier']
        )
        
        # 大比分倾向（取两队中较高的）
        big_tendency = max(
            home_cri_result['cbm_outputs']['big_score_tendency'],
            away_cri_result['cbm_outputs']['big_score_tendency']
        )
        
        # 5. 教练加成到冷门评分
        # 原评分 * (1 + 教练因子权重 * (CRI影响))
        base_score = base_result['total_score']
        coach_bonus = avg_cri * upset_amp * 3  # 最大约30分加成
        adjusted_score = min(100, base_score + coach_bonus * coach_weight)
        
        # 6. 重新确定等级
        level = self._determine_level(adjusted_score)
        
        # 7. 更新建议
        recommendation = self._generate_coach_aware_recommendation(
            base_result, adjusted_score, level,
            home_cri_result, away_cri_result,
            coach_weight
        )
        
        return {
            'base_score': round(base_score, 1),
            'coach_adjustment': round(coach_bonus * coach_weight, 1),
            'adjusted_score': round(adjusted_score, 1),
            'level': level.value,
            'level_chinese': self._level_to_chinese(level),
            'coach_weight': f"{coach_weight*100:.0f}%",
            
            'coach_home': {
                'name': coach_home.name,
                'cri': home_cri_result['total_cri'],
                'type': home_cri_result['coach_type_chinese'],
            },
            'coach_away': {
                'name': coach_away.name,
                'cri': away_cri_result['total_cri'],
                'type': away_cri_result['coach_type_chinese'],
            },
            
            'cbm_outputs': {
                'upset_amplifier': round(upset_amp, 2),
                'big_score_tendency': round(big_tendency, 2),
            },
            
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat(),
        }
    
    def _generate_coach_aware_recommendation(
        self, base_result, adjusted_score, level,
        home_cri, away_cri, coach_weight
    ) -> dict:
        """生成教练感知建议"""
        rec = {
            'overall': '',
            'coach_impact': '',
            'betting': '',
        }
        
        # 总体建议
        if adjusted_score >= 80:
            rec['overall'] = 'STRONG_UPSET_CANDIDATE - 教练因子显著放大冷门概率'
        elif adjusted_score >= 60:
            rec['overall'] = 'WATCH_CLOSELY - 教练因子增加了不确定性'
        else:
            rec['overall'] = 'NORMAL - 教练因子未显著改变风险'
        
        # 教练影响说明
        home_type = home_cri['coach_type_chinese']
        away_type = away_cri['coach_type_chinese']
        
        if '高爆炸' in home_type or '高爆炸' in away_type:
            rec['coach_impact'] = (
                f"注意：{home_cri['coach_name']} 或 {away_cri['coach_name']} "
                "是高爆炸教练，冷门和大比分概率被显著放大。"
            )
        elif '稳定' in home_type and '稳定' in away_type:
            rec['coach_impact'] = (
                "双方教练均为稳定型，比赛倾向于低波动、控制型。"
            )
        
        # 投注建议
        if adjusted_score > base_result['total_score']:
            rec['betting'] = (
                f"教练因子使冷门评分从 {base_result['total_score']:.1f} "
                f"提升至 {adjusted_score:.1f}，"
                "考虑增加冷门/大比分防范。"
            )
        
        return rec


def demo_coach_factor():
    """演示教练因子整合"""
    print("=" * 60)
    print("UpsetDetector v1.1 - Coach Factor Integration Demo")
    print("=" * 60)
    print()
    
    detector = UpsetDetectorWithCoach()
    
    # 场景：USA vs Paraguay 小组赛
    print("[Scenario] USA vs Paraguay - Group Stage (Coach Factor Weight: 15%)")
    print("-" * 60)
    
    usa_coach = WORLD_CUP_2026_COACHES['USA']
    par_coach = WORLD_CUP_2026_COACHES['Paraguay']
    
    result = detector.calculate_upset_score_with_coach(
        coach_home=usa_coach,
        coach_away=par_coach,
        market_prob={'home': 0.46, 'draw': 0.293, 'away': 0.247},
        model_prob={'home': 0.55, 'draw': 0.28, 'away': 0.17},
        market_odds={'home': 2.05, 'draw': 3.23, 'away': 3.83},
        betting_flow={'home': 0.779, 'away': 0.094},
        stage=MatchStage.GROUP_RD1,
    )
    
    print(f"  Base Score: {result['base_score']}/100")
    print(f"  Coach Adjustment: +{result['coach_adjustment']}")
    print(f"  Adjusted Score: {result['adjusted_score']}/100")
    print(f"  Coach Weight: {result['coach_weight']}")
    print()
    print(f"  Home Coach: {result['coach_home']['name']} (CRI: {result['coach_home']['cri']})")
    print(f"  Away Coach: {result['coach_away']['name']} (CRI: {result['coach_away']['cri']})")
    print()
    print(f"  Upset Amplifier: {result['cbm_outputs']['upset_amplifier']}")
    print(f"  Big Score Tendency: {result['cbm_outputs']['big_score_tendency']}")
    print()
    print(f"  Recommendation: {result['recommendation']['overall']}")
    print()
    
    # 场景：淘汰赛（权重35%）
    print("[Scenario] Same Match - Knockout Stage (Coach Factor Weight: 35%)")
    print("-" * 60)
    
    result2 = detector.calculate_upset_score_with_coach(
        coach_home=usa_coach,
        coach_away=par_coach,
        market_prob={'home': 0.46, 'draw': 0.293, 'away': 0.247},
        model_prob={'home': 0.55, 'draw': 0.28, 'away': 0.17},
        market_odds={'home': 2.05, 'draw': 3.23, 'away': 3.83},
        betting_flow={'home': 0.779, 'away': 0.094},
        stage=MatchStage.ROUND_16,  # 淘汰赛！
    )
    
    print(f"  Base Score: {result2['base_score']}/100")
    print(f"  Coach Adjustment: +{result2['coach_adjustment']}")
    print(f"  Adjusted Score: {result2['adjusted_score']}/100")
    print(f"  Coach Weight: {result2['coach_weight']}")
    print()
    print(f"  注意：淘汰赛教练权重从15%提升至35%！")
    print()
    
    print("=" * 60)
    print("UpsetDetector v1.1 - Coach Factor Integration Complete")
    print("=" * 60)


if __name__ == "__main__":
    demo_coach_factor()
