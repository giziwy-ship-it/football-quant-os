#!/usr/bin/env python3
"""TradingAgent - Trading Execution Engine v1.0"""
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, List, Optional

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

class ExchangeName(Enum):
    BETFAIR = "betfair"
    PINNACLE = "pinnacle"
    BET365 = "bet365"
    ASIANS = "asians"
    SBOBET = "sbobet"
    BETDAQ = "betdaq"
    MATCHBOOK = "matchbook"

@dataclass
class Exchange:
    name: ExchangeName
    display_name: str
    commission: float
    min_stake: float
    max_stake: float
    liquidity_score: float
    latency_ms: float
    available: bool = True
    currencies: List[str] = field(default_factory=lambda: ["EUR"])

    def commission_cost(self, stake: float, odds: float) -> float:
        return stake * (odds - 1) * self.commission

@dataclass
class Order:
    id: str
    match_id: str
    market: str
    selection: str
    side: OrderSide
    order_type: OrderType
    stake: float
    odds: float
    exchange: ExchangeName
    created_at: datetime = field(default_factory=datetime.now)
    status: OrderStatus = OrderStatus.PENDING
    filled_stake: float = 0.0
    avg_odds: float = 0.0
    slip: float = 0.0
    commission_paid: float = 0.0
    fills: List[Dict] = field(default_factory=list)

    @property
    def remaining(self) -> float:
        return self.stake - self.filled_stake

    def update_fill(self, amount: float, price: float):
        self.fills.append({'stake': amount, 'odds': price})
        self.filled_stake += amount
        self.avg_odds = sum(f['stake']*f['odds'] for f in self.fills) / self.filled_stake
        if self.side == OrderSide.BACK:
            self.slip = self.odds - self.avg_odds
        else:
            self.slip = self.avg_odds - self.odds
        if self.filled_stake >= self.stake - 0.01:
            self.status = OrderStatus.FILLED
        else:
            self.status = OrderStatus.PARTIAL

class TradingAgent:
    EXCHANGES = {
        ExchangeName.BETFAIR: Exchange(ExchangeName.BETFAIR, "Betfair", 0.02, 2.0, 10000.0, 0.95, 45),
        ExchangeName.PINNACLE: Exchange(ExchangeName.PINNACLE, "Pinnacle", 0.00, 1.0, 50000.0, 0.90, 80),
        ExchangeName.BET365: Exchange(ExchangeName.BET365, "Bet365", 0.00, 0.5, 5000.0, 0.85, 120),
        ExchangeName.ASIANS: Exchange(ExchangeName.ASIANS, "Asian Markets", 0.00, 5.0, 100000.0, 0.98, 60),
        ExchangeName.SBOBET: Exchange(ExchangeName.SBOBET, "SBOBET", 0.00, 1.0, 20000.0, 0.88, 55),
        ExchangeName.BETDAQ: Exchange(ExchangeName.BETDAQ, "BETDAQ", 0.02, 2.0, 8000.0, 0.75, 50),
        ExchangeName.MATCHBOOK: Exchange(ExchangeName.MATCHBOOK, "Matchbook", 0.01, 1.0, 15000.0, 0.80, 40),
    }

    BASE_ODDS = {
        '1x2': {'home': 1.62, 'draw': 4.27, 'away': 5.84},
        'asian': {'upper': 0.95, 'lower': 0.95},
        'over_under': {'over': 0.95, 'under': 0.63},
    }

    EXCHANGE_BIAS = {
        ExchangeName.BETFAIR: 0.0,
        ExchangeName.PINNACLE: -0.01,
        ExchangeName.BET365: +0.02,
        ExchangeName.ASIANS: -0.02,
        ExchangeName.SBOBET: -0.01,
        ExchangeName.BETDAQ: +0.01,
        ExchangeName.MATCHBOOK: 0.0,
    }

    def __init__(self):
        self.orders: Dict[str, Order] = {}

    def _get_odds(self, exchange: ExchangeName, market: str, selection: str) -> Optional[float]:
        o = self.BASE_ODDS.get(market, {}).get(selection)
        return round(o + self.EXCHANGE_BIAS.get(exchange, 0), 2) if o else None

    def route(self, market: str, selection: str, side: OrderSide, target_odds: float, stake: float) -> List[Dict]:
        candidates = []
        for name, ex in self.EXCHANGES.items():
            if not ex.available or stake < ex.min_stake:
                continue
            odds = self._get_odds(name, market, selection)
            if odds is None:
                continue
            if side == OrderSide.BACK:
                odds_score = min(1.0, odds / target_odds) if target_odds > 0 else 0
            else:
                odds_score = min(1.0, target_odds / odds) if odds > 0 else 0
            latency_score = max(0, 1.0 - ex.latency_ms / 200)
            cost_score = 1.0 - ex.commission * 10
            score = odds_score * 0.35 + ex.liquidity_score * 0.30 + latency_score * 0.15 + cost_score * 0.20
            candidates.append({
                'exchange': name, 'display': ex.display_name, 'odds': odds,
                'commission': round(ex.commission_cost(stake, odds), 2),
                'latency': ex.latency_ms, 'liquidity': ex.liquidity_score,
                'score': round(score, 3), 'recommendation': 'GO' if score > 0.7 else 'CAUTION' if score > 0.4 else 'SKIP'
            })
        candidates.sort(key=lambda x: x['score'], reverse=True)
        return candidates

    def submit(self, match_id: str, market: str, selection: str, side: OrderSide, order_type: OrderType, stake: float, odds: float, exchange: ExchangeName, **kwargs) -> Order:
        oid = f"ORD_{match_id}_{exchange.value}_{datetime.now().strftime('%H%M%S%f')}_{random.randint(1000,9999)}"
        order = Order(id=oid, match_id=match_id, market=market, selection=selection, side=side, order_type=order_type, stake=stake, odds=odds, exchange=exchange)
        self.orders[oid] = order
        self._execute(order)
        return order

    def _execute(self, order: Order):
        ex = self.EXCHANGES.get(order.exchange)
        if not ex or not ex.available:
            order.status = OrderStatus.REJECTED
            return
        available = self._get_odds(order.exchange, order.market, order.selection)
        if available is None:
            order.status = OrderStatus.REJECTED
            return
        if order.order_type == OrderType.MARKET:
            fill_odds = available + random.uniform(-0.02, 0.01)
            order.update_fill(order.stake, fill_odds)
            order.commission_paid = ex.commission_cost(order.stake, fill_odds)
            order.status = OrderStatus.FILLED
        elif order.order_type == OrderType.LIMIT:
            if (order.side == OrderSide.BACK and available >= order.odds) or (order.side == OrderSide.LAY and available <= order.odds):
                order.update_fill(order.stake, order.odds)
                order.commission_paid = ex.commission_cost(order.stake, order.odds)
                order.status = OrderStatus.FILLED
            else:
                fill_stake = order.stake * random.uniform(0.3, 0.7)
                order.update_fill(fill_stake, available)
                order.commission_paid = ex.commission_cost(fill_stake, available)
                order.status = OrderStatus.PARTIAL
        elif order.order_type == OrderType.ICEBERG:
            batch = order.stake / 5
            for i in range(5):
                slip = random.uniform(-0.01, 0.02) * (i + 1) / 5
                order.update_fill(min(batch, order.remaining), available + slip)
                order.commission_paid += ex.commission_cost(batch, available + slip)
            order.status = OrderStatus.FILLED if order.remaining < 0.01 else OrderStatus.PARTIAL
        elif order.order_type == OrderType.TWAP:
            slice_stake = order.stake / 10
            for _ in range(10):
                order.update_fill(slice_stake, available + random.uniform(-0.02, 0.02))
                order.commission_paid += ex.commission_cost(slice_stake, available)
            order.status = OrderStatus.FILLED
        elif order.order_type == OrderType.POST:
            if random.random() > 0.5:
                fill_stake = order.stake * random.uniform(0.5, 1.0)
                order.update_fill(fill_stake, order.odds)
                order.commission_paid = ex.commission_cost(fill_stake, order.odds)
                order.status = OrderStatus.FILLED if order.remaining < 0.01 else OrderStatus.PARTIAL
            else:
                order.status = OrderStatus.PENDING

    def status(self, order_id: str) -> Optional[Dict]:
        o = self.orders.get(order_id)
        if not o:
            return None
        return {'order_id': o.id, 'status': o.status.value, 'match': o.match_id, 'market': o.market, 'selection': o.selection, 'side': o.side.value, 'type': o.order_type.value, 'stake': o.stake, 'filled': o.filled_stake, 'remaining': o.remaining, 'fill_pct': round(o.filled_stake/o.stake*100, 1), 'target_odds': o.odds, 'avg_odds': round(o.avg_odds, 2), 'slip': round(o.slip, 4), 'commission': round(o.commission_paid, 2), 'exchange': o.exchange.value, 'fills': len(o.fills)}

    def report(self, order_id: str) -> Optional[Dict]:
        o = self.orders.get(order_id)
        if not o:
            return None
        ex = self.EXCHANGES.get(o.exchange)
        return {'order_id': o.id, 'status': o.status.value, 'strategy': o.order_type.value, 'target_stake': o.stake, 'target_odds': o.odds, 'filled_stake': o.filled_stake, 'avg_odds': round(o.avg_odds, 2), 'slip': round(o.slip, 4), 'slip_pct': round(o.slip/o.odds*100, 2) if o.odds > 0 else 0, 'commission': round(o.commission_paid, 2), 'fills': len(o.fills)}

    def best_execution(self, market: str, selection: str, side: OrderSide, stake: float, target_odds: float) -> Dict:
        routes = self.route(market, selection, side, target_odds, stake)
        if not routes:
            return {'status': 'no_route'}
        best = routes[0]
        if stake > 5000:
            strategy = 'iceberg'
            reason = 'Large stake - minimize market impact'
        elif stake > 1000:
            strategy = 'twap'
            reason = 'Medium stake - price smoothing'
        else:
            strategy = 'market'
            reason = 'Small stake - quick execution'
        return {'status': 'ready', 'best_exchange': best['display'], 'odds': best['odds'], 'strategy': strategy, 'reason': reason, 'commission': best['commission'], 'score': best['score'], 'routes': routes[:3]}

    def slip_analysis(self) -> Dict:
        filled = [o for o in self.orders.values() if o.status in (OrderStatus.FILLED, OrderStatus.PARTIAL)]
        if not filled:
            return {'status': 'no_data'}
        slips = [o.slip for o in filled]
        stakes = [o.filled_stake for o in filled]
        total = sum(stakes)
        w_slip = sum(s*st for s, st in zip(slips, stakes)) / total if total > 0 else 0
        by_type = {}
        for o in filled:
            t = o.order_type.value
            if t not in by_type:
                by_type[t] = []
            by_type[t].append(o.slip)
        return {'orders': len(filled), 'avg_slip': round(sum(slips)/len(slips), 4), 'weighted_slip': round(w_slip, 4), 'max': round(max(slips), 4), 'min': round(min(slips), 4), 'by_strategy': {k: round(sum(v)/len(v), 4) for k, v in by_type.items()}}

    def exchange_stats(self) -> Dict:
        stats = {n.value: {'orders': 0, 'volume': 0.0, 'commission': 0.0} for n in ExchangeName}
        for o in self.orders.values():
            if o.status in (OrderStatus.FILLED, OrderStatus.PARTIAL):
                stats[o.exchange.value]['orders'] += 1
                stats[o.exchange.value]['volume'] += o.filled_stake
                stats[o.exchange.value]['commission'] += o.commission_paid
        return stats

if __name__ == "__main__":
    agent = TradingAgent()
    print("=" * 60)
    print("TradingAgent - Best Execution Analysis")
    print("Market: 1x2 | Selection: home | Stake: 2000 EUR")
    print("=" * 60)

    be = agent.best_execution('1x2', 'home', OrderSide.BACK, 2000, 1.62)
    print(f"Best Exchange: {be['best_exchange']}")
    print(f"Available Odds: {be['odds']}")
    print(f"Recommended Strategy: {be['strategy'].upper()} - {be['reason']}")
    print(f"Expected Commission: {be['commission']} EUR")
    print(f"Route Score: {be['score']}")
    print()
    print("All Routes (Top 3):")
    for r in be['routes']:
        print(f"  {r['display']}: @{r['odds']} | Score: {r['score']} | [{r['recommendation']}]")

    print()
    print("=" * 60)
    print("Order Execution Test - 5 Strategies")
    print("=" * 60)

    strategies = [OrderType.MARKET, OrderType.LIMIT, OrderType.ICEBERG, OrderType.TWAP, OrderType.POST]
    for st in strategies:
        order = agent.submit('USA_PAR', '1x2', 'home', OrderSide.BACK, st, 500, 1.62, ExchangeName.BETFAIR)
        r = agent.report(order.id)
        print(f"\n{st.value.upper()}: Stake {r['target_stake']} @ {r['target_odds']}")
        print(f"  Filled: {r['filled_stake']} @ {r['avg_odds']} | Slip: {r['slip']:+.3f} ({r['slip_pct']:+.2f}%)")
        print(f"  Commission: {r['commission']} EUR | Status: {r['status']} | Fills: {r['fills']}")

    print()
    print("=" * 60)
    print("Slip Analysis")
    print("=" * 60)
    sa = agent.slip_analysis()
    print(f"Total Orders: {sa['orders']}")
    print(f"Avg Slip: {sa['avg_slip']:+.4f}")
    print(f"Weighted Slip: {sa['weighted_slip']:+.4f}")
    print(f"By Strategy: {sa['by_strategy']}")

    print()
    print("=" * 60)
    print("Exchange Stats")
    print("=" * 60)
    es = agent.exchange_stats()
    for name, data in es.items():
        if data['orders'] > 0:
            print(f"{name}: {data['orders']} orders | Volume: {round(data['volume'], 2)} EUR | Commission: {round(data['commission'], 2)} EUR")
