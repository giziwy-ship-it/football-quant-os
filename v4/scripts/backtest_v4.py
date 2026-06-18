#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backtest Engine v4.0 - 世界杯历史回测

使用 2022 世界杯真实数据回测 v4 引擎:
1. Physical AI 预测
2. Market Microstructure 分析
3. Trading Signal 生成
4. Risk Engine 风控
5. Evolution 权重更新

Author: Naga Core Team
Version: 4.0.0
"""

import sys
import os

# 添加项目根目录到路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, PROJECT_ROOT)

import json
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from v4.core.physical_ai import PhysicalAI, TeamState, MarketState
from v4.core.market_micro import MarketMicrostructure
from v4.core.trade_engine import TradingEngine
from v4.core.risk_engine_v4 import RiskEngine, Position
from v4.core.evolution import SelfEvolution


# ============ 球队实力映射 (2022世界杯) ============
TEAM_STRENGTH_2022 = {
    # 强队
    "BRA": {"attack": 0.90, "defense": 0.85, "elo": 1841, "tournament_gene": 0.95},
    "ARG": {"attack": 0.88, "defense": 0.82, "elo": 1773, "tournament_gene": 0.90},
    "FRA": {"attack": 0.87, "defense": 0.80, "elo": 1759, "tournament_gene": 0.90},
    "ENG": {"attack": 0.85, "defense": 0.78, "elo": 1728, "tournament_gene": 0.70},
    "ESP": {"attack": 0.84, "defense": 0.80, "elo": 1715, "tournament_gene": 0.85},
    "NED": {"attack": 0.83, "defense": 0.78, "elo": 1694, "tournament_gene": 0.75},
    "POR": {"attack": 0.82, "defense": 0.77, "elo": 1676, "tournament_gene": 0.70},
    "BEL": {"attack": 0.82, "defense": 0.75, "elo": 1781, "tournament_gene": 0.65},
    "GER": {"attack": 0.83, "defense": 0.78, "elo": 1650, "tournament_gene": 0.90},
    "URU": {"attack": 0.78, "defense": 0.80, "elo": 1638, "tournament_gene": 0.80},
    "CRO": {"attack": 0.78, "defense": 0.80, "elo": 1645, "tournament_gene": 0.85},
    # 中等
    "DEN": {"attack": 0.75, "defense": 0.78, "elo": 1668, "tournament_gene": 0.60},
    "SUI": {"attack": 0.73, "defense": 0.76, "elo": 1608, "tournament_gene": 0.65},
    "USA": {"attack": 0.70, "defense": 0.72, "elo": 1627, "tournament_gene": 0.50},
    "MEX": {"attack": 0.72, "defense": 0.73, "elo": 1649, "tournament_gene": 0.70},
    "POL": {"attack": 0.70, "defense": 0.72, "elo": 1548, "tournament_gene": 0.55},
    "SEN": {"attack": 0.68, "defense": 0.72, "elo": 1584, "tournament_gene": 0.60},
    "WAL": {"attack": 0.65, "defense": 0.70, "elo": 1569, "tournament_gene": 0.50},
    "KOR": {"attack": 0.68, "defense": 0.68, "elo": 1530, "tournament_gene": 0.60},
    "JPN": {"attack": 0.70, "defense": 0.70, "elo": 1559, "tournament_gene": 0.55},
    "ECU": {"attack": 0.65, "defense": 0.68, "elo": 1463, "tournament_gene": 0.45},
    "IRN": {"attack": 0.62, "defense": 0.68, "elo": 1564, "tournament_gene": 0.45},
    # 弱队
    "MAR": {"attack": 0.60, "defense": 0.72, "elo": 1563, "tournament_gene": 0.50},
    "CMR": {"attack": 0.58, "defense": 0.65, "elo": 1485, "tournament_gene": 0.50},
    "CAN": {"attack": 0.60, "defense": 0.62, "elo": 1475, "tournament_gene": 0.30},
    "GHA": {"attack": 0.58, "defense": 0.62, "elo": 1393, "tournament_gene": 0.50},
    "AUS": {"attack": 0.58, "defense": 0.62, "elo": 1488, "tournament_gene": 0.45},
    "CRC": {"attack": 0.55, "defense": 0.65, "elo": 1503, "tournament_gene": 0.55},
    "TUN": {"attack": 0.55, "defense": 0.65, "elo": 1507, "tournament_gene": 0.45},
    "KSA": {"attack": 0.52, "defense": 0.58, "elo": 1437, "tournament_gene": 0.45},
    "QAT": {"attack": 0.50, "defense": 0.55, "elo": 1441, "tournament_gene": 0.25},
}


def load_data() -> tuple:
    """加载2022世界杯数据"""
    base = Path("D:/openclaw-workspace/football_quant_os/data")
    
    with open(base / "worldcup2022_data.json", 'r') as f:
        matches_data = json.load(f)
    
    with open(base / "worldcup2022_odds.json", 'r') as f:
        odds_data = json.load(f)
    
    # 构建 match_id -> odds 映射
    odds_map = {}
    for m in odds_data.get("matches", []):
        odds_map[m["match_id"]] = m
    
    return matches_data, odds_map


def get_team_state(team_code: str, is_home: bool = True) -> TeamState:
    """根据球队代码创建状态"""
    s = TEAM_STRENGTH_2022.get(team_code, {
        "attack": 0.55, "defense": 0.60, "elo": 1500, "tournament_gene": 0.45
    })
    
    return TeamState(
        attack=s["attack"],
        defense=s["defense"],
        form=0.5,  # 简化：默认0.5
        fatigue=0.0,
        morale=0.5,
        home_advantage=0.1 if is_home else 0.0,
        elo=s["elo"],
        xg_for=s["attack"] * 2.5,
        xg_against=(1 - s["defense"]) * 2.0,
        coach_factor=0.0,
        tournament_gene=s["tournament_gene"]
    )


def determine_result(home_score: int, away_score: int) -> str:
    """确定比赛结果"""
    if home_score > away_score:
        return "home"
    elif home_score < away_score:
        return "away"
    else:
        return "draw"


class BacktestRunner:
    """回测执行器"""
    
    def __init__(self, initial_bankroll: float = 10000.0):
        self.physical_ai = PhysicalAI()
        self.market_micro = MarketMicrostructure()
        self.trade_engine = TradingEngine()
        self.risk_engine = RiskEngine(initial_bankroll=initial_bankroll)
        self.evolution = SelfEvolution()
        
        # 回测统计
        self.stats = {
            "total_bets": 0,
            "total_wins": 0,
            "total_pnl": 0.0,
            "bets": [],
            "bankroll_history": [initial_bankroll],
            "signals": []
        }
    
    def run(self, matches_data: Dict, odds_map: Dict):
        """执行回测"""
        group_matches = matches_data.get("group_stage", [])
        
        print(f"=== Football Quant OS v4.0 Backtest ===")
        print(f"Initial Bankroll: ${self.risk_engine.bankroll.current:,.0f}")
        print(f"Matches: {len(group_matches)}\n")
        
        for i, match in enumerate(group_matches):
            match_id = match["match_id"]
            home_code = match["home"]
            away_code = match["away"]
            home_score = match.get("home_score", 0)
            away_score = match.get("away_score", 0)
            
            # 获取赔率
            odds_info = odds_map.get(match_id, {})
            if not odds_info:
                continue
            
            home_odds = odds_info.get("closing_home", 2.0)
            draw_odds = odds_info.get("closing_draw", 3.5)
            away_odds = odds_info.get("closing_away", 2.0)
            
            # 检测诱盘
            market_bias = "balanced"
            notes = odds_info.get("notes", "")
            if "TRAP" in notes.upper():
                if "home" in notes.lower() or "home_up" in odds_info.get("odds_shift", ""):
                    market_bias = "trap_home"
                elif "away" in notes.lower():
                    market_bias = "trap_away"
            
            # === 1. Physical AI 预测 ===
            home_team = get_team_state(home_code, is_home=True)
            away_team = get_team_state(away_code, is_home=False)
            market = MarketState(home_odds=home_odds, draw_odds=draw_odds, away_odds=away_odds)
            
            prediction = self.physical_ai.predict(home_team, away_team, market)
            probs = prediction["probabilities"]
            upset_score = prediction["upset"]["score"]
            
            # === 2. Trading Signal ===
            signal = self.trade_engine.signal(
                probs=probs,
                odds={"home": home_odds, "draw": draw_odds, "away": away_odds},
                upset_score=upset_score,
                market_bias=market_bias,
                confidence=prediction["confidence"]
            )
            
            # 只执行 VALUE_BET / STRONG_VALUE / SHARP_FADE / UPSET_PLAY
            valid_signals = ["value_bet", "strong_value", "sharp_fade", "upset_play"]
            if signal["signal"] not in valid_signals:
                continue
            
            # === 3. 风控检查 ===
            direction = signal.get("direction")
            if not direction:
                continue
            
            odds = signal["details"][direction]["odds"]
            model_prob = signal["details"][direction]["probability"]
            ev = signal["details"][direction]["ev"]
            
            check = self.risk_engine.check(
                match_id=match_id,
                direction=direction,
                odds=odds,
                model_prob=model_prob,
                expected_value=ev
            )
            
            if not check.allowed:
                continue
            
            # === 4. 执行投注 ===
            position = Position(
                match_id=match_id,
                direction=direction,
                odds=odds,
                stake=check.position_size,
                model_prob=model_prob,
                expected_value=ev,
                timestamp=datetime.now()
            )
            
            executed = self.risk_engine.execute_bet(position, check)
            if not executed:
                continue
            
            self.stats["total_bets"] += 1
            
            # === 5. 结算 ===
            actual = determine_result(home_score, away_score)
            won = (direction == actual)
            pnl = self.risk_engine.settle_bet(match_id, won)
            
            if won:
                self.stats["total_wins"] += 1
            self.stats["total_pnl"] += pnl
            
            # 记录
            self.stats["bets"].append({
                "match_id": match_id,
                "home": home_code,
                "away": away_code,
                "direction": direction,
                "odds": odds,
                "stake": round(check.position_size, 2),
                "won": won,
                "pnl": round(pnl, 2),
                "signal": signal["signal"],
                "market_bias": market_bias,
                "bankroll_after": round(self.risk_engine.bankroll.current, 2)
            })
            
            self.stats["bankroll_history"].append(self.risk_engine.bankroll.current)
            
            # 进化记录
            self.evolution.record_result(
                "combined",
                probs,
                actual,
                {"home": home_odds, "draw": draw_odds, "away": away_odds},
                check.position_size,
                pnl
            )
            
            # 每10场更新一次权重
            if self.stats["total_bets"] % 10 == 0:
                self.evolution.update_weights()
                self.physical_ai.layer_weights.update(self.evolution.weights)
        
        return self.generate_report()
    
    def generate_report(self) -> Dict[str, Any]:
        """生成回测报告"""
        bets = self.stats["bets"]
        if not bets:
            return {"error": "没有执行任何投注"}
        
        total_bets = len(bets)
        wins = sum(1 for b in bets if b["won"])
        win_rate = wins / total_bets if total_bets > 0 else 0
        
        total_stake = sum(b["stake"] for b in bets)
        total_pnl = sum(b["pnl"] for b in bets)
        roi = total_pnl / total_stake if total_stake > 0 else 0
        
        final_bankroll = self.risk_engine.bankroll.current
        initial_bankroll = self.stats["bankroll_history"][0]
        total_return = (final_bankroll - initial_bankroll) / initial_bankroll
        
        # 信号分析
        signal_counts = {}
        signal_pnls = {}
        for b in bets:
            sig = b["signal"]
            signal_counts[sig] = signal_counts.get(sig, 0) + 1
            signal_pnls[sig] = signal_pnls.get(sig, 0) + b["pnl"]
        
        # 最大回撤
        peak = initial_bankroll
        max_dd = 0
        for br in self.stats["bankroll_history"]:
            if br > peak:
                peak = br
            dd = (peak - br) / peak
            if dd > max_dd:
                max_dd = dd
        
        # 诱盘检测表现
        trap_bets = [b for b in bets if "trap" in b["market_bias"]]
        trap_wins = sum(1 for b in trap_bets if b["won"])
        trap_pnl = sum(b["pnl"] for b in trap_bets)
        
        report = {
            "summary": {
                "total_bets": total_bets,
                "wins": wins,
                "win_rate": f"{win_rate:.1%}",
                "total_stake": round(total_stake, 2),
                "total_pnl": round(total_pnl, 2),
                "roi": f"{roi:.1%}",
                "final_bankroll": round(final_bankroll, 2),
                "total_return": f"{total_return:.1%}",
                "max_drawdown": f"{max_dd:.1%}"
            },
            "by_signal": {
                sig: {
                    "count": count,
                    "pnl": round(signal_pnls.get(sig, 0), 2),
                    "avg_pnl": round(signal_pnls.get(sig, 0) / count, 2)
                }
                for sig, count in signal_counts.items()
            },
            "trap_detection": {
                "trap_bets": len(trap_bets),
                "trap_wins": trap_wins,
                "trap_win_rate": f"{trap_wins/len(trap_bets):.1%}" if trap_bets else "N/A",
                "trap_pnl": round(trap_pnl, 2)
            },
            "evolution": self.evolution.diagnose(),
            "bet_details": bets
        }
        
        return report


def print_report(report: Dict):
    """打印回测报告"""
    s = report["summary"]
    
    print("\n" + "=" * 60)
    print("Football Quant OS v4.0 Backtest Report")
    print("=" * 60)
    
    print(f"\nBankroll Performance:")
    print(f"  Final:    ${s['final_bankroll']:,.0f}")
    print(f"  Return:   {s['total_return']}")
    print(f"  Max DD:   {s['max_drawdown']}")
    
    print(f"\nTrading Stats:")
    print(f"  Bets:     {s['total_bets']}")
    print(f"  Win Rate: {s['win_rate']}")
    print(f"  PnL:      ${s['total_pnl']:,.0f}")
    print(f"  ROI:      {s['roi']}")
    
    print(f"\nBy Signal:")
    for sig, data in report.get("by_signal", {}).items():
        print(f"  {sig}: {data['count']} bets, PnL=${data['pnl']:,.0f}, Avg=${data['avg_pnl']:,.0f}")
    
    print(f"\nTrap Detection:")
    t = report["trap_detection"]
    print(f"  Trap Bets: {t['trap_bets']}")
    print(f"  Win Rate:  {t['trap_win_rate']}")
    print(f"  PnL:       ${t['trap_pnl']:,.0f}")
    
    print(f"\nEvolution Weights:")
    for r in report["evolution"]["ranking"]:
        print(f"  {r['name']}: {r['weight']:.1%} (Acc={r['accuracy']:.1%})")
    
    print(f"\nRecent 5 Trades:")
    for b in report["bet_details"][-5:]:
        result = "WIN" if b["won"] else "LOSS"
        print(f"  {result} {b['home']} vs {b['away']} -> {b['direction']} @ {b['odds']} | "
              f"Stake=${b['stake']:.0f} PnL=${b['pnl']:+.0f} [{b['signal']}]")
    
    print("\n" + "=" * 60)


# ============ 主入口 ============
if __name__ == "__main__":
    # 加载数据
    matches_data, odds_map = load_data()
    
    # 运行回测
    runner = BacktestRunner(initial_bankroll=10000.0)
    report = runner.run(matches_data, odds_map)
    
    # 打印报告
    print_report(report)
    
    # 保存详细报告
    output_path = Path("D:/openclaw-workspace/football_quant_os/v4/data/backtest_report.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 转换 numpy bool 为 Python bool
    def sanitize(obj):
        if isinstance(obj, dict):
            return {k: sanitize(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [sanitize(v) for v in obj]
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        return obj
    
    with open(output_path, 'w') as f:
        json.dump(sanitize(report), f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed report saved: {output_path}")
