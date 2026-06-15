import json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8')

# 批量分析明天重点比赛
matches = [
    {
        "name": "Brighton vs Man City",
        "home_team": "Brighton & Hove Albion",
        "away_team": "Manchester City",
        "league": "Premier League",
        "home_rank": 8, "away_rank": 2,
        "home_recent": ["W", "L", "D", "W", "L"],
        "away_recent": ["W", "W", "D", "W", "W"],
        "odds": {"home_win": 3.80, "draw": 3.50, "away_win": 1.90}
    },
    {
        "name": "Real Madrid vs Granada",
        "home_team": "Real Madrid",
        "away_team": "Granada",
        "league": "La Liga",
        "home_rank": 1, "away_rank": 18,
        "home_recent": ["W", "W", "D", "W", "W"],
        "away_recent": ["L", "L", "D", "L", "L"],
        "odds": {"home_win": 1.15, "draw": 7.00, "away_win": 15.00}
    },
    {
        "name": "Real Sociedad vs Atletico",
        "home_team": "Real Sociedad",
        "away_team": "Atletico Madrid",
        "league": "La Liga",
        "home_rank": 6, "away_rank": 3,
        "home_recent": ["W", "D", "L", "W", "D"],
        "away_recent": ["W", "L", "W", "D", "W"],
        "odds": {"home_win": 2.60, "draw": 3.20, "away_win": 2.70}
    },
    {
        "name": "Espanyol vs Sevilla",
        "home_team": "Espanyol",
        "away_team": "Sevilla",
        "league": "La Liga",
        "home_rank": 14, "away_rank": 12,
        "home_recent": ["L", "W", "D", "L", "W"],
        "away_recent": ["D", "W", "L", "D", "L"],
        "odds": {"home_win": 2.80, "draw": 3.20, "away_win": 2.50}
    },
    {
        "name": "Bragantino vs Internacional",
        "home_team": "Red Bull Bragantino",
        "away_team": "Internacional",
        "league": "Brasileirão Serie A",
        "home_rank": 10, "away_rank": 4,
        "home_recent": ["W", "L", "D", "W", "L"],
        "away_recent": ["W", "W", "D", "L", "W"],
        "odds": {"home_win": 2.40, "draw": 3.10, "away_win": 3.00}
    }
]

results = []
for m in matches:
    payload = {
        "home_team": m["home_team"],
        "away_team": m["away_team"],
        "league": m["league"],
        "home_team_rank": m["home_rank"],
        "away_team_rank": m["away_rank"],
        "home_recent_5": m["home_recent"],
        "away_recent_5": m["away_recent"],
        "market_odds": m["odds"],
        "bankroll": 10000
    }
    
    req = urllib.request.Request(
        'http://localhost:8000/api/v1/analyze',
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read().decode())
        
        summary = {
            "match": m["name"],
            "odds": m["odds"],
            "prediction": result.get("decision", {}).get("prediction", {}),
            "recommendation": result.get("decision", {}).get("recommended_outcome", ""),
            "risk_level": result.get("risk_control", {}).get("risk_level", ""),
            "allow": result.get("risk_control", {}).get("allow", False),
            "warnings": result.get("risk_control", {}).get("warnings", []),
            "market_odds_used": result.get("decision", {}).get("market_odds_used", False)
        }
        results.append(summary)
        print(f"[OK] {m['name']}")
    except Exception as e:
        print(f"[ERR] {m['name']}: {e}")
        results.append({"match": m["name"], "error": str(e)})

print("\n" + "="*60)
print("BATCH ANALYSIS COMPLETE")
print("="*60)
print(json.dumps(results, ensure_ascii=False, indent=2))
