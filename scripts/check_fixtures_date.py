import json, urllib.request

# 检查5月31日的赛程
url = 'http://localhost:8000/api/v1/fixtures/date/2026-05-31'
req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode())

print(f"Total: {data['total']}")
for f in data['fixtures']:
    if any(team in f['home_team_en'].lower() or team in f['away_team_en'].lower() 
           for team in ['inter', 'barcelona', 'fiorentina', 'betis', 'milan', 'marseille']):
        print(f"[{f['match_time']}] {f['home_team_en']} vs {f['away_team_en']} ({f['league']})")

# 也检查5月28日
print("\n--- 2026-05-28 ---")
url = 'http://localhost:8000/api/v1/fixtures/date/2026-05-28'
req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode())
print(f"Total: {data['total']}")
for f in data['fixtures']:
    if any(team in f['home_team_en'].lower() or team in f['away_team_en'].lower() 
           for team in ['inter', 'barcelona', 'fiorentina', 'betis', 'milan', 'marseille']):
        print(f"[{f['match_time']}] {f['home_team_en']} vs {f['away_team_en']} ({f['league']})")
