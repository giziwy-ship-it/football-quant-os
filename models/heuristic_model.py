from typing import Dict, Any, List
from .base_model import BaseModel


class HeuristicModel(BaseModel):
    """
    启发式模型 (Heuristic Model) - v4.3.6 规则驱动实现
    
    基于历史数据校准系数和规则调整的预测模型。
    这是当前 Football Quant OS 的基准模型。
    """
    
    def __init__(self):
        self._calibration = {
            'group_adjustment': 0.95,
            'knockout_adjustment': 1.20,
            'group_upset_rate': 0.342,
            'knockout_upset_rate': 0.373,
            # 2026赛制新增：12组→32强，第3名可出线
            'worldcup_2026_format': True,
            'third_place_qualify': True,  # 第3名可出线
            # 2026-06-15训练后参数：基于12场世界杯结果（最佳参数）
            'group_stage_conservative': 0.98,  # 训练后：0.92→0.98（首轮进球多）
            'first_round_boost': 0.10,         # 训练后新增：首轮+10%
            'home_favorite_penalty': 0.10,     # 最佳：0.10（热门降权）
            'away_favorite_penalty': 0.10,   # 最佳：0.10
            'draw_boost': 0.05,              # 最佳：0.05（平局提升）
            'upset_threshold': 15,            # 最佳：15
            'africa_offense_boost': 0.12,    # 最佳：0.12
            'asia_offense_boost': 0.15,       # 最佳：0.15
            'concacaf_offense_boost': 0.15,   # 最佳：0.15
            'europe_defense_penalty': 0.08,   # 最佳：0.08
        }
    
    @property
    def name(self) -> str:
        return "HeuristicModel"
    
    @property
    def version(self) -> str:
        return "5.2.0-P1"
    
    @property
    def supported_markets(self) -> List[str]:
        return ['1x2', 'over_under', 'upset_score']
    
    def _is_african_team(self, team_name: str) -> bool:
        """判断是否为非洲球队"""
        african_teams = ['Morocco', 'Tunisia', 'Senegal', 'Cameroon', 'Ghana', 'Nigeria', 'Egypt', 'Algeria', 'Ivory Coast', 'Cape Verde']
        return any(t.lower() in team_name.lower() for t in african_teams)
    
    def _is_asian_team(self, team_name: str) -> bool:
        """判断是否为亚洲球队"""
        asian_teams = ['Japan', 'South Korea', 'Korea', 'Iran', 'Saudi Arabia', 'Australia', 'Qatar', 'Uzbekistan', 'Jordan']
        return any(t.lower() in team_name.lower() for t in asian_teams)
    
    def _is_concacaf_team(self, team_name: str) -> bool:
        """判断是否为北美/中美球队"""
        concacaf_teams = ['United States', 'USA', 'Mexico', 'Canada', 'Costa Rica', 'Honduras', 'Jamaica', 'Panama', 'Haiti', 'Curacao']
        return any(t.lower() in team_name.lower() for t in concacaf_teams)
    
    def _is_european_team(self, team_name: str) -> bool:
        """判断是否为欧洲球队"""
        european_teams = ['Germany', 'France', 'Spain', 'England', 'Italy', 'Netherlands', 'Portugal', 'Belgium', 'Croatia', 'Switzerland', 'Denmark', 'Sweden', 'Poland', 'Czechia', 'Czech', 'Norway', 'Scotland', 'Wales', 'Serbia', 'Turkey', 'Greece', 'Slovenia', 'Slovakia', 'Romania', 'Bosnia', 'Finland', 'Ukraine', 'Russia']
        return any(t.lower() in team_name.lower() for t in european_teams)

    def predict(self, match_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行启发式预测"""
        # 输入校验
        valid, error = self.validate_inputs(match_info)
        if not valid:
            return {'error': error}
        
        stage = match_info.get('stage', 'group')
        
        result = {
            'model_name': self.name,
            'version': self.version,
            'markets': {},
            'confidence': 0.65,  # 启发式模型置信度较低
            'metadata': {
                'calibration': self._calibration,
                'stage': stage
            }
        }
        
        # 1X2 预测
        if '1x2' in self.supported_markets:
            result['markets']['1x2'] = self._predict_1x2(match_info, stage)
        
        # 大小球预测 (简化版)
        if 'over_under' in self.supported_markets:
            result['markets']['over_under'] = self._predict_over_under(match_info, stage)
        
        # 冷门评分
        if 'upset_score' in self.supported_markets:
            result['markets']['upset_score'] = self._calculate_upset_score(match_info, stage)
        
        return result
    
    def _predict_1x2(self, match_info: Dict[str, Any], stage: str) -> Dict[str, Any]:
        """1X2 预测 (2026赛制适配版 + 训练后参数)"""
        h, d, a = match_info['odds_home'], match_info['odds_draw'], match_info['odds_away']
        total = 1/h + 1/d + 1/a
        mkt_home = (1/h) / total
        mkt_draw = (1/d) / total
        mkt_away = (1/a) / total
        
        margin = total - 1
        imp_home = mkt_home / total * (1 - margin)
        imp_draw = mkt_draw / total * (1 - margin)
        imp_away = mkt_away / total * (1 - margin)
        
        # 2026赛制：小组赛第3名可出线 → 更保守，平局概率上升
        if stage == 'group':
            adjustment = self._calibration.get('group_stage_conservative', 0.98)
            # 训练后：首轮进球多，保守系数0.92→0.98
            mod_home = imp_home * adjustment + 0.03
            # 平局概率增加（保守战术）
            draw_boost = self._calibration.get('draw_boost', 0.02)  # 训练后+2%
            
            # 训练后：热门球队降权（市场过度追捧）
            if imp_home > 0.55:  # 热门主胜
                mod_home -= self._calibration.get('home_favorite_penalty', 0.10)
            if imp_away > 0.55:  # 热门客胜
                mod_home += self._calibration.get('away_favorite_penalty', 0.10)
            
            # 第2轮修正：强热门额外惩罚（赔率<1.5）
            if match_info['odds_home'] < 1.5:
                mod_home -= 0.05  # 强热门额外-5%
            if match_info['odds_away'] < 1.5:
                mod_home += 0.05  # 强热门客胜额外-5%
            
            # 第3轮修正：热门vs非热门差距大时，平局概率额外增加
            if abs(imp_home - imp_away) > 0.20:  # 概率差>20%
                draw_boost += 0.03  # 额外+3%平局
            
            # 第4轮修正：如果主胜概率在45%-55%之间，增加平局概率（模糊地带）
            if 0.45 < imp_home < 0.55:
                draw_boost += 0.02  # 模糊地带+2%平局
                
            # 训练后：区域调整（非洲/亚洲/北美进攻超预期）
            home_team = match_info.get('home_team', '')
            away_team = match_info.get('away_team', '')
            if self._is_african_team(home_team):
                mod_home += self._calibration.get('africa_offense_boost', 0.08)
            if self._is_asian_team(home_team):
                mod_home += self._calibration.get('asia_offense_boost', 0.10)
            if self._is_concacaf_team(home_team):
                mod_home += self._calibration.get('concacaf_offense_boost', 0.12)
            if self._is_european_team(away_team):
                mod_home += self._calibration.get('europe_defense_penalty', 0.05)  # 欧洲防守被高估
                
        elif stage == 'knockout':
            adjustment = self._calibration['knockout_adjustment']
            mod_home = imp_home * adjustment + 0.02
            draw_boost = 0.0
        else:
            mod_home = imp_home * 0.95 + 0.025
            draw_boost = 0.0
        
        mod_home = max(0.05, min(0.95, mod_home))
        mod_away = max(0.05, min(0.95, 1 - mod_home - imp_draw - draw_boost))
        mod_draw = 1 - mod_home - mod_away
        mod_draw = max(0.05, min(0.90, mod_draw))
        
        edge_home = mod_home - imp_home
        edge_draw = mod_draw - imp_draw
        edge_away = mod_away - imp_away
        
        recommendations = []
        if edge_home > 0.02:
            recommendations.append(f"主胜 ({edge_home:+.1%})")
        if edge_draw > 0.02:
            recommendations.append(f"平局 ({edge_draw:+.1%})")
        if edge_away > 0.02:
            recommendations.append(f"客胜 ({edge_away:+.1%})")
        
        return {
            'market': '1X2',
            'implied': {'home': round(imp_home, 3), 'draw': round(imp_draw, 3), 'away': round(imp_away, 3)},
            'model': {'home': round(mod_home, 3), 'draw': round(mod_draw, 3), 'away': round(mod_away, 3)},
            'edge': {'home': round(edge_home, 3), 'draw': round(edge_draw, 3), 'away': round(edge_away, 3)},
            'recommendations': recommendations,
            'format_2026': True,
            'trained_params': 'v5.1.1-20260615'  # 标记已训练
        }
    
    def _predict_over_under(self, match_info: Dict[str, Any], stage: str) -> Dict[str, Any]:
        """大小球预测 (2026赛制适配版 + 训练后参数)"""
        if stage == 'knockout':
            model_prob = 0.42
        elif stage == 'final':
            model_prob = 0.40
        elif stage == 'group':
            # 训练后：小组赛保守系数0.92→0.98，但首轮进球多
            model_prob = 0.50  # 训练后：0.45→0.50（首轮进球超预期）
            
            # 训练后：首轮额外加成
            round_num = match_info.get('round', 1)
            if round_num == 1:
                model_prob += self._calibration.get('first_round_boost', 0.10)  # 首轮+10%
        else:
            model_prob = 0.48
        
        # 训练后：强弱悬殊比赛进球数上调
        home_team = match_info.get('home_team', '')
        away_team = match_info.get('away_team', '')
        home_odds = match_info.get('odds_home', 2.0)
        away_odds = match_info.get('odds_away', 2.0)
        
        if home_odds < 1.15 and away_odds > 5.0:  # 强弱悬殊
            model_prob += 0.15  # 训练后：大球+15%
        
        model_prob = max(0.35, min(0.65, model_prob))  # 限制在合理范围
        
        return {
            'market': 'Over/Under',
            'line': 2.5,
            'over_prob': round(model_prob, 3),
            'under_prob': round(1 - model_prob, 3),
            'recommendation': 'No Edge',
            'edge': 0.0,
            'format_2026': True,
            'trained_params': 'v5.1.1-20260615'
        }
    
    def _calculate_upset_score(self, match_info: Dict[str, Any], stage: str) -> int:
        """冷门评分计算 (UpsetDetector v2.0 训练后参数)"""
        h, d, a = match_info['odds_home'], match_info['odds_draw'], match_info['odds_away']
        total = 1/h + 1/d + 1/a
        mkt_home = (1/h) / total
        
        # UpsetDetector v2.0: 阈值45/65/80（更敏感）
        upset_threshold = self._calibration.get('upset_threshold', 15)
        
        historical_upset_rate = self._calibration.get(f'{stage}_upset_rate', 0.342)
        base_upset = 15
        if mkt_home > 0.70:
            base_upset = 38
        elif mkt_home < 0.35:
            base_upset = 32
        
        # UpsetDetector v2.0: 区域冷门因子（基于12场训练结果）
        home_team = match_info.get('home_team', '')
        away_team = match_info.get('away_team', '')
        home_region = match_info.get('home_region', '')
        away_region = match_info.get('away_region', '')
        
        # 区域冷门加成（训练后）
        region_boost = {
            'africa': 0.15, 'asia': 0.10, 'concacaf': 0.12, 
            'south_america': 0.05, 'europe': 0.0
        }
        
        for region in [home_region, away_region]:
            if region in region_boost:
                base_upset += int(region_boost[region] * 100)
        
        # 传统检测（向后兼容）
        if self._is_african_team(home_team) or self._is_african_team(away_team):
            base_upset += 5
        if self._is_asian_team(home_team) or self._is_asian_team(away_team):
            base_upset += 3
        if self._is_concacaf_team(home_team) or self._is_concacaf_team(away_team):
            base_upset += 4
        
        # 小组赛首轮冷门率35%（训练后）
        if stage == 'group' and match_info.get('round', 1) == 1:
            base_upset += 10  # 首轮+10分
        
        upset_score = int(base_upset * (0.9 + (historical_upset_rate - 0.30) * 2))
        return min(upset_score, 65)
    
    def calibrate(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """使用历史数据校准模型"""
        if not historical_data:
            return {
                'calibration_success': False,
                'metrics': {},
                'parameters': self._calibration
            }
        
        # 简化版校准：统计历史爆冷率
        group_matches = [m for m in historical_data if m.get('stage') == 'group']
        knockout_matches = [m for m in historical_data if m.get('stage') == 'knockout']
        
        group_upset_rate = sum(1 for m in group_matches if m.get('is_upset')) / len(group_matches) if group_matches else 0.342
        knockout_upset_rate = sum(1 for m in knockout_matches if m.get('is_upset')) / len(knockout_matches) if knockout_matches else 0.373
        
        self._calibration['group_upset_rate'] = round(group_upset_rate, 3)
        self._calibration['knockout_upset_rate'] = round(knockout_upset_rate, 3)
        
        return {
            'calibration_success': True,
            'metrics': {
                'accuracy': 0.65,  # 占位
                'mae': 1.0,
                'roi': 0.05
            },
            'parameters': self._calibration
        }
