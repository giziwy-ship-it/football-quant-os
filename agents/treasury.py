#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TreasuryAgent - 资金管理中心 v1.0
融合顶级博彩机构资金管理逻辑：动态仓位 + 组合风险 + 对冲 + 实时P&L

核心能力：
1. 动态资金池管理（多币种/多交易所）
2. 根据胜率置信度动态分配注码
3. 组合风险监控（相关性/VaR）
4. 实时P&L跟踪
5. 自动对冲
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import math


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
    timestamp: datetime
    status: str = "open"  # open / settled / cancelled
    result: Optional[str] = None  # win / loss / push
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


class TreasuryAgent:
    """
    资金管理Agent
    
    角色：Treasury Manager + Payment Manager + Settlement Analyst
    
    核心功能：
    - 动态资金池管理
    - 注码分配策略（Kelly + 风险调整）
    - 组合风险监控
    - 实时P&L跟踪
    - 结算与对冲
    """
    
    def __init__(
        self, 
        initial_bankroll: float = 100000.0,
        currency: str = "EUR",
        reserve_pct: float = 0.10,
        daily_limit_pct: float = 0.15,
        max_single_pct: float = 0.05,
        kelly_fraction: float = 0.5
    ):
        """
        初始化资金管理Agent
        
        Args:
            initial_bankroll: 初始资金池
            currency: 币种
            reserve_pct: 储备金比例（默认10%）
            daily_limit_pct: 每日最大投注比例（默认15%）
            max_single_pct: 单场最大投注比例（默认5%）
            kelly_fraction: Kelly分数（默认半Kelly=0.5）
        """
        self.bankroll = BankrollState(
            total_funds=initial_bankroll,
            available=initial_bankroll * (1 - reserve_pct),
            locked=0.0,
            reserve=initial_bankroll * reserve_pct,
            daily_limit=initial_bankroll * daily_limit_pct,
            daily_used=0.0,
            unit_size=initial_bankroll * 0.005,  # 0.5% = 标准注码单位
            currency=currency
        )
        
        self.reserve_pct = reserve_pct
        self.daily_limit_pct = daily_limit_pct
        self.max_single_pct = max_single_pct
        self.kelly_fraction = kelly_fraction
        
        # 持仓记录
        self.positions: List[Position] = []
        self.position_history: List[Position] = []
        
        # 每日重置时间
        self.last_reset = datetime.now()
        
        # 多交易所配置（预留）
        self.exchanges = {
            "betfair": {"balance": 0.0, "currency": "EUR"},
            "pinnacle": {"balance": 0.0, "currency": "EUR"},
            "bet365": {"balance": 0.0, "currency": "EUR"},
        }
        
        # 风险参数
        self.var_confidence = 0.95
        self.max_correlation = 0.7
        self.max_portfolio_variance = 0.1
    
    def _check_daily_reset(self):
        """检查是否需要重置每日限额"""
        now = datetime.now()
        if now.date() > self.last_reset.date():
            self.bankroll.daily_used = 0.0
            self.last_reset = now
    
    def allocate_stake(
        self, 
        opportunity: Dict[str, Any],
        risk_level: str = "medium",
        correlation_with_portfolio: float = 0.0
    ) -> Dict[str, Any]:
        """
        根据机会质量分配注码
        """
        self._check_daily_reset()
        
        probability = opportunity.get('probability', 0.5)
        odds = opportunity.get('odds', 2.0)
        confidence = opportunity.get('confidence', 0.5)
        
        b = odds - 1
        p = probability
        q = 1 - p
        
        if b <= 0 or p <= 0:
            return {'action': 'skip', 'reason': 'invalid', 'stake': 0.0}
        
        kelly = max(0, (b * p - q) / b)
        fraction = kelly * self.kelly_fraction
        
        risk_multipliers = {'low': 1.0, 'medium': 0.5, 'high': 0.25}
        fraction *= risk_multipliers.get(risk_level, 0.5)
        fraction *= confidence
        fraction *= (1.0 - correlation_with_portfolio * 0.5)
        
        available = self.bankroll.available
        stake = available * fraction
        
        max_single = self.bankroll.total_funds * self.max_single_pct
        max_daily = self.bankroll.daily_limit - self.bankroll.daily_used
        
        stake = min(stake, max_single, max_daily, available * 0.5)
        
        if stake < self.bankroll.unit_size:
            return {
                'action': 'skip',
                'reason': 'stake_too_small',
                'kelly': round(kelly, 4),
                'stake': 0.0,
                'unit_size': self.bankroll.unit_size
            }
        
        expected_value = (p * odds - 1) * 100
        
        return {
            'action': 'bet',
            'stake': round(stake, 2),
            'kelly': round(kelly, 4),
            'fraction': round(fraction, 4),
            'expected_value': round(expected_value, 2),
            'risk_level': risk_level,
            'confidence': confidence,
            'max_single': round(max_single, 2),
            'max_daily': round(max_daily, 2),
            'available_after': round(available - stake, 2)
        }
    
    def place_bet(self, position: Position) -> Dict[str, Any]:
        """执行投注"""
        self._check_daily_reset()
        
        if position.stake > self.bankroll.available:
            return {'success': False, 'reason': 'insufficient_funds'}
        
        if position.stake > (self.bankroll.daily_limit - self.bankroll.daily_used):
            return {'success': False, 'reason': 'daily_limit_reached'}
        
        self.bankroll.available -= position.stake
        self.bankroll.locked += position.stake
        self.bankroll.daily_used += position.stake
        
        self.positions.append(position)
        
        return {
            'success': True,
            'position': position,
            'bankroll': self.get_bankroll_summary()
        }
    
    def settle_position(self, match_id: str, result: str, actual_odds: Optional[float] = None) -> Dict[str, Any]:
        """结算持仓"""
        settled = []
        total_pnl = 0.0
        
        for pos in self.positions[:]:
            if pos.match_id == match_id and pos.status == "open":
                pos.status = "settled"
                pos.result = result
                
                odds = actual_odds or pos.odds
                
                if result == "win":
                    pos.payout = pos.stake * odds
                    pos.pnl = pos.payout - pos.stake
                elif result == "push":
                    pos.payout = pos.stake
                    pos.pnl = 0.0
                else:  # loss
                    pos.payout = 0.0
                    pos.pnl = -pos.stake
                
                # 更新资金池
                self.bankroll.locked -= pos.stake
                self.bankroll.available += pos.payout
                self.bankroll.total_funds += pos.pnl
                
                settled.append(pos)
                total_pnl += pos.pnl
                
                # 移动到历史
                self.positions.remove(pos)
                self.position_history.append(pos)
        
        return {
            'settled': len(settled),
            'total_pnl': round(total_pnl, 2),
            'bankroll': self.get_bankroll_summary()
        }
    
    def get_portfolio_risk(self) -> Dict[str, Any]:
        """计算组合风险"""
        open_positions = [p for p in self.positions if p.status == "open"]
        
        if not open_positions:
            return {
                'total_exposure': 0.0,
                'portfolio_variance': 0.0,
                'var_95': 0.0,
                'recommendation': 'maintain'
            }
        
        total_exposure = sum(p.stake for p in open_positions)
        
        # 简化的组合方差计算
        # 假设所有持仓独立（实际应该计算相关性矩阵）
        individual_vars = []
        for p in open_positions:
            p_win = p.expected_value / 100 + 1 / p.odds if p.odds > 0 else 0.5
            var = p.stake ** 2 * p_win * (1 - p_win) * (p.odds - 1) ** 2
            individual_vars.append(var)
        
        portfolio_variance = sum(individual_vars) / (total_exposure ** 2) if total_exposure > 0 else 0
        
        # 简化的VaR计算
        var_95 = total_exposure * 0.15  # 假设15%的潜在损失
        
        return {
            'total_exposure': round(total_exposure, 2),
            'num_positions': len(open_positions),
            'portfolio_variance': round(portfolio_variance, 4),
            'var_95': round(var_95, 2),
            'recommendation': 'reduce' if portfolio_variance > self.max_portfolio_variance else 'maintain',
            'exposure_pct': round(total_exposure / self.bankroll.total_funds, 4)
        }
    
    def get_pnl_report(self, days: int = 7) -> Dict[str, Any]:
        """P&L报告"""
        cutoff = datetime.now() - timedelta(days=days)
        recent = [p for p in self.position_history if p.timestamp > cutoff]
        
        total_pnl = sum(p.pnl for p in recent)
        total_stake = sum(p.stake for p in recent)
        
        wins = [p for p in recent if p.pnl > 0]
        losses = [p for p in recent if p.pnl < 0]
        
        return {
            'period': f'{days} days',
            'total_pnl': round(total_pnl, 2),
            'total_stake': round(total_stake, 2),
            'roi': round(total_pnl / total_stake * 100, 2) if total_stake > 0 else 0.0,
            'win_count': len(wins),
            'loss_count': len(losses),
            'win_rate': round(len(wins) / len(recent) * 100, 1) if recent else 0.0,
            'avg_win': round(sum(p.pnl for p in wins) / len(wins), 2) if wins else 0.0,
            'avg_loss': round(sum(p.pnl for p in losses) / len(losses), 2) if losses else 0.0,
        }
    
    def get_bankroll_summary(self) -> Dict[str, Any]:
        """资金池摘要"""
        return {
            'total_funds': round(self.bankroll.total_funds, 2),
            'available': round(self.bankroll.available, 2),
            'locked': round(self.bankroll.locked, 2),
            'reserve': round(self.bankroll.reserve, 2),
            'exposure_pct': round(self.bankroll.exposure_pct * 100, 2),
            'reserve_pct': round(self.bankroll.reserve_pct * 100, 2),
            'daily_limit': round(self.bankroll.daily_limit, 2),
            'daily_used': round(self.bankroll.daily_used, 2),
            'daily_remaining': round(self.bankroll.daily_limit - self.bankroll.daily_used, 2),
            'unit_size': round(self.bankroll.unit_size, 2),
            'open_positions': len([p for p in self.positions if p.status == "open"])
        }
    
    def get_risk_dashboard(self) -> Dict[str, Any]:
        """风险仪表盘"""
        portfolio = self.get_portfolio_risk()
        pnl = self.get_pnl_report(days=1)
        
        risk_score = 0.0
        if portfolio['exposure_pct'] > 0.5:
            risk_score += 40
        if portfolio['portfolio_variance'] > 0.05:
            risk_score += 30
        if pnl['roi'] < -10:
            risk_score += 20
        if self.bankroll.daily_used / self.bankroll.daily_limit > 0.8:
            risk_score += 10
        
        alert_level = 'green' if risk_score < 30 else 'yellow' if risk_score < 60 else 'red'
        
        return {
            'risk_score': round(risk_score, 1),
            'alert_level': alert_level,
            'portfolio': portfolio,
            'bankroll': self.get_bankroll_summary(),
            'daily_pnl': pnl,
            'timestamp': datetime.now().isoformat()
        }
    
    def hedge_recommendation(self, match_id: str) -> Optional[Dict[str, Any]]:
        """对冲建议"""
        match_positions = [p for p in self.positions if p.match_id == match_id and p.status == "open"]
        
        if not match_positions:
            return None
        
        total_exposure = sum(p.stake for p in match_positions)
        
        if total_exposure < self.bankroll.total_funds * 0.02:
            return None  # 风险太小，不需要对冲
        
        # 建议在其他结果上小额投注对冲
        # 简化版本：建议在相反方向投注10-20%
        hedge_stake = total_exposure * 0.15
        
        return {
            'match_id': match_id,
            'exposure': round(total_exposure, 2),
            'hedge_stake': round(hedge_stake, 2),
            'recommended_odds': None,  # 需要市场数据
            'reason': f'Exposure {total_exposure} exceeds 2% of bankroll'
        }
    
    def multi_currency_support(self, amounts: Dict[str, float]) -> Dict[str, Any]:
        """
        多币种支持
        
        Args:
            amounts: {'EUR': 5000, 'USD': 3000, 'GBP': 2000}
        
        Returns:
            多币种汇总
        """
        # 模拟汇率（实际应从API获取）
        rates = {'EUR': 1.0, 'USD': 0.92, 'GBP': 1.18, 'CNY': 0.13}
        
        total_eur = 0.0
        breakdown = {}
        
        for currency, amount in amounts.items():
            rate = rates.get(currency, 1.0)
            eur_value = amount * rate
            total_eur += eur_value
            breakdown[currency] = {
                'amount': amount,
                'rate': rate,
                'eur_value': round(eur_value, 2)
            }
        
        return {
            'total_eur': round(total_eur, 2),
            'breakdown': breakdown,
            'base_currency': 'EUR'
        }
    
    def monte_carlo_var(self, positions: List[Position], n_simulations: int = 10000) -> Dict[str, Any]:
        """
        蒙特卡洛VaR计算
        
        Args:
            positions: 持仓列表
            n_simulations: 模拟次数
        
        Returns:
            VaR结果
        """
        import random
        
        if not positions:
            return {'var_95': 0.0, 'var_99': 0.0, 'expected_loss': 0.0}
        
        simulated_pnls = []
        
        for _ in range(n_simulations):
            total_pnl = 0.0
            for pos in positions:
                # 模拟比赛结果
                p_win = pos.expected_value / 100 + 1 / pos.odds if pos.odds > 0 else 0.5
                p_win = max(0.01, min(0.99, p_win))
                
                if random.random() < p_win:
                    pnl = pos.stake * (pos.odds - 1)
                else:
                    pnl = -pos.stake
                
                total_pnl += pnl
            
            simulated_pnls.append(total_pnl)
        
        simulated_pnls.sort()
        
        var_95 = abs(simulated_pnls[int(n_simulations * 0.05)])
        var_99 = abs(simulated_pnls[int(n_simulations * 0.01)])
        expected_loss = sum(p for p in simulated_pnls if p < 0) / len(simulated_pnls)
        
        return {
            'var_95': round(var_95, 2),
            'var_99': round(var_99, 2),
            'expected_loss': round(expected_loss, 2),
            'n_simulations': n_simulations,
            'worst_case': round(simulated_pnls[0], 2),
            'best_case': round(simulated_pnls[-1], 2)
        }
    
    def drawdown_analysis(self) -> Dict[str, Any]:
        """
        回撤分析
        
        计算最大回撤和当前回撤状态
        """
        # 基于历史P&L计算回撤
        sorted_history = sorted(self.position_history, key=lambda p: p.timestamp)
        
        if not sorted_history:
            return {'max_drawdown': 0.0, 'current_drawdown': 0.0, 'status': 'no_data'}
        
        cumulative = 0.0
        peak = 0.0
        max_drawdown = 0.0
        
        for pos in sorted_history:
            cumulative += pos.pnl
            if cumulative > peak:
                peak = cumulative
            
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        current_drawdown = peak - cumulative if cumulative < peak else 0.0
        
        # 回撤状态
        max_dd_pct = max_drawdown / self.bankroll.total_funds * 100
        current_dd_pct = current_drawdown / self.bankroll.total_funds * 100
        
        status = 'green' if current_dd_pct < 5 else 'yellow' if current_dd_pct < 10 else 'red'
        
        return {
            'max_drawdown': round(max_drawdown, 2),
            'max_drawdown_pct': round(max_dd_pct, 2),
            'current_drawdown': round(current_drawdown, 2),
            'current_drawdown_pct': round(current_dd_pct, 2),
            'status': status,
            'peak': round(peak, 2),
            'current': round(cumulative, 2)
        }
    
    def markowitz_optimization(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Markowitz组合优化
        
        在风险调整的基础上最大化收益
        
        Args:
            opportunities: 机会列表，每个包含 'probability', 'odds', 'confidence', 'expected_value'
        """
        if not opportunities:
            return {'optimal_allocation': [], 'expected_return': 0.0, 'portfolio_risk': 0.0}
        
        # 简化版本：按夏普比率排序，分配资金
        sharpe_ratios = []
        for i, opp in enumerate(opportunities):
            ev = opp.get('expected_value', 0) / 100
            risk = 1 - opp.get('confidence', 0.5)
            sharpe = ev / risk if risk > 0 else 0
            sharpe_ratios.append({
                'index': i,
                'sharpe': sharpe,
                'opportunity': opp
            })
        
        sharpe_ratios.sort(key=lambda x: x['sharpe'], reverse=True)
        
        # 分配资金：前3个机会分配大部分资金
        allocations = []
        remaining_bankroll = self.bankroll.available * 0.8  # 保留20%作为缓冲
        
        for i, item in enumerate(sharpe_ratios[:3]):
            weight = [0.5, 0.3, 0.2][i] if i < 3 else 0.0
            stake = remaining_bankroll * weight
            
            opp = item['opportunity']
            allocation = self.allocate_stake(opp, risk_level="medium")
            
            if allocation['action'] == 'bet':
                allocations.append({
                    'opportunity': opp,
                    'sharpe': round(item['sharpe'], 2),
                    'weight': weight,
                    'stake': min(allocation['stake'], stake),
                    'expected_value': allocation['expected_value']
                })
        
        total_expected = sum(a['stake'] * a['expected_value'] / 100 for a in allocations)
        total_stake = sum(a['stake'] for a in allocations)
        
        return {
            'optimal_allocation': allocations,
            'expected_return': round(total_expected, 2),
            'total_stake': round(total_stake, 2),
            'portfolio_risk': round(sum(a['stake'] * (1 - a['opportunity']['confidence']) for a in allocations) / total_stake, 4) if total_stake > 0 else 0.0
        }


# ========== 快速测试 ==========
if __name__ == "__main__":
    treasury = TreasuryAgent(initial_bankroll=10000.0)
    
    print("=" * 60)
    print("           TreasuryAgent 资金管理中心")
    print("=" * 60)
    
    print("\n【初始资金池】")
    summary = treasury.get_bankroll_summary()
    for k, v in summary.items():
        print(f"  {k}: {v}")
    
    print("\n【测试注码分配】")
    opportunity = {'probability': 0.58, 'odds': 2.07, 'confidence': 0.72}
    allocation = treasury.allocate_stake(opportunity, risk_level="medium")
    for k, v in allocation.items():
        print(f"  {k}: {v}")
    
    print("\n【模拟投注】")
    if allocation['action'] == 'bet':
        pos = Position(
            match_id="USA_PAR_20260613",
            market="1X2",
            selection="home",
            odds=2.07,
            stake=allocation['stake'],
            expected_value=allocation['expected_value'],
            model_confidence=0.72,
            timestamp=datetime.now()
        )
        result = treasury.place_bet(pos)
        print(f"  投注成功: {result['success']}")
        print(f"  持仓后资金: {result['bankroll']['available']}")
    
    print("\n【风险仪表盘】")
    dashboard = treasury.get_risk_dashboard()
    print(f"  风险分数: {dashboard['risk_score']}")
    print(f"  警报级别: {dashboard['alert_level']}")
    
    print("\n【模拟结算（赢）】")
    settlement = treasury.settle_position("USA_PAR_20260613", "win")
    print(f"  结算数量: {settlement['settled']}")
    print(f"  P&L: {settlement['total_pnl']}")
    print(f"  结算后资金: {settlement['bankroll']['total_funds']}")
    
    print("\n【P&L报告】")
    pnl = treasury.get_pnl_report(days=7)
    for k, v in pnl.items():
        print(f"  {k}: {v}")
