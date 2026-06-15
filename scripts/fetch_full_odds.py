import json, urllib.request

api_key = '6613a9a71107eff8d3f7c5585b49a162'
sport = 'soccer_uefa_champs_league'

url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds?apiKey={api_key}&regions=eu&markets=h2h&oddsFormat=decimal&dateFormat=iso'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode())

for match in data:
    if 'paris saint germain' in match['home_team'].lower() and 'arsenal' in match['away_team'].lower():
        print('=== PSG vs ARSENAL ===')
        print(f'ID: {match["id"]}')
        print(f'Kickoff: {match["commence_time"]}')
        print(f'Total bookmakers: {len(match["bookmakers"])}')
        
        # 收集所有 bookmaker 的 h2h 赔率并做简单平均
        all_odds = {'1': [], 'X': [], '2': []}
        for bm in match['bookmakers']:
            try:
                outcomes = bm['markets'][0]['outcomes']
                odds_map = {o['name'].lower(): o['price'] for o in outcomes}
                
                home_odds = odds_map.get('paris saint germain') or odds_map.get('psg')
                away_odds = odds_map.get('arsenal')
                draw_odds = odds_map.get('draw')
                
                if home_odds:
                    all_odds['1'].append(home_odds)
                if draw_odds:
                    all_odds['X'].append(draw_odds)
                if away_odds:
                    all_odds['2'].append(away_odds)
            except Exception:
                continue
        
        print('\n=== 百家欧赔平均 ===')
        for k, v in all_odds.items():
            if v:
                avg = sum(v) / len(v)
                print(f'{k}: avg={avg:.3f} (n={len(v)}, min={min(v):.3f}, max={max(v):.3f})')
        
        # 输出前5个 bookmaker
        print('\n=== 前5家博彩公司赔率 ===')
        for bm in match['bookmakers'][:5]:
            outcomes = bm['markets'][0]['outcomes']
            odds_str = ', '.join([f"{o['name']}: {o['price']}" for o in outcomes])
            print(f"  {bm['title']}: {odds_str}")
        
        break
