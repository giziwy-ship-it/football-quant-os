import json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8')

# 获取今天所有比赛，列出前30场
url = 'http://localhost:8000/api/v1/fixtures/today'
req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode())

print(f"Total: {data['total']} matches")
print("\n=== All matches (first 30) ===")
for i, f in enumerate(data['fixtures'][:30]):
    print(f"{i+1}. [{f['match_time']}] {f['home_team_en']} vs {f['away_team_en']} ({f['league']})")
