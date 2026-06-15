import json, urllib.request
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 批量分析德乙比赛
matches = [
    {
        "name": "Magdeburg vs Hamburg",
        "home_team": "1.FC Magdeburg",
        "away_team": "Hamburger SV",
        "league": "2. Bundesliga",
        "home_rank": 8, "away_rank": 3,
        "home_recent": ["W", "L", "D", "W", "L"],
        "away_recent": ["W", "W", "D", "L", "W"],
        "odds": {"home_win": 2.50, "draw": 3.40, "away_win": 2.70}
    },
    {
        "name": "Heidenheim vs Paderborn",
        "home_team": "1.FC Heidenheim",
        "away_team": "SC Paderborn 07",
        "league": "2. Bundesliga",
        "home_rank": 5, "away_rank": 7,
        "home_recent": ["D", "W", "L", "W", "D"],
        "away_recent": ["L", "W", "D", "W", "L"],
        "odds": {"home_win": 2.30, "draw": 3.30, "away_win": 3.00}
    },
    {
        "name": "Köln vs Regensburg",
        "home_team": "1.FC Köln",
        "away_team": "SSV Jahn Regensburg",
        "league": "2. Bundesliga",
        "home_rank": 2, "away_rank": 16,
        "home_recent": ["W", "W", "D", "W", "L"],
        "away_recent": ["L", "L", "D", "L", "W"],
        "odds": {"home_win": 1.55, "draw": 4.00, "away_win": 5.50}
    },
    {
        "name": "Nürnberg vs Karlsruher",
        "home_team": "1.FC Nürnberg",
        "away_team": "Karlsruher SC",
        "league": "2. Bundesliga",
        "home_rank": 10, "away_rank": 6,
        "home_recent": ["L", "W", "D", "L", "W"],
        "away_recent": ["W", "D", "W", "L", "D"],
        "odds": {"home_win": 2.60, "draw": 3.30, "away_win": 2.60}
    },
    {
        "name": "Union Berlin vs Erzgebirge Aue",
        "home_team": "1.FC Union Berlin",
        "away_team": "FC Erzgebirge Aue",
        "league": "2. Bundesliga",
        "home_rank": 4, "away_rank": 18,
        "home_recent": ["W", "D", "W", "W", "L"],
        "away_recent": ["L", "L", "L", "D", "L"],
        "odds": {"home_win": 1.40, "draw": 4.50, "away_win": 7.00}
    },
    {
        "name": "Union Berlin vs Magdeburg",
        "home_team": "1.FC Union Berlin",
        "away_team": "1.FC Magdeburg",
        "league": "2. Bundesliga",
        "home_rank": 4, "away_rank": 8,
        "home_recent": ["W", "D", "W", "W", "L"],
        "away_recent": ["W", "L", "D", "W", "L"],
        "odds": {"home_win": 1.90, "draw": 3.50, "away_win": 3.80}
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
        
        # 提取关键信息
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

# 输出完整结果
print("\n" + "="*60)
print("BATCH ANALYSIS COMPLETE")
print("="*60)
print(json.dumps(results, ensure_ascii=False, indent=2))
