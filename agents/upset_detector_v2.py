# -*- coding: utf-8 -*-
"""
UpsetDetector v2.0 - 冷门雷达重训练版
基于2026世界杯12场结果重新训练参数

训练数据：
- 小组赛首轮实际冷门率：37.5%（3/8场，澳大利亚/科特迪瓦/瑞典）
- 原模型冷门评分：均低于30/100，严重低估
- 冷门特征：非洲/亚洲/北美球队对阵欧洲热门时冷门率高

核心修正：
1. 小组赛首轮冷门概率：15%→35%（基于实际数据）
2. 冷门阈值：60/80/90→45/65/80（更敏感）
3. 新增区域冷门因子：非洲+15%，亚洲+10%，北美+12%
4. 豪门热度阈值：70%→60%（更敏感）
5. 赔率波动检测：赔率上升+投注增加→冷门信号
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import math
import json


class UpsetLevel(Enum):
    """冷门等级"""
    NORMAL = "normal"         # 正常比赛 (<45)
    WATCH = "watch"             # 观察 (45-65)
    CANDIDATE = "candidate"     # 冷门候选 (65-80)
    STRONG = "strong"           # 强冷门信号 (80+)


class MatchStage(Enum):
    """比赛阶段"""
    GROUP_RD1 = "group_round_1"    # 小组赛第一轮（最冷门）
    GROUP_RD2 = "group_round_2"    # 小组赛第二轮
    GROUP_RD3 = "group_round_3"    # 小组赛第三轮
    ROUND_16 = "round_of_16"       # 1/8决赛
    QUARTER = "quarter_final"      # 1/4决赛
    SEMI = "semi_final"          # 半决赛
    FINAL = "final"              # 决赛


@dataclass
class UpsetFactors:
    """冷门因子数据"""
    # 一级因子 (20分)
    big_team_hype: float = 0.0        # 0-20, 豪门热度
    odds_reverse: float = 0.0       # 0-20, 赔率反向波动
    
    # 二级因子 (15分)
    abnormal_flow: float = 0.0         # 0-15, 资金流向异常
    region_upset: float = 0.0           # 0-15, 区域冷门因子（新增）
    
    # 三级因子 (10分)
    elo_overvalued: float = 0.0            # 0-10, ELO差距被高估
    xg_undervalued: float = 0.0             # 0-10, xG被低估
    motivation_gap: float = 0.0           # 0-10, 战意差距
    
    @property
    def total_score(self) -> float:
        return sum([
            self.big_team_hype,
            self.odds_reverse,
            self.abnormal_flow,
            self.region_upset,
            self.elo_overvalued,
            self.xg_undervalued,
            self.motivation_gap
        ])


class UpsetDetector:
    """
    冷门雷达 Agent v2.0
    
    训练后参数：
    - 小组赛首轮冷门概率：35%（原15%）
    - 冷门阈值：45/65/80（更敏感）
    - 区域冷门加成：非洲+15%，亚洲+10%，北美+12%
    - 豪门热度检测：60%（原70%）
    """
    
    # 因子权重(100分制)
    WEIGHTS = {
        'big_team_hype': 20,
        'odds_reverse': 20,
        'abnormal_flow': 15,
        'region_upset': 15,  # 新增
        'elo_overvalued': 10,
        'xg_undervalued': 10,
        'motivation_gap': 10,
    }
    
    # 冷门阈值（训练后：更敏感）
    THRESHOLDS = {
        'normal': 45,      # 正常（原60）
        'watch': 65,       # 观察（原80）
        'candidate': 80,   # 强冷门（原90）
    }
    
    # 世界杯阶段冷门概率(训练后：基于12场结果)
    STAGE_UPSET_PROB = {
        MatchStage.GROUP_RD1: 0.35,    # 第一轮冷门概率35%（原15%）
        MatchStage.GROUP_RD2: 0.20,    # 第二轮20%（原18%）
        MatchStage.GROUP_RD3: 0.25,     # 第三轮25%（原28%）
        MatchStage.ROUND_16: 0.12,     # 淘汰赛冷门少
        MatchStage.QUARTER: 0.10,
        MatchStage.SEMI: 0.08,
        MatchStage.FINAL: 0.05,
    }
    
    # 豪门球队（热门被高估）
    BIG_TEAMS = {
        'Argentina', 'Brazil', 'France', 'Germany', 'England', 
        'Spain', 'Portugal', 'Netherlands', 'Italy', 'Belgium',
        '阿根廷', '巴西', '法国', '德国', '英格兰',
        '西班牙', '葡萄牙', '荷兰', '意大利', '比利时',
        'Switzerland', 'Sweden', 'Croatia', 'Denmark', 'Uruguay',
    }
    
    # 区域冷门加成（训练后新增）
    REGION_UPSET_BOOST = {
        'africa': 0.15,      # 非洲球队冷门+15%（实际：科特迪瓦/摩洛哥冷门）
        'asia': 0.10,        # 亚洲球队冷门+10%（实际：澳大利亚/日本冷门）
        'concacaf': 0.12,    # 北美球队冷门+12%（实际：美国/墨西哥/加拿大）
        'south_america': 0.05,  # 南美+5%
        'europe': 0.0,       # 欧洲无加成（热门被高估）
    }
    
    def __init__(self, trained_params: Optional[Dict] = None):
        self.upset_history: List[Dict] = []
        self.big_score_history: List[Dict] = []
        
        # 加载训练参数
        if trained_params:
            self.THRESHOLDS.update(trained_params.get('thresholds', {}))
            self.STAGE_UPSET_PROB.update(trained_params.get('stage_probs', {}))
            self.REGION_UPSET_BOOST.update(trained_params.get('region_boost', {}))
    
    def calculate_upset_score(
        self,
        market_prob: Dict[str, float],
        model_prob: Dict[str, float],
        market_odds: Dict[str, float],
        home_team: str = "",
        away_team: str = "",
        home_region: str = "",
        away_region: str = "",
        elo_home: float = 0,
        elo_away: float = 0,
        xg_home: float = 0,
        xg_away: float = 0,
        betting_flow: Dict[str, float] = None,
        injuries: Dict[str, Any] = None,
        motivation: Dict[str, float] = None,
        stage: MatchStage = MatchStage.GROUP_RD1,
    ) -> Dict[str, Any]:
        """计算冷门评分（训练后版本）"""
        factors = UpsetFactors()
        
        # 1. big_team_hype (20分)
        factors.big_team_hype = self._calculate_big_team_hype(
            market_prob, model_prob, betting_flow, market_odds, home_team, away_team
        )
        
        # 2. odds_reverse (20分)
        factors.odds_reverse = self._calculate_odds_reverse(
            market_odds, model_prob, betting_flow
        )
        
        # 3. abnormal_flow (15分)
        factors.abnormal_flow = self._calculate_abnormal_flow(
            betting_flow, market_odds
        )
        
        # 4. region_upset (15分) - 新增
        factors.region_upset = self._calculate_region_upset(
            home_region, away_region, home_team, away_team, market_prob
        )
        
        # 5. elo_overvalued (10分)
        factors.elo_overvalued = self._calculate_elo_overvalued(
            elo_home, elo_away, market_prob, model_prob
        )
        
        # 6. xg_undervalued (10分)
        factors.xg_undervalued = self._calculate_xg_undervalued(
            xg_home, xg_away, market_prob, model_prob
        )
        
        # 7. motivation_gap (10分)
        factors.motivation_gap = self._calculate_motivation_gap(
            motivation, stage
        )
        
        total_score = factors.total_score
        level = self._determine_level(total_score)
        value_bets = self._find_value_bets(market_prob, model_prob, market_odds)
        recommendation = self._generate_recommendation(total_score, level, value_bets, stage)
        
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
                'region_upset': round(factors.region_upset, 1),
                'elo_overvalued': round(factors.elo_overvalued, 1),
                'xg_undervalued': round(factors.xg_undervalued, 1),
                'motivation_gap': round(factors.motivation_gap, 1),
            },
            'value_bets': value_bets,
            'recommendation': recommendation,
            'timestamp': datetime.now().isoformat(),
        }
    
    def _calculate_big_team_hype(
        self, market_prob, model_prob, betting_flow, market_odds, home_team, away_team
    ) -> float:
        """big_team_hype评分 (0-20) - 训练后：更敏感"""
        score = 0.0
        
        # 检查是否有豪门球队
        has_big_team = any(t in self.BIG_TEAMS for t in [home_team, away_team])
        
        if betting_flow and has_big_team:
            home_flow = betting_flow.get('home', 0.5)
            home_implied = 1.0 / market_odds.get('home', 2.0)
            model_home = model_prob.get('home', 0.5)
            
            # 训练后：60%资金流向即触发（原70%）
            if home_flow > 0.60:
                if home_implied < model_home * 0.85:
                    score += 15
                elif home_implied < model_home * 0.95:
                    score += 10
                else:
                    score += 5
        
        # 检查赔率与概率偏离
        for side in ['home', 'away']:
            implied = 1.0 / market_odds.get(side, 2.0)
            model = model_prob.get(side, 0.5)
            
            if model > implied * 1.5:
                score += 3
            elif model > implied * 1.3:
                score += 1.5
        
        return min(20.0, score)
    
    def _calculate_odds_reverse(self, market_odds, model_prob, betting_flow) -> float:
        """odds_reverse评分 (0-20)"""
        score = 0.0
        
        if betting_flow:
            home_flow = betting_flow.get('home', 0.5)
            home_implied = 1.0 / market_odds.get('home', 2.0)
            model_home = model_prob.get('home', 0.5)
            
            # 60%买主队但隐含概率低（训练后更敏感）
            if home_flow > 0.60 and home_implied < 0.55:
                score += 15
            elif home_flow > 0.55 and home_implied < 0.50:
                score += 8
        
        return min(20.0, score)
    
    def _calculate_abnormal_flow(self, betting_flow, market_odds) -> float:
        """abnormal_flow评分 (0-15)"""
        score = 0.0
        
        if betting_flow:
            home_flow = betting_flow.get('home', 0.5)
            away_flow = betting_flow.get('away', 0.5)
            
            # 80%资金流向一边（异常）
            if max(home_flow, away_flow) > 0.80:
                score += 10
            elif max(home_flow, away_flow) > 0.70:
                score += 6
        
        return min(15.0, score)
    
    def _calculate_region_upset(
        self, home_region, away_region, home_team, away_team, market_prob
    ) -> float:
        """region_upset评分 (0-15) - 新增！"""
        score = 0.0
        
        # 检查区域冷门加成
        regions = {'home': home_region, 'away': away_region}
        teams = {'home': home_team, 'away': away_team}
        
        for side in ['home', 'away']:
            region = regions.get(side, '')
            team = teams.get(side, '')
            
            # 检查是否为弱势区域球队对阵热门
            if region in self.REGION_UPSET_BOOST:
                boost = self.REGION_UPSET_BOOST[region]
                market_p = market_prob.get(side, 0.5)
                
                # 如果弱势区域球队被低估（市场概率<30%）
                if market_p < 0.30 and boost > 0:
                    score += boost * 100  # 转换百分比为分数
                # 如果弱势区域球队市场概率30-45%
                elif market_p < 0.45 and boost > 0:
                    score += boost * 50
        
        return min(15.0, score)
    
    def _calculate_elo_overvalued(self, elo_home, elo_away, market_prob, model_prob) -> float:
        """elo_overvalued评分 (0-10)"""
        score = 0.0
        
        if elo_home > 0 and elo_away > 0:
            elo_diff = abs(elo_home - elo_away)
            market_diff = abs(market_prob.get('home', 0.5) - market_prob.get('away', 0.5))
            model_diff = abs(model_prob.get('home', 0.5) - model_prob.get('away', 0.5))
            
            # ELO差距大但市场差距更大 = 被高估
            if elo_diff > 200 and market_diff > model_diff + 0.1:
                score += 8
            elif elo_diff > 100 and market_diff > model_diff + 0.05:
                score += 4
        
        return min(10.0, score)
    
    def _calculate_xg_undervalued(self, xg_home, xg_away, market_prob, model_prob) -> float:
        """xg_undervalued评分 (0-10)"""
        score = 0.0
        
        if xg_home > 0 and xg_away > 0:
            xg_total = xg_home + xg_away
            market_home = market_prob.get('home', 0.5)
            model_home = model_prob.get('home', 0.5)
            
            # xG强但市场低估
            if xg_home > xg_away * 1.5 and model_home > market_home + 0.1:
                score += 6
            elif xg_away > xg_home * 1.5 and model_prob.get('away', 0.5) > market_prob.get('away', 0.5) + 0.1:
                score += 6
        
        return min(10.0, score)
    
    def _calculate_motivation_gap(self, motivation, stage) -> float:
        """motivation_gap评分 (0-10)"""
        score = 0.0
        
        if motivation:
            home_mot = motivation.get('home', 0.5)
            away_mot = motivation.get('away', 0.5)
            mot_diff = abs(home_mot - away_mot)
            
            if mot_diff > 0.3:
                score += 8
            elif mot_diff > 0.15:
                score += 4
        
        # 小组赛第三轮战意差距最大
        if stage == MatchStage.GROUP_RD3:
            score += 2
        
        return min(10.0, score)
    
    def _determine_level(self, total_score: float) -> UpsetLevel:
        """确定冷门等级（训练后阈值）"""
        if total_score >= self.THRESHOLDS['candidate']:
            return UpsetLevel.STRONG
        elif total_score >= self.THRESHOLDS['watch']:
            return UpsetLevel.CANDIDATE
        elif total_score >= self.THRESHOLDS['normal']:
            return UpsetLevel.WATCH
        else:
            return UpsetLevel.NORMAL
    
    def _level_to_chinese(self, level: UpsetLevel) -> str:
        """冷门等级中文"""
        mapping = {
            UpsetLevel.NORMAL: "正常",
            UpsetLevel.WATCH: "观察",
            UpsetLevel.CANDIDATE: "冷门候选",
            UpsetLevel.STRONG: "强冷门",
        }
        return mapping.get(level, "未知")
    
    def _find_value_bets(self, market_prob, model_prob, market_odds) -> List[Dict]:
        """寻找价值投注"""
        value_bets = []
        
        for outcome in ['home', 'draw', 'away']:
            market_p = market_prob.get(outcome, 0)
            model_p = model_prob.get(outcome, 0)
            odds = market_odds.get(outcome, 0)
            
            if odds > 0:
                edge = model_p - (1.0 / odds)
                if edge > 0.05:  # 5%以上Edge
                    value_bets.append({
                        'outcome': outcome,
                        'market_prob': round(market_p, 3),
                        'model_prob': round(model_p, 3),
                        'edge': round(edge, 3),
                        'odds': odds,
                    })
        
        return value_bets
    
    def _generate_recommendation(self, score, level, value_bets, stage) -> str:
        """生成建议"""
        rec = []
        
        if level == UpsetLevel.STRONG:
            rec.append(f"[ALERT] Strong upset signal! Score: {score}/100")
            rec.append(f"Group stage upset probability: {self.STAGE_UPSET_PROB.get(stage, 0.15)*100:.0f}%")
            
            if value_bets:
                best = max(value_bets, key=lambda x: x['edge'])
                rec.append(f"Value bet: {best['outcome']} @ {best['odds']} (Edge: +{best['edge']:.1%})")
        
        elif level == UpsetLevel.CANDIDATE:
            rec.append(f"[WARN] Upset candidate, score: {score}/100")
            if value_bets:
                rec.append("Consider small bet on value side")
        
        elif level == UpsetLevel.WATCH:
            rec.append(f"[WATCH] Watch level, score: {score}/100")
            rec.append("Market anomaly detected, but signal weak")
        
        else:
            rec.append(f"[OK] Normal match, score: {score}/100")
        
        return " | ".join(rec)
    
    def get_trained_params(self) -> Dict:
        """获取训练后参数"""
        return {
            'version': 'v2.0-trained-20260615',
            'training_matches': 12,
            'thresholds': self.THRESHOLDS,
            'stage_probs': {k.value: v for k, v in self.STAGE_UPSET_PROB.items()},
            'region_boost': self.REGION_UPSET_BOOST,
        }


# 测试
if __name__ == "__main__":
    detector = UpsetDetector()
    
    # 测试：澳大利亚vs土耳其（实际冷门：澳大利亚2-0胜）
    result = detector.calculate_upset_score(
        market_prob={'home': 0.183, 'draw': 0.259, 'away': 0.558},
        model_prob={'home': 0.198, 'draw': 0.247, 'away': 0.555},
        market_odds={'home': 5.20, 'draw': 3.67, 'away': 1.70},
        home_team='Australia',
        away_team='Turkey',
        home_region='asia',
        away_region='europe',
        betting_flow={'home': 0.15, 'away': 0.75},
        stage=MatchStage.GROUP_RD1,
    )
    
    print("=== UpsetDetector v2.0 Test ===")
    print(f"Match: Australia vs Turkey (Actual: 2-0 Australia)")
    print(f"Score: {result['total_score']}/100")
    print(f"Level: {result['level_chinese']} ({result['level']})")
    print(f"Factors: {result['factors']}")
    print(f"Value Bets: {result['value_bets']}")
    print(f"Rec: {result['recommendation']}")
    print()
    
    # 测试：瑞典vs突尼斯（实际冷门：瑞典3-1胜）
    result2 = detector.calculate_upset_score(
        market_prob={'home': 0.581, 'draw': 0.290, 'away': 0.224},
        model_prob={'home': 0.316, 'draw': 0.407, 'away': 0.277},
        market_odds={'home': 1.72, 'draw': 3.45, 'away': 4.47},
        home_team='Sweden',
        away_team='Tunisia',
        home_region='europe',
        away_region='africa',
        betting_flow={'home': 0.75, 'away': 0.15},
        stage=MatchStage.GROUP_RD1,
    )
    
    print(f"Match: Sweden vs Tunisia (Actual: 3-1 Sweden)")
    print(f"Score: {result2['total_score']}/100")
    print(f"Level: {result2['level_chinese']} ({result2['level']})")
    print(f"Factors: {result2['factors']}")
    print()
    
    print("=== Training Params ===")
    print(json.dumps(detector.get_trained_params(), indent=2))
