#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 统一配置加载模块
所有模块共享的配置加载机制
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# 加载 .env 文件（从多个可能的位置）
def load_config():
    """加载环境变量配置"""
    
    # 可能的 .env 文件路径
    env_paths = [
        # 1. 项目根目录（优先）
        PROJECT_ROOT / ".env",
        # 2. 当前目录
        Path(".env"),
        # 3. 用户主目录
        Path.home() / ".openclaw" / "workspace" / "football_quant_os" / ".env",
        # 4. 旧位置（兼容）
        Path.home() / ".openclaw" / "workspace" / "skills" / "naga-core" / "scripts" / "soccer_betting" / ".env",
    ]
    
    loaded = False
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            print(f"[CONFIG] 已加载配置: {env_path}")
            loaded = True
            break
    
    if not loaded:
        print("[CONFIG] ⚠️ 未找到 .env 文件，使用默认配置")
    
    return loaded

# 配置项访问函数
def get_config(key: str, default=None):
    """获取配置项"""
    return os.getenv(key, default)

def get_api_key(service: str) -> str:
    """获取 API 密钥"""
    key_map = {
        "the_odds": "THE_ODDS_API_KEY",
        "football_data": "FOOTBALL_DATA_API_KEY",
    }
    return get_config(key_map.get(service, ""), "")

def get_data_path(filename: str = "") -> str:
    """获取数据文件路径"""
    data_dir = get_config("DATA_DIR", "./data")
    if filename:
        return os.path.join(data_dir, filename)
    return data_dir

# 初始化时自动加载
_config_loaded = False

def ensure_config():
    """确保配置已加载"""
    global _config_loaded
    if not _config_loaded:
        load_config()
        _config_loaded = True

# 模块导入时自动加载配置
ensure_config()


# ============ 测试 ============
if __name__ == "__main__":
    print("=== Football Quant OS 配置测试 ===\n")
    
    # 显示配置状态
    print("[INFO] 配置加载状态:")
    print(f"  THE_ODDS_API_KEY: {'✅ 已配置' if get_api_key('the_odds') else '❌ 未配置'}")
    print(f"  FOOTBALL_DATA_API_KEY: {'✅ 已配置' if get_api_key('football_data') else '❌ 未配置'}")
    print(f"  DATA_DIR: {get_data_path()}")
    print(f"  DEFAULT_BANKROLL: {get_config('DEFAULT_BANKROLL', '10000')}")
    print()
    
    # 显示 API 密钥（部分隐藏）
    odds_key = get_api_key("the_odds")
    if odds_key:
        print(f"[INFO] The Odds API 密钥: {odds_key[:10]}...{odds_key[-4:]}")
    
    print("\n✅ 配置系统正常！")
