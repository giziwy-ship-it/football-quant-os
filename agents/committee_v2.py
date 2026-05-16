#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
委员会决策 Agent v2.0 - Football Quant OS (修复版)
双层加权决策系统
修复: 优先使用市场概率，不强制覆盖
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from typing import Dict, Any, List
from dataclasses import dataclass, field
from enum import Enum


class FundSignalType(Enum):
    """资金信号类型"""
    STRONG_HOME = "strong_home"      # 强烈看好主胜
    HOME_WIN = "home_win"            # 看好主胜
    DRAW = "draw"                    # 看好平局
    AWAY_WIN = "away_win"            # 看好客胜
    STRONG_AWAY = "strong_away"      # 强烈看好客胜
    NEUTRAL = "neutral"              # 中性


@dataclass
class FundSignal:
    """资金信号"""
    signal_type: FundSignalType
    confidence: float  # 0-1
    direction: str      # "home", "away", "neutral"
    strength: str       # "strong", "moderate", "weak"
    source: str         # 信号来源
    weight: float = 1.0
    
    def to_dict(self) -> Dict:
        return {
            "signal_type": self.signal_type.value,
            "confidence": self.confidence,
            "direction": self.direction,
            "strength": self.strength,
            "source": self.source,
            "weight": self.weight
        }


class Committee:
    """
    委员会决策 Agent
    
    修复: 优先使用市场概率，不再强制覆盖
    """
    
    name = "Committee"
    version = "2.1"
    
    def __init__(self):
        self.opinions: List[Dict] = []
        self.fund_signals: List[FundSignal] = []
        self._market_probs: Dict[str, float] = None  # 保存市场概率
    
    def receive_other_opinions(self, opinions: List[Dict]):
        """接收其他Agent的观点"""
        self.opinions = opinions
    
    def receive_fund_signals(self, signals: List[Dict]):
        """
        接收资金信号
        
        修复: 增强错误处理，避免信号映射失败
        """
        self.fund_signals = []
        for signal_data in signals:
            try:
                # 支持字符串或FundSignalType枚举
                signal_type = signal_data.get('signal_type', 'neutral')
                if isinstance(signal_type, str):
                    signal_type = FundSignalType(signal_type)
                
                self.fund_signals.append(FundSignal(
                    signal_type=signal_type,
                    confidence=signal_data.get('confidence', 0.5),
                    direction=signal_data.get('direction', 'neutral'),
                    strength=signal_data.get('strength', 'neutral'),
                    source=signal_data.get('source', 'unknown'),
                    weight=signal_data.get('weight', 1.0)
                ))
            except (ValueError, KeyError) as e:
                print(f"[Committee] 资金信号解析失败: {e}, 信号数据: {signal_data}")
                continue
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        主运行方法 - 双层加权决策
        
        修复: 优先使用市场概率，不再强制覆盖
        """
        # 获取真实赔率数据
        market_odds = match_data.get('market_odds', {})
        
        # 保存市场概率（如果有）
        self._market_probs = None
        if market_odds and all(k in market_odds for k in ['home_win', 'draw', 'away_win']):
            home_odds = market_odds['home_win']
            draw_odds = market_odds['draw']
            away_odds = market_odds['away_win']
            
            home_prob = (1 / home_odds) * 100
            draw_prob = (1 / draw_odds) * 100
            away_prob = (1 / away_odds) * 100
            
            total = home_prob + draw_prob + away_prob
            self._market_probs = {
                "home_win": round(home_prob / total * 100, 2),
                "draw": round(draw_prob / total * 100, 2),
                "away_win": round(away_prob / total * 100, 2)
            }
            print(f"[Committee] 保存市场概率: 主{self._market_probs['home_win']}% 平{self._market_probs['draw']}% 客{self._market_probs['away_win']}%")
        
        if not self.opinions:
            # 没有Agent观点，但有市场概率
            if self._market_probs:
                final_prediction = self._market_probs.copy()
                final_confidence = 0.85
                best = max(final_prediction, key=final_prediction.get)
                
                return {
                    "agent": self.name,
                    "version": self.version,
                    "prediction": final_prediction,
                    "confidence": round(final_confidence, 2),
                    "recommended_outcome": best,
                    "key_factors": ["基于市场赔率概率"],
                    "fund_signal_applied": False,
                    "agent_count": 0,
                    "market_odds_used": True
                }
            
            return {
                "agent": self.name,
                "version": self.version,
                "prediction": {"home_win": 33.3, "draw": 33.3, "away_win": 33.3},
                "confidence": 0.5,
                "key_factors": ["无Agent观点可综合"],
                "fund_signal_applied": False,
                "market_odds_used": False
            }
        
        # ===== 第一层：Agent加权平均 =====
        # 修复: 如果有市场概率，优先使用市场概率，不再强制重新计算
        if self._market_probs:
            # 直接使用市场概率（不再与Agent预测融合）
            final_prediction = self._market_probs.copy()
            print(f"[Committee] 优先使用市场概率: 主{final_prediction['home_win']}% 平{final_prediction['draw']}% 客{final_prediction['away_win']}%")
        else:
            # 没有市场概率，使用Agent加权平均
            final_prediction = self._agent_weighted_average()
            print(f"[Committee] 使用Agent预测概率: 主{final_prediction['home_win']:.1f}% 平{final_prediction['draw']:.1f}% 客{final_prediction['away_win']:.1f}%")
        
        # ===== 第二层：资金信号加权调整 =====
        final_prediction = self._apply_fund_signal_weights(final_prediction)
        
        # ===== 计算综合置信度 =====
        final_confidence = self._calculate_final_confidence()
        
        # ===== 确定推荐结果 =====
        best = max(final_prediction, key=final_prediction.get)
        
        # ===== 生成关键因子 =====
        key_factors = self._generate_key_factors(final_prediction, best)
        
        return {
            "agent": self.name,
            "version": self.version,
            "prediction": final_prediction,
            "confidence": round(final_confidence, 2),
            "recommended_outcome": best,
            "key_factors": key_factors,
            "fund_signal_applied": len(self.fund_signals) > 0,
            "fund_signals": [s.to_dict() for s in self.fund_signals],
            "agent_count": len(self.opinions),
            "market_odds_used": bool(self._market_probs)
        }
    
    def _agent_weighted_average(self) -> Dict[str, float]:
        """
        Agent 加权平均
        
        修复: 仅在没有市场概率时使用
        """
        home = 0
        draw = 0
        away = 0
        total_confidence = 0
        
        for opinion in self.opinions:
            confidence = opinion.get("confidence", 0.7)
            prediction = opinion.get("prediction", {})
            
            home += prediction.get("home_win", 33.3) * confidence
            draw += prediction.get("draw", 33.3) * confidence
            away += prediction.get("away_win", 33.3) * confidence
            total_confidence += confidence
        
        if total_confidence == 0:
            return {"home_win": 33.3, "draw": 33.3, "away_win": 33.3}
        
        total = home + draw + away
        
        return {
            "home_win": home / total * 100,
            "draw": draw / total * 100,
            "away_win": away / total * 100
        }
    
    def _apply_fund_signal_weights(self, prediction: Dict[str, float]) -> Dict[str, float]:
        """应用资金信号权重调整"""
        if not self.fund_signals:
            return prediction
        
        adjusted = prediction.copy()
        
        for signal in self.fund_signals:
            # 根据信号类型调整概率
            if signal.signal_type == FundSignalType.STRONG_HOME:
                adjusted["home_win"] += 5 * signal.confidence * signal.weight
                adjusted["away_win"] -= 3 * signal.confidence * signal.weight
            elif signal.signal_type == FundSignalType.HOME_WIN:
                adjusted["home_win"] += 3 * signal.confidence * signal.weight
                adjusted["away_win"] -= 2 * signal.confidence * signal.weight
            elif signal.signal_type == FundSignalType.DRAW:
                adjusted["draw"] += 4 * signal.confidence * signal.weight
                adjusted["home_win"] -= 2 * signal.confidence * signal.weight
                adjusted["away_win"] -= 2 * signal.confidence * signal.weight
            elif signal.signal_type == FundSignalType.AWAY_WIN:
                adjusted["away_win"] += 3 * signal.confidence * signal.weight
                adjusted["home_win"] -= 2 * signal.confidence * signal.weight
            elif signal.signal_type == FundSignalType.STRONG_AWAY:
                adjusted["away_win"] += 5 * signal.confidence * signal.weight
                adjusted["home_win"] -= 3 * signal.confidence * signal.weight
        
        # 归一化
        total = adjusted["home_win"] + adjusted["draw"] + adjusted["away_win"]
        return {
            "home_win": round(adjusted["home_win"] / total * 100, 2),
            "draw": round(adjusted["draw"] / total * 100, 2),
            "away_win": round(adjusted["away_win"] / total * 100, 2)
        }
    
    def _calculate_final_confidence(self) -> float:
        """计算综合置信度"""
        base_confidence = 0.7
        
        # Agent数量加成
        agent_bonus = min(len(self.opinions) * 0.02, 0.1)
        
        # 资金信号加成
        fund_bonus = 0.0
        if self.fund_signals:
            avg_confidence = sum(s.confidence for s in self.fund_signals) / len(self.fund_signals)
            fund_bonus = avg_confidence * 0.1
        
        return min(base_confidence + agent_bonus + fund_bonus, 0.95)
    
    def _generate_key_factors(self, prediction: Dict[str, float], best: str) -> List[str]:
        """生成关键因子说明"""
        factors = []
        
        # 市场概率说明
        if self._market_probs:
            factors.append(f"基于真实赔率概率: 主{prediction['home_win']:.1f}% 平{prediction['draw']:.1f}% 客{prediction['away_win']:.1f}%")
        else:
            factors.append(f"基于Agent综合预测: 主{prediction['home_win']:.1f}% 平{prediction['draw']:.1f}% 客{prediction['away_win']:.1f}%")
        
        # 推荐结果说明
        if best == "home_win":
            factors.append("推荐主胜")
        elif best == "draw":
            factors.append("推荐平局")
        else:
            factors.append("推荐客胜")
        
        # 资金信号说明
        if self.fund_signals:
            for signal in self.fund_signals:
                factors.append(f"资金信号: {signal.signal_type.value} (置信度{signal.confidence:.0%})")
        
        return factors
