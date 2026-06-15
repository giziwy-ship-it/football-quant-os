import asyncio
import aiohttp
from datetime import datetime

API_KEY = '6613a9a71107eff8d3f7c5585b49a162'
BASE_URL = 'https://api.the-odds-api.com/v4'

async def get_fa_cup_final_odds():
    async with aiohttp.ClientSession() as session:
        url = f'{BASE_URL}/sports/soccer_fa_cup/odds'
        params = {
            'apiKey': API_KEY,
            'regions': 'eu,uk',
            'markets': 'h2h',
            'oddsFormat': 'decimal'
        }
        
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                print(f'找到 {len(data)} 场足总杯比赛\n')
                
                for match in data:
                    home = match.get('home_team', '')
                    away = match.get('away_team', '')
                    commence = match.get('commence_time', '')
                    
                    print(f'[FINAL] {home} vs {away}')
                    print(f'时间: {commence}')
                    print(f'\n实时赔率:')
                    
                    # 收集所有博彩公司赔率
                    all_odds = []
                    for bookmaker in match.get('bookmakers', []):
                        title = bookmaker.get('title', '')
                        markets = bookmaker.get('markets', [])
                        
                        if markets:
                            outcomes = markets[0].get('outcomes', [])
                            odds_dict = {o['name']: o['price'] for o in outcomes}
                            
                            home_odd = odds_dict.get(home, 0)
                            draw_odd = odds_dict.get('Draw', 0)
                            away_odd = odds_dict.get(away, 0)
                            
                            if home_odd and draw_odd and away_odd:
                                all_odds.append({
                                    'bookmaker': title,
                                    'home': home_odd,
                                    'draw': draw_odd,
                                    'away': away_odd
                                })
                    
                    # 显示前10家
                    for odd in all_odds[:10]:
                        print(f"  {odd['bookmaker']}: 主{odd['home']} 平{odd['draw']} 客{odd['away']}")
                    
                    # 计算平均赔率
                    if all_odds:
                        avg_home = sum(o['home'] for o in all_odds) / len(all_odds)
                        avg_draw = sum(o['draw'] for o in all_odds) / len(all_odds)
                        avg_away = sum(o['away'] for o in all_odds) / len(all_odds)
                        
                        print(f'\n[平均赔率]')
                        print(f'  主胜: {avg_home:.2f}')
                        print(f'  平局: {avg_draw:.2f}')
                        print(f'  客胜: {avg_away:.2f}')
                        
                        # 计算隐含概率
                        margin_home = 1 / avg_home
                        margin_draw = 1 / avg_draw
                        margin_away = 1 / avg_away
                        total_margin = margin_home + margin_draw + margin_away
                        
                        prob_home = (margin_home / total_margin) * 100
                        prob_draw = (margin_draw / total_margin) * 100
                        prob_away = (margin_away / total_margin) * 100
                        
                        print(f'\n[隐含概率]')
                        print(f'  主胜: {prob_home:.1f}%')
                        print(f'  平局: {prob_draw:.1f}%')
                        print(f'  客胜: {prob_away:.1f}%')
                        
                        # 寻找最佳赔率
                        best_home = min(all_odds, key=lambda x: x['home'])
                        best_draw = min(all_odds, key=lambda x: x['draw'])
                        best_away = min(all_odds, key=lambda x: x['away'])
                        
                        print(f'\n[最佳赔率]')
                        print(f"  主胜: {best_home['home']} @ {best_home['bookmaker']}")
                        print(f"  平局: {best_draw['draw']} @ {best_draw['bookmaker']}")
                        print(f"  客胜: {best_away['away']} @ {best_away['bookmaker']}")
                        
            else:
                print(f'API 错误: {resp.status}')
                text = await resp.text()
                print(text[:500])

asyncio.run(get_fa_cup_final_odds())
