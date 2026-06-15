import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.multi_market_predictor import MultiMarketPredictor, Match, Prediction

# ============================================================
# 真实数据：Qatar vs Switzerland (2026 World Cup)
# 来源: 500.com + OddsPortal (20+ bookmakers) 实时抓取 2026-06-13
# ============================================================

match = Match(
    home='Qatar',
    away='Switzerland',
    competition='2026 World Cup',
    date='2026-06-14 03:00',
    home_fifa_rank=50,
    away_fifa_rank=15,
    home_recent_form=['D', 'L', 'D', 'L'],  # 0-0 ElSalv, 0-1 Ireland, 1-1 Syria, 0-3 Tunisia
    away_recent_form=['D', 'W', 'D', 'L', 'D'],  # 1-1 Aus, 4-1 Jordan, 0-0 Norway, 3-4 Germany, 1-1 Kosovo
    home_goals_scored=1,   # 最近4场只进1球
    home_goals_conceded=7,  # 丢7球
    away_goals_scored=9,   # 最近5场进9球
    away_goals_conceded=7,  # 丢7球
    # OddsPortal 最佳赔率 (去margin后)
    odds_1x2=(16.00, 7.36, 1.24),  # Best: Home Betfair 16.00 / Draw GGBET 7.36 / Away Mozzartbet 1.24
    odds_ah={
        '+2.0': (1.67, 3.70),  # bet365 from 500.com: Qatar +2.0 @ 1.67
    },
    odds_ou={
        '2.5': (1.61, 1.00),   # BetInAsia Over 2.5 @ 1.61
        '3.0': (1.75, 1.00),   # 估计
    },
    coach_home_cri=5.0,  # 估计
    coach_away_cri=3.5,  # 估计
)

print("=" * 60)
print("NAGA QUANT - REAL DATA MULTI-MARKET PREDICTION")
print("=" * 60)
print()

print(f"Match: {match.home} vs {match.away}")
print(f"Date: {match.date}")
print(f"Competition: {match.competition}")
print()
print("[DATA SOURCES]")
print("  500.com: 6 bookmakers (欧指/让球/大小球/亚盘/投注)")
print("  OddsPortal: 20+ bookmakers (1xBet, bet365, Betfair, Megapari, etc.)")
print("  Betfair Exchange: 39,373 units on Away (89% majority)")
print()
print("[ODDS SUMMARY]")
print(f"  1X2: Home {match.odds_1x2[0]:.2f} | Draw {match.odds_1x2[1]:.2f} | Away {match.odds_1x2[2]:.2f}")
print(f"  AH:  Qatar +2.0 @ {match.odds_ah['+2.0'][0]:.2f}")
print(f"  O/U: 2.5 Over @ {match.odds_ou['2.5'][0]:.2f}")
print(f"  FIFA: Qatar #{match.home_fifa_rank} vs Switzerland #{match.away_fifa_rank}")
print()
print("[RECENT FORM]")
print("  Qatar: D-L-D-L (1 goal scored, 7 conceded in 4 matches)")
print("  Switzerland: D-W-D-L-D (9 goals scored, 7 conceded in 5 matches)")
print("  H2H: 2018 Qatar 1-0 Switzerland (Qatar +13.00 underdog won!)")
print()

# 执行预测
predictor = MultiMarketPredictor(match)
predictions = predictor.predict_all()

print("=" * 60)
print("PREDICTIONS - 6 MARKETS")
print("=" * 60)
print()

for market, preds in predictions.items():
    print(f"[{market}]")
    for p in preds:
        rec = "[RECOMMENDED]" if p.recommended else "[Neutral]"
        print(f"  {p.prediction:25} | Conf: {p.confidence:.0f}% | Edge: {p.edge:+.1%} | {rec}")
        print(f"    {p.reasoning}")
    print()

print("=" * 60)
print("SUMMARY - RECOMMENDED BETS")
print("=" * 60)
print()

all_recommended = []
for market, preds in predictions.items():
    for p in preds:
        if p.recommended:
            all_recommended.append((market, p))

all_recommended.sort(key=lambda x: x[1].edge, reverse=True)

for i, (market, p) in enumerate(all_recommended, 1):
    print(f"{i}. [{market}] {p.prediction}")
    print(f"   Edge: {p.edge:+.1%} | Confidence: {p.confidence:.0f}%")
    print(f"   Reasoning: {p.reasoning}")
    print()

print("=" * 60)
print("AVOID: Swiss Away @ 1.24 (market overvalues, 89% public money)")
print("Risk: MODERATE | Model: Poisson + ELO + Form + Market Bias")
print("=" * 60)
