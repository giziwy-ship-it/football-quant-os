#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
500彩票网 足总杯决赛搜索
找到正确的比赛页面 ID
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def search_fa_cup_500():
    """搜索 500网 足总杯决赛页面"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN"
        )
        page = await context.new_page()
        
        print("[1] 访问 500彩票网 首页...")
        await page.goto("https://www.500.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(3)
        
        # 查找足总杯或搜索框
        print("[2] 查找足总杯决赛...")
        
        # 尝试点击足球
        football_links = await page.query_selector_all('a:has-text("足球")')
        for link in football_links[:3]:
            text = await link.inner_text()
            print(f"  找到: {text}")
            
        # 尝试搜索
        search_inputs = await page.query_selector_all('input')
        for inp in search_inputs[:5]:
            placeholder = await inp.get_attribute('placeholder') or ''
            print(f"  输入框: {placeholder}")
            
        # 直接尝试访问足总杯赛程页面
        print("\n[3] 尝试访问足总杯赛程...")
        
        # 500网 的足总杯页面格式
        possible_urls = [
            "https://live.500.com/fucai.php?e=312",
            "https://odds.500.com/fenxi/ouzhi-1058574.shtml",
            "https://odds.500.com/fenxi/ouzhi-1058575.shtml",
            "https://odds.500.com/fenxi/ouzhi-1058576.shtml",
        ]
        
        for url in possible_urls:
            try:
                print(f"\n  尝试: {url}")
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                await asyncio.sleep(2)
                
                title = await page.title()
                content = await page.content()
                
                if "切尔西" in content or "曼城" in content or "Chelsea" in content or "Manchester City" in content:
                    print(f"  [OK] 找到正确页面!")
                    print(f"  标题: {title}")
                    print(f"  URL: {page.url}")
                    
                    # 保存截图
                    await page.screenshot(path="500_fa_cup_found.png")
                    print(f"  截图已保存")
                    
                    await browser.close()
                    return page.url
                else:
                    print(f"  [NO] 不匹配")
                    
            except Exception as e:
                print(f"  [ERROR] {e}")
        
        await browser.close()
        return None

async def main():
    print("=" * 60)
    print("500彩票网 足总杯决赛页面搜索")
    print("切尔西 vs 曼城")
    print("=" * 60)
    
    url = await search_fa_cup_500()
    
    if url:
        print(f"\n[OK] 找到页面: {url}")
    else:
        print("\n[ERROR] 未找到页面")
        print("\n建议:")
        print("1. 手动访问 500.com 搜索 '足总杯 切尔西 曼城'")
        print("2. 找到比赛页面后复制 URL")
        print("3. URL 格式通常为: https://odds.500.com/fenxi/ouzhi-[ID].shtml")

if __name__ == "__main__":
    asyncio.run(main())
