#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
500彩票网 数据分析全面抓取脚本
抓取所有菜单数据: 专家情报、投注分析、百家欧赔、让球指数、亚盘对比、大小指数、比分指数、走势分析、技术统计
"""

import json
import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

MENU_MAP = {
    "专家情报": "zhuanjia",
    "投注分析": "touzhu",
    "百家欧赔": "oupei",
    "让球指数": "rangqiu",
    "亚盘对比": "yapan",
    "大小指数": "daxiao",
    "比分指数": "bifen",
    "走势分析": "zoushi",
    "技术统计": "jishu"
}

async def scrape_500_data():
    url = "https://odds.500.com/fenxi/shuju-1407203.shtml"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN"
        )
        page = await context.new_page()
        
        print("[1] 加载 500彩票网 数据页...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        title = await page.title()
        print(f"[OK] 页面: {title}")
        
        all_data = {
            "match": "拜仁慕尼黑 vs 巴黎圣日耳曼",
            "url": url,
            "scraped_at": datetime.now().isoformat(),
            "menus": {}
        }
        
        # 获取所有菜单按钮
        menu_buttons = await page.query_selector_all(".nav-menu a, .menu-item a, [class*='nav'] a, .tab a, [class*='fenxi-menu'] a")
        menu_texts = []
        for btn in menu_buttons:
            text = await btn.inner_text()
            if text.strip():
                menu_texts.append(text.strip())
        
        print(f"[2] 发现 {len(menu_texts)} 个菜单: {menu_texts}")
        
        # 逐个点击抓取
        for menu_name in menu_texts:
            if menu_name in ["首页", "返回", "登录"]:
                continue
            
            print(f"\n[3] 抓取菜单: {menu_name} ...")
            
            try:
                # 找到并点击菜单
                selector = f"a:has-text('{menu_name}')"
                btn = await page.query_selector(selector)
                if btn:
                    await btn.click()
                    await asyncio.sleep(3)
                
                # 获取页面文本内容
                page_text = await page.inner_text("body")
                
                # 获取页面内的表格数据
                tables_data = []
                tables = await page.query_selector_all("table")
                for t_idx, table in enumerate(tables):
                    try:
                        rows = await table.query_selector_all("tr")
                        table_rows = []
                        for row in rows:
                            cells = await row.query_selector_all("td, th")
                            row_data = []
                            for cell in cells:
                                text = await cell.inner_text()
                                row_data.append(text.strip())
                            if any(row_data):
                                table_rows.append(row_data)
                        if table_rows:
                            tables_data.append(table_rows)
                    except Exception as e:
                        from core.logger import get_logger
                        logger = get_logger("naga_quant.fixer")
                        logger.error(f"Silent error suppressed: {e}", exc_info=True)
                
                # 获取div区块数据
                sections = []
                divs = await page.query_selector_all("div[class*='panel'], div[class*='box'], div[class*='content'], .data-list, .info-list")
                for div in divs[:10]:
                    try:
                        text = await div.inner_text()
                        if text and 50 < len(text) < 2000:
                            sections.append(text.strip())
                    except Exception as e:
                        from core.logger import get_logger
                        logger = get_logger("naga_quant.fixer")
                        logger.error(f"Silent error suppressed: {e}", exc_info=True)
                
                all_data["menus"][menu_name] = {
                    "raw_text": page_text[:5000],  # 保存前5000字符
                    "tables": tables_data[:5],     # 最多5个表格
                    "sections": sections[:5]        # 最多5个区块
                }
                
                print(f"   表格: {len(tables_data)} | 区块: {len(sections)}")
                
            except Exception as e:
                print(f"   [ERROR] {menu_name}: {e}")
                all_data["menus"][menu_name] = {"error": str(e)}
        
        # 保存完整数据
        json_path = "D:/openclaw-workspace/football_quant_os/data/500_bayern_psg_full.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_data, f, ensure_ascii=False, indent=2)
        
        # 保存完整文本
        text_path = "D:/openclaw-workspace/football_quant_os/data/500_bayern_psg_text.txt"
        full_text = ""
        for menu, data in all_data["menus"].items():
            if "raw_text" in data:
                full_text += f"\n{'='*70}\n[{menu}]\n{'='*70}\n{data['raw_text']}\n"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(full_text)
        
        print(f"\n[RESULT] 抓取完成:")
        print(f"  JSON: {json_path}")
        print(f"  TEXT: {text_path}")
        print(f"  菜单数: {len(all_data['menus'])}")
        
        await browser.close()
        return all_data

if __name__ == "__main__":
    result = asyncio.run(scrape_500_data())
    print("\n" + "="*70)
    print(" 数据摘要:")
    print("="*70)
    for menu, data in result["menus"].items():
        tables = len(data.get("tables", []))
        sections = len(data.get("sections", []))
        print(f"  {menu:15} - 表格:{tables} 区块:{sections}")
