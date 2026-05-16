#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
风险控制 Agent v2.0 - Football Quant OS
增强功能：资金风险联动模块
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
# 简化版本，不依赖core.config
class Config:
    KELLY_MAX_FRACTION = 0.05
    MAX_BET_PCT = 0.10

config = Config()


class MoneyRiskLevel(Enum):
    """资金风险等级"""
    SAFE = "安全"
    CAUTION = "谨慎"
    WARNING = "警告"
    DANGER = "危险"


@dataclass
class KellyAdjustment:
    """凯利调整结果"""
    base_kelly: float
    adjusted_kelly: float
    max_bet_pct: float
    adjustment_reason: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "base_kelly": self.base_kelly,
            "adjusted_kelly": self.adjusted_kelly,
            "max_bet_pct": self.max_bet_pct,
            "adjustment_reason": self.adjustment_reason
        }


class RiskControl:
    """风险控制 Agent v2.0"""
    
    name = "RiskControl"
    version = "2.0"
    
    # 精算师风控参数
    KELLY_MAX_FRACTION = 0.05      # 最大凯利比例 5%
    MAX_BET_PCT = 0.10             # 单次最大投注比例 10%
    
    # 资金风险调整系数
    MONEY_FLOW_ADJUSTMENTS = {
        "STRONG_HOME": {"kelly_mult": 1.0, "max_pct": 0.10, "level": "SAFE"},
        "STRONG_DRAW": {"kelly_mult": 0.9, "max_pct": 0.08, "level": "CAUTION"},
        "STRONG_AWAY": {"kelly_mult": 1.0, "max_pct": 0.10, "level": "SAFE"},
        "MODERATE_HOME": {"kelly_mult": 0.8, "max_pct": 0.08, "level": "CAUTION"},
        "MODERATE_DRAW": {"kelly_mult": 0.7, "max_pct": 0.06, "level": "CAUTION"},
        "MODERATE_AWAY": {"kelly_mult": 0.8, "max_pct": 0.08, "level": "CAUTION"},
        "TRAP_HOME": {"kelly_mult": 0.3, "max_pct": 0.03, "level": "DANGER"},
        "TRAP_DRAW": {"kelly_mult": 0.3, "max_pct": 0.03, "level": "DANGER"},
        "TRAP_AWAY": {"kelly_mult": 0.3, "max_pct": 0.03, "level": "DANGER"},
        "NEUTRAL": {"kelly_mult": 0.7, "max_pct": 0.07, "level": "CAUTION"},
    }
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        主运行方法
        
        Args:
            match_data: 比赛数据字典
                - 基础数据
                - money_flow_analysis: 资金流向分析（来自Analyst）
        """
        warnings = []
        
        # 1. 基础风险检查（原有逻辑）
        base_risk = self._check_base_risk(match_data)
        warnings.extend(base_risk['warnings'])
        
        # 2. 资金风险检查（新增）
        money_risk = None
        if 'money_flow_analysis' in match_data:
            money_risk = self._check_money_flow_risk(match_data['money_flow_analysis'])
            if money_risk['warnings']:
                warnings.extend(money_risk['warnings'])
        
        # 3. 凯利调整（新增）
        kelly_adjustment = None
        if 'money_flow_analysis' in match_data:
            kelly_adjustment = self._adjust_kelly_for_money_flow(
                match_data.get('base_kelly', 0.05),
                match_data['money_flow_analysis']
            )
        
        # 4. 综合风险等级
        risk_level = self._calculate_risk_level(warnings, money_risk)
        
        # 5. 最终决策
        allow = self._make_decision(warnings, risk_level, money_risk)
        
        result = {
            "agent": self.name,
            "version": self.version,
            "risk_level": risk_level,
            "warnings": warnings,
            "allow": allow,
            "confidence": 0.7
        }
        
        if money_risk:
            result['money_risk'] = money_risk
        
        if kelly_adjustment:
            result['kelly_adjustment'] = kelly_adjustment.to_dict()
        
        return result
    
    def _check_base_risk(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """基础风险检查（原有逻辑）"""
        warnings = []
        
        # 检查赔率异常
        odds = match_data.get('market_odds', {})
        home_odds = odds.get('home_win', 2.0)
        away_odds = odds.get('away_win', 2.0)
        draw_odds = odds.get('draw', 3.5)
        
        if home_odds < 1.3 or away_odds < 1.3:
            warnings.append("超低赔率：市场极度看好一方，可能存在陷阱")
        
        # 精算师风控：赔率价值不足拦截
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
        
        return {"warnings": warnings}
    
    def _check_money_flow_risk(self, money_flow_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """检查资金流向风险"""
        warnings = []
        risk_level = "SAFE"
        
        signal = money_flow_analysis.get('signal', 'NEUTRAL')
        confidence = money_flow_analysis.get('confidence', 0.5)
        risk_flags = money_flow_analysis.get('risk_flags', [])
        
        # 诱盘风险
        if 'TRAP' in signal:
            warnings.append(f"[资金警报] {signal} - 建议反向或观望")
            risk_level = "DANGER"
        
        # 风险标志
        for flag in risk_flags:
            warnings.append(f"[资金风险] {flag}")
            if risk_level != "DANGER":
                risk_level = "WARNING"
        
        # 信心度不足
        if confidence < 0.7:
            warnings.append(f"[资金信号] 信心度较低({confidence:.0%})，谨慎参考")
            if risk_level == "SAFE":
                risk_level = "CAUTION"
        
        return {
            "warnings": warnings,
            "risk_level": risk_level,
            "signal": signal,
            "confidence": confidence
        }
    
    def _adjust_kelly_for_money_flow(self, base_kelly: float, 
                                     money_flow_analysis: Dict[str, Any]) -> KellyAdjustment:
        """
        根据资金流向调整凯利比例
        
        调整逻辑：
        - 诱盘信号：大幅降低仓位（30%）
        - 中性信号：适度降低（70%）
        - 强烈信号：保持或微调
        """
        signal = money_flow_analysis.get('signal', 'NEUTRAL')
        
        # 获取调整参数
        adj_params = self.MONEY_FLOW_ADJUSTMENTS.get(signal, 
                                                      {"kelly_mult": 0.7, "max_pct": 0.07, "level": "CAUTION"})
        
        kelly_mult = adj_params['kelly_mult']
        max_pct = adj_params['max_pct']
        
        # 计算调整后的凯利比例
        adjusted_kelly = base_kelly * kelly_mult
        
        # 确保不超过上限
        adjusted_kelly = min(adjusted_kelly, self.KELLY_MAX_FRACTION)
        adjusted_kelly = min(adjusted_kelly, max_pct)
        
        # 生成调整原因
        if 'TRAP' in signal:
            reason = f"检测到诱盘信号({signal})，仓位压缩至{kelly_mult:.0%}"
        elif kelly_mult < 1.0:
            reason = f"资金信号为{signal}，仓位调整至{kelly_mult:.0%}"
        else:
            reason = f"资金信号明确({signal})，维持标准仓位"
        
        return KellyAdjustment(
            base_kelly=base_kelly,
            adjusted_kelly=adjusted_kelly,
            max_bet_pct=max_pct,
            adjustment_reason=reason
        )
    
    def _calculate_risk_level(self, warnings: list, money_risk: Optional[Dict] = None) -> str:
        """计算综合风险等级"""
        # 基础风险等级
        base_level = "LOW"
        if len(warnings) >= 3:
            base_level = "HIGH"
        elif len(warnings) >= 2:
            base_level = "MEDIUM"
        elif any("赔率价值不足" in w for w in warnings):
            base_level = "MEDIUM"
        
        # 如果有资金风险，取更高等级
        if money_risk:
            money_level = money_risk.get('risk_level', 'SAFE')
            level_map = {"SAFE": 0, "CAUTION": 1, "WARNING": 2, "DANGER": 3}
            base_map = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
            
            max_level = max(level_map.get(money_level, 0), base_map.get(base_level, 0))
            reverse_map = {0: "LOW", 1: "MEDIUM", 2: "HIGH", 3: "HIGH"}
            return reverse_map.get(max_level, "LOW")
        
        return base_level
    
    def _make_decision(self, warnings: list, risk_level: str, 
                       money_risk: Optional[Dict] = None) -> bool:
        """做出最终决策"""
        # 基础拦截条件
        if any("赔率价值不足" in w for w in warnings):
            return False
        elif len(warnings) >= 3:
            return False
        
        # 资金风险拦截
        if money_risk:
            signal = money_risk.get('signal', '')
            if 'TRAP' in signal:
                # 诱盘信号不直接拦截，但大幅降低仓位（由Kelly调整处理）
                pass
        
        return True
    
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


# ============ 测试代码 ============

if __name__ == "__main__":
    risk = RiskControl()
    
    # 测试1：基础风险（无资金流向）
    result1 = risk.run({
        "home_team": "水晶宫",
        "away_team": "西汉姆联",
        "home_win": 40,
        "draw": 30,
        "away_win": 30,
        "market_odds": {"home_win": 2.55, "draw": 3.30, "away_win": 2.80},
        "base_kelly": 0.05
    })
    print("=== 测试1：基础风险 ===")
    import json
    print(json.dumps(result1, ensure_ascii=False, indent=2))
    
    # 测试2：诱盘信号
    result2 = risk.run({
        "home_team": "水晶宫",
        "away_team": "西汉姆联",
        "home_win": 40,
        "draw": 30,
        "away_win": 30,
        "market_odds": {"home_win": 2.55, "draw": 3.30, "away_win": 2.80},
        "base_kelly": 0.05,
        "money_flow_analysis": {
            "signal": "TRAP_HOME",
            "confidence": 0.75,
            "key_insights": ["主胜庄家大赚，可能是诱盘"],
            "risk_flags": ["主胜庄家大赚"],
            "recommendation": "主胜可能是诱盘，建议反向或观望"
        }
    })
    print("\n=== 测试2：诱盘信号 ===")
    print(json.dumps(result2, ensure_ascii=False, indent=2))
    
    # 测试3：强烈看好信号
    result3 = risk.run({
        "home_team": "水晶宫",
        "away_team": "西汉姆联",
        "home_win": 40,
        "draw": 30,
        "away_win": 30,
        "market_odds": {"home_win": 2.55, "draw": 3.30, "away_win": 2.80},
        "base_kelly": 0.05,
        "money_flow_analysis": {
            "signal": "STRONG_AWAY",
            "confidence": 0.85,
            "key_insights": ["客胜成交量偏高", "客胜庄家亏损"],
            "risk_flags": [],
            "recommendation": "强烈看好客胜"
        }
    })
    print("\n=== 测试3：强烈看好信号 ===")
    print(json.dumps(result3, ensure_ascii=False, indent=2))
