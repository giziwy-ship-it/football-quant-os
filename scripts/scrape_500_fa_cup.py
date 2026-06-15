#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
500彩票网 数据抓取 - 足总杯决赛: 切尔西 vs 曼城
抓取所有有效数据用于预测修正
"""

import json
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

# 500网 足总杯决赛页面
# 需要搜索实际的比赛 ID
SEARCH_URL = "https://odds.500.com/fenxi/"

async def search_match_500():
    """搜索 500网 上的足总杯决赛"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN"
        )
        page = await context.new_page()
        
        print("[1] 搜索 500网 足总杯决赛...")
        
        # 尝试直接访问足总杯页面
        url = "https://odds.500.com/fenxi/shuju-1407203.shtml"
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(3)
            
            title = await page.title()
            print(f"[OK] 页面: {title}")
            
            # 检查是否是正确的比赛
            page_content = await page.content()
            
            if "切尔西" in page_content or "曼城" in page_content or "Chelsea" in page_content or "Manchester City" in page_content:
                print("[OK] 找到匹配页面!")
                
                # 提取所有数据
                data = await extract_all_data(page)
                
                await browser.close()
                return data
            else:
                print("[WARN] 页面不匹配，尝试搜索...")
                
                # 尝试搜索
                await page.goto("https://www.500.com/", wait_until="domcontentloaded", timeout=30000)
                await asyncio.sleep(2)
                
                # 查找搜索框或足总杯链接
                search_input = await page.query_selector('input[placeholder*="搜索"]') or \
                              await page.query_selector('input[placeholder*="search"]')
                
                if search_input:
                    await search_input.fill("足总杯 切尔西 曼城")
                    await search_input.press("Enter")
                    await asyncio.sleep(3)
                    
                    # 查找结果
                    links = await page.query_selector_all('a')
                    for link in links:
                        text = await link.inner_text()
                        if "切尔西" in text and "曼城" in text:
                            href = await link.get_attribute('href')
                            print(f"[OK] 找到链接: {text} -> {href}")
                            
                            await page.goto(href, wait_until="domcontentloaded", timeout=30000)
                            await asyncio.sleep(3)
                            
                            data = await extract_all_data(page)
                            await browser.close()
                            return data
                
                await browser.close()
                return None
                
        except Exception as e:
            print(f"[ERROR] {e}")
            await browser.close()
            return None

async def extract_all_data(page):
    """提取所有有效数据"""
    
    data = {
        "match": "切尔西 vs 曼城",
        "competition": "足总杯决赛",
        "scraped_at": datetime.now().isoformat(),
        "url": page.url,
        "menus": {}
    }
    
    # 菜单映射
    menu_tabs = [
        ("专家情报", "zhuanjia"),
        ("投注分析", "touzhu"),
        ("百家欧赔", "oupei"),
        ("让球指数", "rangqiu"),
        ("亚盘对比", "yapan"),
        ("大小指数", "daxiao"),
        ("比分指数", "bifen"),
        ("走势分析", "zoushi"),
        ("技术统计", "jishu")
    ]
    
    for menu_name, menu_id in menu_tabs:
        print(f"\n[抓取] {menu_name}...")
        
        try:
            # 点击菜单
            menu_link = await page.query_selector(f'a[href*="{menu_id}"]') or \
                       await page.query_selector(f'text="{menu_name}"')
            
            if menu_link:
                await menu_link.click()
                await asyncio.sleep(2)
                
                # 提取数据
                content = await page.content()
                
                # 根据菜单类型提取特定数据
                if menu_name == "百家欧赔":
                    data["menus"][menu_name] = extract_oupei_data(content)
                elif menu_name == "让球指数":
                    data["menus"][menu_name] = extract_rangqiu_data(content)
                elif menu_name == "大小指数":
                    data["menus"][menu_name] = extract_daxiao_data(content)
                elif menu_name == "技术统计":
                    data["menus"][menu_name] = extract_jishu_data(content)
                else:
                    data["menus"][menu_name] = {"raw_text": content[:2000]}
                
                print(f"[OK] {menu_name} 抓取完成")
            else:
                print(f"[WARN] 未找到 {menu_name} 菜单")
                
        except Exception as e:
            print(f"[ERROR] {menu_name}: {e}")
    
    return data

def extract_oupei_data(content):
    """提取百家欧赔数据"""
    # 提取主要博彩公司赔率
    import re
    
    # 查找赔率表格
    odds_pattern = r'(\d+\.\d+)\s+(\d+\.\d+)\s+(\d+\.\d+)'
    matches = re.findall(odds_pattern, content)
    
    if matches:
        return {
            "odds_count": len(matches),
            "sample_odds": matches[:5],
            "avg_home": sum(float(m[0]) for m in matches[:10]) / min(len(matches), 10),
            "avg_draw": sum(float(m[1]) for m in matches[:10]) / min(len(matches), 10),
            "avg_away": sum(float(m[2]) for m in matches[:10]) / min(len(matches), 10)
        }
    return {"error": "未找到赔率数据"}

def extract_rangqiu_data(content):
    """提取让球指数"""
    import re
    
    # 查找让球数据
    handicap_pattern = r'([+-]?\d+\.?\d*)\s+@\s+(\d+\.\d+)'
    matches = re.findall(handicap_pattern, content)
    
    if matches:
        return {
            "handicaps": matches[:10],
            "count": len(matches)
        }
    return {"error": "未找到让球数据"}

def extract_daxiao_data(content):
    """提取大小球指数"""
    import re
    
    # 查找大小球数据
    over_under_pattern = r'(\d+\.\d+)\s+([大|小])\s+@\s+(\d+\.\d+)'
    matches = re.findall(over_under_pattern, content)
    
    if matches:
        return {
            "over_under": matches[:10],
            "count": len(matches)
        }
    return {"error": "未找到大小球数据"}

def extract_jishu_data(content):
    """提取技术统计"""
    # 提取关键统计数据
    stats = {}
    
    # 查找常见统计项
    stat_patterns = [
        ("possession", r'控球率.*?([\d.]+)%.*?([\d.]+)%'),
        ("shots", r'射门.*?([\d.]+).*?([\d.]+)'),
        ("shots_on_target", r'射正.*?([\d.]+).*?([\d.]+)'),
        ("corners", r'角球.*?([\d.]+).*?([\d.]+)'),
        ("fouls", r'犯规.*?([\d.]+).*?([\d.]+)')
    ]
    
    import re
    for stat_name, pattern in stat_patterns:
        match = re.search(pattern, content)
        if match:
            stats[stat_name] = {
                "home": match.group(1),
                "away": match.group(2)
            }
    
    return stats if stats else {"error": "未找到技术统计"}

async def main():
    print("=" * 60)
    print("500彩票网 数据抓取 - 足总杯决赛")
    print("切尔西 vs 曼城")
    print("=" * 60)
    
    data = await search_match_500()
    
    if data:
        # 保存数据
        filename = f"500_data_fa_cup_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[OK] 数据已保存: {filename}")
        
        # 打印摘要
        print("\n" + "=" * 60)
        print("数据摘要")
        print("=" * 60)
        
        for menu_name, menu_data in data.get("menus", {}).items():
            print(f"\n[{menu_name}]")
            if isinstance(menu_data, dict):
                for key, value in menu_data.items():
                    if key != "raw_text":
                        print(f"  {key}: {value}")
            else:
                print(f"  {str(menu_data)[:200]}")
    else:
        print("\n[ERROR] 未能抓取数据")

if __name__ == "__main__":
    asyncio.run(main())
