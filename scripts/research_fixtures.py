#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赛程数据源调研脚本
测试 ESPN / Football-Data.org / 懂球帝 可用性
"""

import asyncio
import aiohttp
import json
from datetime import datetime

async def test_football_data():
    url = 'https://api.football-data.org/v4/matches'
    headers = {'X-Auth-Token': 'YOUR_API_KEY'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                print(f'Football-Data.org: status {resp.status}')
                return resp.status == 200
    except Exception as e:
        print(f'Football-Data.org: fail - {e}')
        return False

async def test_espn():
    url = 'https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    events = data.get('events', [])
                    print(f'ESPN API: success - {len(events)} matches')
                    # 打印示例数据
                    if events:
                        e = events[0]
                        print(f'  Example: {e.get("name", "N/A")}')
                        # 检查联赛名路径
                        comps = e.get('competitions', [])
                        if comps:
                            comp = comps[0]
                            print(f'  League path 1: {comp.get("competition", {}).get("name", "N/A")}')
                            print(f'  League path 2: {comp.get("name", "N/A")}')
                            print(f'  League path 3: {comp.get("type", {}).get("name", "N/A")}')
                        print(f'  Status: {e.get("status", {}).get("type", {}).get("description", "N/A")}')
                    return True
                else:
                    print(f'ESPN API: status {resp.status}')
                    return False
    except Exception as e:
        print(f'ESPN API: fail - {e}')
        return False

async def test_dongqiudi():
    url = 'https://www.dongqiudi.com/api/app/tabs/web/56.json'
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=10) as resp:
                print(f'Dongqiudi: status {resp.status}')
                if resp.status == 200:
                    data = await resp.json()
                    print(f'  Keys: {list(data.keys())[:10]}')
                return resp.status == 200
    except Exception as e:
        print(f'Dongqiudi: fail - {e}')
        return False

async def main():
    print('=== Data Source Research ===')
    print('[1] ESPN...')
    await test_espn()
    print('[2] Football-Data...')
    await test_football_data()
    print('[3] Dongqiudi...')
    await test_dongqiudi()

if __name__ == '__main__':
    asyncio.run(main())
