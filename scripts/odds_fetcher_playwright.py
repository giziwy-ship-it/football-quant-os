#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""500.com 实时赔率抓取器 - Playwright 版本 (v0.1)
高鲁棒性版本，适合反爬较强的网站
"""
import argparse
import json
import re
from datetime import datetime
from typing import Dict, Any
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout


class OddsFetcherPlaywright:
    BASE = "https://odds.500.com/fenxi"

    def fetch_european_odds(self, match_id: str) -> Dict[str, Any]:
        url = f"{self.BASE}/ouzhi-{match_id}.shtml"
        result = {
            "match_id": match_id, "source": "500.com (Playwright)",
            "success": False, "average": None, "companies": [],
            "url": url, "fetched_at": datetime.now().isoformat()
        }
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                page.goto(url, wait_until="networkidle", timeout=30000)
                try:
                    page.wait_for_selector("table#datatb, tr:has-text('平均')", timeout=8000)
                except PlaywrightTimeout:
                    pass
                html = page.content()
                browser.close()
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(html, "html.parser")
                for row in soup.find_all("tr"):
                    text = row.get_text(strip=True)
                    if "平均" in text:
                        nums = re.findall(r"(\d+\.\d{2})", text)
                        if len(nums) >= 3:
                            result["average"] = {
                                "home": float(nums[0]), "draw": float(nums[1]), "away": float(nums[2])
                            }
                            result["companies"].append({
                                "company": "平均", "home": float(nums[0]),
                                "draw": float(nums[1]), "away": float(nums[2])
                            })
                        break
                result["success"] = bool(result["average"] or result["companies"])
        except Exception as e:
            result["error"] = str(e)
        return result

    def get_odds(self, match_id: str) -> Dict[str, Any]:
        return self.fetch_european_odds(match_id)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--match-id', required=True)
    parser.add_argument('--format', choices=['json', 'text'], default='json')
    args = parser.parse_args()
    fetcher = OddsFetcherPlaywright()
    result = fetcher.get_odds(args.match_id)
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.format == 'json' else str(result))