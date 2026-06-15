#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
500.com 多维度数据抓取 - USA vs Paraguay
整合：投注分析、百家欧赔、让球指数、亚盘对比、大小指数、比分指数
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
import json

MATCH = "USA vs Paraguay"
MATCH_ID = "1359189"
BASE_URL = "https://odds.500.com/fenxi"

URLS = {
    "shuju": f"{BASE_URL}/shuju-{MATCH_ID}.shtml",      # 数据分析
    "touzhu": f"{BASE_URL}/touzhu-{MATCH_ID}.shtml",     # 投注分析
    "ouzhi": f"{BASE_URL}/ouzhi-{MATCH_ID}.shtml",       # 百家欧赔
    "rangqiu": f"{BASE_URL}/rangqiu-{MATCH_ID}.shtml",   # 让球指数
    "yazhi": f"{BASE_URL}/yazhi-{MATCH_ID}.shtml",       # 亚盘对比
    "daxiao": f"{BASE_URL}/daxiao-{MATCH_ID}.shtml",     # 大小指数
    "bifen": f"{BASE_URL}/bifen-{MATCH_ID}.shtml",       # 比分指数
}

async def scrape_page(page, name, url):
    """抓取单个页面"""
    print(f"\n[Scraping] {name}: {url}")
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        await asyncio.sleep(3)
        
        title = await page.title()
        text = await page.inner_text("body")
        
        # 提取表格数据
        tables = await page.query_selector_all("table")
        table_data = []
        for i, table in enumerate(tables[:10]):
            try:
                rows = await table.query_selector_all("tr")
                row_data = []
                for row in rows[:20]:
                    cells = await row.query_selector_all("td, th")
                    cell_text = [await c.inner_text() for c in cells]
                    row_data.append(cell_text)
                table_data.append({"index": i, "rows": row_data})
            except Exception as e:
                from core.logger import get_logger
                logger = get_logger("naga_quant.fixer")
                logger.error(f"Silent error suppressed: {e}", exc_info=True)
        
        return {
            "name": name,
            "url": url,
            "title": title,
            "text_preview": text[:5000],
            "tables": table_data,
            "scraped_at": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "name": name,
            "url": url,
            "error": str(e),
        }

async def main():
    print("=" * 60)
    print(f"500.com Multi-Dimension Scrape - {MATCH}")
    print(f"Time: {datetime.now().isoformat()}")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN"
        )
        page = await context.new_page()
        
        results = {}
        for name, url in URLS.items():
            result = await scrape_page(page, name, url)
            results[name] = result
            print(f"  [OK] {name}: {'success' if 'error' not in result else 'failed'}")
        
        # Save all data
        output = {
            "match": MATCH,
            "match_id": MATCH_ID,
            "scraped_at": datetime.now().isoformat(),
            "pages": results,
        }
        
        filename = f"500_{MATCH_ID}_full_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"[Saved] All data to: {filename}")
        print(f"{'='*60}")
        
        # Quick summary
        print("\n[Quick Summary]")
        for name, data in results.items():
            if 'error' not in data:
                tables_count = len(data.get('tables', []))
                print(f"  {name:12s}: {tables_count:2d} tables")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
