#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据侦察 Agent - Football Quant OS
"""

from typing import Dict, Any


class DataScout:
    """数据侦察 Agent"""
    
    name = "DataScout"
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        home = match_data.get('home_team', '')
        away = match_data.get('away_team', '')
        
        home_win = match_data.get('home_win', 40)
        draw = match_data.get('draw', 30)
        away_win = match_data.get('away_win', 30)
        
        if home_win > 50:
            recommendation = "主胜"
        elif away_win > 45:
            recommendation = "客胜"
        else:
            recommendation = "平局"
        
        confidence = 0.8 if max(home_win, away_win, draw) > 55 else 0.75
        
        return {
            "agent": self.name,
            "prediction": {"home_win": home_win, "draw": draw, "away_win": away_win},
            "confidence": confidence,
            "recommendation": recommendation,
            "key_factors": [f"推荐：{recommendation}", "快速决策模式"]
        }
