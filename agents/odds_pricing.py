#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OddsPricingAgent - 赔率定价中心 v1.0
融合顶级博彩机构定价逻辑：预测概率 → 转换概率 → 加入利润率 → 形成赔率

核心能力：
1. 从预测概率生成标准赔率（含利润率管理）
2. 市场偏差检测与修正
3. 动态盘口调整（Book Balancing）
4. 亚洲盘口/大小球盘口生成
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import math


@dataclass
class MarketConditions:
    """市场条件参数"""
    league_type: str = "World Cup"        # 联赛类型：五大联赛 / 小众联赛
    match_importance: str = "group"       # 比赛重要性：世界杯小组赛/淘汰赛/友谊赛
    market_liquidity: float = 0.8         # 市场流动性：0-1
    public_bias: float = 0.0              # 公众偏好偏差：-0.2到+0.2（正=倾向热门）
    competition_stage: str = "group"       # 赛事阶段
    home_advantage: float = 0.05          # 主场优势修正
    time_to_match: float = 24.0           # 距比赛开始小时数


@dataclass
class PricingOutput:
    """定价输出"""
    odds: Dict[str, float]                # 标准赔率
    implied_prob: Dict[str, float]        # 隐含概率
    overround: float                      # 利润率（水分）
    margin: float                         # 实际利润率
    confidence: float                     # 定价置信度
    fair_odds: Dict[str, float]           # 公平赔率（无利润）
    bookmaker_edge: float                 # 庄家优势


class OddsPricingAgent:
    """
    赔率定价Agent
    
    角色：Chief Trader + Senior Trader + Odds Analyst + Market Maker
    
    定价流程：
    预测概率 → 市场转换（公众偏差）→ 加入利润率（Overround）→ 形成赔率
    """
    
    # 顶级机构利润率标准
    OVERROUND_PROFILES = {
        "top_tier": {          # 顶级市场（Pinnacle/Betfair）
            "rate": 0.015,     # 1.5%利润率
            "description": "顶级市场，低利润高流动性"
        },
        "premium": {           # 高端市场（Bet365/William Hill）
            "rate": 0.025,     # 2.5%利润率
            "description": "高端市场，中等利润"
        },
        "mass_market": {       # 大众市场（亚洲盘口）
            "rate": 0.05,      # 5%利润率
            "description": "大众市场，标准利润"
        },
        "low_liquidity": {     # 低流动性市场
            "rate": 0.08,      # 8%利润率
            "description": "低流动性，高利润保护"
        }
    }
    
    # 联赛利润率调整系数
    LEAGUE_MARGIN = {
        "World Cup": 0.98,      # 世界杯：低利润，高流量
        "Champions League": 0.98,
        "Premier League": 0.99,
        "La Liga": 1.01,
        "Serie A": 1.02,
        "Bundesliga": 1.01,
        "Ligue 1": 1.03,
        "Friendly": 1.05,       # 友谊赛：高利润，低流动性
        "Lower League": 1.08,   # 低级别联赛
    }
    
    # 赛事阶段调整
    STAGE_MARGIN = {
        "group": 1.00,          # 小组赛：标准
        "round_of_16": 0.98,   # 16强：略低
        "quarter": 0.97,        # 8强：更低
        "semi": 0.95,           # 半决赛：低利润
        "final": 0.93,          # 决赛：最低利润，最高流量
        "qualifier": 1.05,      # 预选赛：高利润
    }
    
    def __init__(self, profile: str = "premium"):
        """
        初始化定价Agent
        
        Args:
            profile: 利润率配置（top_tier/premium/mass_market/low_liquidity）
        """
        self.profile = profile
        self.base_overround = self.OVERROUND_PROFILES[profile]["rate"]
        self.trading_history = []
    
    def price_match(
        self, 
        predictions: Dict[str, float],
        market_conditions: Optional[MarketConditions] = None,
        custom_margin: Optional[float] = None
    ) -> PricingOutput:
        """
        核心定价函数：从预测概率生成标准赔率
        
        Args:
            predictions: 预测概率 {'home': 0.55, 'draw': 0.25, 'away': 0.20}
            market_conditions: 市场条件
            custom_margin: 自定义利润率（覆盖默认）
        
        Returns:
            PricingOutput: 定价输出
        """
        market_conditions = market_conditions or MarketConditions()
        
        # Step 1: 获取原始概率
        raw_prob = predictions.copy()
        
        # Step 2: 市场转换（考虑公众偏差）
        # 公众倾向于买热门，需要修正概率分布
        adjusted_prob = self._apply_market_bias(raw_prob, market_conditions.public_bias)
        
        # Step 3: 计算动态利润率
        overround = self._calculate_overround(market_conditions, custom_margin)
        
        # Step 4: 生成赔率
        odds = self._prob_to_odds(adjusted_prob, overround)
        
        # Step 5: 计算公平赔率（无利润）
        fair_odds = self._prob_to_odds(raw_prob, overround=0)
        
        # Step 6: 计算隐含概率
        implied_prob = self._odds_to_implied_prob(odds)
        
        # Step 7: 计算实际利润率
        margin = sum(1/v for v in odds.values()) - 1
        
        # Step 8: 定价置信度
        confidence = self._calculate_confidence(adjusted_prob, overround, market_conditions)
        
        return PricingOutput(
            odds=odds,
            implied_prob=implied_prob,
            overround=overround,
            margin=margin,
            confidence=confidence,
            fair_odds=fair_odds,
            bookmaker_edge=margin
        )
    
    def _apply_market_bias(self, probs: Dict[str, float], bias: float) -> Dict[str, float]:
        """
        应用市场偏差修正
        
        公众倾向于买热门（主队/强队），需要调整概率分布
        使热门赔率更低，冷门赔率更高
        
        Args:
            probs: 原始概率
            bias: 偏差系数（正=热门更热，负=冷门更冷）
        """
        # 找出最热门（概率最高）
        max_key = max(probs, key=probs.get)
        max_prob = probs[max_key]
        
        adjusted = {}
        for key, prob in probs.items():
            if key == max_key:
                # 热门概率增加（使赔率更低）
                adjusted[key] = prob * (1 + bias * 0.5)
            else:
                # 冷门概率减少（使赔率更高）
                adjusted[key] = prob * (1 - bias * 0.3)
        
        # 归一化
        total = sum(adjusted.values())
        return {k: v/total for k, v in adjusted.items()}
    
    def _calculate_overround(self, conditions: MarketConditions, custom: Optional[float] = None) -> float:
        """计算动态利润率"""
        if custom is not None:
            return custom
        
        # 基础利润率
        base = self.base_overround
        
        # 联赛调整
        league_mult = self.LEAGUE_MARGIN.get(conditions.league_type, 1.0)
        
        # 赛事阶段调整
        stage_mult = self.STAGE_MARGIN.get(conditions.competition_stage, 1.0)
        
        # 流动性调整
        # 流动性越低，利润率越高
        liquidity_mult = 1.0 + (1.0 - conditions.market_liquidity) * 0.5
        
        # 时间调整
        # 临近比赛，利润率降低（吸引更多投注）
        time_mult = 1.0 - (24 - conditions.time_to_match) / 48 * 0.2
        time_mult = max(0.8, time_mult)
        
        overround = base * league_mult * stage_mult * liquidity_mult * time_mult
        
        return round(overround, 4)
    
    def _prob_to_odds(self, probs: Dict[str, float], overround: float) -> Dict[str, float]:
        """概率转换为赔率"""
        odds = {}
        for key, prob in probs.items():
            if prob > 0:
                odds[key] = round(1 / (prob * (1 + overround)), 2)
            else:
                odds[key] = 999.0
        return odds
    
    def _odds_to_implied_prob(self, odds: Dict[str, float]) -> Dict[str, float]:
        """赔率转隐含概率"""
        probs = {k: 1/v for k, v in odds.items()}
        total = sum(probs.values())
        return {k: round(v/total, 4) for k, v in probs.items()}
    
    def _calculate_confidence(self, probs: Dict[str, float], overround: float, conditions: MarketConditions) -> float:
        """计算定价置信度"""
        # 概率集中度
        max_prob = max(probs.values())
        concentration = max_prob / sum(probs.values())
        
        # 利润率影响（利润率越高，置信度越低）
        margin_factor = 1.0 - overround * 5
        
        # 时间影响（临近比赛，置信度更高）
        time_factor = 1.0 - (24 - conditions.time_to_match) / 48
        
        confidence = concentration * margin_factor * time_factor * 100
        return round(min(confidence, 100), 2)
    
    def generate_corner_odds(self, corner_prob: Dict[str, float]) -> Dict[str, Any]:
        """
        生成角球盘口
        
        Args:
            corner_prob: 角球概率 {'home': 0.55, 'away': 0.45, 'over_9.5': 0.48, 'under_9.5': 0.52}
        """
        return {
            'handicap': self._calculate_fair_handicap(corner_prob),
            'upper': 0.95,
            'lower': 0.95,
            'type': 'corner_handicap'
        }
    
    def generate_card_odds(self, card_prob: Dict[str, float]) -> Dict[str, Any]:
        """
        生成黄牌/红牌盘口
        
        Args:
            card_prob: 黄牌概率 {'over_3.5': 0.55, 'under_3.5': 0.45}
        """
        return {
            'line': 3.5,
            'over': round(0.95 * (card_prob['under_3.5'] / card_prob['over_3.5']), 2) if card_prob['over_3.5'] > card_prob['under_3.5'] else 0.95,
            'under': round(0.95 * (card_prob['over_3.5'] / card_prob['under_3.5']), 2) if card_prob['under_3.5'] > card_prob['over_3.5'] else 0.95,
            'type': 'card_over_under'
        }
    
    def generate_first_goal_odds(self, first_goal_prob: Dict[str, float]) -> Dict[str, Any]:
        """
        生成首球盘口
        
        Args:
            first_goal_prob: {'home': 0.50, 'away': 0.40, 'none': 0.10}
        """
        odds = self._prob_to_odds(first_goal_prob, overround=0.03)
        return {
            'odds': odds,
            'type': 'first_goal'
        }
    
    def generate_half_time_odds(self, ht_prob: Dict[str, float]) -> Dict[str, Any]:
        """
        生成半场盘口
        
        Args:
            ht_prob: {'home': 0.35, 'draw': 0.45, 'away': 0.20}
        """
        odds = self._prob_to_odds(ht_prob, overround=0.02)
        return {
            'odds': odds,
            'type': 'half_time'
        }
    
    def generate_odd_even_odds(self, odd_even_prob: Dict[str, float]) -> Dict[str, Any]:
        """
        生成单双数盘口
        
        Args:
            odd_even_prob: {'odd': 0.50, 'even': 0.50}
        """
        odds = self._prob_to_odds(odd_even_prob, overround=0.05)
        return {
            'odds': odds,
            'type': 'odd_even'
        }
    
    def generate_handicap(
        self, 
        asian_prob: Dict[str, float],
        handicap_line: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        生成亚洲让球盘
        
        Args:
            asian_prob: 亚洲盘概率 {'upper': 0.50, 'lower': 0.50}
            handicap_line: 让球数（自动计算如果None）
        """
        # 如果未提供盘口，计算公平盘口
        if handicap_line is None:
            handicap_line = self._calculate_fair_handicap(asian_prob)
        
        # 计算水位
        upper_prob = asian_prob.get('upper', 0.5)
        lower_prob = asian_prob.get('lower', 0.5)
        
        # 标准水位：上下盘都接近0.95
        # 如果概率不平衡，调整水位
        base_water = 0.95
        
        if upper_prob > lower_prob:
            upper_water = round(base_water * (lower_prob / upper_prob), 2)
            lower_water = base_water
        else:
            upper_water = base_water
            lower_water = round(base_water * (upper_prob / lower_prob), 2)
        
        # 确保水位不低于0.80
        upper_water = max(0.80, upper_water)
        lower_water = max(0.80, lower_water)
        
        return {
            'handicap': handicap_line,
            'upper': upper_water,
            'lower': lower_water,
            'upper_prob': round(upper_prob, 4),
            'lower_prob': round(lower_prob, 4),
            'commission': round(1 - upper_water * upper_prob - lower_water * lower_prob, 4),
            'type': 'asian_handicap'
        }
    
    def _calculate_fair_handicap(self, probs: Dict[str, float]) -> float:
        """计算公平让球盘"""
        # 简化的让球盘计算
        # 实际应该基于实力差和预期进球
        home_prob = probs.get('home', 0.5)
        away_prob = probs.get('away', 0.5)
        
        # 概率差转换为让球
        diff = home_prob - away_prob
        
        if diff > 0.3:
            return -1.0
        elif diff > 0.15:
            return -0.5
        elif diff > -0.15:
            return 0.0
        elif diff > -0.3:
            return 0.5
        else:
            return 1.0
    
    def generate_over_under(self, total_goals_prob: Dict[str, float], line: float = 2.5) -> Dict[str, Any]:
        """
        生成大小球盘
        
        Args:
            total_goals_prob: 总进球概率分布
            line: 盘口线（默认2.5）
        """
        # 计算大于和小于的概率
        def parse_goals(g):
            if g.endswith('+'):
                return float(g[:-1]) + 1  # 5+ 视为 6
            return float(g)
        
        over_prob = sum(p for g, p in total_goals_prob.items() if parse_goals(g) > line)
        under_prob = sum(p for g, p in total_goals_prob.items() if parse_goals(g) <= line)
        
        total = over_prob + under_prob
        over_prob /= total
        under_prob /= total
        
        # 生成水位
        base_water = 0.95
        
        if over_prob > under_prob:
            over_water = round(base_water * (under_prob / over_prob), 2)
            under_water = base_water
        else:
            over_water = base_water
            under_water = round(base_water * (over_prob / under_prob), 2)
        
        return {
            'line': line,
            'over': round(over_water, 2),
            'under': round(under_water, 2),
            'over_prob': round(over_prob, 4),
            'under_prob': round(under_prob, 4),
            'type': 'over_under'
        }
    
    def adjust_odds_realtime(
        self, 
        current_odds: Dict[str, float],
        betting_flow: Dict[str, float],
        risk_exposure: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        实时赔率调整（Book Balancing）
        
        当某个方向投注过多时，自动调整赔率以平衡资金流
        
        Args:
            current_odds: 当前赔率
            betting_flow: 投注流向 {'home': 10000, 'draw': 3000, 'away': 2000}
            risk_exposure: 风险敞口
        """
        total_flow = sum(betting_flow.values())
        if total_flow == 0:
            return {'odds': current_odds, 'adjusted': False}
        
        # 计算各方向投注比例
        flow_ratio = {k: v/total_flow for k, v in betting_flow.items()}
        
        adjusted_odds = current_odds.copy()
        adjustments = {}
        
        for key, ratio in flow_ratio.items():
            if ratio > 0.6:
                # 投注过多：降低赔率（减少吸引力）
                adjusted_odds[key] *= 0.95
                adjustments[key] = "decreased (heavy flow)"
            elif ratio < 0.15:
                # 投注过少：提高赔率（增加吸引力）
                adjusted_odds[key] *= 1.10
                adjustments[key] = "increased (light flow)"
        
        # 确保最低赔率不低于1.01
        adjusted_odds = {k: max(1.01, v) for k, v in adjusted_odds.items()}
        
        # 记录交易历史
        self.trading_history.append({
            'timestamp': datetime.now(),
            'odds': {k: round(v, 2) for k, v in adjusted_odds.items()},
            'flow': {k: round(v, 4) for k, v in flow_ratio.items()},
            'adjustments': adjustments.copy()
        })
        
        return {
            'odds': {k: round(v, 2) for k, v in adjusted_odds.items()},
            'adjusted': True,
            'adjustments': adjustments,
            'flow_ratio': {k: round(v, 4) for k, v in flow_ratio.items()}
        }
    
    def compare_with_market(
        self, 
        our_odds: Dict[str, float],
        market_odds: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        与市场价格对比，识别价值投注
        
        Args:
            our_odds: 我们的定价
            market_odds: 市场平均赔率
        """
        value_bets = {}
        
        for key in our_odds:
            if key in market_odds:
                our = our_odds[key]
                market = market_odds[key]
                
                # 如果我们的赔率 > 市场赔率，市场可能低估了该结果
                if our < market:
                    edge = (market / our - 1) * 100
                    value_bets[key] = {
                        'our_odds': our,
                        'market_odds': market,
                        'edge': round(edge, 2),
                        'signal': 'value_detected' if edge > 5 else 'slight_value'
                    }
        
        return {
            'value_opportunities': value_bets,
            'total_opportunities': len(value_bets)
        }
    
    def aggregate_bookmaker_odds(self, bookmaker_odds: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        多博彩公司赔率聚合
        
        Args:
            bookmaker_odds: {
                'bet365': {'home': 2.10, 'draw': 3.40, 'away': 3.80},
                'pinnacle': {'home': 2.15, 'draw': 3.35, 'away': 3.90},
                'betfair': {'home': 2.12, 'draw': 3.40, 'away': 4.10}
            }
        
        Returns:
            聚合后的最优赔率、平均赔率、赔率差异分析
        """
        if not bookmaker_odds:
            return {'error': 'no_bookmaker_data'}
        
        # 收集每个方向的赔率
        directions = ['home', 'draw', 'away']
        aggregated = {}
        
        for direction in directions:
            odds_list = []
            for bookmaker, odds in bookmaker_odds.items():
                if direction in odds and odds[direction] > 1.0:
                    odds_list.append({'bookmaker': bookmaker, 'odds': odds[direction]})
            
            if not odds_list:
                continue
            
            # 排序：从大到小（找最优赔率）
            odds_list.sort(key=lambda x: x['odds'], reverse=True)
            
            best = odds_list[0]
            avg = sum(o['odds'] for o in odds_list) / len(odds_list)
            
            # 计算差异
            variance = sum((o['odds'] - avg) ** 2 for o in odds_list) / len(odds_list)
            std = variance ** 0.5
            
            aggregated[direction] = {
                'best': best['odds'],
                'best_bookmaker': best['bookmaker'],
                'average': round(avg, 2),
                'count': len(odds_list),
                'std': round(std, 3),
                'all_odds': odds_list
            }
        
        # 计算聚合后的隐含概率
        best_probs = {k: 1/v['best'] for k, v in aggregated.items()}
        total = sum(best_probs.values())
        implied = {k: round(v/total, 4) for k, v in best_probs.items()}
        
        # 寻找套利机会
        arbitrage = self._check_arbitrage_opportunity(aggregated)
        
        return {
            'aggregated': aggregated,
            'implied_prob': implied,
            'arbitrage_opportunity': arbitrage,
            'total_bookmakers': len(bookmaker_odds)
        }
    
    def _check_arbitrage_opportunity(self, aggregated: Dict) -> Dict[str, Any]:
        """检查套利机会"""
        if len(aggregated) < 3:
            return {'exists': False}
        
        # 使用最优赔率计算利润率
        best_odds = {k: v['best'] for k, v in aggregated.items()}
        margin = sum(1/o for o in best_odds.values()) - 1
        
        if margin < 0:
            # 利润率 < 0 意味着无风险套利
            return {
                'exists': True,
                'margin': round(margin, 4),
                'profit_pct': round(abs(margin) * 100, 2),
                'best_odds': best_odds
            }
        
        return {'exists': False, 'margin': round(margin, 4)}
    
    def get_odds_trend(self, match_id: str) -> Dict[str, Any]:
        """
        获取赔率历史趋势
        
        Args:
            match_id: 比赛ID
        """
        history = [h for h in self.trading_history if h.get('match_id') == match_id]
        
        if not history:
            return {'match_id': match_id, 'history': [], 'trend': 'no_data'}
        
        # 分析趋势
        first = history[0]
        last = history[-1]
        
        trends = {}
        for direction in ['home', 'draw', 'away']:
            if direction in first['odds'] and direction in last['odds']:
                change = (last['odds'][direction] - first['odds'][direction]) / first['odds'][direction]
                trends[direction] = {
                    'change_pct': round(change * 100, 2),
                    'trend': 'up' if change > 0.05 else 'down' if change < -0.05 else 'stable',
                    'first': first['odds'][direction],
                    'last': last['odds'][direction]
                }
        
        return {
            'match_id': match_id,
            'data_points': len(history),
            'time_span_hours': (last['timestamp'] - first['timestamp']).total_seconds() / 3600,
            'trends': trends
        }
    
    def get_pricing_report(self, pricing_output: PricingOutput) -> str:
        """生成定价报告"""
        lines = [
            "=" * 60,
            "           OddsPricingAgent 定价报告",
            "=" * 60,
            "",
            "【赔率输出】",
            f"  主胜: @{pricing_output.odds.get('home', 'N/A')}",
            f"  平局: @{pricing_output.odds.get('draw', 'N/A')}",
            f"  客胜: @{pricing_output.odds.get('away', 'N/A')}",
            "",
            "【公平赔率（无利润）】",
            f"  主胜: @{pricing_output.fair_odds.get('home', 'N/A')}",
            f"  平局: @{pricing_output.fair_odds.get('draw', 'N/A')}",
            f"  客胜: @{pricing_output.fair_odds.get('away', 'N/A')}",
            "",
            "【隐含概率】",
            f"  主胜: {pricing_output.implied_prob.get('home', 0)*100:.1f}%",
            f"  平局: {pricing_output.implied_prob.get('draw', 0)*100:.1f}%",
            f"  客胜: {pricing_output.implied_prob.get('away', 0)*100:.1f}%",
            "",
            "【利润率分析】",
            f"  Overround: {pricing_output.overround:.2%}",
            f"  Margin: {pricing_output.margin:.2%}",
            f"  Bookmaker Edge: {pricing_output.bookmaker_edge:.2%}",
            "",
            f"  定价置信度: {pricing_output.confidence:.1f}%",
            "=" * 60,
        ]
        return "\n".join(lines)


# ========== 快速测试 ==========
if __name__ == "__main__":
    agent = OddsPricingAgent(profile="premium")
    
    # 测试：美国 vs 巴拉圭
    predictions = {"home": 0.55, "draw": 0.25, "away": 0.20}  # 美国主场
    
    conditions = MarketConditions(
        league_type="World Cup",
        match_importance="group",
        market_liquidity=0.9,
        public_bias=0.1,  # 公众倾向热门（美国东道主）
        competition_stage="group",
        time_to_match=12.0  # 12小时后比赛
    )
    
    output = agent.price_match(predictions, conditions)
    print(agent.get_pricing_report(output))
    
    print("\n" + "=" * 60)
    print("【亚洲让球盘】")
    asian = {"home": 0.55, "away": 0.45}
    handicap = agent.generate_handicap(asian)
    print(f"  盘口: {handicap['handicap']}")
    print(f"  上盘水位: {handicap['upper']}")
    print(f"  下盘水位: {handicap['lower']}")
    
    print("\n" + "=" * 60)
    print("【大小球盘】")
    goals = {"0": 0.06, "1": 0.22, "2": 0.32, "3": 0.22, "4": 0.12, "5+": 0.06}
    ou = agent.generate_over_under(goals, line=2.5)
    print(f"  盘口: {ou['line']}")
    print(f"  大球: {ou['over']} (概率: {ou['over_prob']*100:.1f}%)")
    print(f"  小球: {ou['under']} (概率: {ou['under_prob']*100:.1f}%)")
    
    print("\n" + "=" * 60)
    print("【实时赔率调整模拟】")
    # 模拟大量投注买美国胜
    flow = {"home": 80000, "draw": 15000, "away": 5000}
    adjusted = agent.adjust_odds_realtime(output.odds, flow, {})
    print(f"  原始赔率: {output.odds}")
    print(f"  调整后: {adjusted['odds']}")
    print(f"  调整原因: {adjusted['adjustments']}")
    
    print("\n" + "=" * 60)
    print("【与市场价格对比】")
    market = {"home": 2.07, "draw": 3.30, "away": 3.87}  # OddsPortal平均
    comparison = agent.compare_with_market(output.odds, market)
    if comparison['total_opportunities'] > 0:
        for key, val in comparison['value_opportunities'].items():
            print(f"  {key}: 市场@{val['market_odds']} vs 我们@{val['our_odds']} (edge: {val['edge']}%)")
    else:
        print("  未发现价值投注机会")
