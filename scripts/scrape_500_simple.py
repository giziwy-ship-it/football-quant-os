#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
500彩票网 简化抓取脚本 - 直接抓取页面可见数据
"""

import json
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def scrape_500_simple():
    url = "https://odds.500.com/fenxi/shuju-1407203.shtml"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN"
        )
        page = await context.new_page()
        
        print("[1] 加载页面...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        title = await page.title()
        print(f"[OK] {title}")
        
        # 获取完整页面文本
        print("[2] 提取页面文本...")
        full_text = await page.inner_text("body")
        
        # 提取表格数据
        print("[3] 提取表格...")
        tables = await page.query_selector_all("table")
        tables_data = []
        for t_idx, table in enumerate(tables):
            try:
                rows = await table.query_selector_all("tr")
                table_rows = []
                for row in rows:
                    cells = await row.query_selector_all("td, th")
                    row_data = [await c.inner_text() for c in cells]
                    if any(row_data):
                        table_rows.append(row_data)
                if table_rows:
                    tables_data.append({"index": t_idx, "rows": table_rows})
            except Exception as e:
                from core.logger import get_logger
                logger = get_logger("naga_quant.fixer")
                logger.error(f"Silent error suppressed: {e}", exc_info=True)
        
        # 提取关键div区块
        print("[4] 提取数据区块...")
        key_sections = []
        selectors = [
            "[class*='fenxi']",
            "[class*='data']",
            "[class*='info']",
            "[class*='panel']",
            "[id*='fenxi']",
            "[id*='data']"
        ]
        for sel in selectors:
            try:
                elements = await page.query_selector_all(sel)
                for el in elements[:5]:
                    text = await el.inner_text()
                    if text and 100 < len(text) < 3000:
                        key_sections.append(text.strip())
            except Exception as e:
                from core.logger import get_logger
                logger = get_logger("naga_quant.fixer")
                logger.error(f"Silent error suppressed: {e}", exc_info=True)
        
        data = {
            "match": "拜仁慕尼黑 vs 巴黎圣日耳曼",
            "url": url,
            "title": title,
            "scraped_at": datetime.now().isoformat(),
            "tables_count": len(tables_data),
            "tables": tables_data[:10],
            "sections": key_sections[:10],
            "raw_text": full_text[:10000]  # 保存前10000字符
        }
        
        # 保存
        json_path = "D:/openclaw-workspace/football_quant_os/data/500_bayern_psg.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        text_path = "D:/openclaw-workspace/football_quant_os/data/500_bayern_psg_text.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        print(f"\n[RESULT]")
        print(f"  JSON: {json_path}")
        print(f"  TEXT: {text_path}")
        print(f"  表格数: {len(tables_data)}")
        print(f"  区块数: {len(key_sections)}")
        print(f"  文本长度: {len(full_text)}")
        
        await browser.close()
        return data

if __name__ == "__main__":
    result = asyncio.run(scrape_500_simple())
    print("\n" + "="*70)
    print(" 完成")
    print("="*70)
