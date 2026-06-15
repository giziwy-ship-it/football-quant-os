import json, urllib.request

# 调用 /analyze API 进行九智能体分析
# 欧冠半决赛次回合: Inter vs Barcelona
payload = {
    "home_team": "Internazionale",
    "away_team": "Barcelona",
    "league": "UEFA Champions League",
    "home_team_rank": 2,  # Serie A 冠军
    "away_team_rank": 1,  # La Liga 冠军
    "home_recent_5": ["W", "W", "D", "W", "L"],
    "away_recent_5": ["W", "W", "W", "D", "W"],
    "market_odds": {
        "home_win": 2.70,  # 估计赔率
        "draw": 3.40,
        "away_win": 2.60
    },
    "bankroll": 10000
}

req = urllib.request.Request(
    'http://localhost:8000/api/v1/analyze',
    data=json.dumps(payload).encode('utf-8'),
    headers={'Content-Type': 'application/json'},
    method='POST'
)

resp = urllib.request.urlopen(req, timeout=60)
result = json.loads(resp.read().decode())
print(json.dumps(result, ensure_ascii=False, indent=2))
