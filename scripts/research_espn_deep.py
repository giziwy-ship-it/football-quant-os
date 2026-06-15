#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赛程数据源调研脚本 - 深度探测 ESPN 数据结构
"""

import asyncio
import aiohttp
import json

async def test_espn_deep():
    url = 'https://site.api.espn.com/apis/site/v2/sports/soccer/all/scoreboard'
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    events = data.get('events', [])
                    print(f'ESPN API: {len(events)} matches')
                    
                    if events:
                        e = events[0]
                        print(f'\n=== 完整数据结构 ===')
                        print(json.dumps(e, indent=2, ensure_ascii=False)[:3000])
                    return True
                else:
                    print(f'ESPN API: status {resp.status}')
                    return False
    except Exception as e:
        print(f'ESPN API: fail - {e}')
        return False

async def main():
    await test_espn_deep()

if __name__ == '__main__':
    asyncio.run(main())
