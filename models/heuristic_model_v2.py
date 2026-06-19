from typing import Dict, Any, List
import numpy as np
from .base_model import BaseModel


class HeuristicModelV2(BaseModel):
    """
    启发式模型 v2.0 - 注入 Bridgewater 宏观制度
    增强: 赛事阶段制度分类 + 四象限框架 + 动态校准
    
    相比 v5.1:
    - 四象限制度分类: 小组赛/淘汰赛/决赛的系统性差异
    - 制度检测: 自动识别当前赛事所处制度
    - 动态校准: 根据制度切换调整参数
    - 全天候启发: 不同制度下的最优策略配置
    """
    
    def __init__(self):
        self._calibration = {
            'group_adjustment': 0.95,
            'knockout_adjustment': 1.20,
            'group_upset_rate': 0.342,
            'knockout_upset_rate': 0.373,
            'worldcup_2026_format': True,
            'third_place_qualify': True,
        }
        
        # Bridgewater 风格四象限制度
        self.REGIME_FRAMEWORK = {
            'expansion': {  # 小组赛初期 - 进攻活跃
                'stage': ['group_rd1', 'group_rd2'],
                'characteristics': 'high_scoring, upset_prone, aggressive',
                'goal_expectation': 1.4,  # 场均进球高
                'upset_probability': 0.35,
                'draw_probability': 0.25,
                'favoured_style': 'offensive',
                'calibration': {
                    'group_stage_conservative': 0.98,
                    'first_round_boost': 0.10,
                    'home_favorite_penalty': 0.10,
                    'draw_boost': 0.05,
                    'underdog_boost': 0.15,
                }
            },
            'contraction': {  # 小组赛末轮 - 保守计算
                'stage': ['group_rd3'],
                'characteristics': 'strategic, calculated, conservative',
                'goal_expectation': 1.0,
                'upset_probability': 0.25,
                'draw_probability': 0.30,
                'favoured_style': 'defensive',
                'calibration': {
                    'group_stage_conservative': 0.85,
                    'first_round_boost': 0.0,
                    'home_favorite_penalty': 0.05,
                    'draw_boost': 0.08,
                    'underdog_boost': 0.05,
                }
            },
            'tightening': {  # 淘汰赛 - 极端保守
                'stage': ['round_16', 'quarter'],
                'characteristics': 'ultra_defensive, low_scoring, penalty_prone',
                'goal_expectation': 0.8,
                'upset_probability': 0.15,
                'draw_probability': 0.35,
                'favoured_style': 'ultra_defensive',
                'calibration': {
                    'group_stage_conservative': 0.75,
                    'first_round_boost': 0.0,
                    'home_favorite_penalty': 0.05,
                    'draw_boost': 0.10,
                    'underdog_boost': 0.05,
                }
            },
            'depression': {  # 决赛 - 保守到极致
                'stage': ['semi', 'final'],
                'characteristics': 'extreme_caution, set_piece_focused, error_avoidance',
                'goal_expectation': 0.6,
                'upset_probability': 0.08,
                'draw_probability': 0.40,
                'favoured_style': 'extreme_caution',
                'calibration': {
                    'group_stage_conservative': 0.70,
                    'first_round_boost': 0.0,
                    'home_favorite_penalty': 0.0,
                    'draw_boost': 0.12,
                    'underdog_boost': 0.0,
                }
            }
        }
    
    @property
    def name(self) -> str:
        return "HeuristicModelV2"
    
    @property
    def version(self) -> str:
        return "2.0"
    
    @property
    def supported_markets(self) -> List[str]:
        return ['1x2', 'over_under', 'upset_score']
    
    def detect_regime(self, stage: str) -> Dict[str, Any]:
        """检测当前赛事制度"""
        for regime_name, regime_info in self.REGIME_FRAMEWORK.items():
            if stage in regime_info['stage']:
                return {
                    'regime': regime_name,
                    'characteristics': regime_info['characteristics'],
                    'goal_expectation': regime_info['goal_expectation'],
                    'upset_probability': regime_info['upset_probability'],
                    'draw_probability': regime_info['draw_probability'],
                    'favoured_style': regime_info['favoured_style'],
                    'calibration': regime_info['calibration']
                }
        
        # 默认返回扩张制度
        return self.detect_regime('group_rd1')
    
    def predict(self, match_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行启发式预测"""
        stage = match_info.get('stage', 'group_rd1')
        regime = self.detect_regime(stage)
        
        result = {
            'model_name': self.name,
            'version': self.version,
            'markets': {},
            'confidence': 0.65,
            'metadata': {
                'regime': regime,
                'stage': stage
            }
        }
        
        # 1X2 预测
        if '1x2' in self.supported_markets:
            result['markets']['1x2'] = self._predict_1x2(match_info, regime)
        
        # 大小球预测
        if 'over_under' in self.supported_markets:
            result['markets']['over_under'] = self._predict_over_under(match_info, regime)
        
        # 冷门评分
        if 'upset_score' in self.supported_markets:
            result['markets']['upset_score'] = self._calculate_upset_score(match_info, regime)
        
        return result
    
    def _predict_1x2(self, match_info: Dict, regime: Dict) -> Dict[str, Any]:
        """基于制度的 1X2 预测"""
        home = match_info.get('home', '')
        away = match_info.get('away', '')
        
        # 基础概率 (均匀分布)
        prob_home = 0.33
        prob_draw = 0.33
        prob_away = 0.34
        
        # 制度调整
        draw_boost = regime['calibration']['draw_boost']
        prob_draw += draw_boost
        prob_home -= draw_boost / 2
        prob_away -= draw_boost / 2
        
        # 热门惩罚
        home_odds = match_info.get('odds_home', 2.0)
        if home_odds < 1.5:
            penalty = regime['calibration']['home_favorite_penalty']
            prob_home -= penalty
            prob_away += penalty
        
        # 冷门提升
        away_odds = match_info.get('odds_away', 2.0)
        if away_odds > 5.0:
            boost = regime['calibration']['underdog_boost']
            prob_away += boost
            prob_home -= boost
        
        # 归一化
        total = prob_home + prob_draw + prob_away
        return {
            'probabilities': {
                'home': round(prob_home / total, 3),
                'draw': round(prob_draw / total, 3),
                'away': round(prob_away / total, 3)
            },
            'regime_adjusted': True
        }
    
    def _predict_over_under(self, match_info: Dict, regime: Dict) -> Dict[str, Any]:
        """基于制度的大小球预测"""
        goal_expectation = regime['goal_expectation']
        
        # 球队进攻调整
        home_offense = 0.0
        away_offense = 0.0
        
        if self._is_african_team(match_info.get('home', '')):
            home_offense = 0.12
        elif self._is_asian_team(match_info.get('home', '')):
            home_offense = 0.15
        
        adjusted_lambda = goal_expectation + home_offense + away_offense
        
        return {
            'lambda': round(adjusted_lambda, 2),
            'goal_expectation': goal_expectation,
            'regime': regime['regime']
        }
    
    def _calculate_upset_score(self, match_info: Dict, regime: Dict) -> Dict[str, Any]:
        """基于制度的冷门评分"""
        base_score = 30.0
        
        # 制度调整
        if regime['regime'] == 'expansion':
            base_score += 15  # 小组赛更容易爆冷
        elif regime['regime'] == 'depression':
            base_score -= 10  # 决赛不易爆冷
        
        # 赔率调整
        odds_away = match_info.get('odds_away', 3.0)
        if odds_away > 5.0:
            base_score += 10
        elif odds_away > 3.0:
            base_score += 5
        
        return {
            'score': min(base_score, 100),
            'regime': regime['regime'],
            'upset_probability': regime['upset_probability']
        }
    
    @staticmethod
    def _is_african_team(team: str) -> bool:
        return any(t.lower() in team.lower() for t in ['Morocco', 'Senegal', 'Cameroon', 'Ghana', 'Nigeria', 'Egypt', 'Ivory Coast'])
    
    @staticmethod
    def _is_asian_team(team: str) -> bool:
        return any(t.lower() in team.lower() for t in ['Japan', 'Korea', 'Iran', 'Saudi', 'Australia', 'Qatar', 'Uzbekistan', 'Jordan'])
    
    def get_regime_transition_guide(self) -> Dict[str, Any]:
        """获取制度切换指南"""
        return {
            'transitions': [
                {'from': 'expansion', 'to': 'contraction', 'trigger': '小组赛末轮', 'adjustment': '降低进球预期 15%'},
                {'from': 'contraction', 'to': 'tightening', 'trigger': '进入淘汰赛', 'adjustment': '降低进球预期 20%, 提升平局概率'},
                {'from': 'tightening', 'to': 'depression', 'trigger': '半决赛/决赛', 'adjustment': '极端保守, 关注点球'}
            ],
            'recommendation': '根据制度切换动态调整策略参数'
        }
    
    def calibrate(self, stage: str = 'group', upset_rate: float = None, **kwargs) -> Dict[str, Any]:
        """校准模型参数 - 实现抽象方法"""
        if upset_rate is not None:
            self._calibration['group_upset_rate'] = upset_rate
        
        regime = self.detect_regime(stage)
        return {
            'status': 'calibrated',
            'stage': stage,
            'regime': regime['regime'],
            'calibration': self._calibration
        }
