#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 Agent - Football Quant OS
"""

import math
from typing import Dict, Any


class Analyst:
    """数据分析 Agent"""
    
    name = "Analyst"
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        home_win = match_data.get('home_win', 40)
        draw = match_data.get('draw', 30)
        away_win = match_data.get('away_win', 30)
        
        probs = [home_win, draw, away_win]
        entropy = self._entropy(probs)
        
        key_factors = []
        if entropy < 0.8:
            key_factors.append(f"低熵分布({entropy:.2f})：确定性高")
        else:
            key_factors.append(f"高熵分布({entropy:.2f})：不确定性高")
        
        eg = match_data.get('expected_goals', 2.5)
        if eg > 3.0:
            key_factors.append(f"高进球预期({eg:.1f})")
        elif eg < 2.0:
            key_factors.append(f"低进球预期({eg:.1f})")
        
        # 统计学调整
        mean = sum(probs) / 3
        adj = (mean - 33.33) * 0.1
        home_win = home_win * (1 + adj / 100)
        away_win = away_win * (1 + adj / 100)
        total = home_win + draw + away_win
        
        return {
            "agent": self.name,
            "prediction": {
                "home_win": round(home_win / total * 100, 2),
                "draw": round(draw / total * 100, 2),
                "away_win": round(away_win / total * 100, 2)
            },
            "confidence": 0.85,
            "entropy": round(entropy, 3),
            "key_factors": key_factors
        }
    
    def _entropy(self, probs: list) -> float:
        entropy = 0
        for p in probs:
            if p > 0:
                pn = p / 100
                entropy -= pn * math.log2(pn)
        return entropy / math.log2(3)
