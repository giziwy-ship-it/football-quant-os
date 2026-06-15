#!/usr/bin/env python3
"""UpsetDetector - 冷门雷达 v1.0
基于老法拉利研究框架：市场定价错误(Mispricing)检测系统

核心逻辑：
- 不是寻找"必中信号"，而是寻找市场定价错误
- 顶级机构问："市场低估了什么？"
- 真实概率 > 市场概率 = 价值投注(Value Bet)

100分冷门评分模型：
- big_team_hype: 20分
- odds_reverse: 20分  
- abnormal_flow: 15分
- injury_risk: 15分
- elo_overvalued: 10分
- xg_undervalued: 10分
- motivation_gap: 10分

输出：
- 80+ = 重点冷门候选
- 60-80 = 观察
- 60以下 = 正常比赛
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math


class UpsetLevel(Enum):
    """冷门等级"""
    NORMAL = "normal"         # 正常比赛 (<60)
    WATCH = "watch"             # 观察 (60-80)
    CANDIDATE = "candidate"     # 冷门候选 (80+)
    STRONG = "strong"           # 强冷门信号 (90+)


class MatchStage(Enum):
    """比赛阶段"""
    GROUP_RD1 = "group_round_1"    # 小组赛第一轮
    GROUP_RD2 = "group_round_2"    # 小组赛第二轮
    GROUP_RD3 = "group_round_3"    # 小组赛第三轮(最冷门)
    ROUND_16 = "round_of_16"       # 1/8决赛
    QUARTER = "quarter_final"      # 1/4决赛
    SEMI = "semi_final"          # 半决赛
    FINAL = "final"              # 决赛


@dataclass
class UpsetFactors:
    """冷门因子数据"""
    # 一级因子 (20分)
    big_team_hype: float = 0.0        # 0-20, 公众投注比例
    odds_reverse: float = 0.0       # 0-20, 赔率异常变动
    
    # 二级因子 (15分)
    abnormal_flow: float = 0.0         # 0-15, 资金流向异常
    injury_risk: float = 0.0           # 0-15, 关键球员伤病
    
    # 三级因子 (10分)
    elo_overvalued: float = 0.0            # 0-10, ELO差距被高估
    xg_undervalued: float = 0.0             # 0-10, xG被低估
    motivation_gap: float = 0.0           # 0-10, motivation_gap
    
    @property
    def total_score(self) -> float:
        return sum([
            self.big_team_hype,
            self.odds_reverse,
            self.abnormal_flow,
            self.injury_risk,
            self.elo_overvalued,
            self.xg_undervalued,
            self.motivation_gap
        ])


@dataclass
class BigScoreFactors:
    """大比分因子"""
    total_xg: float = 0.0          # 两队近10场场均xG之和
    total_xga: float = 0.0         # 两队近10场场均xGA之和
    pace: float = 0.0            # 比赛节奏评分
    defense_gap: float = 0.0        # defense_gap
    big_score_history: float = 0.0       # big_score_history
    
    @property
    def big_score_probability(self) -> float:
        """大比分概率"""
        # xG总值 > 4.0 时，大比分概率高
        xg_factor = min(1.0, self.total_xg / 5.0)
        xga_factor = min(1.0, self.total_xga / 5.0)
        pace_factor = self.pace / 10.0
        
        return round((xg_factor * 0.35 + xga_factor * 0.35 + pace_factor * 0.30) * 100, 1)


class UpsetDetector:
    """
    冷门雷达 Agent
    
    角色：市场定价错误侦探 + 冷门信号猎人
    
    核心问题：不是"谁会赢？"而是"市场低估了什么？"
    """
    
    # 因子权重(100分制)
    WEIGHTS = {
        'big_team_hype': 20,
        'odds_reverse': 20,
        'abnormal_flow': 15,
        'injury_risk': 15,
        'elo_overvalued': 10,
        'xg_undervalued': 10,
        'motivation_gap': 10,
    }
    
    # 冷门阈值
    THRESHOLDS = {
        'normal': 60,      # 正常
        'watch': 80,       # 观察
        'candidate': 90,   # 强冷门
    }
    
    # 世界杯阶段冷门概率(历史数据)
    STAGE_UPSET_PROB = {
        MatchStage.GROUP_RD1: 0.15,    # 第一轮冷门概率15%
        MatchStage.GROUP_RD2: 0.18,    # 第二轮18%
        MatchStage.GROUP_RD3: 0.28,     # 第三轮最冷门28%
        MatchStage.ROUND_16: 0.12,     # 淘汰赛冷门少
        MatchStage.QUARTER: 0.10,
        MatchStage.SEMI: 0.08,
        MatchStage.FINAL: 0.05,
    }
    
    # 豪门球队(公众投注热门)
    BIG_TEAMS = {
        'Argentina', 'Brazil', 'France', 'Germany', 'England', 
        'Spain', 'Portugal', 'Netherlands', 'Italy', 'Belgium',
        '阿根廷', '巴西', '法国', '德国', '英格兰',
        '西班牙', '葡萄牙', '荷兰', '意大利', '比利时',
    }
    
    def __init__(self):
        self.upset_history: List[Dict] = []
        self.big_score_history: List[Dict] = []
    
    def calculate_upset_score(
        self,
        market_prob: Dict[str, float],      # 市场概率 {home: 0.60, draw: 0.25, away: 0.15}
        model_prob: Dict[str, float],       # 模型概率 {home: 0.45, draw: 0.30, away: 0.25}
        market_odds: Dict[str, float],      # 市场赔率 {home: 1.67, draw: 4.00, away: 6.67}
        elo_home: float = 0,
        elo_away: float = 0,
        xg_home: float = 0,
        xg_away: float = 0,
        betting_flow: Dict[str, float] = None,  # 投注流向 {home: 0.75, away: 0.25}
        injuries: Dict[str, Any] = None,      # 伤病信息
        motivation: Dict[str, float] = None,   # 战意 {home: 0.9, away: 0.6}
        stage: MatchStage = MatchStage.GROUP_RD1,
    ) -> Dict[str, Any]:
        """
        计算冷门评分
        
        核心逻辑：真实概率 vs 市场概率的偏差
        """
        factors = UpsetFactors()
        
        # 1. big_team_hype (20分)
        factors.big_team_hype = self._calculate_豪门热度(
            market_prob, model_prob, betting_flow, market_odds
        )
        
        # 2. odds_reverse (20分)
        factors.odds_reverse = self._calculate_赔率波动(
            market_odds, model_prob, betting_flow
        )
        
        # 3. abnormal_flow (15分)
        factors.abnormal_flow = self._calculate_资金流异常(
            betting_flow, market_odds
        )
        
        # 4. injury_risk (15分)
        factors.injury_risk = self._calculate_伤病影响(
            injuries, market_prob
        )
        
        # 5. elo_overvalued (10分)
        factors.elo_overvalued = self._calculate_ELO偏差(
            elo_home, elo_away, market_prob, model_prob
        )
        
        # 6. xg_undervalued (10分)
        factors.xg_undervalued = self._calculate_xG偏差(
            xg_home, xg_away, market_prob, model_prob
        )
        
        # 7. motivation_gap (10分)
        factors.motivation_gap = self._calculate_motivation_gap(
            motivation, stage
        )
        
        # 计算总分
        total_score = factors.total_score
        
        # 确定等级
        level = self._determine_level(total_score)
        
        # 计算价值投注
        value_bets = self._find_value_bets(
            market_prob, model_prob, market_odds
        )
        
        # 生成建议
        recommendation = self._generate_recommendation(
            total_score, level, value_bets, stage
        )
        
        return {
            'match_stage': stage.value,
            'stage_upset_prob': self.STAGE_UPSET_PROB.get(stage, 0.15),
            'total_score': round(total_score, 1),
            'level': level.value,
            'level_chinese': self._level_to_chinese(level),
            'factors': {
                'big_team_hype': round(factors.big_team_hype, 1),
                'odds_reverse': round(factors.odds_reverse, 1),
                'abnormal_flow': round(factors.abnormal_flow, 1),
                'injury_risk': round(factors.injury_risk, 1),
                'elo_overvalued': round(factors.elo_overvalued, 1),
                'xg_undervalued': round(factors.xg_undervalued, 1),
                'motivation_gap': round(factors.motivation_gap, 1),
            },
            'value_bets': value_bets,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat(),
        }
    
    def _calculate_豪门热度(
        self,
        market_prob: Dict[str, float],
        model_prob: Dict[str, float],
        betting_flow: Optional[Dict[str, float]],
        market_odds: Dict[str, float]
    ) -> float:
        """big_team_hype评分 (0-20)"""
        score = 0.0
        
        # 检查市场是否过度偏向热门
        if betting_flow:
            home_flow = betting_flow.get('home', 0.5)
            # 如果80%+资金流向主队，但赔率不降反升
            if home_flow > 0.75:
                # 获取市场隐含概率
                home_implied = 1.0 / market_odds.get('home', 2.0)
                model_home = model_prob.get('home', 0.5)
                
                # 如果市场隐含概率 < 模型概率(说明市场低估了)
                if home_implied < model_home * 0.85:
                    score += 15  # 强信号：热门被高估
                elif home_implied < model_home * 0.95:
                    score += 10  # 中等信号
                else:
                    score += 5   # 弱信号
        
        # 检查赔率与概率的偏离
        for side in ['home', 'away']:
            implied = 1.0 / market_odds.get(side, 2.0)
            model = model_prob.get(side, 0.5)
            
            # 如果市场隐含概率远低于模型概率(市场严重低估)
            if model > implied * 1.5:
                score += 3
            elif model > implied * 1.3:
                score += 1.5
        
        return min(20.0, score)
    
    def _calculate_赔率波动(
        self,
        market_odds: Dict[str, float],
        model_prob: Dict[str, float],
        betting_flow: Optional[Dict[str, float]]
    ) -> float:
        """odds_reverse评分 (0-20)"""
        score = 0.0
        
        # 核心：odds_reverse = 投注多但赔率上升
        if betting_flow:
            home_flow = betting_flow.get('home', 0.5)
            home_implied = 1.0 / market_odds.get('home', 2.0)
            model_home = model_prob.get('home', 0.5)
            
            # 80%买主队，但隐含概率只有50%(说明赔率没有相应下降)
            if home_flow > 0.70 and home_implied < 0.55:
                score += 15  # 经典异常：大量投注但赔率未降
            elif home_flow > 0.60 and home_implied < 0.50:
                score += 10
        
        # 检查赔率是否合理(根据模型概率)
        for side in ['home', 'draw', 'away']:
            implied = 1.0 / market_odds.get(side, 2.0)
            model = model_prob.get(side, 0.33)
            
            # 如果赔率隐含的胜率与模型概率差距 > 10%
            gap = abs(implied - model)
            if gap > 0.15:
                score += 3  # 显著偏差
            elif gap > 0.10:
                score += 1.5
        
        return min(20.0, score)
    
    def _calculate_资金流异常(
        self,
        betting_flow: Optional[Dict[str, float]],
        market_odds: Dict[str, float]
    ) -> float:
        """abnormal_flow评分 (0-15)"""
        if not betting_flow:
            return 0.0
        
        score = 0.0
        home_flow = betting_flow.get('home', 0.5)
        away_flow = betting_flow.get('away', 0.5)
        
        # 极端不平衡：80% vs 20%
        if home_flow > 0.80 or away_flow > 0.80:
            score += 10
        elif home_flow > 0.70 or away_flow > 0.70:
            score += 7
        elif home_flow > 0.60 or away_flow > 0.60:
            score += 3
        
        # 检查是否出现"赔率不降反升"(大量投注但赔率没降)
        home_implied = 1.0 / market_odds.get('home', 2.0)
        if home_flow > 0.70 and home_implied < 0.50:
            score += 5  # 异常：大量投注但隐含概率低
        
        return min(15.0, score)
    
    def _calculate_伤病影响(
        self,
        injuries: Optional[Dict[str, Any]],
        market_prob: Dict[str, float]
    ) -> float:
        """injury_risk评分 (0-15)"""
        if not injuries:
            return 0.0
        
        score = 0.0
        
        for team, team_injuries in injuries.items():
            if not team_injuries:
                continue
            
            for injury in team_injuries:
                player = injury.get('player', '')
                importance = injury.get('importance', 'medium')  # low/medium/high/critical
                position = injury.get('position', '')
                
                # 核心球员伤病
                if importance == 'critical':
                    score += 8
                elif importance == 'high':
                    score += 5
                elif importance == 'medium':
                    score += 2
                
                # 关键位置(门将、核心前锋、组织核心)
                if position in ['GK', 'ST', 'CAM', 'CDM']:
                    score += 2
        
        return min(15.0, score)
    
    def _calculate_ELO偏差(
        self,
        elo_home: float,
        elo_away: float,
        market_prob: Dict[str, float],
        model_prob: Dict[str, float]
    ) -> float:
        """elo_overvalued评分 (0-10)"""
        if elo_home == 0 or elo_away == 0:
            return 0.0
        
        score = 0.0
        elo_diff = elo_home - elo_away
        
        # 市场隐含的主队概率
        market_home = market_prob.get('home', 0.5)
        model_home = model_prob.get('home', 0.5)
        
        # 如果ELO差距大，但市场概率与模型概率差距也大
        # 说明市场可能过度反应了ELO差距
        if elo_diff > 200:  # 主队ELO高200+
            if market_home > model_home * 1.2:
                score += 8  # 市场过度高估主队
            elif market_home > model_home * 1.1:
                score += 5
        elif elo_diff > 100:
            if market_home > model_home * 1.2:
                score += 5
            elif market_home > model_home * 1.1:
                score += 3
        
        # 反之：如果ELO差距小，但市场概率差距大(市场可能低估了)
        if abs(elo_diff) < 100:
            if market_home < model_home * 0.85:
                score += 5  # 市场低估了主队
        
        return min(10.0, score)
    
    def _calculate_xG偏差(
        self,
        xg_home: float,
        xg_away: float,
        market_prob: Dict[str, float],
        model_prob: Dict[str, float]
    ) -> float:
        """xg_undervalued评分 (0-10)"""
        if xg_home == 0 or xg_away == 0:
            return 0.0
        
        score = 0.0
        
        # 主队xG被低估
        home_xg_strength = xg_home / max(xg_away, 0.1)
        market_home = market_prob.get('home', 0.5)
        model_home = model_prob.get('home', 0.5)
        
        # 如果xG显示主队进攻强，但市场概率低
        if home_xg_strength > 1.5 and market_home < model_home * 0.9:
            score += 7  # 市场严重低估了主队进攻
        elif home_xg_strength > 1.2 and market_home < model_home * 0.95:
            score += 4
        
        # 如果xG差距与市场概率差距不一致
        xg_diff = xg_home - xg_away
        prob_diff = model_home - market_home
        
        if xg_diff > 0.5 and prob_diff > 0.1:
            score += 3  # xG和模型都看好主队，但市场不看好
        
        return min(10.0, score)
    
    def _calculate_motivation_gap(
        self,
        motivation: Optional[Dict[str, float]],
        stage: MatchStage
    ) -> float:
        """motivation_gap评分 (0-10)"""
        if not motivation:
            return 0.0
        
        score = 0.0
        home_mot = motivation.get('home', 0.8)
        away_mot = motivation.get('away', 0.8)
        mot_diff = abs(home_mot - away_mot)
        
        # motivation_gap大
        if mot_diff > 0.4:
            score += 7
        elif mot_diff > 0.3:
            score += 5
        elif mot_diff > 0.2:
            score += 2
        
        # 小组赛第三轮特殊因子
        if stage == MatchStage.GROUP_RD3:
            if home_mot < 0.5 or away_mot < 0.5:
                score += 3  # 已出线/淘汰，战意低
        
        # 淘汰赛(战意都高，差异小)
        if stage in [MatchStage.ROUND_16, MatchStage.QUARTER, MatchStage.SEMI, MatchStage.FINAL]:
            score *= 0.5  # 淘汰赛motivation_gap通常不大
        
        return min(10.0, score)
    
    def _determine_level(self, score: float) -> UpsetLevel:
        """根据评分确定冷门等级"""
        if score >= 90:
            return UpsetLevel.STRONG
        elif score >= 80:
            return UpsetLevel.CANDIDATE
        elif score >= 60:
            return UpsetLevel.WATCH
        else:
            return UpsetLevel.NORMAL
    
    def _level_to_chinese(self, level: UpsetLevel) -> str:
        """等级中文翻译"""
        mapping = {
            UpsetLevel.NORMAL: '正常比赛',
            UpsetLevel.WATCH: '观察',
            UpsetLevel.CANDIDATE: '冷门候选',
            UpsetLevel.STRONG: '强冷门信号',
        }
        return mapping.get(level, '未知')
    
    def _find_value_bets(
        self,
        market_prob: Dict[str, float],
        model_prob: Dict[str, float],
        market_odds: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """
        寻找价值投注
        
        核心：真实概率 > 市场隐含概率
        """
        value_bets = []
        
        for side in ['home', 'draw', 'away']:
            implied = 1.0 / market_odds.get(side, 2.0)
            model = model_prob.get(side, 0.33)
            odds = market_odds.get(side, 2.0)
            
            # 计算edge
            edge = (model - implied) / implied if implied > 0 else 0
            
            if edge > 0.15:  # 15%以上edge
                value_bets.append({
                    'side': side,
                    'odds': odds,
                    'market_implied': round(implied, 3),
                    'model_prob': round(model, 3),
                    'edge': round(edge * 100, 1),
                    'level': 'strong_value' if edge > 0.30 else 'value' if edge > 0.15 else 'slight',
                    'recommendation': 'STRONG_BET' if edge > 0.30 else 'BET' if edge > 0.15 else 'SKIP'
                })
        
        return sorted(value_bets, key=lambda x: x['edge'], reverse=True)
    
    def _generate_recommendation(
        self,
        score: float,
        level: UpsetLevel,
        value_bets: List[Dict],
        stage: MatchStage
    ) -> Dict[str, Any]:
        """生成建议"""
        rec = {
            'overall': '',
            'value_bet': '',
            'avoid': '',
            'stage_note': '',
        }
        
        # 总体建议
        if score >= 90:
            rec['overall'] = 'STRONG_UPSET_CANDIDATE - 重点冷门候选，市场严重定价错误'
        elif score >= 80:
            rec['overall'] = 'UPSET_CANDIDATE - 冷门候选，存在价值投注'
        elif score >= 60:
            rec['overall'] = 'WATCH_CLOSELY - 密切关注，轻微异常'
        else:
            rec['overall'] = 'NORMAL - 正常比赛，市场定价合理'
        
        # 价值投注建议
        if value_bets:
            best = value_bets[0]
            rec['value_bet'] = f"推荐: {best['side'].upper()} @ {best['odds']} (edge: +{best['edge']}%)"
        else:
            rec['value_bet'] = '未发现显著价值投注'
        
        # 避免投注
        if score >= 80:
            rec['avoid'] = '避免投注热门方(市场可能严重高估)'
        
        # 阶段注释
        if stage == MatchStage.GROUP_RD3:
            rec['stage_note'] = '小组赛第三轮：历史冷门概率最高(28%)，注意motivation_gap'
        elif stage in [MatchStage.ROUND_16, MatchStage.QUARTER]:
            rec['stage_note'] = '淘汰赛阶段：冷门概率较低，但可能出加时/点球'
        
        return rec
    
    def calculate_big_score(
        self,
        xg_home: float,
        xg_away: float,
        xga_home: float,
        xga_away: float,
        pace_home: float = 5.0,    # 节奏 1-10
        pace_away: float = 5.0,
        historical_big_score_rate: float = 0.0,  # big_score_history
    ) -> Dict[str, Any]:
        """
        大比分预测
        
        核心：xG总值 + 节奏 + 防守质量
        """
        factors = BigScoreFactors()
        factors.total_xg = xg_home + xg_away
        factors.total_xga = xga_home + xga_away
        factors.pace = (pace_home + pace_away) / 2
        factors.defense_gap = abs(xga_home - xga_away)
        factors.big_score_history = historical_big_score_rate
        
        prob = factors.big_score_probability
        
        # 推荐总进球
        if factors.total_xg > 4.0:
            suggested_total = '大2.5/3.0'
            expected_goals = round(factors.total_xg, 1)
        elif factors.total_xg > 3.0:
            suggested_total = '大2.5'
            expected_goals = round(factors.total_xg, 1)
        else:
            suggested_total = '小2.5'
            expected_goals = round(factors.total_xg, 1)
        
        return {
            'big_score_probability': prob,
            'expected_goals': expected_goals,
            'suggested_total': suggested_total,
            'xg_sum': round(factors.total_xg, 2),
            'xga_sum': round(factors.total_xga, 2),
            'pace': round(factors.pace, 1),
            'factors': {
                'total_xg': factors.total_xg,
                'total_xga': factors.total_xga,
                'pace': factors.pace,
                'defense_gap': factors.defense_gap,
                'big_score_history': factors.big_score_history,
            }
        }
    
    def get_upset_report(self, result: Dict[str, Any]) -> str:
        """生成冷门报告"""
        lines = [
            "=" * 60,
            "           UpsetDetector - 冷门雷达报告",
            "=" * 60,
            "",
            f"【冷门评分】",
            f"  总分: {result['total_score']}/100",
            f"  等级: {result['level'].upper()} ({result['level_chinese']})",
            f"  阶段冷门概率: {result['stage_upset_prob']*100:.0f}%",
            "",
            f"【因子分解】",
        ]
        
        for factor, score in result['factors'].items():
            bar = "*" * int(score / 2) + "-" * (10 - int(score / 2))
            lines.append(f"  {factor:12s} {bar} {score:.1f}/{self.WEIGHTS[factor]}")
        
        lines.extend([
            "",
            f"【价值投注】",
        ])
        
        if result['value_bets']:
            for bet in result['value_bets']:
                lines.append(f"  {bet['side'].upper()}: @{bet['odds']} (market: {bet['market_implied']*100:.1f}% vs model: {bet['model_prob']*100:.1f}%) edge: +{bet['edge']}%")
        else:
            lines.append("  未发现显著价值投注")
        
        rec = result['recommendation']
        lines.extend([
            "",
            f"【建议】",
            f"  总体: {rec['overall']}",
            f"  投注: {rec['value_bet']}",
        ])
        
        if rec['avoid']:
            lines.append(f"  避免: {rec['avoid']}")
        if rec['stage_note']:
            lines.append(f"  阶段: {rec['stage_note']}")
        
        lines.append("=" * 60)
        return "\n".join(lines)


# ========== 快速测试 ==========
if __name__ == "__main__":
    detector = UpsetDetector()
    
    print("=" * 60)
    print("           UpsetDetector - 冷门雷达 v1.0")
    print("           基于市场定价错误(Mispricing)检测")
    print("=" * 60)
    print()
    
    # 测试案例1: 沙特2:1阿根廷(2022世界杯经典冷门)
    print("【测试案例1】沙特 vs 阿根廷(2022世界杯)")
    print("  模拟：市场严重低估沙特，高估阿根廷")
    
    result1 = detector.calculate_upset_score(
        market_prob={'home': 0.08, 'draw': 0.12, 'away': 0.80},   # 市场：阿根廷80%胜率
        model_prob={'home': 0.25, 'draw': 0.30, 'away': 0.45},    # 模型：沙特25%，更合理
        market_odds={'home': 12.5, 'draw': 8.33, 'away': 1.25},   # 市场赔率
        elo_home=1450, elo_away=1850,                              # ELO差距400
        xg_home=1.2, xg_away=1.8,
        betting_flow={'home': 0.05, 'away': 0.95},                 # 95%买阿根廷
        injuries={'away': [{'player': '迪马利亚', 'importance': 'high', 'position': 'RW'}]},
        motivation={'home': 0.95, 'away': 0.85},
        stage=MatchStage.GROUP_RD1,
    )
    
    print(detector.get_upset_report(result1))
    print()
    
    # 测试案例2: 韩国2:0德国(2018世界杯)
    print("【测试案例2】韩国 vs 德国(2018世界杯)")
    print("  模拟：德国已出线，韩国背水一战")
    
    result2 = detector.calculate_upset_score(
        market_prob={'home': 0.10, 'draw': 0.15, 'away': 0.75},
        model_prob={'home': 0.20, 'draw': 0.25, 'away': 0.55},
        market_odds={'home': 10.0, 'draw': 6.67, 'away': 1.33},
        elo_home=1520, elo_away=1950,
        xg_home=1.0, xg_away=2.0,
        betting_flow={'home': 0.08, 'away': 0.92},
        motivation={'home': 1.0, 'away': 0.6},  # 德国已提前出线，战意低
        stage=MatchStage.GROUP_RD3,  # 第三轮最冷门
    )
    
    print(detector.get_upset_report(result2))
    print()