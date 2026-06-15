#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
500.com 投注分析抓取测试 - USA vs Paraguay
"""

import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

async def scrape_500_touzhu():
    url = "https://odds.500.com/fenxi/touzhu-1359189.shtml"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN"
        )
        page = await context.new_page()
        
        print(f"[1] 加载 {url}...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
        except Exception as e:
            print(f"[ERROR] 页面加载失败: {e}")
            return None
        
        title = await page.title()
        print(f"[OK] 页面标题: {title}")
        
        # 获取页面文本内容
        page_text = await page.inner_text("body")
        
        # 保存原始文本
        output_file = f"500_usa_paraguay_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write(f"Title: {title}\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")
            f.write(page_text[:10000])  # 前10000字符
        
        print(f"[2] 原始文本已保存到: {output_file}")
        
        # 尝试提取投注分析数据
        print("\n[3] 尝试提取投注分析数据...")
        
        # 查找包含关键信息的表格
        tables = await page.query_selector_all("table")
        print(f"  发现 {len(tables)} 个表格")
        
        data = {
            "match": "USA vs Paraguay",
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "title": title,
            "tables": []
        }
        
        for i, table in enumerate(tables[:5]):  # 只处理前5个表格
            try:
                rows = await table.query_selector_all("tr")
                table_data = []
                for row in rows[:10]:  # 每表前10行
                    cells = await row.query_selector_all("td, th")
                    row_text = [await cell.inner_text() for cell in cells]
                    table_data.append(row_text)
                
                data["tables"].append({
                    "index": i,
                    "rows": table_data
                })
                
                print(f"  Table {i}: {len(rows)} rows")
            except Exception as e:
                print(f"  Table {i}: 解析失败 - {e}")
        
        # 保存结构化数据
        json_file = f"500_usa_paraguay_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[4] 结构化数据已保存到: {json_file}")
        
        await browser.close()
        return data

if __name__ == "__main__":
    print("=" * 60)
    print("500.com 投注分析抓取 - USA vs Paraguay")
    print("=" * 60)
    print()
    
    result = asyncio.run(scrape_500_touzhu())
    
    if result:
        print("\n[5] 数据预览:")
        for table in result["tables"]:
            print(f"\nTable {table['index']}:")
            for row in table["rows"][:5]:
                print(f"  {row}")
    else:
        print("\n[ERROR] 抓取失败")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)