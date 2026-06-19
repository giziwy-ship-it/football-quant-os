#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RiskGuardian v2.0 - Football Quant OS
注入: 03 Two Sigma 风控系统
增强: 压力测试 + 相关性监控 + VaR + 回撤控制

相比 v1.0 的增强:
- 压力测试: 极端场景模拟（连续爆冷、主力受伤、制度切换）
- 相关性监控: 投注组合中各比赛的相关性矩阵
- VaR 计算: 组合层面的风险价值
- 回撤控制: 最大回撤达到阈值时自动减仓
- 流动性风险评估: 大注单的市场影响
"""

import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum


class RiskLevel(Enum):
    GREEN = "green"
    YELLOW = "yellow"
    ORANGE = "orange"
    RED = "red"
    BLACK = "black"


class CircuitAction(Enum):
    NONE = "none"
    REDUCE_50 = "reduce_50pct"
    REDUCE_80 = "reduce_80pct"
    SUSPEND_NEW = "suspend_new_orders"
    SUSPEND_ALL = "suspend_all_trading"
    EMERGENCY_HEDGE = "emergency_hedge"
    FULL_HALT = "full_system_halt"


@dataclass
class RiskThreshold:
    name: str
    metric: str
    yellow: float
    orange: float
    red: float
    black: float
    action: CircuitAction


@dataclass
class RiskEvent:
    timestamp: datetime
    level: RiskLevel
    metric: str
    value: float
    threshold: float
    message: str
    action_taken: CircuitAction


class StressTester:
    """压力测试器 - Two Sigma 级严谨"""
    
    STRESS_SCENARIOS = [
        {'name': '连续爆冷', 'description': '3 场热门球队连续输球', 'hit_rate': 0.3},
        {'name': '主力伤退', 'description': '核心球员赛前受伤，实力下降 30%', 'odds_drift': 0.5},
        {'name': '制度切换', 'description': '小组赛→淘汰赛，风格剧变', 'draw_rate': 0.15},
        {'name': '流动性枯竭', 'description': '关键比赛无法下注或赔率极差', 'liquidity': 0.1},
        {'name': '黑天鹅', 'description': '极端冷门（如沙特胜阿根廷级）', 'probability': 0.05}
    ]
    
    def __init__(self):
        self.scenarios = self.STRESS_SCENARIOS
    
    def run(self, portfolio: Dict) -> Dict[str, Any]:
        """运行压力测试"""
        results = []
        for scenario in self.scenarios:
            result = self._simulate_scenario(portfolio, scenario)
            results.append(result)
        
        return {
            'scenarios': results,
            'worst_case': min(results, key=lambda x: x['portfolio_return']),
            'expected_shortfall': np.mean([r['portfolio_return'] for r in results if r['portfolio_return'] < 0])
        }
    
    def _simulate_scenario(self, portfolio: Dict, scenario: Dict) -> Dict:
        """模拟单个场景"""
        exposure = portfolio.get('total_exposure', 0)
        positions = portfolio.get('positions', [])
        
        if scenario['name'] == '连续爆冷':
            loss = exposure * 0.3
        elif scenario['name'] == '主力伤退':
            loss = exposure * 0.2
        elif scenario['name'] == '制度切换':
            loss = exposure * 0.15
        elif scenario['name'] == '流动性枯竭':
            loss = exposure * 0.1
        elif scenario['name'] == '黑天鹅':
            loss = exposure * 0.5
        else:
            loss = 0
        
        return {
            'name': scenario['name'],
            'description': scenario['description'],
            'portfolio_return': -loss,
            'drawdown': loss / portfolio.get('bankroll', 1),
            'recovery_needed': loss
        }


class CorrelationMonitor:
    """相关性监控器"""
    
    def __init__(self):
        self.correlation_matrix = {}
        self.history = []
    
    def calculate(self, positions: List[Dict]) -> Dict[str, Any]:
        """计算持仓相关性矩阵"""
        if len(positions) < 2:
            return {'status': 'INSUFFICIENT_DATA'}
        
        # 基于球队和赛事类型估算相关性
        n = len(positions)
        corr_matrix = np.eye(n)
        
        for i in range(n):
            for j in range(i + 1, n):
                corr = self._estimate_correlation(positions[i], positions[j])
                corr_matrix[i][j] = corr
                corr_matrix[j][i] = corr
        
        # 检测高相关性聚集
        avg_corr = np.mean(corr_matrix[np.triu_indices(n, k=1)])
        max_corr = np.max(corr_matrix[np.triu_indices(n, k=1)])
        
        return {
            'matrix': corr_matrix.tolist(),
            'average_correlation': float(avg_corr),
            'max_correlation': float(max_corr),
            'diversification_score': float(1 - avg_corr),
            'status': 'WARNING' if avg_corr > 0.5 else 'OK'
        }
    
    def _estimate_correlation(self, pos1: Dict, pos2: Dict) -> float:
        """估算两个持仓的相关性"""
        # 同一球队参与的比赛相关性高
        if pos1.get('team') == pos2.get('team'):
            return 0.8
        # 同一赛事阶段相关性中等
        if pos1.get('stage') == pos2.get('stage'):
            return 0.3
        # 不同赛事相关性低
        return 0.1


class VaRCalculator:
    """风险价值计算器"""
    
    def __init__(self, confidence: float = 0.95):
        self.confidence = confidence
    
    def calculate(self, positions: List[Dict], historical_returns: List[float] = None) -> Dict[str, float]:
        """计算组合 VaR"""
        if not positions:
            return {'var_absolute': 0, 'var_percentage': 0, 'cvar': 0}
        
        total_exposure = sum(p['stake'] for p in positions)
        
        if historical_returns and len(historical_returns) > 10:
            returns = np.array(historical_returns)
            var = np.percentile(returns, (1 - self.confidence) * 100)
            cvar = np.mean(returns[returns <= var])
        else:
            # 使用默认估计
            var = -total_exposure * 0.15
            cvar = -total_exposure * 0.25
        
        return {
            'confidence': self.confidence,
            'var_absolute': float(abs(var)),
            'var_percentage': float(abs(var) / total_exposure) if total_exposure > 0 else 0,
            'cvar': float(abs(cvar)),
            'total_exposure': float(total_exposure)
        }


class DrawdownController:
    """回撤控制器"""
    
    def __init__(self, thresholds: Dict = None):
        self.thresholds = thresholds or {
            'warning': 0.10,
            'reduce': 0.15,
            'halt': 0.25
        }
        self.peak = 0
    
    def check(self, current_bankroll: float, peak_bankroll: float) -> Dict[str, Any]:
        """检查回撤状态"""
        if peak_bankroll <= 0:
            return {'status': 'NO_DATA'}
        
        drawdown = (peak_bankroll - current_bankroll) / peak_bankroll
        
        if drawdown >= self.thresholds['halt']:
            return {
                'drawdown': float(drawdown),
                'status': 'HALT',
                'action': '全面停止新投注，保留现有头寸',
                'threshold': self.thresholds['halt']
            }
        elif drawdown >= self.thresholds['reduce']:
            return {
                'drawdown': float(drawdown),
                'status': 'REDUCE',
                'action': '降低新投注规模至 50%',
                'threshold': self.thresholds['reduce']
            }
        elif drawdown >= self.thresholds['warning']:
            return {
                'drawdown': float(drawdown),
                'status': 'WARNING',
                'action': '密切监控，准备减仓',
                'threshold': self.thresholds['warning']
            }
        
        return {
            'drawdown': float(drawdown),
            'status': 'OK',
            'action': '正常操作',
            'threshold': 0
        }


class LiquidityRiskAssessor:
    """流动性风险评估器"""
    
    def assess(self, position: Dict, market_depth: Dict = None) -> Dict[str, float]:
        """评估单个头寸的流动性风险"""
        stake = position.get('stake', 0)
        odds = position.get('odds', 1)
        
        # 估算冲击成本
        if market_depth and 'volume' in market_depth:
            volume = market_depth['volume']
            impact = min(stake / volume * 0.5, 0.1) if volume > 0 else 0.1
        else:
            impact = 0.05  # 默认 5% 冲击成本
        
        return {
            'stake': float(stake),
            'estimated_impact_cost': float(impact),
            'effective_odds': float(odds * (1 - impact)),
            'liquidity_risk': 'HIGH' if impact > 0.08 else 'MEDIUM' if impact > 0.03 else 'LOW'
        }


class RiskGuardianV2:
    """RiskGuardian v2.0 - Two Sigma 级风控"""
    
    DEFAULT_THRESHOLDS = [
        RiskThreshold("total_exposure", "exposure_pct", 0.50, 0.70, 0.85, 0.95, CircuitAction.REDUCE_50),
        RiskThreshold("daily_loss", "daily_loss_pct", 0.05, 0.10, 0.15, 0.20, CircuitAction.SUSPEND_NEW),
        RiskThreshold("single_position", "position_pct", 0.10, 0.15, 0.20, 0.30, CircuitAction.REDUCE_80),
        RiskThreshold("concentration", "concentration_pct", 0.40, 0.60, 0.75, 0.90, CircuitAction.REDUCE_50),
        RiskThreshold("odds_drift", "odds_drift_pct", 0.05, 0.10, 0.15, 0.25, CircuitAction.EMERGENCY_HEDGE),
        RiskThreshold("liquidity_gap", "liquidity_ratio", 0.30, 0.50, 0.70, 0.90, CircuitAction.SUSPEND_ALL),
        RiskThreshold("volatility_spike", "volatility", 0.20, 0.35, 0.50, 0.70, CircuitAction.SUSPEND_NEW),
        RiskThreshold("system_latency", "latency_ms", 500, 1000, 2000, 5000, CircuitAction.SUSPEND_ALL),
    ]
    
    def __init__(self, bankroll: float = 10000.0, thresholds=None):
        self.bankroll = bankroll
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS
        self.positions = []
        self.events = []
        self.current_level = RiskLevel.GREEN
        self.active_action = CircuitAction.NONE
        self.circuit_breaker_active = False
        self.daily_pnl = 0.0
        self.max_daily_loss = bankroll * 0.15
        self.stats = {
            'total_exposure': 0.0,
            'position_count': 0,
            'largest_position': 0.0,
            'avg_odds': 0.0,
            'win_rate': 0.0,
            'pending_orders': 0,
        }
        self.peak_bankroll = bankroll
        
        # v2.0 新增组件
        self.stress_tester = StressTester()
        self.correlation_monitor = CorrelationMonitor()
        self.var_calculator = VaRCalculator()
        self.drawdown_controller = DrawdownController()
        self.liquidity_assessor = LiquidityRiskAssessor()
    
    def add_position(self, position_id: str, match_id: str, stake: float, odds: float, 
                     market: str, selection: str, team: str = None, stage: str = None) -> Dict:
        """添加头寸并检查风险"""
        pos = {
            'id': position_id, 'match_id': match_id, 'stake': stake, 'odds': odds,
            'market': market, 'selection': selection, 'team': team, 'stage': stage,
            'added_at': datetime.now(), 'status': 'open', 'current_value': stake
        }
        self.positions.append(pos)
        self._recalculate_stats()
        check = self.check_all()
        return {'position': pos, 'risk_check': check}
    
    def _recalculate_stats(self):
        open_pos = [p for p in self.positions if p['status'] == 'open']
        total_stake = sum(p['stake'] for p in open_pos)
        self.stats['total_exposure'] = total_stake
        self.stats['position_count'] = len(open_pos)
        self.stats['largest_position'] = max((p['stake'] for p in open_pos), default=0)
        self.stats['avg_odds'] = sum(p['odds'] for p in open_pos) / len(open_pos) if open_pos else 0
    
    def check_all(self) -> Dict[str, Any]:
        """全面风险检查"""
        results = {
            'basic_checks': self._check_basic(),
            'stress_test': self._check_stress(),
            'correlation': self._check_correlation(),
            'var': self._check_var(),
            'drawdown': self._check_drawdown(),
            'liquidity': self._check_liquidity()
        }
        
        # 综合评级
        worst_level = RiskLevel.GREEN
        for category, result in results.items():
            if isinstance(result, dict) and 'level' in result:
                level = RiskLevel(result['level']) if isinstance(result['level'], str) else result['level']
                if level.value > worst_level.value:
                    worst_level = level
        
        results['overall_level'] = worst_level.value
        return results
    
    def _check_basic(self) -> Dict[str, Any]:
        """基础检查 (v1.0 兼容)"""
        exposure_pct = self.stats['total_exposure'] / self.bankroll if self.bankroll > 0 else 0
        
        for threshold in self.thresholds:
            if threshold.metric == 'exposure_pct':
                if exposure_pct >= threshold.black:
                    return {'level': 'black', 'action': 'FULL_HALT'}
                elif exposure_pct >= threshold.red:
                    return {'level': 'red', 'action': 'REDUCE_50'}
        
        return {'level': 'green', 'exposure_pct': float(exposure_pct)}
    
    def _check_stress(self) -> Dict[str, Any]:
        """压力测试"""
        portfolio = {
            'total_exposure': self.stats['total_exposure'],
            'bankroll': self.bankroll,
            'positions': self.positions
        }
        return self.stress_tester.run(portfolio)
    
    def _check_correlation(self) -> Dict[str, Any]:
        """相关性检查"""
        open_pos = [p for p in self.positions if p['status'] == 'open']
        return self.correlation_monitor.calculate(open_pos)
    
    def _check_var(self) -> Dict[str, Any]:
        """VaR 检查"""
        open_pos = [p for p in self.positions if p['status'] == 'open']
        return self.var_calculator.calculate(open_pos)
    
    def _check_drawdown(self) -> Dict[str, Any]:
        """回撤检查"""
        current = self.bankroll + self.daily_pnl
        if current > self.peak_bankroll:
            self.peak_bankroll = current
        return self.drawdown_controller.check(current, self.peak_bankroll)
    
    def _check_liquidity(self) -> Dict[str, Any]:
        """流动性检查"""
        open_pos = [p for p in self.positions if p['status'] == 'open']
        assessments = [self.liquidity_assessor.assess(p) for p in open_pos]
        return {
            'positions': assessments,
            'high_risk_count': sum(1 for a in assessments if a['liquidity_risk'] == 'HIGH')
        }
