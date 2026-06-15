import os, json, urllib.request

api_key = '6613a9a71107eff8d3f7c5585b49a162'
sport = 'soccer_uefa_champs_league'

url = f'https://api.the-odds-api.com/v4/sports/{sport}/odds?apiKey={api_key}&regions=eu&markets=h2h&oddsFormat=decimal&dateFormat=iso'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode())

for match in data:
    home = match['home_team'].lower()
    away = match['away_team'].lower()
    if 'arsenal' in home or 'arsenal' in away or 'psg' in home or 'psg' in away or 'paris' in home or 'paris' in away:
        print('=== MATCH FOUND ===')
        print(f'ID: {match["id"]}')
        print(f'Home: {match["home_team"]}')
        print(f'Away: {match["away_team"]}')
        print(f'Commence: {match["commence_time"]}')
        print(f'Bookmakers: {len(match["bookmakers"])}')
        
        if match['bookmakers']:
            bm = match['bookmakers'][0]
            outcomes = bm['markets'][0]['outcomes']
            odds = {o['name']: o['price'] for o in outcomes}
            print(f'Odds ({bm["title"]}): {json.dumps(odds, ensure_ascii=False)}')
        break
else:
    print('Arsenal vs PSG not found in active fixtures')
    print(f'Total matches fetched: {len(data)}')
    if data:
        print('First match:', data[0]['home_team'], 'vs', data[0]['away_team'])
