#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2022 World Cup Full System Backtest
Football Quant OS World Cup Module

Full Pipeline:
  1. Pure Elo baseline (existing model)
  2. Full System: Elo + 5-layer signals + Trap Detection + Kelly v2.0

Tracks:
  - Prediction accuracy
  - Bankroll evolution (€10,000 start)
  - Kelly vs All-in comparison
  - Trap detection effectiveness
"""

import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from data.worldcup2026_data import get_team
from core.worldcup_integrator import (
    WorldCupPipeline, KellyConservative, DecisionTree,
    MarketSignalEngine, TrapDetector, MarketRegimeClassifier,
    MarketRegime
)


TEAM_ELO_2022 = {
    "BRA": 1980, "BEL": 1960, "ARG": 1950, "FRA": 1930, "ENG": 1900, "ESP": 1880,
    "NED": 1870, "POR": 1860, "GER": 1840, "URU": 1820, "CRO": 1800, "DEN": 1790,
    "MEX": 1760, "SUI": 1750, "USA": 1740, "SEN": 1730, "WAL": 1720, "IRN": 1700,
    "SRB": 1690, "MAR": 1680, "JPN": 1670, "POL": 1660, "KOR": 1650, "TUN": 1630,
    "AUS": 1620, "CAN": 1600, "CMR": 1580, "ECU": 1570, "KSA": 1560, "QAT": 1550,
    "GHA": 1540, "CRC": 1530,
}


def pure_elo_prob(home: str, away: str) -> Dict[str, float]:
    """Pure Elo baseline model"""
    home_elo = TEAM_ELO_2022.get(home, 1600)
    away_elo = TEAM_ELO_2022.get(away, 1600)
    elo_diff = home_elo - away_elo
    prob_home = 1 / (1 + 10 ** (-elo_diff / 400))
    prob_away = 1 - prob_home
    draw_prob = max(0.15, min(0.30, 0.25 - abs(prob_home - 0.5) * 0.2))
    total = prob_home + draw_prob + prob_away
    return {"home": prob_home / total, "draw": draw_prob / total, "away": prob_away / total,
            "home_elo": home_elo, "away_elo": away_elo, "elo_diff": elo_diff}


class MatchRecord:
    def __init__(self, data: Dict):
        self.match_id = data["match_id"]
        self.group = data["group"]
        self.date = data["date"]
        self.home = data["home"]
        self.away = data["away"]
        self.home_score = data["home_score"]
        self.away_score = data["away_score"]
        self.home_pen = data.get("home_pen", 0)
        self.away_pen = data.get("away_pen", 0)

    @property
    def outcome(self) -> str:
        if self.home_score > self.away_score: return "home_win"
        elif self.home_score < self.away_score: return "away_win"
        return "draw"

    @property
    def is_draw(self) -> bool:
        return self.home_score == self.away_score

    def __repr__(self):
        return f"{self.home} {self.home_score}-{self.away_score} {self.away}"


class BacktestRunner:
    def __init__(self, bankroll: float = 10000):
        self.bankroll_start = bankroll
        self.bankroll_elo = bankroll
        self.bankroll_full = bankroll
        self.bankroll_kelly = bankroll
        self.kelly = KellyConservative(bankroll)
        self.kelly.reset_daily()  # Reset daily for each match in backtest
        
        self.results = {
            "elo_only": {"total": 0, "correct": 0, "bets": 0, "wins": 0, "losses": 0, "profit": 0, "bankroll": []},
            "full_system": {"total": 0, "correct": 0, "bets": 0, "wins": 0, "losses": 0, "profit": 0, "bankroll": [], "traps_detected": 0, "traps_correct": 0},
            "kelly": {"total": 0, "bets": 0, "wins": 0, "losses": 0, "profit": 0, "bankroll": []},
            "matches": [],
        }
    
    def load_data(self) -> Tuple[List[MatchRecord], List[Dict]]:
        base = os.path.dirname(__file__)
        with open(os.path.join(base, "data", "worldcup2022_data.json"), 'r') as f:
            data = json.load(f)
        with open(os.path.join(base, "data", "worldcup2022_odds.json"), 'r') as f:
            odds_data = json.load(f)
        
        matches = []
        for m in data.get("group_stage", []):
            matches.append(MatchRecord(m))
        
        odds_map = {o["match_id"]: o for o in odds_data.get("matches", [])}
        return matches, odds_map
    
    def build_market_data(self, odds: Dict) -> Dict:
        """从赔率数据构建市场数据"""
        if not odds or not all(k in odds for k in ["closing_home", "closing_draw", "closing_away"]):
            return {
                "market_odds": {"home": 2.0, "draw": 3.2, "away": 3.5},
                "market_prob": {"home": 0.33, "draw": 0.33, "away": 0.33},
                "odds_changes": [],
                "odds_history": [],
                "current_odds": {"home": 2.0, "draw": 3.2, "away": 3.5},
                "media_consensus": 0.5,
                "historical_odds": {"trap_frequency": 0.1},
            }
        
        c = odds.get("closing_home", 2.0)
        d = odds.get("closing_draw", 3.2)
        a = odds.get("closing_away", 3.5)
        
        # 隐含概率（去水）
        total = 1/c + 1/d + 1/a
        market_prob = {
            "home": (1/c) / total,
            "draw": (1/d) / total,
            "away": (1/a) / total,
        }
        
        # 模拟赔率变化用于ACC计算
        o = odds.get("opening_home", c * 1.1)
        shift = (c - o) / o  # 负=降赔，正=升赔
        
        return {
            "market_odds": {"home": c, "draw": d, "away": a},
            "market_prob": market_prob,
            "odds_changes": [{"direction": -1 if c < o else 1}],
            "odds_history": [{"odds": o, "timestamp": 0}, {"odds": c, "timestamp": 1}],
            "current_odds": {"home": c, "draw": d, "away": a},
            "media_consensus": odds.get("media_home", 0.5),
            "historical_odds": {"trap_frequency": 0.1},
        }
    
    def run_pure_elo(self, match: MatchRecord, odds: Dict) -> Dict:
        """纯Elo策略：Elo概率 > 市场概率则押注（方向一致）"""
        model = pure_elo_prob(match.home, match.away)
        market_data = self.build_market_data(odds) if odds else None
        market_prob = market_data["market_prob"] if market_data else {"home": 0.33, "draw": 0.33, "away": 0.33}
        
        # 选择Elo预测方向
        best = max(model["home"], model["draw"], model["away"])
        direction = "home" if model["home"] == best else ("draw" if model["draw"] == best else "away")
        
        # 如果Elo方向概率 > 市场概率，押注
        if model[direction] > market_prob[direction] + 0.05:
            bet = 200  # 固定2%
            self.results["elo_only"]["bets"] += 1
            
            odds_home = odds.get("closing_home", 2.0) if odds else 2.0
            odds_draw = odds.get("closing_draw", 3.2) if odds else 3.2
            odds_away = odds.get("closing_away", 3.5) if odds else 3.5
            
            if direction == "home" and match.outcome == "home_win":
                win = bet * (odds_home - 1)
                self.results["elo_only"]["wins"] += 1
            elif direction == "away" and match.outcome == "away_win":
                win = bet * (odds_away - 1)
                self.results["elo_only"]["wins"] += 1
            elif direction == "draw" and match.outcome == "draw":
                win = bet * (odds_draw - 1)
                self.results["elo_only"]["wins"] += 1
            else:
                win = -bet
                self.results["elo_only"]["losses"] += 1
            
            self.bankroll_elo += win
            self.results["elo_only"]["profit"] += win
        
        self.results["elo_only"]["total"] += 1
        self.results["elo_only"]["bankroll"].append(self.bankroll_elo)
        
        return {"direction": direction, "model_prob": model[direction], "market_prob": market_prob[direction]}
    
    def run_full_system(self, match: MatchRecord, odds: Dict) -> Dict:
        """完整系统：五层信号 + 诱盘检测 + 决策树 + Kelly"""
        model = pure_elo_prob(match.home, match.away)
        market_data = self.build_market_data(odds)
        
        # 计算PD（盘口偏离）
        pd_home = market_data["market_prob"]["home"] - model["home"]
        pd_draw = market_data["market_prob"]["draw"] - model["draw"]
        pd_away = market_data["market_prob"]["away"] - model["away"]
        max_pd = max(abs(pd_home), abs(pd_draw), abs(pd_away))
        
        # 方向：模型概率高的一方（价值方）
        best_model = max(model["home"], model["draw"], model["away"])
        value_direction = "home" if model["home"] == best_model else ("draw" if model["draw"] == best_model else "away")
        
        # 诱盘检测
        is_trap = False
        trap_reason = ""
        
        # 条件1：高PD + 媒体高度一致 = 热门诱盘
        media_consensus = odds.get("media_home", 0.5) if odds else 0.5
        if abs(max_pd) > 0.15 and media_consensus > 0.8 and value_direction == "home":
            is_trap = True
            trap_reason = f"High PD ({max_pd:.2f}) + Media consensus ({media_consensus:.0%}) = Home Trap"
        
        # 条件2：临场升赔（热门方）+ 无基本面支撑 = 诱盘确认
        if odds:
            o = odds.get("opening_home", odds["closing_home"] * 1.1)
            c = odds["closing_home"]
            if c > o * 1.05 and media_consensus > 0.7 and value_direction == "home":
                is_trap = True
                trap_reason = f"Home odds rising ({o:.2f} -> {c:.2f}) + Media consensus = Trap"
        
        # 决策树 Step 0-4
        action = "ABANDON"
        bet_direction = None
        bet_amount = 0
        
        # Step 0: |PD| > 阈值？
        if abs(max_pd) < 0.05:
            action = "ABANDON"
        else:
            # Step 1: 诱盘检查
            if is_trap:
                action = "CONTRARIAN"  # 反向操作
                bet_direction = "away" if value_direction == "home" else "home"
                bet_amount = 100  # 反诱盘小注
            else:
                # Step 2: 信息盘/价值盘
                action = "EXECUTE"
                bet_direction = value_direction
                
                # Kelly计算
                if odds:
                    model_p = model[bet_direction]
                    market_o = odds.get(f"closing_{bet_direction}", 2.0)
                    kelly_result = self.kelly.calculate(model_p, market_o, bet_direction)
                    if kelly_result["action"] == "BET":
                        bet_amount = kelly_result["bet_amount"]
                    else:
                        action = "ABANDON"
                        bet_amount = 0
                else:
                    bet_amount = 100  # 无赔率，小额测试
        
        # 执行投注
        if action in ("EXECUTE", "CONTRARIAN") and bet_amount > 0 and bet_direction:
            self.results["full_system"]["bets"] += 1
            
            if bet_direction == "home" and match.outcome == "home_win":
                win = bet_amount * (odds["closing_home"] - 1) if odds else bet_amount
                self.results["full_system"]["wins"] += 1
            elif bet_direction == "away" and match.outcome == "away_win":
                win = bet_amount * (odds["closing_away"] - 1) if odds else bet_amount
                self.results["full_system"]["wins"] += 1
            elif bet_direction == "draw" and match.outcome == "draw":
                win = bet_amount * (odds["closing_draw"] - 1) if odds else bet_amount
                self.results["full_system"]["wins"] += 1
            else:
                win = -bet_amount
                self.results["full_system"]["losses"] += 1
                self.kelly.record_result(False)
            
            if win > 0:
                self.kelly.record_result(True)
            
            self.bankroll_full += win
            self.results["full_system"]["profit"] += win
        
        self.results["full_system"]["total"] += 1
        self.results["full_system"]["bankroll"].append(self.bankroll_full)
        
        if is_trap:
            self.results["full_system"]["traps_detected"] += 1
            # 检查反诱盘是否正确
            if action == "CONTRARIAN":
                if (bet_direction == "away" and match.outcome == "away_win") or \
                   (bet_direction == "home" and match.outcome == "home_win"):
                    self.results["full_system"]["traps_correct"] += 1
        
        return {
            "action": action,
            "direction": bet_direction,
            "amount": bet_amount,
            "is_trap": is_trap,
            "trap_reason": trap_reason,
            "pd": max_pd,
            "model_prob": model,
        }
    
    def run(self):
        matches, odds_map = self.load_data()
        
        print("=" * 60)
        print("2022 FIFA World Cup - Full System Backtest")
        print("=" * 60)
        print(f"\nStarting Bankroll: EUR {self.bankroll_start:,.0f}")
        print(f"Total Matches: {len(matches)}")
        print(f"Matches with odds data: {len(odds_map)}")
        
        for match in matches:
            odds = odds_map.get(match.match_id)
            
            # 纯Elo
            elo_result = self.run_pure_elo(match, odds)
            
            # 完整系统
            full_result = self.run_full_system(match, odds)
            
            # 记录
            self.results["matches"].append({
                "match_id": match.match_id,
                "match": str(match),
                "outcome": match.outcome,
                "elo": elo_result,
                "full": full_result,
            })
        
        self.print_report()
    
    def print_report(self):
        r = self.results
        
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS")
        print("=" * 60)
        
        # 纯Elo
        elo = r["elo_only"]
        print(f"\n[1] PURE ELO STRATEGY")
        print(f"  Bets: {elo['bets']}/{elo['total']} ({elo['bets']/elo['total']*100:.1f}%)")
        print(f"  Wins: {elo['wins']}, Losses: {elo['losses']}")
        if elo['bets'] > 0:
            print(f"  Win Rate: {elo['wins']/elo['bets']*100:.1f}%")
            print(f"  Profit: EUR {elo['profit']:+.0f}")
            print(f"  ROI: {elo['profit']/(elo['bets']*200)*100:.1f}%")
        print(f"  Final Bankroll: EUR {self.bankroll_elo:,.0f}")
        print(f"  Return: {(self.bankroll_elo/self.bankroll_start - 1)*100:+.1f}%")
        
        # 完整系统
        full = r["full_system"]
        print(f"\n[2] FULL SYSTEM (Elo + Signals + Trap + Kelly)")
        print(f"  Bets: {full['bets']}/{full['total']} ({full['bets']/full['total']*100:.1f}%)")
        print(f"  Wins: {full['wins']}, Losses: {full['losses']}")
        if full['bets'] > 0:
            print(f"  Win Rate: {full['wins']/full['bets']*100:.1f}%")
            print(f"  Profit: EUR {full['profit']:+.0f}")
        print(f"  Traps Detected: {full['traps_detected']}")
        print(f"  Traps Correct: {full['traps_correct']}")
        if full['traps_detected'] > 0:
            print(f"  Trap Accuracy: {full['traps_correct']/full['traps_detected']*100:.1f}%")
        print(f"  Final Bankroll: EUR {self.bankroll_full:,.0f}")
        print(f"  Return: {(self.bankroll_full/self.bankroll_start - 1)*100:+.1f}%")
        
        # 对比
        print(f"\n[3] COMPARISON")
        diff = self.bankroll_full - self.bankroll_elo
        print(f"  Full vs Elo: EUR {diff:+.0f} ({diff/self.bankroll_start*100:+.1f}%)")
        print(f"  Full System Advantage: {'+' if diff > 0 else ''}{diff/self.bankroll_start*100:.1f}%")
        
        # 关键比赛分析
        print(f"\n[4] KEY MATCHES ANALYSIS")
        upsets = [m for m in r["matches"] if m["full"]["is_trap"]]
        for m in upsets[:5]:
            print(f"  {m['match']:30s} | Outcome: {m['outcome']:10s} | Action: {m['full']['action']:12s} | "
                  f"Trap: {m['full']['is_trap']} | {m['full']['trap_reason'][:50]}")
        
        print("\n" + "=" * 60)
        
        # 导出
        self.export_results()
    
    def export_results(self, filepath: str = None):
        if not filepath:
            filepath = os.path.join(os.path.dirname(__file__), 
                                   "data", "backtest_2022_fullsystem.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"Results exported to: {filepath}")


if __name__ == "__main__":
    runner = BacktestRunner(bankroll=10000)
    runner.run()
