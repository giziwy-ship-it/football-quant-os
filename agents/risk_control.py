#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险控制 Agent - Football Quant OS
"""

from typing import Dict, Any
from core.config import config


class RiskControl:
    """风险控制 Agent"""
    
    name = "RiskControl"
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        warnings = []
        
        # 检查赔率异常
        odds = match_data.get('market_odds', {})
        home_odds = odds.get('home_win', 2.0)
        away_odds = odds.get('away_win', 2.0)
        draw_odds = odds.get('draw', 3.5)
        
        if home_odds < 1.3 or away_odds < 1.3:
            warnings.append("超低赔率：市场极度看好一方，可能存在陷阱")
        
        # ⭐ 精算师风控：赔率价值不足拦截
        home_prob = match_data.get('home_win', 40) / 100
        away_prob = match_data.get('away_win', 30) / 100
        draw_prob = match_data.get('draw', 30) / 100
        
        home_ev = (home_prob * home_odds - 1) * 100
        away_ev = (away_prob * away_odds - 1) * 100
        draw_ev = (draw_prob * draw_odds - 1) * 100
        
        max_ev = max(home_ev, away_ev, draw_ev)
        if max_ev < 5:
            warnings.append(f"赔率价值不足：最高期望收益仅{max_ev:+.1f}%，无投注价值")
        elif max_ev < 10:
            warnings.append(f"赔率价值偏薄：最高期望收益{max_ev:+.1f}%，建议观望")
        
        # 检查数据完整性
        required = ['home_team', 'away_team', 'market_odds']
        missing = [r for r in required if r not in match_data]
        if missing:
            warnings.append(f"数据缺失：{', '.join(missing)}")
        
        # 冷门风险
        home_win = match_data.get('home_win', 40)
        away_win = match_data.get('away_win', 30)
        if abs(home_win - away_win) < 10:
            warnings.append("势均力敌：结果高度不确定")
        
        risk_level = "LOW"
        if len(warnings) >= 3:
            risk_level = "HIGH"
        elif len(warnings) >= 2:
            risk_level = "MEDIUM"
        elif any("赔率价值不足" in w for w in warnings):
            risk_level = "MEDIUM"
        elif len(warnings) >= 1:
            risk_level = "LOW"
        
        # 精算师拦截：价值不足直接 block
        allow = True
        if any("赔率价值不足" in w for w in warnings):
            allow = False
        elif len(warnings) >= 3:
            allow = False
        
        return {
            "agent": self.name,
            "risk_level": risk_level,
            "warnings": warnings,
            "allow": allow,
            "confidence": 0.7
        }
    
    def check(self, decision: Dict[str, Any], bankroll: float = 1000) -> Dict[str, Any]:
        """兼容接口"""
        warnings = decision.get("key_factors", [])
        risk_level = "LOW"
        
        # 检查资金是否足够
        if bankroll < 500:
            risk_level = "HIGH"
            allow = False
        else:
            allow = True
        
        return {
            "risk_level": risk_level,
            "allow": allow,
            "warnings": warnings if isinstance(warnings, list) else []
        }
