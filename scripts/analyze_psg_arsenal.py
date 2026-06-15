import json, urllib.request

# 调用 /analyze API 进行九智能体分析
payload = {
    "home_team": "Paris Saint Germain",
    "away_team": "Arsenal",
    "league": "UEFA Champions League",
    "home_team_rank": 3,
    "away_team_rank": 4,
    "home_recent_5": ["W", "W", "D", "W", "W"],
    "away_recent_5": ["W", "W", "W", "L", "W"],
    "market_odds": {
        "1": 2.474,
        "X": 3.317,
        "2": 3.037
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
