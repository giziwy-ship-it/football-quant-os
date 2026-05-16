#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
凯利公式资金模型 - 带精算师风控

核心思想：
- 原始凯利 = 激进
- 压缩凯利（≤5%）= 能活下来
"""

from typing import Dict, Any
from core.config import config


class Kelly:
    """
    凯利公式资金管理模型
    
    风控策略：
    1. 计算原始凯利比例
    2. 应用半凯莉保守策略
    3. 压缩到最大5%（防爆仓）
    4. 限制单次最大投注为资金池10%
    """
    
    def __init__(self, bankroll: float = None):
        self.bankroll = bankroll or config.DEFAULT_BANKROLL
    
    def calculate(self, probability: float, odds: float, bankroll: float = None) -> Dict[str, Any]:
        """
        计算凯利投注建议
        
        Args:
            probability: 获胜概率 (0-1)
            odds: 赔率
            bankroll: 当前资金池
        """
        bankroll = bankroll or self.bankroll
        
        b = odds - 1
        p = probability
        q = 1 - p
        
        # 原始凯利比例
        if b <= 0:
            kelly_fraction = 0.0
        else:
            kelly_fraction = (b * p - q) / b
        
        kelly_fraction = max(0, kelly_fraction)
        
        # 半凯莉策略
        half_kelly = kelly_fraction * config.KELLY_DEFAULT_FRACTION
        
        # ⭐ 精算师风控：压缩凯利（≤5%）
        safe_fraction = min(half_kelly, config.KELLY_MAX_FRACTION)
        
        # 计算投注金额
        stake = bankroll * safe_fraction
        max_bet = bankroll * config.MAX_BET_PCT
        stake = min(stake, max_bet)
        
        # 期望收益
        expected_value = (p * odds - 1) * 100
        
        # 风险评级
        if safe_fraction >= 0.04:
            risk_level = "HIGH"
        elif safe_fraction >= 0.02:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "probability": round(probability, 4),
            "odds": odds,
            "kelly_fraction": round(kelly_fraction, 4),
            "half_kelly": round(half_kelly, 4),
            "safe_fraction": round(safe_fraction, 4),
            "stake": round(stake, 2),
            "max_bet": round(max_bet, 2),
            "expected_value": round(expected_value, 2),
            "risk_level": risk_level,
            "bankroll": bankroll
        }
    
    def batch_calculate(self, scenarios: list, bankroll: float = None) -> list:
        """批量计算多个场景"""
        return [self.calculate(s["prob"], s["odds"], bankroll) for s in scenarios]
