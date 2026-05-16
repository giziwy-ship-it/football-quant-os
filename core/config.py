#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置 - Football Quant OS
"""

import os
from typing import Dict, Any


class Config:
    """系统配置"""
    
    # 版本
    VERSION = "4.1.0"
    SYSTEM_NAME = "Football Quant OS"
    
    # 默认资金
    DEFAULT_BANKROLL = 10000
    
    # 凯利风控参数
    KELLY_MAX_FRACTION = 0.05      # 最大凯利比例 5%（精算师风控）
    KELLY_DEFAULT_FRACTION = 0.5   # 默认半凯莉
    MAX_BET_PCT = 0.10             # 单次最大投注比例 10%
    
    # Redis 配置
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    USE_REDIS = os.getenv("USE_REDIS", "false").lower() == "true"
    
    # Agent 配置
    AGENT_PARALLEL_WORKERS = 8
    
    # 数据路径
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    BACKTEST_DATASET = os.path.join(DATA_DIR, "backtest_dataset.json")
    
    # 联赛欧战系数
    LEAGUE_COEFFICIENTS = {
        'Premier League': 98.5, 'EPL': 98.5, '英超': 98.5,
        'La Liga': 89.0, '西甲': 89.0,
        'Serie A': 81.0, '意甲': 81.0,
        'Bundesliga': 79.5, '德甲': 79.5,
        'Ligue 1': 59.5, '法甲': 59.5,
        'Champions League': 100.0, '欧冠': 100.0,
        'Europa League': 75.0, '欧联': 75.0,
    }


config = Config()
