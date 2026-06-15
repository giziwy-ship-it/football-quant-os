import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

TEAM_ELO_2022 = {
    "BRA": 1980, "BEL": 1960, "ARG": 1950, "FRA": 1930, "ENG": 1900, "ESP": 1880,
    "NED": 1870, "POR": 1860, "GER": 1840, "URU": 1820, "CRO": 1800, "DEN": 1790,
    "MEX": 1760, "SUI": 1750, "USA": 1740, "SEN": 1730, "WAL": 1720, "IRN": 1700,
    "SRB": 1690, "MAR": 1680, "JPN": 1670, "POL": 1660, "KOR": 1650, "TUN": 1630,
    "AUS": 1620, "CAN": 1600, "CMR": 1580, "ECU": 1570, "KSA": 1560, "QAT": 1550,
    "GHA": 1540, "CRC": 1530,
}

def pure_elo_prob(home, away):
    home_elo = TEAM_ELO_2022.get(home, 1600)
    away_elo = TEAM_ELO_2022.get(away, 1600)
    elo_diff = home_elo - away_elo
    prob_home = 1 / (1 + 10 ** (-elo_diff / 400))
    prob_away = 1 - prob_home
    draw_prob = max(0.15, min(0.30, 0.25 - abs(prob_home - 0.5) * 0.2))
    total = prob_home + draw_prob + prob_away
    return {"home": prob_home / total, "draw": draw_prob / total, "away": prob_away / total}

class HybridKelly:
    def __init__(self, bankroll=10000):
        self.bankroll = bankroll
        self.kelly_fraction = 0.45
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.daily_risk_used = 0.0
        self.daily_risk_limit = 0.15
        self.vig = 0.05

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
        bet_pct = min(bet_pct, 0.03)
        self.daily_risk_used += bet_pct
        return {'action': 'BET' if bet_pct > 0 else 'NO_BET',
                'direction': direction, 'edge': edge, 'kelly_raw': kelly_f,
                'bet_pct': bet_pct, 'bet_amount': self.bankroll * bet_pct}

    def record_result(self, won):
        if won: self.consecutive_wins += 1; self.consecutive_losses = 0
        else: self.consecutive_losses += 1; self.consecutive_wins = 0

    def reset_daily(self):
        self.daily_risk_used = 0.0

class HybridBacktestRunner:
    def __init__(self, bankroll=10000):
        self.bankroll_start = bankroll
        self.bankroll_elo = bankroll
        self.bankroll_full = bankroll
        self.kelly = HybridKelly(bankroll)
        self.kelly.reset_daily()
        self.results = {
            "elo_only": {"total": 0, "bets": 0, "wins": 0, "losses": 0, "profit": 0, "bankroll": []},
            "hybrid": {"total": 0, "bets": 0, "wins": 0, "losses": 0, "profit": 0,
                      "bankroll": [], "executes": 0, "abandons": 0, "motivation_filter": 0},
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

    def get_motivation(self, match_id, home, away, group, odds_data):
        """战意因子：-0.10 to +0.10，基于生死战/已出线/荣誉战"""
        motivation = 0.0
        notes = odds_data.get("notes", "")
        
        # 已出线球队/轮换 = 战意-0.08（因为可能放水）
        if "already qualified" in notes.lower() or "reserves" in notes.lower() or "rotation" in notes.lower():
            motivation -= 0.08
        
        # 生死战/必须赢 = 战意+0.05
        if "need to win" in notes.lower() or "must win" in notes.lower() or "eliminated" in notes.lower():
            motivation += 0.05
        
        # 首场比赛 = 战意基准（0）
        # 末轮比赛 = 已出线球队可能放水
        if match_id[0].upper() in "ABCDEFGH" and len(match_id) == 2 and match_id[1] in "56":
            # 第3轮小组赛
            if "already qualified" in notes.lower():
                motivation -= 0.08
        
        return max(-0.10, min(0.10, motivation))

    def run_pure_elo(self, match, odds):
        model = pure_elo_prob(match["home"], match["away"])
        market_data = self.build_market_data(odds)
        market_prob = market_data["market_prob"] if market_data else {"home": 0.33, "draw": 0.33, "away": 0.33}
        
        best = max(model["home"], model["draw"], model["away"])
        direction = "home" if model["home"] == best else ("draw" if model["draw"] == best else "away")
        
        if model[direction] > market_prob[direction] + 0.03:
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

    def run_hybrid(self, match, odds):
        model = pure_elo_prob(match["home"], match["away"])
        market_data = self.build_market_data(odds)
        
        if not market_data:
            self.results["hybrid"]["total"] += 1
            self.results["hybrid"]["bankroll"].append(self.bankroll_full)
            self.results["hybrid"]["abandons"] += 1
            return
        
        market_prob = market_data["market_prob"]
        
        # 战意因子调整
        motivation = self.get_motivation(match["match_id"], match["home"], match["away"], match["group"], odds)
        
        # 应用战意调整：已出线球队 Elo 降低，生死战球队 Elo 提升
        if motivation < -0.05:
            # 热门方（Elo高）已出线 -> 降低其概率
            if model["home"] > model["away"]:
                model["home"] *= (1 + motivation)  # motivation is negative, so this reduces
            else:
                model["away"] *= (1 + motivation)
        elif motivation > 0.03:
            # 生死战球队提升
            if model["home"] < model["away"]:
                model["home"] *= (1 + motivation)
            else:
                model["away"] *= (1 + motivation)
        
        # 重新归一化
        total = model["home"] + model["draw"] + model["away"]
        model = {k: v/total for k, v in model.items()}
        
        # PD 计算
        pd_home = market_prob["home"] - model["home"]
        pd_draw = market_prob["draw"] - model["draw"]
        pd_away = market_prob["away"] - model["away"]
        max_pd = max(abs(pd_home), abs(pd_draw), abs(pd_away))
        
        # 价值方向
        best_model = max(model["home"], model["draw"], model["away"])
        value_dir = "home" if model["home"] == best_model else ("draw" if model["draw"] == best_model else "away")
        
        # 决策：|PD| > 0.03 + 正期望值 + 战意调整后
        action = "ABANDON"
        bet_dir = None
        bet_amount = 0
        
        if abs(max_pd) >= 0.03 and model[value_dir] > market_prob[value_dir] + 0.05:
            action = "EXECUTE"
            bet_dir = value_dir
            
            # Kelly 计算
            if odds:
                model_p = model[bet_dir]
                market_o = odds.get(f"closing_{bet_dir}", 2.0)
                kelly_result = self.kelly.calculate(model_p, market_o, bet_dir)
                if kelly_result["action"] == "BET":
                    bet_amount = kelly_result["bet_amount"]
                else:
                    action = "ABANDON"
                    bet_amount = 0
            else:
                bet_amount = 100
        
        if action == "EXECUTE" and bet_amount > 0 and bet_dir:
            self.results["hybrid"]["bets"] += 1
            self.results["hybrid"]["executes"] += 1
            
            o = odds.get(f"closing_{bet_dir}", 2.0) if odds else 2.0
            actual = "home_win" if match["home_score"] > match["away_score"] else \
                     ("away_win" if match["home_score"] < match["away_score"] else "draw")
            
            won = ((bet_dir == "home" and actual == "home_win") or
                   (bet_dir == "away" and actual == "away_win") or
                   (bet_dir == "draw" and actual == "draw"))
            
            if won:
                win = bet_amount * (o - 1)
                self.results["hybrid"]["wins"] += 1
                self.kelly.record_result(True)
            else:
                win = -bet_amount
                self.results["hybrid"]["losses"] += 1
                self.kelly.record_result(False)
            
            self.bankroll_full += win
            self.results["hybrid"]["profit"] += win
        else:
            self.results["hybrid"]["abandons"] += 1
            actual = "home_win" if match["home_score"] > match["away_score"] else \
                     ("away_win" if match["home_score"] < match["away_score"] else "draw")
        
        self.results["hybrid"]["total"] += 1
        self.results["hybrid"]["bankroll"].append(self.bankroll_full)
        
        self.results["matches"].append({
            "match_id": match["match_id"],
            "match": f"{match['home']} {match['home_score']}-{match['away_score']} {match['away']}",
            "outcome": actual,
            "action": action,
            "bet_dir": bet_dir,
            "bet_amount": bet_amount,
            "motivation": motivation,
            "pd": max_pd,
            "model": model,
            "market": market_prob,
        })

    def run(self):
        matches, odds_map = self.load_data()
        
        print("=" * 60)
        print("2022 World Cup - Hybrid Strategy (A+B) Backtest")
        print("A: Pure ELO with positive edge + Kelly")
        print("B: Motivation factor (qualified/do-or-die/rotation)")
        print("=" * 60)
        print(f"\nStarting Bankroll: EUR {self.bankroll_start:,.0f}")
        print(f"Total Matches: {len(matches)}")
        
        for match in matches:
            odds = odds_map.get(match["match_id"])
            self.run_pure_elo(match, odds)
            self.run_hybrid(match, odds)
        
        self.print_report()

    def print_report(self):
        r = self.results
        
        print("\n" + "=" * 60)
        print("BACKTEST RESULTS - Hybrid (A+B)")
        print("=" * 60)
        
        elo = r["elo_only"]
        print(f"\n[1] PURE ELO (Baseline)")
        print(f"  Bets: {elo['bets']}/{elo['total']} ({elo['bets']/elo['total']*100:.1f}%)")
        print(f"  Wins: {elo['wins']}, Losses: {elo['losses']}")
        if elo['bets'] > 0:
            print(f"  Win Rate: {elo['wins']/elo['bets']*100:.1f}%")
            print(f"  Profit: EUR {elo['profit']:+.0f}")
            print(f"  ROI: {elo['profit']/(elo['bets']*200)*100:.1f}%")
        print(f"  Final Bankroll: EUR {self.bankroll_elo:,.0f}")
        print(f"  Return: {(self.bankroll_elo/self.bankroll_start - 1)*100:+.1f}%")
        
        hybrid = r["hybrid"]
        print(f"\n[2] HYBRID (A + B: Motivation Factor)")
        print(f"  Bets: {hybrid['bets']}/{hybrid['total']} ({hybrid['bets']/hybrid['total']*100:.1f}%)")
        print(f"  Executes: {hybrid['executes']}, Abandons: {hybrid['abandons']}")
        print(f"  Wins: {hybrid['wins']}, Losses: {hybrid['losses']}")
        if hybrid['bets'] > 0:
            print(f"  Win Rate: {hybrid['wins']/hybrid['bets']*100:.1f}%")
            print(f"  Profit: EUR {hybrid['profit']:+.0f}")
        print(f"  Final Bankroll: EUR {self.bankroll_full:,.0f}")
        print(f"  Return: {(self.bankroll_full/self.bankroll_start - 1)*100:+.1f}%")
        
        print(f"\n[3] COMPARISON")
        diff = self.bankroll_full - self.bankroll_elo
        print(f"  Hybrid vs Elo: EUR {diff:+.0f} ({diff/self.bankroll_start*100:+.1f}%)")
        print(f"  Capital Efficiency: Hybrid {hybrid['bets']/hybrid['total']*100:.1f}% vs Elo {elo['bets']/elo['total']*100:.1f}%")
        
        print(f"\n[4] TOP EXECUTED BETS")
        executes = [m for m in r["matches"] if m["action"] == "EXECUTE"]
        sorted_exec = sorted(executes, key=lambda x: x["bet_amount"], reverse=True)[:10]
        for m in sorted_exec:
            result = "WIN" if ((m['bet_dir'] == 'home' and m['outcome'] == 'home_win') or
                              (m['bet_dir'] == 'away' and m['outcome'] == 'away_win') or
                              (m['bet_dir'] == 'draw' and m['outcome'] == 'draw')) else "LOSS"
            print(f"  {m['match']:30s} | {m['bet_dir']:5s} EUR {m['bet_amount']:6.0f} | {result} | Mot: {m['motivation']:+.2f} | PD: {m['pd']:+.3f}")
        
        print(f"\n[5] MOTIVATION FILTER EFFECT")
        high_mot = [m for m in r["matches"] if m["action"] == "EXECUTE" and abs(m["motivation"]) >= 0.05]
        if high_mot:
            wins = sum(1 for m in high_mot if ((m['bet_dir'] == 'home' and m['outcome'] == 'home_win') or
                                                (m['bet_dir'] == 'away' and m['outcome'] == 'away_win')))
            print(f"  High motivation matches: {len(high_mot)} | Wins: {wins} | Rate: {wins/len(high_mot)*100:.1f}%")
        
        print("\n" + "=" * 60)
        
        with open(os.path.join(os.path.dirname(__file__), "data", "backtest_2022_hybrid.json"), 'w') as f:
            json.dump(r, f, indent=2)
        print("Results saved to backtest_2022_hybrid.json")

if __name__ == "__main__":
    runner = HybridBacktestRunner(bankroll=10000)
    runner.run()
