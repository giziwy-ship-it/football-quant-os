import asyncio
import aiohttp

API_KEY = '6613a9a71107eff8d3f7c5585b49a162'
BASE_URL = 'https://api.the-odds-api.com/v4'

async def get_odds():
    async with aiohttp.ClientSession() as session:
        url = f'{BASE_URL}/sports/soccer_epl/odds'
        params = {
            'apiKey': API_KEY,
            'regions': 'eu',
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        }
        
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f'找到 {len(data)} 场比赛')
                
                for match in data:
                    home = match.get('home_team', '')
                    away = match.get('away_team', '')
                    if 'Manchester City' in home or 'Manchester City' in away or 'Chelsea' in home or 'Chelsea' in away:
                        print(f'\n[FINAL] {home} vs {away}')
                        print(f'时间: {match.get("commence_time")}')
                        
                        for bookmaker in match.get('bookmakers', [])[:3]:
                            title = bookmaker.get('title')
                            markets = bookmaker.get('markets', [])
                            if markets:
                                outcomes = markets[0].get('outcomes', [])
                                odds = {o['name']: o['price'] for o in outcomes}
                                home_odd = odds.get(home, '?')
                                draw_odd = odds.get('Draw', '?')
                                away_odd = odds.get(away, '?')
                                print(f'  {title}: 主{home_odd} 平{draw_odd} 客{away_odd}')
            else:
                print(f'API 错误: {resp.status}')
                text = await resp.text()
                print(text[:500])

asyncio.run(get_odds())
