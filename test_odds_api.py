import asyncio
import httpx
import json

async def test_odds_api():
    api_key = "6613a9a71107eff8d3f7c5585b49a162"
    base_url = "https://api.the-odds-api.com/v4"
    
    # 1. 获取支持的运动列表
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(f"{base_url}/sports", params={"apiKey": api_key})
        print(f"Sports API status: {resp.status_code}")
        sports = resp.json()
        wc_sports = [s for s in sports if 'world' in s.get('key', '').lower() or 'cup' in s.get('key', '').lower()]
        print(f"World Cup sports: {json.dumps(wc_sports, indent=2, ensure_ascii=False)[:500]}")
        
        # 2. 尝试获取soccer_fifa_world_cup的赔率
        sport = "soccer_fifa_world_cup"
        resp2 = await client.get(
            f"{base_url}/sports/{sport}/odds",
            params={
                "apiKey": api_key,
                "regions": "eu",
                "markets": "h2h",
                "oddsFormat": "decimal",
                "dateFormat": "iso"
            }
        )
        print(f"\nOdds API status: {resp2.status_code}")
        if resp2.status_code == 200:
            data = resp2.json()
            print(f"Total matches: {len(data)}")
            # 查找韩国vs捷克
            for match in data:
                home = match.get('home_team', '')
                away = match.get('away_team', '')
                if 'Korea' in home or 'Korea' in away or 'Czech' in home or 'Czech' in away:
                    print(f"\nFound match: {home} vs {away}")
                    print(json.dumps(match, indent=2, ensure_ascii=False)[:2000])
                    break
            else:
                print("\nKorea vs Czech not found in current odds. Showing first match:")
                if data:
                    print(json.dumps(data[0], indent=2, ensure_ascii=False)[:1500])
        else:
            print(f"Error: {resp2.text[:500]}")

asyncio.run(test_odds_api())