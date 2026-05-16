#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OddsPortal H2H 数据抓取脚本 v2 - 增强稳定性
抓取拜仁 vs PSG 的历史交锋、近期战绩、赔率数据
"""

import json
import asyncio
from playwright.async_api import async_playwright

async def scrape_oddsportal_h2h():
    url = "https://www.oddsportal.com/football/h2h/bayern-munich-nVp0wiqd/psg-CjhkPw0k/"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
            locale="en-US"
        )
        page = await context.new_page()
        
        print("[1] 加载页面 (最大60秒)...")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        except Exception as e:
            print(f"[WARN] 首次加载超时，继续执行... {e}")
        
        # 等待页面稳定
        print("[2] 等待页面渲染...")
        await asyncio.sleep(5)
        
        # 处理可能的 Cookie 弹窗
        try:
            cookie_btn = await page.query_selector("button:has-text('Accept'), button:has-text('Agree'), [class*='cookie'] button")
            if cookie_btn:
                await cookie_btn.click()
                await asyncio.sleep(1)
                print("[OK] Cookie 弹窗已处理")
        except:
            pass
        
        # 提取页面标题
        title = await page.title()
        print(f"[OK] 页面: {title}")
        
        # 数据容器
        data = {
            "match": "Bayern Munich vs PSG",
            "url": url,
            "page_title": title,
            "h2h_records": [],
            "recent_form": {"home": [], "away": []},
            "odds": {},
            "scraped_at": None,
            "raw_text": ""
        }
        
        # 1. 抓取页面全部文本
        print("[3] 提取页面文本...")
        try:
            data["raw_text"] = await page.inner_text("body")
        except:
            pass
        
        # 2. 查找所有表格数据
        print("[4] 抓取表格数据...")
        tables = await page.query_selector_all("table")
        print(f"  发现 {len(tables)} 个表格")
        
        for idx, table in enumerate(tables):
            try:
                rows = await table.query_selector_all("tr")
                table_data = []
                for row in rows:
                    cells = await row.query_selector_all("td, th")
                    row_texts = []
                    for cell in cells:
                        text = await cell.inner_text()
                        row_texts.append(text.strip())
                    if any(row_texts):
                        table_data.append(row_texts)
                
                if table_data:
                    # 判断表格类型
                    flat = " ".join([" ".join(r) for r in table_data])
                    if any(x in flat for x in ["Bayern", "Munich", "PSG", "Paris"]):
                        if "H2H" in flat or "head" in flat.lower() or len([r for r in table_data if "Bayern" in " ".join(r) and "PSG" in " ".join(r)]) > 0:
                            data["h2h_records"].extend(table_data)
                            print(f"  表格 {idx}: H2H 数据 {len(table_data)} 行")
                        elif "Bayern" in flat or "Munich" in flat:
                            data["recent_form"]["home"].extend(table_data)
                            print(f"  表格 {idx}: 拜仁近期战绩 {len(table_data)} 行")
                        elif "PSG" in flat or "Paris" in flat:
                            data["recent_form"]["away"].extend(table_data)
                            print(f"  表格 {idx}: PSG 近期战绩 {len(table_data)} 行")
            except Exception as e:
                pass
        
        # 3. 尝试提取赔率
        print("[5] 抓取赔率...")
        odds_selectors = [
            "[class*='odd']",
            "[class*='average']",
            ".table-main td",
            "[class*='betting']",
            "[class*='price']"
        ]
        all_odds = []
        for sel in odds_selectors:
            try:
                els = await page.query_selector_all(sel)
                for el in els[:30]:
                    text = await el.inner_text()
                    if text and any(c.isdigit() for c in text):
                        all_odds.append(text.strip())
            except:
                pass
        data["odds_raw"] = list(set(all_odds))
        
        # 4. 提取 div 区块文本（可能包含比分、战绩）
        print("[6] 提取区块数据...")
        divs = await page.query_selector_all("div[class*='h2h'], div[class*='head'], div[class*='form'], div[class*='recent']")
        section_data = []
        for div in divs[:20]:
            try:
                text = await div.inner_text()
                if text and len(text) < 2000:
                    section_data.append(text.strip())
            except:
                pass
        data["sections"] = section_data
        
        # 保存完整页面文本
        from datetime import datetime
        data["scraped_at"] = datetime.now().isoformat()
        
        text_path = "D:/openclaw-workspace/football_quant_os/data/oddsportal_bayern_psg_text.txt"
        with open(text_path, "w", encoding="utf-8") as f:
            f.write(data["raw_text"])
        
        json_path = "D:/openclaw-workspace/football_quant_os/data/oddsportal_bayern_psg.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n[RESULT] 保存完成:")
        print(f"  JSON: {json_path}")
        print(f"  TEXT: {text_path}")
        print(f"  H2H 记录: {len(data['h2h_records'])} 条")
        print(f"  区块数据: {len(section_data)} 个")
        
        await browser.close()
        return data

if __name__ == "__main__":
    result = asyncio.run(scrape_oddsportal_h2h())
    print("\n" + "="*70)
    print("数据预览:")
    print("="*70)
    preview = {k: v for k, v in result.items() if k != "raw_text"}
    print(json.dumps(preview, ensure_ascii=False, indent=2)[:3000])
