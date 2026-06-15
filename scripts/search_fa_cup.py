import asyncio
import aiohttp

API_KEY = '6613a9a71107eff8d3f7c5585b49a162'
BASE_URL = 'https://api.the-odds-api.com/v4'

async def get_all_sports():
    async with aiohttp.ClientSession() as session:
        # 获取所有赛事类型
        url = f'{BASE_URL}/sports'
        params = {'apiKey': API_KEY}
        
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                print('所有赛事类型:')
                for sport in data:
                    key = sport.get('key', '')
                    title = sport.get('title', '')
                    if 'soccer' in key or 'cup' in key or 'england' in key:
                        print(f'  {key}: {title}')
            else:
                print(f'错误: {resp.status}')

async def search_fa_cup():
    async with aiohttp.ClientSession() as session:
        # 尝试不同的赛事key
        sports_to_try = [
            'soccer_fa_cup',
            'soccer_england_efl_cup', 
            'soccer_epl',
            'soccer_uefa_champs_league'
        ]
        
        for sport_key in sports_to_try:
            url = f'{BASE_URL}/sports/{sport_key}/odds'
            params = {
                'apiKey': API_KEY,
                'regions': 'eu',
                'markets': 'h2h',
                'oddsFormat': 'decimal'
            }
            
            try:
                async with session.get(url, params=params, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        print(f'\n[{sport_key}] 找到 {len(data)} 场比赛')
                        
                        for match in data[:5]:
                            home = match.get('home_team', '')
                            away = match.get('away_team', '')
                            print(f'  - {home} vs {away}')
                    elif resp.status == 404:
                        print(f'[{sport_key}] 赛事不存在')
                    else:
                        print(f'[{sport_key}] 错误: {resp.status}')
            except Exception as e:
                print(f'[{sport_key}] 异常: {e}')

asyncio.run(get_all_sports())
print('\n' + '='*50 + '\n')
asyncio.run(search_fa_cup())
