import json, urllib.request

# 调用 /analyze API 进行九智能体分析
# 欧协联决赛: Fiorentina vs Real Betis
payload = {
    "home_team": "Fiorentina",
    "away_team": "Real Betis",
    "league": "UEFA Europa Conference League",
    "home_team_rank": 6,  # Serie A 排名估计
    "away_team_rank": 5,  # La Liga 排名估计
    "home_recent_5": ["W", "D", "W", "L", "W"],
    "away_recent_5": ["W", "W", "D", "W", "L"],
    "market_odds": {
        "home_win": 2.50,  # 注意：必须使用 home_win/draw/away_win 键名
        "draw": 3.30,
        "away_win": 2.90
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
