#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Risk & Capital Engine (RCE) v4.0
风险与资本引擎 - 对冲基金的生存线

核心功能：
1. Kelly Criterion (标准 + 分数 + 多相关)
2. 回撤保护 (Drawdown Guard)
3. 仓位上限 (Position Limits)
4. 相关性惩罚 (Correlation Penalty)
5. 资金曲线管理

Author: Naga Core Team
Version: 4.0.0
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class BankrollState:
    """资金状态"""
    current: float = 10000.0            # 当前资金
    peak: float = 10000.0               # 历史最高
    total_bet: float = 0.0              # 当前总仓位
    daily_bet: float = 0.0              # 当日投注额
    equity_curve: List[float] = field(default_factory=list)
    
    @property
    def drawdown(self) -> float:
        """当前回撤"""
        if self.peak <= 0:
            return 0.0
        return (self.peak - self.current) / self.peak
    
    @property
    def is_in_drawdown(self) -> bool:
        return self.drawdown > 0.05  # 5%回撤线


@dataclass
class Position:
    """持仓"""
    match_id: str
    direction: str                      # home/draw/away
    odds: float
    stake: float
    model_prob: float
    expected_value: float
    timestamp: datetime
    
    def potential_return(self) -> float:
        return self.stake * (self.odds - 1)
    
    def potential_loss(self) -> float:
        return self.stake


@dataclass
class RiskCheckResult:
    """风控检查结果"""
    allowed: bool
    position_size: float
    kelly_fraction: float
    risk_level: str                     # LOW / MEDIUM / HIGH / BLOCKED
    warnings: List[str] = field(default_factory=list)
    adjustments: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "allowed": self.allowed,
            "position_size": round(self.position_size, 4),
            "kelly_fraction": round(self.kelly_fraction, 4),
            "risk_level": self.risk_level,
            "warnings": self.warnings,
            "adjustments": self.adjustments
        }


class RiskEngine:
    """
    风控引擎 v4.0
    
    关键升级：
    1. Fractional Kelly (f=0.25 默认)
    2. Simultaneous bet correlation penalty
    3. Drawdown-based dynamic deleveraging
    4. Daily exposure cap
    """
    
    VERSION = "4.0.0"
    
    # 风控参数
    KELLY_FRACTION = 0.25               # 分数Kelly (标准Kelly × 0.25)
    MAX_SINGLE_BET_PCT = 0.05           # 单注最大5%
    MAX_DAILY_EXPOSURE_PCT = 0.20       # 日最大暴露20%
    MAX_TOTAL_EXPOSURE_PCT = 0.30       # 总最大暴露30%
    
    # 回撤保护
    DRAWDOWN_YELLOW = 0.10              # 10% 黄牌
    DRAWDOWN_RED = 0.15                 # 15% 红牌
    DRAWDOWN_BLACK = 0.25               # 25% 黑牌 (停盘)
    
    # Kelly调整系数
    DRAWDOWN_ADJUSTMENTS = {
        0.05: 1.0,                      # <5%: 正常
        0.10: 0.7,                      # 5-10%: 降仓30%
        0.15: 0.4,                      # 10-15%: 降仓60%
        0.25: 0.0,                      # >15%: 停止
    }
    
    def __init__(self, initial_bankroll: float = 10000.0):
        self.bankroll = BankrollState(current=initial_bankroll, peak=initial_bankroll)
        self.positions: List[Position] = []
        self.daily_stats = {
            "date": datetime.now().date(),
            "bet_count": 0,
            "total_stake": 0.0,
            "total_return": 0.0
        }
    
    def kelly(
        self,
        prob: float,
        odds: float,
        fraction: float = None
    ) -> float:
        """
        分数Kelly Criterion
        
        f* = (p × b - q) / b
        其中 b = odds - 1 (净赔率)
        
        实际仓位 = f* × fraction (默认0.25)
        """
        if odds <= 1 or prob <= 0 or prob >= 1:
            return 0.0
        
        b = odds - 1  # 净赔率
        q = 1 - prob
        
        # 标准Kelly
        kelly_full = (prob * b - q) / b
        
        if kelly_full <= 0:
            return 0.0
        
        # 分数Kelly
        frac = fraction if fraction is not None else self.KELLY_FRACTION
        return kelly_full * frac
    
    def correlated_kelly(
        self,
        bets: List[Dict[str, Any]]
    ) -> List[float]:
        """
        多相关押注的Kelly调整
        
        当同时押多场比赛时，这些押注不是独立的。
        标准Kelly会高估仓位。
        
        简化方案：
        - 假设相关性矩阵为对角阵 + 常数ρ
        - 对每注施加相关惩罚
        
        Args:
            bets: [{"prob": p, "odds": o, "correlation": ρ}, ...]
        
        Returns:
            调整后的Kelly比例列表
        """
        n = len(bets)
        if n == 0:
            return []
        
        # 计算独立Kelly
        independent_kelly = []
        for bet in bets:
            k = self.kelly(bet["prob"], bet["odds"])
            independent_kelly.append(k)
        
        if n == 1:
            return independent_kelly
        
        # 相关惩罚
        adjusted = []
        for i, bet in enumerate(bets):
            corr = bet.get("correlation", 0.0)
            
            # 相关惩罚公式：仓位 × (1 - ρ × (n-1) × 0.5)
            penalty = 1 - corr * (n - 1) * 0.3
            penalty = max(0.3, penalty)  # 最低保留30%
            
            adjusted_k = independent_kelly[i] * penalty
            adjusted.append(adjusted_k)
        
        return adjusted
    
    def drawdown_adjustment(self) -> float:
        """
        回撤动态调整
        
        根据当前回撤水平调整所有仓位
        """
        dd = self.bankroll.drawdown
        
        # 查找适用的调整系数
        adjustment = 1.0
        for threshold, adj in sorted(self.DRAWDOWN_ADJUSTMENTS.items()):
            if dd >= threshold:
                adjustment = adj
        
        return adjustment
    
    def check(
        self,
        match_id: str,
        direction: str,
        odds: float,
        model_prob: float,
        expected_value: float,
        correlation_with_existing: float = 0.0
    ) -> RiskCheckResult:
        """
        主风控检查
        
        Args:
            match_id: 比赛ID
            direction: 方向
            odds: 赔率
            model_prob: 模型概率
            expected_value: 期望收益
            correlation_with_existing: 与现有持仓的相关性
        
        Returns:
            RiskCheckResult
        """
        warnings = []
        adjustments = []
        
        # 1. 计算Kelly仓位
        kelly_frac = self.kelly(model_prob, odds)
        
        # 2. 回撤调整
        dd_adj = self.drawdown_adjustment()
        if dd_adj < 1.0:
            adjustments.append(f"回撤保护: 当前回撤{self.bankroll.drawdown:.1%} → Kelly×{dd_adj:.0%}")
        
        # 3. 相关惩罚
        corr_penalty = 1 - correlation_with_existing * 0.3
        corr_penalty = max(0.5, corr_penalty)
        if correlation_with_existing > 0:
            adjustments.append(f"相关惩罚: ρ={correlation_with_existing:.2f} → Kelly×{corr_penalty:.0%}")
        
        # 4. 综合调整
        adjusted_kelly = kelly_frac * dd_adj * corr_penalty
        
        # 5. 硬顶限制
        position_size = adjusted_kelly * self.bankroll.current
        
        # 单注上限
        max_single = self.bankroll.current * self.MAX_SINGLE_BET_PCT
        if position_size > max_single:
            position_size = max_single
            adjustments.append(f"触及单注上限: {self.MAX_SINGLE_BET_PCT:.0%}")
        
        # 日暴露上限
        daily_exposure = self.daily_stats["total_stake"] + position_size
        max_daily = self.bankroll.current * self.MAX_DAILY_EXPOSURE_PCT
        if daily_exposure > max_daily:
            position_size = max(0, max_daily - self.daily_stats["total_stake"])
            adjustments.append(f"触及日暴露上限: {self.MAX_DAILY_EXPOSURE_PCT:.0%}")
        
        # 总暴露上限
        total_exposure = sum(p.stake for p in self.positions) + position_size
        max_total = self.bankroll.current * self.MAX_TOTAL_EXPOSURE_PCT
        if total_exposure > max_total:
            position_size = max(0, max_total - sum(p.stake for p in self.positions))
            adjustments.append(f"触及总暴露上限: {self.MAX_TOTAL_EXPOSURE_PCT:.0%}")
        
        # 6. 拦截条件
        risk_level = "LOW"
        allowed = True
        
        # EV 检查
        if expected_value < -0.05:
            warnings.append(f"负期望: EV={expected_value:+.1%}")
            risk_level = "HIGH"
            allowed = False
        elif expected_value < 0.03:
            warnings.append(f"薄利: EV={expected_value:+.1%}")
            risk_level = "MEDIUM"
        
        # 赔率价值检查
        if odds < 1.3:
            warnings.append(f"超低赔率: {odds} (价值不足)")
            risk_level = "HIGH"
        
        # 回撤拦截
        if self.bankroll.drawdown > self.DRAWDOWN_RED:
            warnings.append(f"严重回撤: {self.bankroll.drawdown:.1%} → 停止交易")
            risk_level = "BLOCKED"
            allowed = False
        elif self.bankroll.drawdown > self.DRAWDOWN_YELLOW:
            warnings.append(f"中度回撤: {self.bankroll.drawdown:.1%} → 降仓")
            risk_level = "HIGH"
        
        # 概率合理性
        if model_prob < 0.15 and odds > 5:
            warnings.append("低概率高赔率: 可能是陷阱")
        
        return RiskCheckResult(
            allowed=allowed and position_size > 0,
            position_size=position_size,
            kelly_fraction=adjusted_kelly,
            risk_level=risk_level,
            warnings=warnings,
            adjustments=adjustments
        )
    
    def execute_bet(
        self,
        position: Position,
        result: RiskCheckResult
    ) -> bool:
        """
        执行投注
        
        更新资金状态和持仓列表
        """
        if not result.allowed or result.position_size <= 0:
            return False
        
        position.stake = result.position_size
        self.positions.append(position)
        
        self.bankroll.current -= position.stake
        self.bankroll.total_bet += position.stake
        self.daily_stats["total_stake"] += position.stake
        self.daily_stats["bet_count"] += 1
        
        return True
    
    def settle_bet(
        self,
        match_id: str,
        won: bool
    ) -> float:
        """
        结算投注
        
        Args:
            match_id: 比赛ID
            won: 是否赢
        
        Returns:
            净盈亏
        """
        # 找到对应持仓
        position = None
        for i, p in enumerate(self.positions):
            if p.match_id == match_id:
                position = p
                idx = i
                break
        
        if not position:
            return 0.0
        
        if won:
            profit = position.potential_return()
            self.bankroll.current += position.stake + profit
            self.daily_stats["total_return"] += profit
            pnl = profit
        else:
            pnl = -position.stake
            self.daily_stats["total_return"] += pnl
        
        # 移除持仓
        self.positions.pop(idx)
        self.bankroll.total_bet -= position.stake
        
        # 更新峰值
        if self.bankroll.current > self.bankroll.peak:
            self.bankroll.peak = self.bankroll.current
        
        # 记录权益曲线
        self.bankroll.equity_curve.append(self.bankroll.current)
        
        return pnl
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """获取组合摘要"""
        total_stake = sum(p.stake for p in self.positions)
        total_exposure = total_stake / self.bankroll.current if self.bankroll.current > 0 else 0
        
        return {
            "bankroll": {
                "current": round(self.bankroll.current, 2),
                "peak": round(self.bankroll.peak, 2),
                "drawdown": round(self.bankroll.drawdown, 4),
                "is_in_drawdown": self.bankroll.is_in_drawdown
            },
            "positions": {
                "count": len(self.positions),
                "total_stake": round(total_stake, 2),
                "exposure_pct": round(total_exposure, 4)
            },
            "daily": {
                "bet_count": self.daily_stats["bet_count"],
                "total_stake": round(self.daily_stats["total_stake"], 2),
                "total_return": round(self.daily_stats["total_return"], 2)
            },
            "limits": {
                "max_single": f"{self.MAX_SINGLE_BET_PCT:.0%}",
                "max_daily": f"{self.MAX_DAILY_EXPOSURE_PCT:.0%}",
                "max_total": f"{self.MAX_TOTAL_EXPOSURE_PCT:.0%}"
            }
        }


# ============ 快速测试 ============
if __name__ == "__main__":
    engine = RiskEngine(initial_bankroll=10000)
    
    # 测试1: 标准Kelly
    print("=== 测试1: 标准Kelly ===")
    k = engine.kelly(prob=0.55, odds=1.85)
    print(f"P=0.55, O=1.85 → Kelly={k:.2%} (分数: {k*4:.2%})")
    
    # 测试2: 风控检查
    print("\n=== 测试2: 风控检查 ===")
    result = engine.check(
        match_id="WC2026-001",
        direction="home",
        odds=1.85,
        model_prob=0.55,
        expected_value=0.0175,
        correlation_with_existing=0.0
    )
    print(f"允许: {result.allowed}")
    print(f"仓位: ¥{result.position_size:.2f}")
    print(f"风险等级: {result.risk_level}")
    print(f"警告: {result.warnings}")
    print(f"调整: {result.adjustments}")
    
    # 测试3: 回撤保护
    print("\n=== 测试3: 回撤保护 ===")
    engine.bankroll.current = 8500  # 模拟15%回撤
    result3 = engine.check(
        match_id="WC2026-002",
        direction="away",
        odds=3.5,
        model_prob=0.30,
        expected_value=0.05,
        correlation_with_existing=0.2
    )
    print(f"回撤: {engine.bankroll.drawdown:.1%}")
    print(f"允许: {result3.allowed}")
    print(f"调整: {result3.adjustments}")
    
    # 测试4: 组合摘要
    print("\n=== 测试4: 组合摘要 ===")
    summary = engine.get_portfolio_summary()
    print(f"资金: ¥{summary['bankroll']['current']}")
    print(f"回撤: {summary['bankroll']['drawdown']:.1%}")
