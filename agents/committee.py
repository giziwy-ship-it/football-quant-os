#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
委员会决策 Agent - Football Quant OS
"""

from typing import Dict, Any, List


class Committee:
    """委员会决策 Agent"""
    
    name = "Committee"
    
    def __init__(self):
        self.opinions: List[Dict] = []
    
    def receive_other_opinions(self, opinions: List[Dict]):
        self.opinions = [o for o in opinions if isinstance(o, dict)]
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.opinions:
            return {
                "agent": self.name,
                "prediction": {"home_win": 33.3, "draw": 33.3, "away_win": 33.3},
                "confidence": 0.5,
                "key_factors": ["无Agent观点可综合"]
            }
        
        # 加权平均
        home_total = 0
        draw_total = 0
        away_total = 0
        weight_total = 0
        
        for op in self.opinions:
            if "prediction" not in op:
                continue
            pred = op["prediction"]
            conf = op.get("confidence", 0.7)
            
            home_total += pred.get("home_win", 33) * conf
            draw_total += pred.get("draw", 33) * conf
            away_total += pred.get("away_win", 33) * conf
            weight_total += conf
        
        if weight_total == 0:
            weight_total = 1
        
        home = home_total / weight_total
        draw = draw_total / weight_total
        away = away_total / weight_total
        total = home + draw + away
        
        prediction = {
            "home_win": round(home / total * 100, 2),
            "draw": round(draw / total * 100, 2),
            "away_win": round(away / total * 100, 2)
        }
        
        best = max(prediction, key=prediction.get)
        avg_conf = sum(o.get("confidence", 0.7) for o in self.opinions) / len(self.opinions)
        
        return {
            "agent": self.name,
            "prediction": prediction,
            "confidence": round(min(avg_conf + 0.05, 0.95), 2),
            "recommended_outcome": best,
            "key_factors": [f"综合{len(self.opinions)}个Agent观点", f"推荐：{best}"]
        }
    
    def decide(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """兼容接口"""
        opinions = [v for k, v in data.items() if isinstance(v, dict) and "prediction" in v]
        self.receive_other_opinions(opinions)
        return self.run({})
