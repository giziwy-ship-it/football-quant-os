#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Market Microstructure Engine (MME) v4.0
市场微结构引擎 - 赔率变动的深层解读

核心洞察：不是看赔率"是多少"，而是看赔率"怎么变"

Author: Naga Core Team
Version: 4.0.0
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class OddsMovementType(Enum):
    """赔率变动类型"""
    STABLE = "stable"              # 稳定
    DRIFT = "drift"                # 缓慢漂移
    STEAM = "steam"                #  steam (同向大量涌入)
    REVERSE = "reverse"            # 逆向变动
    SPIKE = "spike"                # 突刺（短时大幅变动）
    PLUNGE = "plunge"              #  plunging (快速单向)


class MarketBias(Enum):
    """市场偏向"""
    BALANCED = "balanced"          # 均衡
    HEAVY_HOME = "heavy_home"      #  Heavy主胜
    HEAVY_AWAY = "heavy_away"      #  Heavy客胜
    HEAVY_DRAW = "heavy_draw"      #  Heavy平局
    SHARP_HOME = "sharp_home"      #  Sharp主
    SHARP_AWAY = "sharp_away"      #  Sharp客
    TRAP_HOME = "trap_home"        # 诱主
    TRAP_AWAY = "trap_away"        # 诱客
    CHAOS = "chaos"                # 混沌


@dataclass
class OddsSnapshot:
    """赔率快照"""
    timestamp: datetime
    home_odds: float
    draw_odds: float
    away_odds: float
    home_prob: float = 0.0
    draw_prob: float = 0.0
    away_prob: float = 0.0
    volume: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "odds": {"home": self.home_odds, "draw": self.draw_odds, "away": self.away_odds},
            "probabilities": {"home": self.home_prob, "draw": self.draw_prob, "away": self.away_prob},
            "volume": self.volume
        }


@dataclass
class MicrostructureSignal:
    """微结构信号"""
    movement_type: OddsMovementType
    market_bias: MarketBias
    momentum: Dict[str, float]          # 各方向动量
    liquidity_pressure: float           # 流动性压力 0-1
    smart_money_flow: float             # 聪明钱流向 -1~1
    divergence_score: float             # 分歧度 0-1
    sync_score: float                   # 同步性 0-1
    acceleration: Dict[str, float]      # 加速度
    recommendation: str                 # 建议
    confidence: float = 0.0
    
    def to_dict(self) -> Dict:
        return {
            "movement_type": self.movement_type.value,
            "market_bias": self.market_bias.value,
            "momentum": self.momentum,
            "liquidity_pressure": round(self.liquidity_pressure, 4),
            "smart_money_flow": round(self.smart_money_flow, 4),
            "divergence_score": round(self.divergence_score, 4),
            "sync_score": round(self.sync_score, 4),
            "acceleration": self.acceleration,
            "recommendation": self.recommendation,
            "confidence": round(self.confidence, 4)
        }


class MarketMicrostructure:
    """
    市场微结构引擎 v4.0
    
    核心算法：
    1. 赔率动量 = 赔率序列的一阶导数
    2. 流动性压力 = tanh(交易量 / 基准)
    3. 聪明钱流向 = 动量 × 流动性压力 × 方向因子
    4. 分歧度 = 各公司赔率标准差 / 均值
    5. 同步性 = 同向变动公司比例
    """
    
    VERSION = "4.0.0"
    
    def __init__(self):
        self.odds_history: List[OddsSnapshot] = []
        self.max_history = 100
    
    def add_snapshot(self, snapshot: OddsSnapshot):
        """添加赔率快照"""
        self.odds_history.append(snapshot)
        if len(self.odds_history) > self.max_history:
            self.odds_history.pop(0)
    
    def odds_momentum(
        self,
        direction: str = "home",
        window: int = 5
    ) -> float:
        """
        赔率动量 - 一阶导数
        
        Args:
            direction: "home", "draw", "away"
            window: 计算窗口
        
        Returns:
            动量值 (正=赔率上升=不被看好, 负=赔率下降=被看好)
        """
        if len(self.odds_history) < window + 1:
            return 0.0
        
        recent = self.odds_history[-window:]
        odds_series = np.array([getattr(s, f"{direction}_odds") for s in recent])
        
        # 线性回归斜率
        x = np.arange(len(odds_series))
        slope = np.polyfit(x, odds_series, 1)[0]
        
        # 标准化
        avg_odds = np.mean(odds_series)
        if avg_odds > 0:
            normalized_slope = slope / avg_odds
        else:
            normalized_slope = 0
        
        return normalized_slope
    
    def liquidity_pressure(self, volume: float, baseline: float = 10000) -> float:
        """
        流动性压力
        
        Args:
            volume: 当前交易量
            baseline: 基准交易量
        
        Returns:
            压力值 0-1
        """
        return float(np.tanh(volume / baseline))
    
    def smart_money_flow(
        self,
        direction: str = "home",
        volume: float = 0
    ) -> float:
        """
        聪明钱流向指标
        
        核心假设：大额交易驱动赔率变动 = 知情交易
        公式：SMF = odds_momentum × liquidity_pressure × sign(momentum)
        
        正 = 聪明钱流向该方向 (赔率下降 = 被看好)
        负 = 聪明钱逃离该方向
        """
        momentum = self.odds_momentum(direction)
        pressure = self.liquidity_pressure(volume)
        
        # 赔率下降（动量负）= 被看好 = 正流向
        flow = -momentum * pressure * 10  # 放大信号
        return float(np.tanh(flow))
    
    def divergence_score(
        self,
        bookmaker_odds: List[Dict[str, float]]
    ) -> float:
        """
        市场分歧度
        
        不同公司赔率的标准差 / 均值
        高分歧 = 价格发现阶段 或 信息不对称
        """
        if len(bookmaker_odds) < 2:
            return 0.0
        
        home_odds = [b["home"] for b in bookmaker_odds]
        draw_odds = [b["draw"] for b in bookmaker_odds]
        away_odds = [b["away"] for b in bookmaker_odds]
        
        def calc_div(odds_list):
            arr = np.array(odds_list)
            mean = np.mean(arr)
            std = np.std(arr)
            return std / mean if mean > 0 else 0
        
        div_home = calc_div(home_odds)
        div_draw = calc_div(draw_odds)
        div_away = calc_div(away_odds)
        
        return float(np.mean([div_home, div_draw, div_away]))
    
    def sync_score(
        self,
        movements: List[Dict[str, float]]
    ) -> float:
        """
        市场同步性
        
        各公司同向变动的比例
        >0.7: 高度一致（市场共识）
        <0.4: 严重分歧（拉扯/诱导）
        """
        if not movements:
            return 0.5
        
        # 计算各方向的同向比例
        home_moves = [m.get("home", 0) for m in movements]
        away_moves = [m.get("away", 0) for m in movements]
        
        def sync_ratio(moves):
            pos = sum(1 for m in moves if m > 0.001)
            neg = sum(1 for m in moves if m < -0.001)
            total = len(moves)
            if total == 0:
                return 0.5
            return max(pos, neg) / total
        
        home_sync = sync_ratio(home_moves)
        away_sync = sync_ratio(away_moves)
        
        return float(np.mean([home_sync, away_sync]))
    
    def detect_movement_type(
        self,
        window: int = 5
    ) -> OddsMovementType:
        """检测赔率变动类型"""
        if len(self.odds_history) < window + 1:
            return OddsMovementType.STABLE
        
        recent = self.odds_history[-window:]
        home_series = [s.home_odds for s in recent]
        
        # 计算变化特征
        changes = [home_series[i+1] - home_series[i] for i in range(len(home_series)-1)]
        avg_change = np.mean(np.abs(changes))
        max_change = np.max(np.abs(changes))
        
        # 方向一致性
        pos_changes = sum(1 for c in changes if c > 0)
        neg_changes = sum(1 for c in changes if c < 0)
        direction_consistency = max(pos_changes, neg_changes) / len(changes) if changes else 0
        
        if max_change > avg_change * 3 and max_change > 0.1:
            return OddsMovementType.SPIKE
        elif avg_change > 0.05:
            if direction_consistency > 0.8:
                return OddsMovementType.PLUNGE
            else:
                return OddsMovementType.CHAOS
        elif avg_change > 0.02:
            if direction_consistency > 0.7:
                return OddsMovementType.STEAM
            else:
                return OddsMovementType.DRIFT
        elif any(c * changes[i-1] < 0 for i, c in enumerate(changes[1:], 1)):
            return OddsMovementType.REVERSE
        
        return OddsMovementType.STABLE
    
    def detect_market_bias(
        self,
        model_probs: Dict[str, float],
        market_probs: Dict[str, float]
    ) -> MarketBias:
        """
        检测市场偏向/诱盘
        
        对比模型概率与市场概率的偏离：
        - 市场明显偏向某方向但模型不支持 = 诱盘
        - 市场与模型一致 = 共识
        - 市场极度偏向 = 可能有内幕
        """
        home_dev = market_probs["home"] - model_probs["home"]
        draw_dev = market_probs["draw"] - model_probs["draw"]
        away_dev = market_probs["away"] - model_probs["away"]
        
        # 检测诱盘：市场概率显著高于模型概率
        trap_threshold = 0.08
        
        if home_dev > trap_threshold and model_probs["home"] < 0.45:
            return MarketBias.TRAP_HOME
        elif away_dev > trap_threshold and model_probs["away"] < 0.45:
            return MarketBias.TRAP_AWAY
        
        # 检测 Heavy 偏向
        heavy_threshold = 0.15
        if market_probs["home"] > model_probs["home"] + heavy_threshold:
            return MarketBias.HEAVY_HOME
        elif market_probs["away"] > model_probs["away"] + heavy_threshold:
            return MarketBias.HEAVY_AWAY
        elif market_probs["draw"] > model_probs["draw"] + heavy_threshold:
            return MarketBias.HEAVY_DRAW
        
        # Sharp 偏向 (市场与模型背离但可能 market 更对)
        sharp_threshold = 0.1
        if home_dev < -sharp_threshold:
            return MarketBias.SHARP_HOME
        elif away_dev < -sharp_threshold:
            return MarketBias.SHARP_AWAY
        
        return MarketBias.BALANCED
    
    def analyze(
        self,
        model_probs: Dict[str, float],
        market_probs: Dict[str, float],
        bookmaker_odds: List[Dict[str, float]] = None,
        volume: float = 0
    ) -> MicrostructureSignal:
        """
        主分析入口
        
        Args:
            model_probs: 模型概率 {"home": p, "draw": p, "away": p}
            market_probs: 市场概率
            bookmaker_odds: 各公司赔率列表
            volume: 交易量
        
        Returns:
            MicrostructureSignal
        """
        # 动量
        momentum = {
            "home": self.odds_momentum("home"),
            "draw": self.odds_momentum("draw"),
            "away": self.odds_momentum("away")
        }
        
        # 流动性压力
        pressure = self.liquidity_pressure(volume)
        
        # 聪明钱流向
        smf_home = self.smart_money_flow("home", volume)
        smf_away = self.smart_money_flow("away", volume)
        
        # 分歧度
        div = self.divergence_score(bookmaker_odds) if bookmaker_odds else 0.0
        
        # 同步性 (简化：基于历史变动)
        movements = []
        if len(self.odds_history) >= 2:
            for i in range(1, min(10, len(self.odds_history))):
                prev = self.odds_history[-i-1]
                curr = self.odds_history[-i]
                movements.append({
                    "home": curr.home_odds - prev.home_odds,
                    "away": curr.away_odds - prev.away_odds
                })
        sync = self.sync_score(movements)
        
        # 变动类型
        move_type = self.detect_movement_type()
        
        # 市场偏向
        bias = self.detect_market_bias(model_probs, market_probs)
        
        # 加速度
        acceleration = {
            "home": self.odds_momentum("home", 3) - self.odds_momentum("home", 10),
            "away": self.odds_momentum("away", 3) - self.odds_momentum("away", 10)
        }
        
        # 生成建议
        recommendation = self._generate_recommendation(
            move_type, bias, smf_home, smf_away, div, sync
        )
        
        # 置信度
        confidence = self._calculate_confidence(move_type, sync, div)
        
        return MicrostructureSignal(
            movement_type=move_type,
            market_bias=bias,
            momentum=momentum,
            liquidity_pressure=pressure,
            smart_money_flow=smf_home - smf_away,  # 净流向
            divergence_score=div,
            sync_score=sync,
            acceleration=acceleration,
            recommendation=recommendation,
            confidence=confidence
        )
    
    def _generate_recommendation(
        self,
        move_type: OddsMovementType,
        bias: MarketBias,
        smf_home: float,
        smf_away: float,
        div: float,
        sync: float
    ) -> str:
        """生成交易建议"""
        if bias in (MarketBias.TRAP_HOME, MarketBias.TRAP_AWAY):
            return f"⚠️ 诱盘检测: {bias.value} - 建议反向或观望"
        
        if move_type == OddsMovementType.STEAM:
            if smf_home > 0.3:
                return "🔥 主胜 steam - 聪明钱涌入"
            elif smf_away > 0.3:
                return "🔥 客胜 steam - 聪明钱涌入"
        
        if move_type == OddsMovementType.SPIKE:
            return "⚡ 赔率突刺 - 可能有内幕消息，谨慎"
        
        if div > 0.1 and sync < 0.4:
            return "🌊 市场严重分歧 - 价格发现阶段，观望"
        
        if bias in (MarketBias.SHARP_HOME, MarketBias.SHARP_AWAY):
            return f"📉 Sharp偏向: {bias.value} - 模型可能低估了"
        
        if sync > 0.8:
            return "✅ 市场高度共识 - 跟随市场"
        
        return "➖ 无显著信号 - 按模型执行"
    
    def _calculate_confidence(
        self,
        move_type: OddsMovementType,
        sync: float,
        div: float
    ) -> float:
        """计算信号置信度"""
        base = 0.5
        
        if move_type in (OddsMovementType.STEAM, OddsMovementType.PLUNGE):
            base += 0.2
        elif move_type in (OddsMovementType.SPIKE, OddsMovementType.CHAOS):
            base -= 0.2
        
        # 同步性越高越可信
        base += sync * 0.2
        
        # 分歧度越低越可信
        base -= div * 0.5
        
        return float(np.clip(base, 0.1, 0.95))


# ============ 快速测试 ============
if __name__ == "__main__":
    mme = MarketMicrostructure()
    
    # 模拟历史赔率
    import random
    random.seed(42)
    base_h, base_d, base_a = 1.8, 3.5, 4.2
    
    for i in range(20):
        # 模拟主胜赔率缓慢下降（被看好）
        home_odds = base_h - i * 0.02 + random.gauss(0, 0.01)
        away_odds = base_a + i * 0.01 + random.gauss(0, 0.02)
        draw_odds = base_d + random.gauss(0, 0.01)
        
        snapshot = OddsSnapshot(
            timestamp=datetime.now() + timedelta(minutes=i*5),
            home_odds=max(1.01, home_odds),
            draw_odds=max(1.01, draw_odds),
            away_odds=max(1.01, away_odds)
        )
        mme.add_snapshot(snapshot)
    
    model_probs = {"home": 0.55, "draw": 0.25, "away": 0.20}
    market_probs = {"home": 0.58, "draw": 0.23, "away": 0.19}
    
    signal = mme.analyze(model_probs, market_probs, volume=15000)
    
    print("=== Market Microstructure v4.0 测试 ===")
    for k, v in signal.to_dict().items():
        print(f"{k}: {v}")
