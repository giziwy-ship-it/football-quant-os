#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TradingAgent v2.0 - Football Quant OS
注入: 10 Virtu 执行算法
增强: 订单拆分 + 滑点控制 + 执行质量分析 + 对账引擎

相比 v1.0:
- 订单拆分: 大单拆分为多个小单，减少市场影响
- 滑点测量: 实际赔率 vs 预期赔率的偏差
- 订单状态管理: 全生命周期跟踪
- 执行质量分析: 每笔投注的成本评估
- 对账引擎: 本地记录 vs 平台记录的一致性
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional
import numpy as np


class OrderSide(Enum):
    BACK = "back"
    LAY = "lay"


class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    ICEBERG = "iceberg"
    TWAP = "twap"
    POST = "post"


class OrderStatus(Enum):
    PENDING = "pending"
    PARTIAL = "partial"
    FILLED = "filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class Fill:
    """成交记录"""
    stake: float
    odds: float
    timestamp: datetime
    exchange: str


@dataclass
class Order:
    """增强版订单"""
    id: str
    match_id: str
    market: str
    selection: str
    side: OrderSide
    order_type: OrderType
    total_stake: float
    target_odds: float
    exchange: str
    created_at: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    filled_stake: float = 0.0
    avg_odds: float = 0.0
    slip: float = 0.0
    commission_paid: float = 0.0
    fills: List[Fill] = field(default_factory=list)
    
    # v2.0 新增
    slices: List['Order'] = field(default_factory=list)
    slice_index: int = 0
    total_slices: int = 1
    
    @property
    def remaining(self) -> float:
        return self.total_stake - self.filled_stake
    
    def update_fill(self, amount: float, price: float, exchange: str = ""):
        fill = Fill(stake=amount, odds=price, timestamp=datetime.now(), exchange=exchange)
        self.fills.append(fill)
        self.filled_stake += amount
        
        if self.filled_stake > 0:
            self.avg_odds = sum(f.stake * f.odds for f in self.fills) / self.filled_stake
        
        if self.side == OrderSide.BACK:
            self.slip = self.target_odds - self.avg_odds
        else:
            self.slip = self.avg_odds - self.target_odds
        
        if self.filled_stake >= self.total_stake - 0.01:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIAL


class OrderSlicer:
    """订单拆分器 - Virtu 级执行优化"""
    
    def __init__(self, max_slice_size: float = 500, min_slice_size: float = 50):
        self.max_slice_size = max_slice_size
        self.min_slice_size = min_slice_size
    
    def slice(self, order: Order) -> List[Order]:
        """将大单拆分为多个小单"""
        if order.total_stake <= self.max_slice_size:
            return [order]
        
        n_slices = int(np.ceil(order.total_stake / self.max_slice_size))
        slice_size = order.total_stake / n_slices
        
        slices = []
        for i in range(n_slices):
            slice_order = Order(
                id=f"{order.id}_slice_{i}",
                match_id=order.match_id,
                market=order.market,
                selection=order.selection,
                side=order.side,
                order_type=order.order_type,
                total_stake=min(slice_size, order.total_stake - i * slice_size),
                target_odds=order.target_odds,
                exchange=order.exchange,
                total_slices=n_slices,
                slice_index=i
            )
            slices.append(slice_order)
        
        return slices


class SlippageMonitor:
    """滑点监控器"""
    
    def __init__(self):
        self.slip_history = []
    
    def record(self, order: Order) -> None:
        """记录滑点"""
        if order.filled_stake > 0:
            self.slip_history.append({
                'timestamp': datetime.now().isoformat(),
                'match_id': order.match_id,
                'target_odds': order.target_odds,
                'avg_odds': order.avg_odds,
                'slip': order.slip,
                'slip_pct': order.slip / order.target_odds if order.target_odds > 0 else 0,
                'stake': order.filled_stake
            })
    
    def get_stats(self) -> Dict[str, float]:
        """获取滑点统计"""
        if not self.slip_history:
            return {'avg_slip': 0, 'max_slip': 0, 'avg_slip_pct': 0}
        
        slips = [s['slip'] for s in self.slip_history]
        slip_pcts = [s['slip_pct'] for s in self.slip_history]
        
        return {
            'avg_slip': round(np.mean(slips), 4),
            'max_slip': round(np.max(slips), 4),
            'avg_slip_pct': round(np.mean(slip_pcts), 4),
            'max_slip_pct': round(np.max(slip_pcts), 4),
            'sample_size': len(self.slip_history)
        }


class ExecutionQualityAnalyzer:
    """执行质量分析器"""
    
    def __init__(self):
        self.executions = []
    
    def analyze(self, order: Order) -> Dict[str, Any]:
        """分析单笔执行质量"""
        if order.filled_stake <= 0:
            return {'status': 'NOT_EXECUTED'}
        
        # 成本分析
        expected_cost = order.total_stake * (order.target_odds - 1)
        actual_cost = order.filled_stake * (order.avg_odds - 1)
        cost_diff = actual_cost - expected_cost
        
        # 时间分析
        execution_time = (datetime.now() - order.created_at).total_seconds()
        
        quality = {
            'order_id': order.id,
            'fill_rate': round(order.filled_stake / order.total_stake, 4),
            'slip_cost': round(cost_diff, 2),
            'slip_pct': round(order.slip / order.target_odds * 100, 2) if order.target_odds > 0 else 0,
            'execution_time': round(execution_time, 2),
            'commission': round(order.commission_paid, 2),
            'total_cost': round(cost_diff + order.commission_paid, 2),
            'quality_score': self._calculate_quality_score(order)
        }
        
        self.executions.append(quality)
        return quality
    
    def _calculate_quality_score(self, order: Order) -> float:
        """计算执行质量分数 (0-100)"""
        score = 100.0
        
        # 滑点扣分
        if order.slip > 0:
            slip_pct = order.slip / order.target_odds if order.target_odds > 0 else 0
            score -= slip_pct * 500  # 1% 滑点扣 5 分
        
        # 填充率扣分
        fill_rate = order.filled_stake / order.total_stake if order.total_stake > 0 else 0
        score -= (1 - fill_rate) * 20  # 未填充部分扣分
        
        return max(score, 0)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        if not self.executions:
            return {'status': 'NO_DATA'}
        
        scores = [e['quality_score'] for e in self.executions]
        slips = [e['slip_pct'] for e in self.executions]
        
        return {
            'total_orders': len(self.executions),
            'avg_quality_score': round(np.mean(scores), 2),
            'avg_slip_pct': round(np.mean(slips), 4),
            'best_execution': round(np.max(scores), 2),
            'worst_execution': round(np.min(scores), 2),
            'grade': 'A' if np.mean(scores) > 90 else 'B' if np.mean(scores) > 75 else 'C'
        }


class ReconciliationEngine:
    """对账引擎"""
    
    def __init__(self):
        self.discrepancies = []
    
    def reconcile(self, local_orders: List[Order], platform_records: List[Dict]) -> Dict[str, Any]:
        """对账本地记录与平台记录"""
        local_map = {o.id: o for o in local_orders}
        platform_map = {r['id']: r for r in platform_records}
        
        matched = 0
        discrepancies = []
        
        for order_id, local_order in local_map.items():
            if order_id not in platform_map:
                discrepancies.append({
                    'type': 'MISSING_PLATFORM',
                    'order_id': order_id,
                    'local_stake': local_order.filled_stake
                })
                continue
            
            platform_record = platform_map[order_id]
            
            # 检查金额一致性
            if abs(local_order.filled_stake - platform_record.get('stake', 0)) > 0.01:
                discrepancies.append({
                    'type': 'STAKE_MISMATCH',
                    'order_id': order_id,
                    'local_stake': local_order.filled_stake,
                    'platform_stake': platform_record.get('stake', 0)
                })
            
            # 检查赔率一致性
            if abs(local_order.avg_odds - platform_record.get('odds', 0)) > 0.01:
                discrepancies.append({
                    'type': 'ODDS_MISMATCH',
                    'order_id': order_id,
                    'local_odds': local_order.avg_odds,
                    'platform_odds': platform_record.get('odds', 0)
                })
            
            matched += 1
        
        self.discrepancies.extend(discrepancies)
        
        return {
            'matched': matched,
            'total_local': len(local_orders),
            'total_platform': len(platform_records),
            'discrepancies': discrepancies,
            'discrepancy_rate': len(discrepancies) / max(len(local_orders), 1),
            'status': 'RECONCILED' if not discrepancies else 'DISCREPANCY_FOUND'
        }


class TradingAgentV2:
    """TradingAgent v2.0 - Virtu 级执行优化"""
    
    def __init__(self, bankroll: float = 10000):
        self.bankroll = bankroll
        self.orders: List[Order] = []
        self.slicer = OrderSlicer()
        self.slip_monitor = SlippageMonitor()
        self.quality_analyzer = ExecutionQualityAnalyzer()
        self.reconciliation = ReconciliationEngine()
        self.stats = {
            'total_orders': 0,
            'total_filled': 0,
            'total_slip_cost': 0.0,
            'avg_execution_time': 0.0
        }
    
    def create_order(self, match_id: str, market: str, selection: str,
                     side: OrderSide, stake: float, odds: float,
                     order_type: OrderType = OrderType.LIMIT) -> Order:
        """创建订单"""
        order = Order(
            id=f"order_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self.orders)}",
            match_id=match_id,
            market=market,
            selection=selection,
            side=side,
            order_type=order_type,
            total_stake=stake,
            target_odds=odds,
            exchange="default"
        )
        
        # 如果是大单，自动拆分
        if order_type == OrderType.ICEBERG or order_type == OrderType.TWAP:
            order.slices = self.slicer.slice(order)
        
        self.orders.append(order)
        self.stats['total_orders'] += 1
        
        return order
    
    def execute_order(self, order_id: str, actual_odds: float, 
                      filled_amount: float = None) -> Dict[str, Any]:
        """执行订单"""
        order = next((o for o in self.orders if o.id == order_id), None)
        if not order:
            return {'error': 'Order not found'}
        
        fill_amount = filled_amount or order.remaining
        order.update_fill(fill_amount, actual_odds)
        
        # 记录滑点
        self.slip_monitor.record(order)
        
        # 分析执行质量
        quality = self.quality_analyzer.analyze(order)
        
        self.stats['total_filled'] += fill_amount
        
        return {
            'order': order,
            'quality': quality,
            'slip': order.slip
        }
    
    def get_slip_report(self) -> Dict[str, Any]:
        """获取滑点报告"""
        return self.slip_monitor.get_stats()
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """获取执行摘要"""
        return self.quality_analyzer.get_summary()
    
    def reconcile(self, platform_records: List[Dict]) -> Dict[str, Any]:
        """执行对账"""
        filled_orders = [o for o in self.orders if o.filled_stake > 0]
        return self.reconciliation.reconcile(filled_orders, platform_records)
    
    def get_order_lifecycle(self, order_id: str) -> Dict[str, Any]:
        """获取订单全生命周期"""
        order = next((o for o in self.orders if o.id == order_id), None)
        if not order:
            return {'error': 'Order not found'}
        
        return {
            'order_id': order.id,
            'created_at': order.created_at.isoformat(),
            'status': order.status.value,
            'total_stake': order.total_stake,
            'filled_stake': order.filled_stake,
            'target_odds': order.target_odds,
            'avg_odds': order.avg_odds,
            'slip': order.slip,
            'fills': [
                {
                    'stake': f.stake,
                    'odds': f.odds,
                    'timestamp': f.timestamp.isoformat()
                } for f in order.fills
            ]
        }
