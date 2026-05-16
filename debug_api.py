#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
调试脚本 - 查看完整 API 返回结构
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json

BASE_URL = "http://localhost:8005/api/v1"

match_request = {
    "home_team": "曼城",
    "away_team": "利物浦",
    "league": "英超",
    "home_team_rank": 2,
    "away_team_rank": 1,
    "market_odds": {
        "home_win": 3.50,
        "draw": 3.40,
        "away_win": 2.10
    },
    "bankroll": 10000
}

print("[API CALL] 发送分析请求...")
try:
    response = requests.post(f"{BASE_URL}/analyze", json=match_request)
    result = response.json()
    
    print("\n[FULL RESPONSE]")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
except Exception as e:
    print(f"[FAIL] API 调用失败: {e}")
