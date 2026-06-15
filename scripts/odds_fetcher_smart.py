#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能赔率抓取器（Smart Fetcher）
策略：优先使用轻量级 requests 版本，失败时自动 fallback 到 Playwright 版本
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any

SCRIPT_DIR = Path(__file__).parent


def run_script(script_name: str, match_id: str) -> Dict[str, Any]:
    script_path = SCRIPT_DIR / script_name
    if not script_path.exists():
        return {"success": False, "error": f"脚本不存在: {script_name}"}
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--match-id", match_id, "--format", "json"],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        else:
            return {"success": False, "error": result.stderr or result.stdout}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_odds_smart(match_id: str, use_pro: bool = False) -> Dict[str, Any]:
    """
    智能抓取 - 自动选择最优策略
    
    Args:
        match_id: 比赛ID
        use_pro: 是否直接使用 Playwright Pro（跳过轻量版）
    
    策略：
    1. 默认: 先尝试轻量 requests，失败再 fallback 到 Playwright Pro
    2. use_pro=True: 直接使用 Playwright Pro（适合反爬强的网站）
    """
    if use_pro:
        print("[Smart] 使用 Playwright Pro 专业版...", file=sys.stderr)
        data = run_script("odds_fetcher_playwright_pro.py", match_id)
        if data.get("success"):
            data["fetcher_used"] = "playwright_pro"
            data["fallback_used"] = False
            return data
        return {
            "match_id": match_id, "success": False,
            "error": "Playwright Pro 抓取失败",
            "fetcher_used": "playwright_pro", "fallback_used": False
        }
    
    # 默认策略：先轻量，后 Pro
    print("[Smart] 尝试轻量级抓取器 (requests)...", file=sys.stderr)
    data = run_script("scrape_500_simple.py", match_id)
    if data.get("success"):
        data["fetcher_used"] = "requests"
        data["fallback_used"] = False
        return data
    
    print("[Smart] 轻量级失败，切换到 Playwright Pro 专业版...", file=sys.stderr)
    data = run_script("odds_fetcher_playwright_pro.py", match_id)
    if data.get("success"):
        data["fetcher_used"] = "playwright_pro"
        data["fallback_used"] = True
        return data
    
    # 最后尝试旧版 Playwright（兼容）
    print("[Smart] Pro 失败，尝试旧版 Playwright...", file=sys.stderr)
    data = run_script("odds_fetcher_playwright.py", match_id)
    if data.get("success"):
        data["fetcher_used"] = "playwright_legacy"
        data["fallback_used"] = True
        return data
    
    return {
        "match_id": match_id, "success": False,
        "error": "所有抓取器均失败",
        "fetcher_used": "none", "fallback_used": True
    }


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('--match-id', required=True)
    p.add_argument('--format', choices=['json', 'text'], default='json')
    # Playwright Pro 相关
    parser.add_argument('--pro', action='store_true', help='使用 Playwright Pro 专业版')
    parser.add_argument('--no-pro', action='store_true', dest='pro', const=False, nargs=0, help='禁用 Pro 版')
    parser.add_argument('--stealth', action='store_true', default=True, help='启用 Stealth 模式')
    parser.add_argument('--no-stealth', action='store_true', dest='stealth', const=False, nargs=0, help='禁用 Stealth')
    parser.add_argument('--intercept', action='store_true', default=True, help='拦截资源加速')
    parser.add_argument('--no-intercept', action='store_true', dest='intercept', const=False, nargs=0, help='不拦截资源')
    parser.add_argument('--max-retries', type=int, default=3, help='最大重试次数')
    
    args = p.parse_args()
    r = get_odds_smart(args.match_id, use_pro=args.pro)
    print(json.dumps(r, ensure_ascii=False, indent=2) if args.format == 'json' else str(r))
