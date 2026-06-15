#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统配置 - Football Quant OS (P0 安全修复版)
轻量安全方案：开发模式免认证，生产模式强制认证
"""

import os
from typing import Dict, Any

# 加载环境变量（优先 .env.local，其次 .env）
# 使用 config.py 所在目录作为基准路径
_CONFIG_DIR = os.path.dirname(os.path.abspath(__file__))

def _load_env_file(filepath):
    """手动加载 .env 文件"""
    if not os.path.isabs(filepath):
        filepath = os.path.join(_CONFIG_DIR, '..', filepath)
    filepath = os.path.abspath(filepath)
    
    if os.path.exists(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    if key not in os.environ:
                        os.environ[key] = value

# 加载顺序：.env.local > .env
_load_env_file('.env.local')
_load_env_file('.env')


class Config:
    """系统配置"""
    
    # 版本
    VERSION = "4.1.0-p0"
    SYSTEM_NAME = "Football Quant OS"
    
    # 默认资金
    DEFAULT_BANKROLL = int(os.getenv('DEFAULT_BANKROLL', 10000))
    
    # 凯利风控参数
    KELLY_MAX_FRACTION = float(os.getenv('KELLY_MAX_FRACTION', 0.05))
    KELLY_DEFAULT_FRACTION = 0.5
    MAX_BET_PCT = float(os.getenv('MAX_BET_PCT', 0.10))
    
    # Redis 配置
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    USE_REDIS = os.getenv('USE_REDIS', 'false').lower() == 'true'
    
    # Agent 配置
    AGENT_PARALLEL_WORKERS = 8
    
    # 数据路径
    DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    BACKTEST_DATASET = os.path.join(DATA_DIR, 'backtest_dataset.json')
    
    # API 密钥（从环境变量读取，不再硬编码）
    THE_ODDS_API_KEY = os.getenv('THE_ODDS_API_KEY', '')
    FOOTBALL_DATA_API_KEY = os.getenv('FOOTBALL_DATA_API_KEY', '')
    ESPN_BASE_URL = os.getenv('ESPN_BASE_URL', 'https://site.api.espn.com/apis/site/v2/sports')
    
    # ========== P0 安全：认证配置 ==========
    # dev = 开发模式（localhost/127.0.0.1 免认证）
    # prod = 生产模式（强制 API Key 认证）
    AUTH_MODE = os.getenv('AUTH_MODE', 'dev').lower()
    DEV_API_KEY = os.getenv('DEV_API_KEY', 'naga_dev')
    PROD_API_KEY = os.getenv('PROD_API_KEY', 'change_me_in_production')
    
    # 允许的 hosts（开发模式自动包含 localhost）
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')
    
    # 认证白名单路径（这些路径不需要认证）
    AUTH_WHITELIST = ['/health', '/docs', '/openapi.json', '/redoc']
    
    @classmethod
    def is_dev_mode(cls) -> bool:
        """是否为开发模式"""
        return cls.AUTH_MODE == 'dev'
    
    @classmethod
    def is_prod_mode(cls) -> bool:
        """是否为生产模式"""
        return cls.AUTH_MODE == 'prod'
    
    @classmethod
    def get_api_key(cls) -> str:
        """获取当前有效的 API Key"""
        if cls.is_prod_mode():
            return cls.PROD_API_KEY
        return cls.DEV_API_KEY
    
    # 联赛欧战系数
    LEAGUE_COEFFICIENTS = {
        'Premier League': 98.5, 'EPL': 98.5, '英超': 98.5,
        'La Liga': 89.0, '西甲': 89.0,
        'Serie A': 81.0, '意甲': 81.0,
        'Bundesliga': 79.5, '德甲': 79.5,
        'Ligue 1': 59.5, '法甲': 59.5,
        'Champions League': 100.0, '欧冠': 100.0,
        'Europa League': 75.0, '欧联': 75.0,
        'World Cup 2026': 100.0, 'WC2026': 100.0, '世界杯': 100.0,
    }
    
    # 国家队赛事系数
    NATIONAL_TEAM_COEFFICIENTS = {
        'FIFA World Cup': 100.0,
        'UEFA Euro': 95.0,
        'Copa America': 92.0,
        'AFC Asian Cup': 80.0,
        'Africa Cup of Nations': 78.0,
        'CONCACAF Gold Cup': 75.0,
        'FIFA World Cup Qualifiers': 70.0,
        'Friendly': 50.0,
    }


config = Config()
