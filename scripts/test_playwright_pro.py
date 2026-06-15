#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Playwright Pro 抓取器测试脚本
验证 stealth、拦截、重试等功能
"""

import sys
sys.path.insert(0, 'D:/openclaw-workspace/football_quant_os/scripts')

from odds_fetcher_playwright_pro import OddsFetcherPlaywrightPro, FetcherConfig, fetch_odds

print("=" * 60)
print("Playwright Pro Fetcher Test")
print("=" * 60)

# 测试1: 快捷函数（自动管理生命周期）
print("\n[Test 1] 快捷函数测试")
print("-" * 40)
result = fetch_odds(
    "1359233",
    headless=True,
    stealth=True,
    max_retries=2,
    intercept_resources=True
)
print(f"Match ID: {result['match_id']}")
print(f"Success: {result['success']}")
print(f"Attempts: {result['attempts']}")
print(f"Stealth: {result['stealth_applied']}")
print(f"Intercepted: {result['intercepted_resources']} resources")
if result['average']:
    print(f"Average Odds: {result['average']['home']} / {result['average']['draw']} / {result['average']['away']}")
else:
    print(f"Error: {result.get('error', 'Unknown')}")

# 测试2: Context Manager 模式
print("\n[Test 2] Context Manager 模式")
print("-" * 40)
config = FetcherConfig(
    headless=True,
    stealth=True,
    max_retries=2,
    intercept_resources=True,
    random_delay=True,
    mouse_movement=True
)

with OddsFetcherPlaywrightPro(config) as fetcher:
    result2 = fetcher.get_odds("1359233")
    print(f"Success: {result2['success']}")
    print(f"Companies found: {len(result2['companies'])}")

# 测试3: 调试模式（有头 + 截图）
print("\n[Test 3] 调试模式（有头 + 截图）")
print("-" * 40)
print("Note: 有头模式会弹出浏览器窗口，10秒后自动关闭")
import time
config_debug = FetcherConfig(
    headless=False,  # 有头模式
    stealth=True,
    max_retries=1,
    intercept_resources=False,
    save_screenshot_on_error=True,
    screenshot_dir="logs/screenshots"
)

with OddsFetcherPlaywrightPro(config_debug) as fetcher:
    result3 = fetcher.get_odds("1359233")
    print(f"Success: {result3['success']}")
    time.sleep(2)  # 让用户看到浏览器

print("\n" + "=" * 60)
print("All tests completed!")
print("=" * 60)
