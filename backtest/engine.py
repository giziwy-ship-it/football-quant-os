#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
回测引擎 - Football Quant OS
核心闭环验证工具
"""

import json
import os
from typing import Dict, List, Any
from models.kelly import Kelly


class BacktestEngine:
    """
    回测引擎
    
    支持策略：
    - kelly_compressed: 压缩凯利（≤5%）
    - kelly_half: 半凯莉
    - kelly_full: 原始凯利
    - flat: 固定金额
    """
    
    def __init__(self, bankroll: float = 1000, strategy: str = "kelly_compressed"):
        self.initial_bankroll = bankroll
        self.bankroll = bankroll
        self.strategy = strategy
        self.history = []
        self.trades = []
    
    def run(self, path: str = "data/backtest_dataset.json") -> Dict[str, Any]:
        """运行回测"""
        
        if not os.path.exists(path):
            # 尝试相对路径
            base_dir = os.path.dirname(os.path.dirname(__file__))
            path = os.path.join(base_dir, path)
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        kelly = Kelly(bankroll=self.bankroll)
        
        for match in data:
            prob = match["prob"]
            odds = match["odds"]
            result = match["result"]
            
            # 计算投注
            if self.strategy == "flat":
                stake = self.initial_bankroll * 0.02  # 固定2%
                bet_info = {"stake": stake, "safe_fraction": 0.02}
            else:
                bet_info = kelly.calculate(prob, odds, self.bankroll)
                
                if self.strategy == "kelly_half":
                    stake = self.bankroll * bet_info["half_kelly"]
                elif self.strategy == "kelly_full":
                    stake = self.bankroll * bet_info["kelly_fraction"]
                else:  # kelly_compressed
                    stake = bet_info["stake"]
            
            stake = min(stake, self.bankroll)  # 不能超仓
            
            # 结算
            if result == "win":
                profit = stake * (odds - 1)
                self.bankroll += profit
                trade_result = "win"
            else:
                self.bankroll -= stake
                trade_result = "loss"
            
            self.trades.append({
                "match_id": match.get("match_id"),
                "stake": round(stake, 2),
                "odds": odds,
                "prob": prob,
                "result": trade_result,
                "bankroll_after": round(self.bankroll, 2)
            })
            self.history.append(round(self.bankroll, 2))
        
        return self._generate_report()
    
    def _generate_report(self) -> Dict[str, Any]:
        """生成回测报告"""
        wins = len([t for t in self.trades if t["result"] == "win"])
        losses = len([t for t in self.trades if t["result"] == "loss"])
        total = len(self.trades)
        
        win_rate = wins / total if total > 0 else 0
        roi = (self.bankroll - self.initial_bankroll) / self.initial_bankroll
        
        # 最大回撤
        peak = self.initial_bankroll
        max_drawdown = 0
        for val in self.history:
            if val > peak:
                peak = val
            drawdown = (peak - val) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            "strategy": self.strategy,
            "initial_bankroll": self.initial_bankroll,
            "final_bankroll": round(self.bankroll, 2),
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate * 100, 2),
            "roi": round(roi * 100, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "history": self.history,
            "trades": self.trades
        }


def compare_strategies(path: str = "data/backtest_dataset.json", bankroll: float = 1000) -> Dict[str, Any]:
    """对比多种策略"""
    strategies = ["kelly_compressed", "kelly_half", "kelly_full", "flat"]
    results = {}
    
    for strategy in strategies:
        engine = BacktestEngine(bankroll=bankroll, strategy=strategy)
        results[strategy] = engine.run(path)
    
    return {
        "comparison": results,
        "best_strategy": max(results, key=lambda k: results[k]["final_bankroll"])
    }
