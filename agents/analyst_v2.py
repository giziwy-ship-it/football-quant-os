#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 Agent v2.0 - Football Quant OS
升级版：支持资金信号分析、赔率偏差检测、市场共识分析
"""

import math
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class MarketSignal:
    """市场信号"""
    type: str           # strong_home / moderate_home / trap_home / neutral / etc.
    confidence: float   # 0.0 - 1.0
    description: str
    source: str         # odds / volume / pattern


class Analyst:
    """数据分析 Agent v2.0"""
    
    name = "Analyst_v2"
    
    def __init__(self):
        self.signals: List[MarketSignal] = []
        self.entropy_threshold = 0.8
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """完整分析流程"""
        # 1. 基础概率分析
        home_win = match_data.get('home_win', 40)
        draw = match_data.get('draw', 30)
        away_win = match_data.get('away_win', 30)
        
        probs = [home_win, draw, away_win]
        entropy = self._entropy(probs)
        
        # 2. 关键因子分析
        key_factors = self._analyze_key_factors(match_data, entropy)
        
        # 3. 赔率偏差分析（如果有赔率数据）
        odds_analysis = self._analyze_odds(match_data)
        
        # 4. 资金信号分析（如果有资金流向数据）
        money_flow = match_data.get('money_flow', {})
        if money_flow:
            self._analyze_money_flow(money_flow)
        
        # 5. 统计学调整
        adjusted_probs = self._statistical_adjustment(probs)
        
        # 6. 生成信号
        signals = self._generate_signals(adjusted_probs, odds_analysis, match_data)
        
        return {
            "agent": self.name,
            "prediction": {
                "home_win": round(adjusted_probs[0], 2),
                "draw": round(adjusted_probs[1], 2),
                "away_win": round(adjusted_probs[2], 2)
            },
            "confidence": self._calculate_confidence(adjusted_probs, entropy),
            "entropy": round(entropy, 3),
            "key_factors": key_factors,
            "odds_analysis": odds_analysis,
            "signals": signals,
            "money_flow_signals": [s.__dict__ for s in self.signals]
        }
    
    def _analyze_key_factors(self, match_data: Dict, entropy: float) -> List[str]:
        """分析关键因子"""
        factors = []
        
        if entropy < 0.8:
            factors.append(f"低熵分布({entropy:.2f})：确定性高")
        else:
            factors.append(f"高熵分布({entropy:.2f})：不确定性高")
        
        eg = match_data.get('expected_goals', 2.5)
        if eg > 3.0:
            factors.append(f"高进球预期({eg:.1f}): 大球概率高")
        elif eg < 2.0:
            factors.append(f"低进球预期({eg:.1f}): 小球概率高")
        
        # 排名差距
        rank_diff = match_data.get('home_rank', 50) - match_data.get('away_rank', 50)
        if abs(rank_diff) > 20:
            leader = "主队" if rank_diff < 0 else "客队"
            factors.append(f"排名差距大({abs(rank_diff)}位): {leader}实力占优")
        
        # 近期状态
        home_form = match_data.get('home_form', [])
        away_form = match_data.get('away_form', [])
        if home_form and away_form:
            home_wins = sum(1 for r in home_form if r == 'W')
            away_wins = sum(1 for r in away_form if r == 'W')
            if home_wins >= 4 and away_wins <= 1:
                factors.append(f"主队状态极佳({home_wins}/5胜)")
            elif away_wins >= 4 and home_wins <= 1:
                factors.append(f"客队状态极佳({away_wins}/5胜)")
        
        return factors
    
    def _analyze_odds(self, match_data: Dict) -> Dict[str, Any]:
        """分析赔率数据"""
        odds = match_data.get('odds', {})
        if not odds:
            return {"available": False}
        
        home_odds = odds.get('home', 1.0)
        draw_odds = odds.get('draw', 1.0)
        away_odds = odds.get('away', 1.0)
        
        # 计算隐含概率（去水前）
        total_prob = 1/home_odds + 1/draw_odds + 1/away_odds
        
        return {
            "available": True,
            "home_implied": round(1/home_odds / total_prob * 100, 2),
            "draw_implied": round(1/draw_odds / total_prob * 100, 2),
            "away_implied": round(1/away_odds / total_prob * 100, 2),
            "margin": round((total_prob - 1) * 100, 2),
            "value_bet": self._find_value_bet(match_data, home_odds, draw_odds, away_odds)
        }
    
    def _find_value_bet(self, match_data: Dict, h: float, d: float, a: float) -> Optional[str]:
        """寻找价值投注"""
        model_probs = [match_data.get('home_win', 40), 
                      match_data.get('draw', 30), 
                      match_data.get('away_win', 30)]
        
        total_prob = 1/h + 1/d + 1/a
        implied = [1/h/total_prob*100, 1/d/total_prob*100, 1/a/total_prob*100]
        
        # 如果模型概率显著高于隐含概率，存在价值
        for i, (model, market) in enumerate(zip(model_probs, implied)):
            if model - market > 5:
                return ["home", "draw", "away"][i]
        
        return None
    
    def _analyze_money_flow(self, money_flow: Dict):
        """分析资金流向"""
        # 大额投注方向
        home_big = money_flow.get('home_big_bets', 0)
        away_big = money_flow.get('away_big_bets', 0)
        
        if home_big > away_big * 2:
            self.signals.append(MarketSignal(
                type="strong_home", confidence=0.8,
                description="大额资金强烈倾向主胜", source="volume"
            ))
        elif away_big > home_big * 2:
            self.signals.append(MarketSignal(
                type="strong_away", confidence=0.8,
                description="大额资金强烈倾向客胜", source="volume"
            ))
    
    def _statistical_adjustment(self, probs: List[float]) -> List[float]:
        """统计学调整"""
        mean = sum(probs) / 3
        adj = (mean - 33.33) * 0.1
        
        home = probs[0] * (1 + adj / 100)
        draw = probs[1]
        away = probs[2] * (1 - adj / 100)
        
        total = home + draw + away
        return [home/total*100, draw/total*100, away/total*100]
    
    def _generate_signals(self, probs: List[float], odds_analysis: Dict, 
                         match_data: Dict) -> List[str]:
        """生成交易信号"""
        signals = []
        
        # 主场优势信号
        if probs[0] > 60:
            signals.append("STRONG_HOME: 模型强烈看好主胜")
        elif probs[0] > 50:
            signals.append("MODERATE_HOME: 模型适度看好主胜")
        
        # 价值投注信号
        if odds_analysis.get("available"):
            vb = odds_analysis.get("value_bet")
            if vb:
                signals.append(f"VALUE_BET: {vb} 方向存在价值投注机会")
        
        # 诱盘检测
        if match_data.get('odds', {}).get('home', 0) < 1.3 and probs[0] < 50:
            signals.append("TRAP_HOME: 低赔率但模型不看好，可能是诱盘")
        
        return signals
    
    def _calculate_confidence(self, probs: List[float], entropy: float) -> float:
        """计算置信度"""
        base = 0.85
        
        # 熵惩罚
        if entropy > 0.9:
            base -= 0.15
        elif entropy > 0.8:
            base -= 0.05
        
        # 集中度奖励
        max_prob = max(probs)
        if max_prob > 70:
            base += 0.05
        
        return min(0.95, max(0.5, base))
    
    def _entropy(self, probs: list) -> float:
        """计算熵"""
        entropy = 0
        for p in probs:
            if p > 0:
                pn = p / 100
                entropy -= pn * math.log2(pn)
        return entropy / math.log2(3)
