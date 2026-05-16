#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""查看完整API响应"""

import requests
import json
import sys
sys.stdout.reconfigure(encoding='utf-8')

payload = {
    'home_team': '罗马',
    'away_team': '亚特兰大',
    'league': '意甲',
    'home_team_rank': 6,
    'away_team_rank': 3,
    'market_odds': {'home_win': 2.40, 'draw': 3.40, 'away_win': 2.80}
}

r = requests.post('http://127.0.0.1:8000/api/v1/analyze', json=payload, timeout=30)
print(f"状态码: {r.status_code}")
print(f"完整响应:")
print(json.dumps(r.json(), ensure_ascii=False, indent=2))
