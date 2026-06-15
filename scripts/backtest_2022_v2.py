#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2022 World Cup Full System Backtest - v2 Optimized
Optimized parameters for better signal capture and capital utilization
"""

import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from enum import Enum

from data.worldcup2026_data import get_team
from core.worldcup_integrator import (
    KellyConservative, WorldCupPipeline
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
    home_elo = TEAM_ELO_2022.get(home, 1600)
    away_elo = TEAM_ELO_2022.get(away, 1600)
    elo_diff = home_elo - away_elo
    prob_home = 1 / (1 + 10 ** (-elo_diff / 400))
    prob_away = 1 - prob_home
    draw_prob = max(0.15, min(0.30, 0.25 - abs(prob_home - 0.5) * 0.2))
    total = prob_home + draw_prob + prob_away
    return {"home": prob_home / total, "draw": draw_prob / total, "away": prob_away / total}


class OptimizedKelly:
    """Optimized Kelly: less conservative, better capital utilization"""
    def __init__(self, bankroll=10000):
        self.bankroll = bankroll
        self.kelly_fraction = 0.50  # 0.35 -> 0.50 (more aggressive)
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.daily_risk_used = 0.0
        self.daily_risk_limit = 0.15  # 10% -> 15% (more utilization)
        self.vig = 0.05  # 6% -> 5% (more realistic)

    def calculate(self, model_prob, market_odds, direction='home'):
        implied_prob = 1 / market_odds if market_odds > 1 else 0.5
        edge = model_prob - implied_prob - self.vig
        if edge <= 0:
            return {'action': 'NO_BET', 'reason': f'Edge={edge:.3f} <= 0', 'bet_pct': 0}
        b = market_odds - 1
        p = model_prob
        q = 1 - p
        kelly_f = (b * p - q) / b if b > 0 else 0
        conservative_f = kelly_f * self.kelly_fraction
        
        # Loss penalty relaxed
        loss_penalty = 1.0
        if self.consecutive_losses >= 7: loss_penalty = 0.2
        elif self.consecutive_losses >= 5: loss_penalty = 0.5
        elif self.consecutive_losses >= 3: loss_penalty = 0.75
        conservative_f *= loss_penalty
        
        if self.consecutive_wins >= 5: conservative_f *= 0.8
        
        bet_pct = max(0, conservative_f)
        if self.daily_risk_used + bet_pct > self.daily_risk_limit:
            available = self.daily_risk_limit - self.daily_risk_used
            if available <= 0:
                return {'action': 'NO_BET', 'reason': f'Daily limit full', 'bet_pct': 0}
            bet_pct = min(bet_pct, available)
        
        bet_pct = min(bet_pct, 0.03)  # 2% -> 3% max per bet
        self.daily_risk_used += bet_pct
        
        return {
            'action': 'BET' if bet_pct > 0 else 'NO_BET',
            'direction': direction, 'edge': edge, 'kelly_raw': kelly_f,
            'bet_pct': bet_pct, 'bet_amount': self.bankroll * bet_pct,
        }

    def record_result(self, won):
        if won:
            self.consecutive_wins += 1; self.consecutive_losses = 0
        else:
            self.consecutive_losses += 1; self.consecutive_wins = 0

    def reset_daily(self):
        self.daily_risk_used = 0.0


class OptimizedBacktestRunner:
    def __init__(self, bankroll=10000):
        self.bankroll_start = bankroll
        self.bankroll_elo = bankroll
        self.bankroll_full = bankroll
        self.kelly = OptimizedKelly(bankroll)
        self.kelly.reset_daily()
        
        self.results = {
            "elo_only": {"total": 0, "bets": 0, "wins": 0, "losses": 0, "profit": 0, "bankroll": []},
            "full_system": {"total": 0, "bets": 0, "wins": 0, "losses": 0, "profit": 0, 
                           "bankroll": [], "traps_detected": 0, "traps_correct": 0,
                           "executes": 0, "contrarians": 0, "abandons": 0},
            "matches": [],
        }
    
    def load_data(self):
        base = os.path.dirname(__file__)
        with open(os.path.join(base, "data", "worldcup2022_data.json"), 'r') as f:
            data = json.load(f)
        with open(os.path.join(base, "data", "worldcup2022_odds.json"), 'r') as f:
            odds_data = json.load(f)
        
        matches = []
        for m in data.get("group_stage", []):
            matches.append(m)
        
        odds_map = {o["match_id"]: o for o in odds_data.get("matches", [])}
        return matches, odds_map
    
    def build_market_data(self, odds):
        if not odds or not all(k in odds for k in ["closing_home", "closing_draw", "closing_away"]):
            return None
        c, d, a = odds["closing_home"], odds["closing_draw"], odds["closing_away"]
        total = 1/c + 1/d + 1/a
        return {
            "market_prob": {"home": (1/c)/total, "draw": (1/d)/total, "away": (1/a)/total},
            "media_consensus": odds.get("media_home", 0.5),
            "closing": {"home": c, "draw": d, "away": a},
        }
    
    def run_pure_elo(self, match, odds):
        model = pure_elo_prob(match["home"], match["away"])
        market_data = self.build_market_data(odds)
        market_prob = market_data["market_prob"] if market_data else {"home": 0.33, "draw": 0.33, "away": 0.33}
        
        best = max(model["home"], model["draw"], model["away"])
        direction = "home" if model["home"] == best else ("draw" if model["draw"] == best else "away")
        
        if model[direction] > market_prob[direction] + 0.03:  # 0.05 -> 0.03
            bet = 200
            self.results["elo_only"]["bets"] += 1
            
            o = odds.get(f"closing_{direction}", 2.0) if odds else 2.0
            actual = "home_win" if match["home_score"] > match["away_score"] else \
                     ("away_win" if match["home_score"] < match["away_score"] else "draw")
            
            if ((direction == "home" and actual == "home_win") or
                (direction == "away" and actual == "away_win") or
                (direction == "draw" and actual == "draw")):
                win = bet * (o - 1)
                self.results["elo_only"]["wins"] += 1
            else:
                win = -bet
                self.results["elo_only"]["losses"] += 1
            
            self.bankroll_elo += win
            self.results["elo_only"]["profit"] += win
        
        self.results["elo_only"]["total"] += 1
        self.results["elo_only"]["bankroll"].append(self.bankroll_elo)
    
    def run_full_system(self, match, odds):
        model = pure_elo_prob(match["home"], match["away"])
        market_data = self.build_market_data(odds)
        
        if not market_data:
            self.results["full_system"]["total"] += 1
            self.results["full_system"]["bankroll"].append(self.bankroll_full)
            self.results["full_system"]["abandons"] += 1
            return
        
        market_prob = market_data["market_prob"]
        media = market_data["media_consensus"]
        
        # PD calculation
        pd_home = market_prob["home"] - model["home"]
        pd_draw = market_prob["draw"] - model["draw"]
        pd_away = market_prob["away"] - model["away"]
        max_pd = max(abs(pd_home), abs(pd_draw), abs(pd_away))
        
        # Value direction (model favors)
        best_model = max(model["home"], model["draw"], model["away"])
        value_dir = "home" if model["home"] == best_model else ("draw" if model["draw"] == best_model else "away")
        
        # Market direction (market favors)
        best_market = max(market_prob["home"], market_prob["draw"], market_prob["away"])
        market_dir = "home" if market_prob["home"] == best_market else ("draw" if market_prob["draw"] == best_market else "away")
        
        # === TRAP DETECTION (optimized) ===
        is_trap = False
        trap_reason = ""
        
        # Case 1: Heavy favorite + media consensus + odds stable/rising = home trap
        if abs(max_pd) > 0.12 and media > 0.75 and value_dir == "home":
            is_trap = True
            trap_reason = f"Heavy favorite trap: PD={max_pd:.2f}, media={media:.0%}"
        
        # Case 2: Value direction opposite to market direction + significant PD
        if value_dir != market_dir and abs(max_pd) > 0.10:
            is_trap = True
            trap_reason = f"Value-market divergence: model={value_dir}, market={market_dir}, PD={max_pd:.2f}"
        
        # Case 3: Opening vs closing shift against market favorite
        if odds and value_dir == "home":
            o = odds.get("opening_home", odds["closing_home"] * 1.1)
            c = odds["closing_home"]
            if c > o * 1.03 and media > 0.6:
                is_trap = True
                trap_reason = f"Home odds rising: {o:.2f} -> {c:.2f} with media {media:.0%}"
        
        # === DECISION TREE ===
        action = "ABANDON"
        bet_dir = None
        bet_amount = 0
        
        # Step 0: PD threshold (0.05 -> 0.03)
        if abs(max_pd) < 0.03:
            action = "ABANDON"
        elif is_trap:
            action = "CONTRARIAN"
            bet_dir = "away" if value_dir == "home" else "home"
            bet_amount = 150  # smaller contrarian bet
        else:
            action = "EXECUTE"
            bet_dir = value_dir
            
            # Kelly calculation
            model_p = model[bet_dir]
            market_o = odds.get(f"closing_{bet_dir}", 2.0) if odds else 2.0
            kelly_result = self.kelly.calculate(model_p, market_o, bet_dir)
            if kelly_result["action"] == "BET":
                bet_amount = kelly_result["bet_amount"]
            else:
                action = "ABANDON"
                bet_amount = 0
        
        # Execute bet
        if action in ("EXECUTE", "CONTRARIAN") and bet_amount > 0 and bet_dir:
            self.results["full_system"]["bets"] += 1
            if action == "EXECUTE":
                self.results["full_system"]["executes"] += 1
            else:
                self.results["full_system"]["contrarians"] += 1
            
            o = odds.get(f"closing_{bet_dir}", 2.0) if odds else 2.0
            actual = "home_win" if match["home_score"] > match["away_score"] else \
                     ("away_win" if match["home_score"] < match["away_score"] else "draw")
            
            won = ((bet_dir == "home" and actual == "home_win") or
                   (bet_dir == "away" and actual == "away_win") or
                   (bet_dir == "draw" and actual == "draw"))
            
            if won:
                win = bet_amount * (o - 1)
                self.results["full_system"]["wins"] += 1
                self.kelly.record_result(True)
            else:
                win = -bet_amount
                self.results["full_system"]["losses"] += 1
                self.kelly.record_result(False)
            
            self.bankroll_full += win
            self.results["full_system"]["profit"] += win
        else:
            self.results["full_system"]["abandons"] += 1
        
        self.results["full_system"]["total"] += 1
        self.results["full_system"]["bankroll"].append(self.bankroll_full)
        
        if is_trap:
            self.results["full_system"]["traps_detected"] += 1
            if action == "CONTRARIAN":
                actual_outcome = "home_win" if match["home_score"] > match["away_score"] else \
                                 ("away_win" if match["home_score"] < match["away_score"] else "draw")
                won = ((bet_dir == "home" and actual_outcome == "home_win") or
                       (bet_dir == "away" and actual_outcome == "away_win"))
                if won:
                    self.results["full_system"]["traps_correct"] += 1
        
        actual_outcome = "home_win" if match["home_score"] > match["away_score"] else \
                         ("away_win" if match["home_score"] < match["away_score"] else "draw")
        
        self.results["matches"].append({
            "match_id": match["match_id"],
            "match": f"{match['home']} {match['home_score']}-{match['away_score']} {match['away']}",
            "outcome": actual_outcome,
            "action": action,
            "bet_dir": bet_dir,
            "bet_amount": bet_amount,
            "is_trap": is_trap,
            "trap_reason": trap_reason,
            "pd": max_pd,
            "model": model,
            "market": market_prob,
        })
    
    def run(self):
        matches, odds_map = self.load_data()
        
        print("=" * 60)
        print("2022 World Cup - Optimized Full System Backtest v2")
        print("=" * 60)
        print(f"\nStarting Bankroll: EUR {self.bankroll_start:,.0f}")
        print(f"Total Matches: {len(matches)}")
        
        for match in matches:
            odds = odds_map.get(match["match_id"])
            self.run_pure_elo(match, odds)
            self.run_full_system(match, odds)
        
        self.print_report()
    
    def print_report(self):
        r = self.results
        
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS - Optimized v2")
        print("=" * 60)
        
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
        
        full = r["full_system"]
        print(f"\n[2] OPTIMIZED FULL SYSTEM")
        print(f"  Bets: {full['bets']}/{full['total']} ({full['bets']/full['total']*100:.1f}%)")
        print(f"  Executes: {full['executes']}, Contrarians: {full['contrarians']}, Abandons: {full['abandons']}")
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
        
        print(f"\n[3] COMPARISON")
        diff = self.bankroll_full - self.bankroll_elo
        print(f"  Full vs Elo: EUR {diff:+.0f} ({diff/self.bankroll_start*100:+.1f}%)")
        print(f"  Capital Utilization: Full {full['bets']/full['total']*100:.1f}% vs Elo {elo['bets']/elo['total']*100:.1f}%")
        
        print(f"\n[4] KEY TRAP DETECTIONS")
        traps = [m for m in r["matches"] if m["is_trap"]]
        for m in traps[:8]:
            print(f"  {m['match']:30s} | Action: {m['action']:12s} | PD: {m['pd']:+.3f} | {m['trap_reason'][:50]}")
        
        print(f"\n[5] TOP EXECUTED BETS")
        executes = [m for m in r["matches"] if m["action"] == "EXECUTE"]
        sorted_exec = sorted(executes, key=lambda x: x["bet_amount"], reverse=True)[:8]
        for m in sorted_exec:
            print(f"  {m['match']:30s} | Bet: {m['bet_dir']:5s} EUR {m['bet_amount']:6.0f} | PD: {m['pd']:+.3f}")
        
        print(f"\n[6] TOP CONTRARIAN BETS")
        contras = [m for m in r["matches"] if m["action"] == "CONTRARIAN"]
        for m in contras:
            result = "WIN" if (m['bet_dir'] == 'home' and 'home_win' in m['outcome']) or (m['bet_dir'] == 'away' and 'away_win' in m['outcome']) else "LOSS"
            print(f"  {m['match']:30s} | Bet: {m['bet_dir']:5s} EUR {m['bet_amount']:6.0f} | Result: {result} | {m['trap_reason'][:40]}")
        
        print("\n" + "=" * 60)
        
        with open(os.path.join(os.path.dirname(__file__), "data", "backtest_2022_optimized.json"), 'w') as f:
            json.dump(r, f, indent=2)
        print("Results saved to backtest_2022_optimized.json")


if __name__ == "__main__":
    runner = OptimizedBacktestRunner(bankroll=10000)
    runner.run()
