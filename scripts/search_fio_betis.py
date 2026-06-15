import json, urllib.request

api_key = '6613a9a71107eff8d3f7c5585b49a162'

# Try multiple sport keys to find Fiorentina vs Betis
sport_keys = [
    'soccer_uefa_europa_conference_league',
    'soccer_uefa_europa_league',
    'soccer_uefa_champs_league',
    'soccer_uefa_euro_qualification',
    'soccer_efl_championship',
    'soccer_bundesliga',
    'soccer_serie_a',
    'soccer_laliga',
    'soccer_epl',
    'soccer_ligue_one',
    'soccer_primeira_liga',
    'soccer_uefa_nations_league',
    'soccer_uefa_champs_league_qualification',
    'soccer_uefa_europa_conference_league_qualification',
    'soccer_uefa_europa_league_qualification'
]

for sport in sport_keys:
    try:
        url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds?apiKey={api_key}&regions=eu&markets=h2h&oddsFormat=decimal&dateFormat=iso'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=10)
        data = json.loads(resp.read().decode())
        
        for match in data:
            home = match['home_team'].lower()
            away = match['away_team'].lower()
            if 'fiorentina' in home or 'fiorentina' in away or 'betis' in home or 'betis' in away:
                print(f'=== FOUND: {match["home_team"]} vs {match["away_team"]} ===')
                print(f'Sport: {sport}')
                print(f'ID: {match["id"]}')
                print(f'Kickoff: {match["commence_time"]}')
                print(f'Total bookmakers: {len(match["bookmakers"])}')
                
                # Collect all bookmaker odds
                all_odds = {'1': [], 'X': [], '2': []}
                for bm in match['bookmakers']:
                    try:
                        outcomes = bm['markets'][0]['outcomes']
                        odds_map = {o['name'].lower(): o['price'] for o in outcomes}
                        
                        home_odds = odds_map.get(match['home_team'].lower()) or odds_map.get(match['home_team'].lower().replace(' ', ''))
                        away_odds = odds_map.get(match['away_team'].lower()) or odds_map.get(match['away_team'].lower().replace(' ', ''))
                        draw_odds = odds_map.get('draw')
                        
                        # Also try partial matches
                        if not home_odds:
                            for k in odds_map:
                                if 'fiorentina' in k or 'betis' in k:
                                    if 'fiorentina' in match['home_team'].lower() and 'fiorentina' in k:
                                        home_odds = odds_map[k]
                                    if 'betis' in match['home_team'].lower() and 'betis' in k:
                                        home_odds = odds_map[k]
                                    if 'fiorentina' in match['away_team'].lower() and 'fiorentina' in k:
                                        away_odds = odds_map[k]
                                    if 'betis' in match['away_team'].lower() and 'betis' in k:
                                        away_odds = odds_map[k]
                        
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
                
                print('\n=== Top 5 Bookmakers ===')
                for bm in match['bookmakers'][:5]:
                    outcomes = bm['markets'][0]['outcomes']
                    odds_str = ', '.join([f"{o['name']}: {o['price']}" for o in outcomes])
                    print(f"  {bm['title']}: {odds_str}")
                
                print('\n' + '='*50)
                break
        else:
            continue
        break
    except Exception as e:
        print(f'{sport}: {e}')
        continue

print('Done searching.')
