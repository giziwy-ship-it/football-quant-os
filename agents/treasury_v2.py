#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TreasuryAgent v2.0 - Football Quant OS
注入: 12 Man Group 组合优化
增强: 多策略资金分配 + Black-Litterman + 风险平价 + 约束框架

相比 v1.0:
- 多策略资金分配: 不同预测模型的资金分配
- Black-Litterman: 结合市场赔率 + 模型预测
- 风险平价: 每个策略贡献相等风险
- 约束框架: 单场上限/单日上限/总敞口上限
- 场景分析: 不同赛事密度下的资金分配
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math
import numpy as np


@dataclass
class Position:
    """持仓记录"""
    match_id: str
    market: str
    selection: str
    odds: float
    stake: float
    expected_value: float
    model_confidence: float
    strategy_id: str
    timestamp: datetime
    status: str = "open"
    result: Optional[str] = None
    payout: float = 0.0
    pnl: float = 0.0


@dataclass
class BankrollState:
    """资金池状态"""
    total_funds: float = 100000.0
    available: float = 65000.0
    locked: float = 25000.0
    reserve: float = 10000.0
    daily_limit: float = 15000.0
    daily_used: float = 0.0
    unit_size: float = 500.0
    currency: str = "EUR"
    
    @property
    def exposure_pct(self) -> float:
        return self.locked / self.total_funds if self.total_funds > 0 else 0
    
    @property
    def reserve_pct(self) -> float:
        return self.reserve / self.total_funds if self.total_funds > 0 else 0


class StrategyAllocator:
    """策略分配器 - Black-Litterman + 风险平价"""
    
    def __init__(self, strategies: List[str] = None):
        self.strategies = strategies or ['heuristic', 'poisson', 'xgboost', 'ensemble']
        self.returns_history = {s: [] for s in self.strategies}
        self.confidence_map = {s: 0.5 for s in self.strategies}
    
    def black_litterman(self, market_views: Dict[str, float], 
                        market_caps: Dict[str, float] = None) -> Dict[str, float]:
        """
        Black-Litterman 模型
        
        结合市场赔率（先验）+ 模型预测（观点）
        """
        if market_caps is None:
            market_caps = {s: 1.0 / len(self.strategies) for s in self.strategies}
        
        # 市场均衡权重
        equilibrium = market_caps
        
        # 投资者观点
        views = market_views
        
        # 合并（简化版）
        tau = 0.05  # 不确定性参数
        weights = {}
        
        for strategy in self.strategies:
            market_weight = equilibrium.get(strategy, 0.25)
            view_weight = views.get(strategy, 0.5)
            
            # 加权平均
            weights[strategy] = (1 - tau) * market_weight + tau * view_weight
        
        # 归一化
        total = sum(weights.values())
        return {k: v / total for k, v in weights.items()}
    
    def risk_parity(self, risks: Dict[str, float]) -> Dict[str, float]:
        """
        风险平价分配
        
        每个策略对组合风险的贡献相等
        """
        inverse_risks = {k: 1.0 / max(v, 0.001) for k, v in risks.items()}
        total = sum(inverse_risks.values())
        return {k: v / total for k, v in inverse_risks.items()}
    
    def ic_weighted(self, ics: Dict[str, float]) -> Dict[str, float]:
        """
        IC 加权分配
        
        根据近期信息系数分配权重
        """
        positive_ics = {k: max(v, 0.01) for k, v in ics.items()}
        total = sum(positive_ics.values())
        return {k: v / total for k, v in positive_ics.items()}
    
    def allocate(self, method: str = 'black_litterman', **kwargs) -> Dict[str, float]:
        """执行分配"""
        if method == 'black_litterman':
            return self.black_litterman(kwargs.get('views', {}))
        elif method == 'risk_parity':
            return self.risk_parity(kwargs.get('risks', {s: 0.2 for s in self.strategies}))
        elif method == 'ic_weighted':
            return self.ic_weighted(kwargs.get('ics', {s: 0.05 for s in self.strategies}))
        elif method == 'equal':
            return {s: 1.0 / len(self.strategies) for s in self.strategies}
        else:
            return self.black_litterman(kwargs.get('views', {}))


class ConstraintManager:
    """约束管理器"""
    
    DEFAULT_CONSTRAINTS = {
        'max_single_position': 0.05,      # 单头寸 5%
        'max_daily_exposure': 0.15,       # 日敞口 15%
        'max_total_exposure': 0.50,      # 总敞口 50%
        'max_single_match': 0.10,        # 单场比赛 10%
        'max_industry_concentration': 0.30,  # 集中度 30%
        'min_reserve': 0.10,             # 储备金 10%
    }
    
    def __init__(self, constraints: Dict[str, float] = None):
        self.constraints = constraints or self.DEFAULT_CONSTRAINTS
    
    def check(self, proposal: Dict[str, Any], current_state: BankrollState) -> Dict[str, Any]:
        """检查约束是否满足"""
        violations = []
        
        # 检查单头寸
        stake = proposal.get('stake', 0)
        if stake / current_state.total_funds > self.constraints['max_single_position']:
            violations.append({
                'type': 'MAX_SINGLE_POSITION',
                'limit': self.constraints['max_single_position'],
                'actual': round(stake / current_state.total_funds, 4),
                'message': '单头寸超过限制'
            })
        
        # 检查日敞口
        if (current_state.daily_used + stake) / current_state.total_funds > self.constraints['max_daily_exposure']:
            violations.append({
                'type': 'MAX_DAILY_EXPOSURE',
                'limit': self.constraints['max_daily_exposure'],
                'actual': round((current_state.daily_used + stake) / current_state.total_funds, 4),
                'message': '日敞口超过限制'
            })
        
        # 检查总敞口
        if (current_state.locked + stake) / current_state.total_funds > self.constraints['max_total_exposure']:
            violations.append({
                'type': 'MAX_TOTAL_EXPOSURE',
                'limit': self.constraints['max_total_exposure'],
                'actual': round((current_state.locked + stake) / current_state.total_funds, 4),
                'message': '总敞口超过限制'
            })
        
        # 检查储备金
        if (current_state.total_funds - current_state.locked - stake) / current_state.total_funds < self.constraints['min_reserve']:
            violations.append({
                'type': 'MIN_RESERVE',
                'limit': self.constraints['min_reserve'],
                'actual': round((current_state.total_funds - current_state.locked - stake) / current_state.total_funds, 4),
                'message': '储备金不足'
            })
        
        return {
            'passed': len(violations) == 0,
            'violations': violations
        }
    
    def adjust_for_constraints(self, desired_stake: float, 
                               current_state: BankrollState) -> float:
        """根据约束调整注码"""
        # 检查单头寸
        max_single = current_state.total_funds * self.constraints['max_single_position']
        
        # 检查日敞口
        max_daily = current_state.total_funds * self.constraints['max_daily_exposure']
        remaining_daily = max_daily - current_state.daily_used
        
        # 检查总敞口
        max_total = current_state.total_funds * self.constraints['max_total_exposure']
        remaining_total = max_total - current_state.locked
        
        # 检查储备金
        min_reserve = current_state.total_funds * self.constraints['min_reserve']
        max_stake_reserve = current_state.total_funds - current_state.locked - min_reserve
        
        # 取最小值
        adjusted = min(desired_stake, max_single, remaining_daily, remaining_total, max_stake_reserve)
        return max(adjusted, 0)


class ScenarioAnalyzer:
    """场景分析器"""
    
    SCENARIOS = {
        'normal': {'match_density': 3, 'volatility': 0.15},
        'high_density': {'match_density': 8, 'volatility': 0.25},
        'low_density': {'match_density': 1, 'volatility': 0.10},
        'tournament_peak': {'match_density': 12, 'volatility': 0.30},
    }
    
    def analyze(self, scenario: str, bankroll: float) -> Dict[str, Any]:
        """分析场景下的资金分配建议"""
        config = self.SCENARIOS.get(scenario, self.SCENARIOS['normal'])
        density = config['match_density']
        volatility = config['volatility']
        
        # 根据密度调整单位注码
        if density <= 2:
            unit_size = bankroll * 0.02
        elif density <= 5:
            unit_size = bankroll * 0.015
        else:
            unit_size = bankroll * 0.01
        
        # 根据波动率调整储备金
        reserve = bankroll * (0.10 + volatility * 0.5)
        
        return {
            'scenario': scenario,
            'match_density': density,
            'volatility': volatility,
            'recommended_unit': round(unit_size, 2),
            'recommended_reserve': round(reserve, 2),
            'max_daily_exposure': round(bankroll * 0.15, 2),
            'max_positions': int(density * 2)
        }


class TreasuryAgentV2:
    """TreasuryAgent v2.0 - Man Group 级资金优化"""
    
    def __init__(self, 
                 initial_bankroll: float = 100000.0,
                 currency: str = "EUR",
                 reserve_pct: float = 0.10,
                 daily_limit_pct: float = 0.15,
                 max_single_pct: float = 0.05,
                 kelly_fraction: float = 0.5):
        
        self.bankroll = BankrollState(
            total_funds=initial_bankroll,
            available=initial_bankroll * (1 - reserve_pct),
            locked=0.0,
            reserve=initial_bankroll * reserve_pct,
            daily_limit=initial_bankroll * daily_limit_pct,
            daily_used=0.0,
            unit_size=initial_bankroll * 0.005,
            currency=currency
        )
        
        self.kelly_fraction = kelly_fraction
        self.positions: List[Position] = []
        self.allocator = StrategyAllocator()
        self.constraint_manager = ConstraintManager()
        self.scenario_analyzer = ScenarioAnalyzer()
        
        # 策略权重
        self.strategy_weights = {}
        
    def allocate_strategy_weights(self, method: str = 'black_litterman', **kwargs) -> Dict[str, float]:
        """分配策略权重"""
        self.strategy_weights = self.allocator.allocate(method, **kwargs)
        return self.strategy_weights
    
    def calculate_kelly(self, prob: float, odds: float) -> Dict[str, float]:
        """计算 Kelly 注码"""
        if odds <= 1 or prob <= 0 or prob >= 1:
            return {'kelly_fraction': 0, 'half_kelly': 0, 'stake': 0, 'ev': 0}
        
        b = odds - 1
        q = 1 - prob
        kelly = (b * prob - q) / b
        
        if kelly <= 0:
            return {'kelly_fraction': 0, 'half_kelly': 0, 'stake': 0, 'ev': 0}
        
        half_kelly = kelly * self.kelly_fraction
        stake = self.bankroll.total_funds * half_kelly
        
        # 应用策略权重
        if self.strategy_weights:
            # 根据策略调整注码
            pass
        
        # 约束检查
        adjusted_stake = self.constraint_manager.adjust_for_constraints(stake, self.bankroll)
        
        return {
            'kelly_fraction': round(kelly, 4),
            'half_kelly': round(half_kelly, 4),
            'stake': round(adjusted_stake, 2),
            'ev': round((prob * odds - 1) * adjusted_stake, 2)
        }
    
    def place_position(self, match_id: str, market: str, selection: str,
                       odds: float, stake: float, confidence: float,
                       strategy_id: str = 'ensemble') -> Dict[str, Any]:
        """下注意"""
        # 检查约束
        check = self.constraint_manager.check({'stake': stake}, self.bankroll)
        if not check['passed']:
            return {'error': 'Constraint violation', 'violations': check['violations']}
        
        # 创建持仓
        position = Position(
            match_id=match_id,
            market=market,
            selection=selection,
            odds=odds,
            stake=stake,
            expected_value=(odds - 1) * stake,
            model_confidence=confidence,
            strategy_id=strategy_id,
            timestamp=datetime.now()
        )
        
        self.positions.append(position)
        self.bankroll.locked += stake
        self.bankroll.available -= stake
        self.bankroll.daily_used += stake
        
        return {
            'position': position,
            'bankroll_state': self.get_bankroll_summary()
        }
    
    def get_bankroll_summary(self) -> Dict[str, Any]:
        """获取资金摘要"""
        return {
            'total_funds': self.bankroll.total_funds,
            'available': round(self.bankroll.available, 2),
            'locked': round(self.bankroll.locked, 2),
            'reserve': round(self.bankroll.reserve, 2),
            'exposure_pct': round(self.bankroll.exposure_pct, 4),
            'daily_used': round(self.bankroll.daily_used, 2),
            'daily_remaining': round(self.bankroll.daily_limit - self.bankroll.daily_used, 2),
            'open_positions': len([p for p in self.positions if p.status == 'open'])
        }
    
    def get_scenario_analysis(self, scenario: str) -> Dict[str, Any]:
        """获取场景分析"""
        return self.scenario_analyzer.analyze(scenario, self.bankroll.total_funds)
    
    def get_strategy_allocation(self) -> Dict[str, Any]:
        """获取策略分配"""
        return {
            'method': 'black_litterman',
            'weights': self.strategy_weights,
            'recommendation': self._allocation_recommendation()
        }
    
    def _allocation_recommendation(self) -> str:
        """分配建议"""
        if not self.strategy_weights:
            return '请先执行策略分配'
        
        best_strategy = max(self.strategy_weights, key=self.strategy_weights.get)
        return f'建议增加 {best_strategy} 权重至 {self.strategy_weights[best_strategy]:.1%}'


__all__ = ['TreasuryAgentV2', 'StrategyAllocator', 'ConstraintManager', 'ScenarioAnalyzer']
