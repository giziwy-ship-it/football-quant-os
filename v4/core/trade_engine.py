#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Signal & Trade Engine (STE) v4.0
信号与交易引擎 - 从概率到交易决策

核心逻辑：
- VALUE BET: 模型概率 × 赔率 > 1 + margin
- HEDGE: 市场与模型背离时的对冲
- ARBITRAGE: 跨市场套利
- UPSET PLAY: 高冷门风险时的高赔率博弈

Author: Naga Core Team
Version: 4.0.0
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class TradeSignal(Enum):
    """交易信号"""
    VALUE_BET = "value_bet"              # 价值投注
    STRONG_VALUE = "strong_value"        # 强价值
    HEDGE = "hedge"                      # 对冲
    ARBITRAGE = "arbitrage"              # 套利
    UPSET_PLAY = "upset_play"            # 冷门博弈
    AVOID = "avoid"                      # 回避
    NO_TRADE = "no_trade"               # 不交易
    SHARP_FADE = "sharp_fade"           # 反向 sharp


class TradeDirection(Enum):
    """交易方向"""
    HOME = "home"
    DRAW = "draw"
    AWAY = "away"
    BOTH_SIDES = "both_sides"           # 对冲


@dataclass
class TradeDecision:
    """交易决策"""
    signal: TradeSignal
    direction: TradeDirection
    stake_pct: float                    # 仓位百分比
    expected_value: float               # 期望收益
    odds: float                         # 投注赔率
    probability: float                  # 模型概率
    market_prob: float                  # 市场概率
    upside: float                       # 上行空间
    downside: float                     # 下行风险
    rationale: str                      # 决策理由
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "signal": self.signal.value,
            "direction": self.direction.value,
            "stake_pct": round(self.stake_pct, 4),
            "expected_value": round(self.expected_value, 4),
            "odds": self.odds,
            "probability": round(self.probability, 4),
            "market_prob": round(self.market_prob, 4),
            "upside": round(self.upside, 4),
            "downside": round(self.downside, 4),
            "rationale": self.rationale,
            "confidence": round(self.confidence, 4)
        }


class TradingEngine:
    """
    交易引擎 v4.0
    
    核心公式：
    EV = P_model × Odds - 1
    
    信号矩阵：
    EV > 0.10 + 高置信度 → STRONG_VALUE
    EV > 0.05 → VALUE_BET
    EV < -0.10 → AVOID (市场已充分定价)
    诱盘信号 → SHARP_FADE (反向)
    冷门风险 > 0.7 → UPSET_PLAY (高赔率方向)
    """
    
    VERSION = "4.0.0"
    
    # 信号阈值
    STRONG_VALUE_THRESHOLD = 0.10
    VALUE_THRESHOLD = 0.05
    AVOID_THRESHOLD = -0.10
    UPSET_EV_THRESHOLD = 0.15
    
    def __init__(self):
        pass
    
    def calculate_ev(
        self,
        prob: float,
        odds: float
    ) -> float:
        """
        计算期望收益
        EV = P × O - 1
        
        Returns:
            EV > 0: 正期望
            EV < 0: 负期望
        """
        return prob * odds - 1
    
    def calculate_edge(
        self,
        model_prob: float,
        market_prob: float
    ) -> float:
        """
        计算 edge（模型 vs 市场）
        edge = model_prob - market_prob
        
        正 edge = 模型比市场更看好
        负 edge = 市场比模型更看好
        """
        return model_prob - market_prob
    
    def signal(
        self,
        probs: Dict[str, float],
        odds: Dict[str, float],
        upset_score: float = 0.0,
        market_bias: str = "balanced",
        confidence: float = 0.7
    ) -> Dict[str, Any]:
        """
        主信号生成方法
        
        Args:
            probs: 模型概率 {"home": p, "draw": p, "away": p}
            odds: 赔率 {"home": o, "draw": o, "away": o}
            upset_score: 冷门分数 0-1
            market_bias: 市场偏向 (来自 MME)
            confidence: 模型置信度
        
        Returns:
            完整交易信号分析
        """
        results = {}
        best_ev = -999
        best_direction = None
        
        for direction in ["home", "draw", "away"]:
            if direction not in probs or direction not in odds:
                continue
            
            p = probs[direction]
            o = odds[direction]
            
            ev = self.calculate_ev(p, o)
            market_prob = 1 / o  # 简化：假设无抽水
            edge = self.calculate_edge(p, market_prob)
            
            results[direction] = {
                "probability": p,
                "odds": o,
                "ev": round(ev, 4),
                "edge": round(edge, 4),
                "market_prob": round(market_prob, 4)
            }
            
            if ev > best_ev:
                best_ev = ev
                best_direction = direction
        
        # 确定交易信号
        signal_type, trade_dir, stake, rationale = self._determine_signal(
            results, best_direction, best_ev, upset_score, market_bias, confidence
        )
        
        # 计算上下行
        best_result = results.get(best_direction, {})
        upside = best_ev if best_ev > 0 else 0
        downside = -1.0  # 最坏情况：全亏
        
        return {
            "signal": signal_type.value,
            "direction": trade_dir.value if trade_dir else None,
            "best_ev": round(best_ev, 4),
            "best_direction": best_direction,
            "stake_pct": round(stake, 4),
            "expected_value": round(best_ev, 4),
            "upside": round(upside, 4),
            "downside": downside,
            "rationale": rationale,
            "confidence": round(confidence, 4),
            "details": results,
            "upset_score": upset_score,
            "market_bias": market_bias
        }
    
    def _determine_signal(
        self,
        results: Dict,
        best_dir: str,
        best_ev: float,
        upset_score: float,
        market_bias: str,
        confidence: float
    ) -> Tuple[TradeSignal, Optional[TradeDirection], float, str]:
        """
        确定交易信号
        
        决策树：
        1. 诱盘 → SHARP_FADE (反向)
        2. 冷门风险高 + 高赔率方向有正EV → UPSET_PLAY
        3. EV > 0.10 → STRONG_VALUE
        4. EV > 0.05 → VALUE_BET
        5. EV < -0.10 → AVOID
        6. 其他 → NO_TRADE
        """
        # 诱盘检测
        if "trap" in market_bias.lower():
            # 反向操作
            trap_dir = "home" if "home" in market_bias.lower() else "away"
            opposite = "away" if trap_dir == "home" else "home"
            opp_result = results.get(opposite, {})
            opp_ev = opp_result.get("ev", -1)
            
            if opp_ev > 0:
                return (
                    TradeSignal.SHARP_FADE,
                    TradeDirection(opposite),
                    min(0.03, opp_ev * 0.5),
                    f"诱盘检测: {market_bias} → 反向 {opposite} (EV={opp_ev:+.1%})"
                )
            else:
                return (
                    TradeSignal.AVOID,
                    None,
                    0.0,
                    f"诱盘检测: {market_bias} → 反向无正EV，回避"
                )
        
        # 冷门博弈
        if upset_score > 0.7:
            # 找高赔率方向
            for direction in ["away", "draw", "home"]:
                r = results.get(direction, {})
                if r.get("odds", 0) > 3.0 and r.get("ev", -1) > -0.05:
                    return (
                        TradeSignal.UPSET_PLAY,
                        TradeDirection(direction),
                        0.02,
                        f"冷门博弈: 高冷门风险({upset_score:.2f}) + 高赔率({r['odds']})"
                    )
        
        # 标准信号
        if best_ev > self.STRONG_VALUE_THRESHOLD and confidence > 0.7:
            stake = min(best_ev * 0.8, 0.08)
            return (
                TradeSignal.STRONG_VALUE,
                TradeDirection(best_dir),
                stake,
                f"强价值信号: {best_dir} EV={best_ev:+.1%}"
            )
        elif best_ev > self.VALUE_THRESHOLD:
            stake = min(best_ev * 0.6, 0.05)
            return (
                TradeSignal.VALUE_BET,
                TradeDirection(best_dir),
                stake,
                f"价值信号: {best_dir} EV={best_ev:+.1%}"
            )
        elif best_ev < self.AVOID_THRESHOLD:
            return (
                TradeSignal.AVOID,
                None,
                0.0,
                f"市场过度定价: 最高EV仅{best_ev:+.1%}，无价值"
            )
        else:
            return (
                TradeSignal.NO_TRADE,
                None,
                0.0,
                f"无显著信号: 最高EV={best_ev:+.1%}"
            )
    
    def arbitrage_scan(
        self,
        odds_by_bookmaker: Dict[str, Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        """
        套利扫描
        
        检查是否存在跨公司套利机会：
        1/home_best + 1/draw_best + 1/away_best < 1
        """
        arbitrage_opps = []
        
        # 找出各方向最佳赔率
        best_odds = {"home": [], "draw": [], "away": []}
        for bookmaker, odds in odds_by_bookmaker.items():
            for direction in ["home", "draw", "away"]:
                if direction in odds:
                    best_odds[direction].append((bookmaker, odds[direction]))
        
        # 排序
        for direction in best_odds:
            best_odds[direction].sort(key=lambda x: x[1], reverse=True)
        
        # 检查套利 (简化：只检查最佳组合)
        if all(len(best_odds[d]) > 0 for d in ["home", "draw", "away"]):
            h_book, h_odds = best_odds["home"][0]
            d_book, d_odds = best_odds["draw"][0]
            a_book, a_odds = best_odds["away"][0]
            
            arb_value = 1/h_odds + 1/d_odds + 1/a_odds
            
            if arb_value < 1:
                profit = (1 - arb_value) * 100
                arbitrage_opps.append({
                    "type": "sure_bet",
                    "profit_pct": round(profit, 2),
                    "combination": {
                        "home": {"bookmaker": h_book, "odds": h_odds},
                        "draw": {"bookmaker": d_book, "odds": d_odds},
                        "away": {"bookmaker": a_book, "odds": a_odds}
                    },
                    "arb_value": round(arb_value, 4)
                })
        
        return arbitrage_opps
    
    def multi_market_synthesis(
        self,
        predictions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        多市场综合
        
        综合1x2、让球、大小球的信号，找出最优投注组合
        """
        # 简化版：找出各市场最佳EV
        best_by_market = {}
        
        for market, pred in predictions.items():
            best_ev = -999
            best_dir = None
            for direction, data in pred.get("details", {}).items():
                ev = data.get("ev", -999)
                if ev > best_ev:
                    best_ev = ev
                    best_dir = direction
            
            best_by_market[market] = {
                "direction": best_dir,
                "ev": best_ev,
                "market": market
            }
        
        # 排序找出最优
        sorted_markets = sorted(
            best_by_market.values(),
            key=lambda x: x["ev"],
            reverse=True
        )
        
        return {
            "best_market": sorted_markets[0] if sorted_markets else None,
            "all_markets": sorted_markets,
            "recommendation": f"优先投注: {sorted_markets[0]['market']} {sorted_markets[0]['direction']}"
            if sorted_markets else "无正EV市场"
        }


# ============ 快速测试 ============
if __name__ == "__main__":
    engine = TradingEngine()
    
    # 测试1: 标准价值投注
    print("=== 测试1: 价值投注 ===")
    result1 = engine.signal(
        probs={"home": 0.55, "draw": 0.25, "away": 0.20},
        odds={"home": 1.85, "draw": 3.6, "away": 4.5},
        upset_score=0.3,
        market_bias="balanced",
        confidence=0.75
    )
    print(f"信号: {result1['signal']} | 方向: {result1['direction']} | 仓位: {result1['stake_pct']:.1%}")
    print(f"理由: {result1['rationale']}")
    
    # 测试2: 诱盘
    print("\n=== 测试2: 诱盘 ===")
    result2 = engine.signal(
        probs={"home": 0.40, "draw": 0.30, "away": 0.30},
        odds={"home": 1.50, "draw": 3.8, "away": 6.0},
        upset_score=0.5,
        market_bias="trap_home",
        confidence=0.7
    )
    print(f"信号: {result2['signal']} | 方向: {result2['direction']} | 仓位: {result2['stake_pct']:.1%}")
    print(f"理由: {result2['rationale']}")
    
    # 测试3: 冷门博弈
    print("\n=== 测试3: 冷门博弈 ===")
    result3 = engine.signal(
        probs={"home": 0.60, "draw": 0.22, "away": 0.18},
        odds={"home": 1.55, "draw": 4.0, "away": 5.5},
        upset_score=0.75,
        market_bias="balanced",
        confidence=0.6
    )
    print(f"信号: {result3['signal']} | 方向: {result3['direction']} | 仓位: {result3['stake_pct']:.1%}")
    print(f"理由: {result3['rationale']}")
    
    # 测试4: 套利扫描
    print("\n=== 测试4: 套利扫描 ===")
    odds_data = {
        "bet365": {"home": 1.90, "draw": 3.50, "away": 4.20},
        "pinnacle": {"home": 1.95, "draw": 3.40, "away": 4.50},
        "betfair": {"home": 1.92, "draw": 3.60, "away": 4.10},
    }
    arbs = engine.arbitrage_scan(odds_data)
    if arbs:
        print(f"发现套利! 利润: {arbs[0]['profit_pct']:.2f}%")
    else:
        print("无套利机会")
