#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
500.com 投注分析抓取 - Canada vs Bosnia
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def scrape_500_touzhu():
    url = "https://odds.500.com/fenxi/touzhu-1359182.shtml"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN"
        )
        page = await context.new_page()
        
        print(f"[1] Loading {url}...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[ERROR] Page load failed: {e}")
            return None
        
        title = await page.title()
        print(f"[OK] Page title: {title}")
        
        # Get page text
        page_text = await page.inner_text("body")
        
        # Save raw text
        output_file = f"500_can_bih_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write(f"Title: {title}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")
            f.write(page_text[:10000])
        
        print(f"[2] Raw text saved: {output_file}")
        
        # Extract betting data
        print("\n[3] Extracting betting data...")
        
        tables = await page.query_selector_all("table")
        print(f"  Found {len(tables)} tables")
        
        data = {
            "match": "Canada vs Bosnia",
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "title": title,
            "tables": []
        }
        
        for i, table in enumerate(tables[:5]):
            try:
                rows = await table.query_selector_all("tr")
                table_data = []
                for row in rows[:10]:
                    cells = await row.query_selector_all("td, th")
                    row_text = [await cell.inner_text() for cell in cells]
                    table_data.append(row_text)
                
                data["tables"].append({
                    "index": i,
                    "rows": table_data
                })
                
                print(f"  Table {i}: {len(rows)} rows")
            except Exception as e:
                print(f"  Table {i}: Parse failed - {e}")
        
        # Save structured data
        json_file = f"500_can_bih_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[4] Structured data saved: {json_file}")
        
        await browser.close()
        return data

if __name__ == "__main__":
    print("=" * 60)
    print("500.com Betting Analysis - Canada vs Bosnia")
    print("=" * 60)
    print()
    
    result = asyncio.run(scrape_500_touzhu())
    
    if result:
        print("\n[5] Data preview:")
        for table in result["tables"]:
            print(f"\nTable {table['index']}:")
            for row in table["rows"][:5]:
                print(f"  {row}")
    else:
        print("\n[ERROR] Scrape failed")
    
    print("\n" + "=" * 60)
    print("Done")
    print("=" * 60)
