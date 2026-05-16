#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分析 Agent v2.0 - Football Quant OS
增强功能：资金流向分析模块
"""

import math
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class MoneyFlowSignal(Enum):
    """资金流向信号类型"""
    STRONG_HOME = "强烈看好主胜"
    MODERATE_HOME = "适度看好主胜"
    STRONG_DRAW = "强烈看好平局"
    MODERATE_DRAW = "适度看好平局"
    STRONG_AWAY = "强烈看好客胜"
    MODERATE_AWAY = "适度看好客胜"
    TRAP_HOME = "主胜可能是诱盘"
    TRAP_DRAW = "平局可能是诱盘"
    TRAP_AWAY = "客胜可能是诱盘"
    NEUTRAL = "资金流向中性"


@dataclass
class MoneyFlowAnalysis:
    """资金流向分析结果"""
    signal: MoneyFlowSignal
    confidence: float
    key_insights: list
    risk_flags: list
    recommendation: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "signal": self.signal.value,
            "confidence": self.confidence,
            "key_insights": self.key_insights,
            "risk_flags": self.risk_flags,
            "recommendation": self.recommendation
        }


class Analyst:
    """数据分析 Agent v2.0"""
    
    name = "Analyst"
    version = "2.0"
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        主运行方法 - 使用真实赔率数据
        
        Args:
            match_data: 比赛数据字典
                - market_odds: 市场赔率（来自Odds API）
                - money_flow: 资金流向数据（来自DataScout）
        """
        # 获取真实赔率数据
        market_odds = match_data.get('market_odds', {})
        
        # 如果有真实赔率，转换为概率
        if market_odds and all(k in market_odds for k in ['home_win', 'draw', 'away_win']):
            # 赔率转概率（去 margin）
            home_odds = market_odds['home_win']
            draw_odds = market_odds['draw']
            away_odds = market_odds['away_win']
            
            # 计算隐含概率
            home_prob = (1 / home_odds) * 100
            draw_prob = (1 / draw_odds) * 100
            away_prob = (1 / away_odds) * 100
            
            # 归一化
            total = home_prob + draw_prob + away_prob
            home_win = round(home_prob / total * 100, 2)
            draw = round(draw_prob / total * 100, 2)
            away_win = round(away_prob / total * 100, 2)
            
            print(f"[Analyst] 真实赔率转换: 主{home_win}% 平{draw}% 客{away_win}%")
        else:
            # 使用默认概率
            home_win = match_data.get('home_win', 40)
            draw = match_data.get('draw', 30)
            away_win = match_data.get('away_win', 30)
            print(f"[Analyst] 使用默认概率: 主{home_win}% 平{draw}% 客{away_win}%")
        
        # 1. 基础统计分析
        base_result = self._analyze_base(home_win, draw, away_win, match_data)
        
        # 2. 资金流向分析（如果数据存在）
        money_flow_analysis = None
        if 'money_flow' in match_data:
            money_flow_analysis = self._analyze_money_flow(match_data['money_flow'])
            base_result['key_factors'].append(f"资金信号：{money_flow_analysis.signal.value}")
        
        # 3. 组装结果
        result = {
            "agent": self.name,
            "version": self.version,
            "prediction": base_result['prediction'],
            "confidence": base_result['confidence'],
            "entropy": base_result['entropy'],
            "key_factors": base_result['key_factors'],
        }
        
        if money_flow_analysis:
            result['money_flow_analysis'] = money_flow_analysis.to_dict()
        
        return result
    
    def _analyze_base(self, home_win: float, draw: float, away_win: float, match_data: Dict) -> Dict:
        """基础数据分析"""
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
        home_win_adj = home_win * (1 + adj / 100)
        away_win_adj = away_win * (1 + adj / 100)
        total = home_win_adj + draw + away_win_adj
        
        return {
            "prediction": {
                "home_win": round(home_win_adj / total * 100, 2),
                "draw": round(draw / total * 100, 2),
                "away_win": round(away_win_adj / total * 100, 2)
            },
            "confidence": 0.85,
            "entropy": round(entropy, 3),
            "key_factors": key_factors
        }
    
    def _analyze_money_flow(self, money_flow: Dict[str, Any]) -> MoneyFlowAnalysis:
        """
        资金流向核心分析算法
        
        分析维度：
        1. 成交量偏离度（必发 vs 欧赔概率）
        2. 庄家盈亏方向
        3. 盈亏指数
        4. 冷热指数
        5. 大额交易动向
        """
        # 提取数据
        euro_home_prob = money_flow.get('euro_home_prob', 33.3)
        euro_draw_prob = money_flow.get('euro_draw_prob', 33.3)
        euro_away_prob = money_flow.get('euro_away_prob', 33.4)
        
        bf_home_volume = money_flow.get('bf_home_volume', 0)
        bf_draw_volume = money_flow.get('bf_draw_volume', 0)
        bf_away_volume = money_flow.get('bf_away_volume', 0)
        bf_total = bf_home_volume + bf_draw_volume + bf_away_volume
        
        if bf_total == 0:
            return MoneyFlowAnalysis(
                signal=MoneyFlowSignal.NEUTRAL,
                confidence=0.5,
                key_insights=["无成交量数据"],
                risk_flags=[],
                recommendation="参考其他因素"
            )
        
        # 计算成交量占比
        bf_home_pct = bf_home_volume / bf_total * 100
        bf_draw_pct = bf_draw_volume / bf_total * 100
        bf_away_pct = bf_away_volume / bf_total * 100
        
        # 1. 成交量偏离度分析
        home_deviation = bf_home_pct - euro_home_prob
        draw_deviation = bf_draw_pct - euro_draw_prob
        away_deviation = bf_away_pct - euro_away_prob
        
        # 2. 庄家盈亏分析
        bookmaker_home_pnl = money_flow.get('bookmaker_home_pnl', 0)
        bookmaker_draw_pnl = money_flow.get('bookmaker_draw_pnl', 0)
        bookmaker_away_pnl = money_flow.get('bookmaker_away_pnl', 0)
        
        # 3. 盈亏指数分析
        profit_index_home = money_flow.get('profit_index_home', 0)
        profit_index_draw = money_flow.get('profit_index_draw', 0)
        profit_index_away = money_flow.get('profit_index_away', 0)
        
        # 4. 冷热指数
        cold_hot_home = money_flow.get('cold_hot_index_home')
        cold_hot_draw = money_flow.get('cold_hot_index_draw')
        cold_hot_away = money_flow.get('cold_hot_index_away')
        
        # ===== 核心判断逻辑 =====
        
        insights = []
        risk_flags = []
        
        # 信号强度计算
        home_score = 0
        draw_score = 0
        away_score = 0
        
        # 成交量偏离度评分（±5%以上视为显著）
        if home_deviation > 5:
            home_score += 2
            insights.append(f"主胜成交量偏高 {home_deviation:.1f}%")
        elif home_deviation < -5:
            home_score -= 1
            insights.append(f"主胜成交量偏低 {home_deviation:.1f}%")
            
        if draw_deviation > 5:
            draw_score += 2
            insights.append(f"平局成交量偏高 {draw_deviation:.1f}%")
        elif draw_deviation < -5:
            draw_score -= 1
            
        if away_deviation > 5:
            away_score += 2
            insights.append(f"客胜成交量偏高 {away_deviation:.1f}%")
        elif away_deviation < -5:
            away_score -= 1
        
        # 庄家盈亏评分（庄家亏损 = 市场真实看好）
        if bookmaker_home_pnl < -50000:  # 亏损超过5万
            home_score += 2
            insights.append("主胜庄家亏损，市场资金涌入")
        elif bookmaker_home_pnl > 200000:  # 盈利超过20万
            home_score -= 2
            risk_flags.append("主胜庄家大赚，可能是诱盘")
            
        if bookmaker_draw_pnl < -50000:
            draw_score += 2
            insights.append("平局庄家亏损")
        elif bookmaker_draw_pnl > 200000:
            draw_score -= 2
            risk_flags.append("平局庄家大赚")
            
        if bookmaker_away_pnl < -50000:
            away_score += 2
            insights.append("客胜庄家亏损，市场资金涌入")
        elif bookmaker_away_pnl > 200000:
            away_score -= 2
            risk_flags.append("客胜庄家大赚")
        
        # 盈亏指数评分（负值 = 玩家有利，正值 = 庄家有利）
        if profit_index_home < -5:
            home_score += 1
        elif profit_index_home > 10:
            home_score -= 1
            risk_flags.append("主胜盈亏指数偏高")
            
        if profit_index_draw < -5:
            draw_score += 1
        elif profit_index_draw > 10:
            draw_score -= 1
            
        if profit_index_away < -5:
            away_score += 1
        elif profit_index_away > 10:
            away_score -= 1
            risk_flags.append("客胜盈亏指数偏高")
        
        # 冷热指数评分
        if cold_hot_home and cold_hot_home > 10:
            home_score -= 1
            risk_flags.append("主胜过热")
        if cold_hot_draw and cold_hot_draw > 10:
            draw_score -= 1
        if cold_hot_away and cold_hot_away > 10:
            away_score -= 1
            risk_flags.append("客胜过热")
        
        # ===== 最终信号判断 =====
        
        max_score = max(home_score, draw_score, away_score)
        min_score = min(home_score, draw_score, away_score)
        
        # 判断信号类型
        if max_score >= 4:
            # 强烈看好信号
            if home_score == max_score:
                if bookmaker_home_pnl > 100000:
                    signal = MoneyFlowSignal.TRAP_HOME
                    confidence = 0.75
                    recommendation = "⚠️ 主胜可能是诱盘，建议反向或观望"
                else:
                    signal = MoneyFlowSignal.STRONG_HOME
                    confidence = 0.85
                    recommendation = "✅ 强烈看好主胜，资金信号明确"
            elif draw_score == max_score:
                if bookmaker_draw_pnl > 100000:
                    signal = MoneyFlowSignal.TRAP_DRAW
                    confidence = 0.75
                    recommendation = "⚠️ 平局可能是诱盘"
                else:
                    signal = MoneyFlowSignal.STRONG_DRAW
                    confidence = 0.85
                    recommendation = "✅ 强烈看好平局"
            else:
                if bookmaker_away_pnl > 100000:
                    signal = MoneyFlowSignal.TRAP_AWAY
                    confidence = 0.75
                    recommendation = "⚠️ 客胜可能是诱盘"
                else:
                    signal = MoneyFlowSignal.STRONG_AWAY
                    confidence = 0.85
                    recommendation = "✅ 强烈看好客胜"
        elif max_score >= 2:
            # 适度看好信号
            if home_score == max_score:
                signal = MoneyFlowSignal.MODERATE_HOME
                confidence = 0.75
                recommendation = "👍 适度看好主胜"
            elif draw_score == max_score:
                signal = MoneyFlowSignal.MODERATE_DRAW
                confidence = 0.75
                recommendation = "👍 适度看好平局"
            else:
                signal = MoneyFlowSignal.MODERATE_AWAY
                confidence = 0.75
                recommendation = "👍 适度看好客胜"
        else:
            signal = MoneyFlowSignal.NEUTRAL
            confidence = 0.6
            recommendation = "😐 资金流向中性，参考其他因素"
        
        # 如果没有洞察，添加默认说明
        if not insights:
            insights.append("成交量分布与欧赔概率基本一致")
        
        return MoneyFlowAnalysis(
            signal=signal,
            confidence=confidence,
            key_insights=insights,
            risk_flags=risk_flags,
            recommendation=recommendation
        )
    
    def _entropy(self, probs: list) -> float:
        """计算熵值"""
        entropy = 0
        for p in probs:
            if p > 0:
                pn = p / 100
                entropy -= pn * math.log2(pn)
        return entropy / math.log2(3)


# ============ 测试代码 ============

if __name__ == "__main__":
    analyst = Analyst()
    
    # 测试1：无资金流向
    result1 = analyst.run({
        "home_team": "水晶宫",
        "away_team": "西汉姆联",
        "home_win": 40,
        "draw": 30,
        "away_win": 30
    })
    print("=== 测试1：基础分析 ===")
    import json
    print(json.dumps(result1, ensure_ascii=False, indent=2))
    
    # 测试2：有资金流向（水晶宫 vs 西汉姆联真实数据）
    money_flow_data = {
        "match_id": "1202700",
        "home_team": "水晶宫",
        "away_team": "西汉姆联",
        "euro_home_odds": 2.55,
        "euro_draw_odds": 3.30,
        "euro_away_odds": 2.80,
        "euro_home_prob": 37.3,
        "euro_draw_prob": 28.8,
        "euro_away_prob": 33.9,
        "bf_home_price": 2.72,
        "bf_draw_price": 3.5,
        "bf_away_price": 2.92,
        "bf_home_volume": 866675,
        "bf_draw_volume": 554147,
        "bf_away_volume": 887415,
        "bf_total_volume": 2308237,
        "bookmaker_home_pnl": -49119,
        "bookmaker_draw_pnl": 368723,
        "bookmaker_away_pnl": -283015,
        "profit_index_home": -3,
        "profit_index_draw": 15,
        "profit_index_away": -13,
        "cold_hot_index_home": None,
        "cold_hot_index_draw": -17,
        "cold_hot_index_away": 13,
        "large_transactions": [],
        "data_source": "manual",
        "fetch_time": "2026-04-20T22:00:00"
    }
    
    result2 = analyst.run({
        "home_team": "水晶宫",
        "away_team": "西汉姆联",
        "home_win": 40,
        "draw": 30,
        "away_win": 30,
        "money_flow": money_flow_data
    })
    print("\n=== 测试2：资金流向分析 ===")
    print(json.dumps(result2, ensure_ascii=False, indent=2))
