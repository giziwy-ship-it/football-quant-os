#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赛程模块测试脚本
验证 ESPN 客户端 + API 端点
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import asyncio
import aiohttp


async def test_fixtures_today():
    """测试今天赛程端点"""
    print("=" * 70)
    print("测试1: GET /api/v1/fixtures/today")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/api/v1/fixtures/today", timeout=20) as resp:
            print(f"状态码: {resp.status}")
            
            if resp.status == 200:
                data = await resp.json()
                print(f"日期: {data.get('date')}")
                print(f"总场数: {data.get('total')}")
                print(f"联赛: {', '.join(data.get('leagues', []))}")
                print()
                
                # 显示前5场
                fixtures = data.get('fixtures', [])
                print(f"前5场比赛:")
                for i, f in enumerate(fixtures[:5], 1):
                    print(f"  {i}. {f['match_time']} | {f['league']}")
                    print(f"     {f['home_team']} vs {f['away_team']} ({f['status']})")
                    if f.get('home_score') is not None:
                        print(f"     比分: {f['home_score']}-{f['away_score']}")
                
                if len(fixtures) > 5:
                    print(f"  ... 还有 {len(fixtures) - 5} 场")
                
                return True
            else:
                text = await resp.text()
                print(f"错误: {text[:200]}")
                return False


async def test_fixtures_date():
    """测试指定日期赛程端点"""
    print()
    print("=" * 70)
    print("测试2: GET /api/v1/fixtures/date/2026-05-05")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/api/v1/fixtures/date/2026-05-05", timeout=20) as resp:
            print(f"状态码: {resp.status}")
            
            if resp.status == 200:
                data = await resp.json()
                print(f"日期: {data.get('date')}")
                print(f"总场数: {data.get('total')}")
                return True
            else:
                text = await resp.text()
                print(f"错误: {text[:200]}")
                return False


async def test_fixtures_invalid_date():
    """测试无效日期"""
    print()
    print("=" * 70)
    print("测试3: GET /api/v1/fixtures/date/invalid")
    print("=" * 70)
    
    async with aiohttp.ClientSession() as session:
        async with session.get("http://localhost:8000/api/v1/fixtures/date/invalid", timeout=10) as resp:
            print(f"状态码: {resp.status}")
            data = await resp.json()
            print(f"响应: {data}")
            return True


async def main():
    print("Football Quant OS - 赛程模块测试")
    print()
    
    results = []
    
    try:
        results.append(("today", await test_fixtures_today()))
    except Exception as e:
        print(f"测试1失败: {e}")
        results.append(("today", False))
    
    try:
        results.append(("date", await test_fixtures_date()))
    except Exception as e:
        print(f"测试2失败: {e}")
        results.append(("date", False))
    
    try:
        results.append(("invalid", await test_fixtures_invalid_date()))
    except Exception as e:
        print(f"测试3失败: {e}")
        results.append(("invalid", False))
    
    print()
    print("=" * 70)
    print("测试结果汇总")
    print("=" * 70)
    for name, ok in results:
        status = "✅ 通过" if ok else "❌ 失败"
        print(f"  {name}: {status}")
    
    all_pass = all(ok for _, ok in results)
    print()
    if all_pass:
        print("🎉 所有测试通过！赛程模块工作正常。")
    else:
        print("⚠️ 部分测试失败，请检查服务状态。")


if __name__ == "__main__":
    asyncio.run(main())
