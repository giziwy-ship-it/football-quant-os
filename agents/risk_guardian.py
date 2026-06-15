#!/usr/bin/env python3
"""RiskGuardian - Risk Monitoring & Circuit Breaker v1.0"""
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional

class RiskLevel(Enum):
    GREEN = "green"       # Normal
    YELLOW = "yellow"     # Warning
    ORANGE = "orange"     # Elevated
    RED = "red"           # Critical
    BLACK = "black"       # System halt

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
    position_id: Optional[str] = None

class RiskGuardian:
    """Real-time risk monitoring with circuit breaker logic"""
    
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
        self.positions: List[Dict] = []
        self.events: List[RiskEvent] = []
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
    
    def add_position(self, position_id: str, match_id: str, stake: float, odds: float, market: str, selection: str) -> Dict:
        """Add a position and immediately check risk"""
        pos = {
            'id': position_id, 'match_id': match_id, 'stake': stake, 'odds': odds,
            'market': market, 'selection': selection, 'added_at': datetime.now(),
            'status': 'open', 'current_value': stake,
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
        """Run full risk check across all metrics"""
        results = {}
        worst_level = RiskLevel.GREEN
        worst_action = CircuitAction.NONE
        
        for threshold in self.thresholds:
            metric_value = self._get_metric(threshold.metric)
            level = self._evaluate_level(metric_value, threshold)
            
            results[threshold.name] = {
                'metric': threshold.metric,
                'value': round(metric_value, 4),
                'threshold': level,
                'level': level.value,
            }
            
            if self._level_value(level) > self._level_value(worst_level):
                worst_level = level
                if level in (RiskLevel.ORANGE, RiskLevel.RED, RiskLevel.BLACK):
                    worst_action = threshold.action
        
        # Update system state
        if worst_level != self.current_level:
            self._trigger_action(worst_level, worst_action, results)
        
        self.current_level = worst_level
        self.active_action = worst_action
        self.circuit_breaker_active = worst_level in (RiskLevel.RED, RiskLevel.BLACK)
        
        return {
            'overall_level': worst_level.value,
            'circuit_breaker': self.circuit_breaker_active,
            'action': worst_action.value,
            'metrics': results,
            'positions': self.stats['position_count'],
            'exposure': round(self.stats['total_exposure'], 2),
            'exposure_pct': round(self.stats['total_exposure'] / self.bankroll, 2),
            'daily_pnl': round(self.daily_pnl, 2),
            'daily_pnl_pct': round(self.daily_pnl / self.bankroll, 4),
            'recommendation': self._get_recommendation(worst_level),
        }
    
    def _get_metric(self, metric_name: str) -> float:
        """Get current value for a metric"""
        if metric_name == 'exposure_pct':
            return self.stats['total_exposure'] / self.bankroll if self.bankroll > 0 else 0
        elif metric_name == 'daily_loss_pct':
            return abs(min(0, self.daily_pnl)) / self.bankroll if self.bankroll > 0 else 0
        elif metric_name == 'position_pct':
            return self.stats['largest_position'] / self.bankroll if self.bankroll > 0 else 0
        elif metric_name == 'concentration_pct':
            if not self.positions:
                return 0
            markets = {}
            for p in self.positions:
                if p['status'] == 'open':
                    m = p['market']
                    markets[m] = markets.get(m, 0) + p['stake']
            if not markets:
                return 0
            total = sum(markets.values())
            return max(markets.values()) / total if total > 0 else 0
        elif metric_name == 'odds_drift_pct':
            # Simulate odds drift
            return random.uniform(0, 0.08)
        elif metric_name == 'liquidity_ratio':
            # Simulate liquidity gap
            return random.uniform(0, 0.4)
        elif metric_name == 'volatility':
            # Simulate volatility
            return random.uniform(0, 0.3)
        elif metric_name == 'latency_ms':
            return random.uniform(50, 800)
        return 0.0
    
    def _evaluate_level(self, value: float, threshold: RiskThreshold) -> RiskLevel:
        if value >= threshold.black:
            return RiskLevel.BLACK
        elif value >= threshold.red:
            return RiskLevel.RED
        elif value >= threshold.orange:
            return RiskLevel.ORANGE
        elif value >= threshold.yellow:
            return RiskLevel.YELLOW
        return RiskLevel.GREEN
    
    def _level_value(self, level: RiskLevel) -> int:
        return {'green': 0, 'yellow': 1, 'orange': 2, 'red': 3, 'black': 4}.get(level.value, 0)
    
    def _trigger_action(self, level: RiskLevel, action: CircuitAction, results: Dict):
        event = RiskEvent(
            timestamp=datetime.now(), level=level, metric='system',
            value=0, threshold=0, message=f'Risk level changed to {level.value}',
            action_taken=action
        )
        self.events.append(event)
    
    def _get_recommendation(self, level: RiskLevel) -> str:
        recs = {
            RiskLevel.GREEN: 'NORMAL_OPS - All systems green',
            RiskLevel.YELLOW: 'WATCH_CLOSELY - Monitor metrics closely',
            RiskLevel.ORANGE: 'REDUCE_EXPOSURE - Reduce position sizes',
            RiskLevel.RED: 'SUSPEND_NEW - Halt new orders immediately',
            RiskLevel.BLACK: 'FULL_HALT - Emergency stop all trading',
        }
        return recs.get(level, 'UNKNOWN')
    
    def can_place_order(self, stake: float, odds: float, market: str) -> Dict:
        """Check if a new order can be placed under current risk constraints"""
        if self.circuit_breaker_active:
            return {'allowed': False, 'reason': f'Circuit breaker active: {self.current_level.value}'}
        
        new_exposure = self.stats['total_exposure'] + stake
        if new_exposure > self.bankroll * 0.85:
            return {'allowed': False, 'reason': 'Exceeds 85% exposure limit'}
        
        if stake > self.bankroll * 0.20:
            return {'allowed': False, 'reason': 'Single position exceeds 20% bankroll'}
        
        if self.daily_pnl < -self.max_daily_loss:
            return {'allowed': False, 'reason': 'Daily loss limit reached'}
        
        # Check market concentration
        markets = {}
        for p in self.positions:
            if p['status'] == 'open':
                m = p['market']
                markets[m] = markets.get(m, 0) + p['stake']
        markets[market] = markets.get(market, 0) + stake
        total = sum(markets.values())
        max_conc = max(markets.values()) / total if total > 0 else 0
        if max_conc > 0.75:
            return {'allowed': False, 'reason': 'Market concentration exceeds 75%'}
        
        return {'allowed': True, 'reason': 'Risk check passed'}
    
    def update_pnl(self, pnl: float):
        """Update daily P&L"""
        self.daily_pnl += pnl
        self.check_all()
    
    def get_risk_report(self) -> str:
        """Generate formatted risk report"""
        check = self.check_all()
        lines = [
            "=" * 60,
            "           RiskGuardian - Risk Monitor Report",
            "=" * 60,
            "",
            f"[SYSTEM STATUS]",
            f"  Overall Level: {check['overall_level'].upper()}",
            f"  Circuit Breaker: {'ACTIVE' if check['circuit_breaker'] else 'INACTIVE'}",
            f"  Active Action: {check['action']}",
            "",
            f"[PORTFOLIO METRICS]",
            f"  Open Positions: {check['positions']}",
            f"  Total Exposure: {check['exposure']} EUR ({check['exposure_pct']*100:.1f}%)",
            f"  Daily P&L: {check['daily_pnl']:.2f} EUR ({check['daily_pnl_pct']*100:.2f}%)",
            "",
            f"[RISK METRICS]",
        ]
        for name, data in check['metrics'].items():
            color = 'RED' if data['level'] in ('red', 'black') else 'ORG' if data['level'] == 'orange' else 'YEL' if data['level'] == 'yellow' else 'GRN'
            lines.append(f"  {color} {name}: {data['value']:.2%} (threshold: {data['level']})")
        lines.extend([
            "",
            f"[RECOMMENDATION]",
            f"  {check['recommendation']}",
            "",
            f"[ORDER GATE]",
            f"  New orders: {'ALLOWED' if not self.circuit_breaker_active else 'BLOCKED'}",
            "=" * 60,
        ])
        return "\n".join(lines)
    
    def reset_daily(self):
        """Reset daily stats"""
        self.daily_pnl = 0.0
        self.events.clear()
        self.current_level = RiskLevel.GREEN
        self.active_action = CircuitAction.NONE
        self.circuit_breaker_active = False

if __name__ == "__main__":
    guardian = RiskGuardian(bankroll=10000)
    
    print("=" * 60)
    print("RiskGuardian - Risk Monitoring System")
    print("=" * 60)
    print()
    
    # Add positions
    positions = [
        ('POS001', 'USA_PAR', 800, 1.62, '1x2', 'home'),
        ('POS002', 'GER_FRA', 1200, 2.10, '1x2', 'home'),
        ('POS003', 'BRA_ARG', 600, 0.95, 'asian', 'upper'),
        ('POS004', 'ENG_ITA', 1500, 1.85, '1x2', 'home'),
        ('POS005', 'NED_POR', 700, 0.95, 'over_under', 'over'),
    ]
    
    for pid, mid, stake, odds, market, sel in positions:
        result = guardian.add_position(pid, mid, stake, odds, market, sel)
        print(f"Added {pid}: {stake} EUR @ {odds} on {market}/{sel}")
    
    print()
    print(guardian.get_risk_report())
    
    print()
    print("[ORDER GATE CHECKS]")
    checks = [
        (500, 1.60, '1x2'),
        (3000, 2.00, '1x2'),
        (500, 0.95, 'asian'),
    ]
    for stake, odds, market in checks:
        result = guardian.can_place_order(stake, odds, market)
        status = 'ALLOWED' if result['allowed'] else 'BLOCKED'
        print(f"  Order {stake} EUR @ {odds} on {market}: {status} - {result['reason']}")
    
    print()
    print("[SIMULATED LOSS - TRIGGERING RISK LEVEL]")
    guardian.update_pnl(-1200)  # -12% daily loss
    print(guardian.get_risk_report())
    
    print()
    print("[ORDER GATE AFTER LOSS]")
    result = guardian.can_place_order(500, 1.60, '1x2')
    status = 'ALLOWED' if result['allowed'] else 'BLOCKED'
    print(f"  Order 500 EUR: {status} - {result['reason']}")
