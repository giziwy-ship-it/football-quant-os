import json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8')

# 用500彩票网的完整数据重新分析PSG vs Arsenal
# 包含诱盘识别信号

payload = {
    "home_team": "Paris Saint Germain",
    "away_team": "Arsenal",
    "league": "UEFA Champions League",
    "home_team_rank": 3,
    "away_team_rank": 4,
    "home_recent_5": ["W", "W", "D", "W", "W"],
    "away_recent_5": ["W", "W", "W", "L", "W"],
    "market_odds": {
        "home_win": 2.41,  # 500网百家欧赔
        "draw": 3.26,
        "away_win": 3.02
    },
    # 完整资金流向数据（按analyst_v2.py格式）
    "money_flow": {
        "euro_home_prob": 39.4,  # 百家欧赔概率
        "euro_draw_prob": 29.1,
        "euro_away_prob": 31.4,
        "bf_home_volume": 30304486,  # 必发成交量
        "bf_draw_volume": 5479355,
        "bf_away_volume": 10777706,
        "bookmaker_home_pnl": -31017937,  # 庄家盈亏
        "bookmaker_draw_pnl": 27931740,
        "bookmaker_away_pnl": 12611773,
        "profit_index_home": -67,  # 盈亏指数
        "profit_index_draw": 59,
        "profit_index_away": 27,
        "cold_hot_index_home": 65,  # 冷热指数
        "cold_hot_index_draw": -60,
        "cold_hot_index_away": -27
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
