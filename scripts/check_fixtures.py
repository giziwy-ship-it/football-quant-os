import json, urllib.request

# 检查今天的赛程
url = 'http://localhost:8000/api/v1/fixtures/today'
req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
resp = urllib.request.urlopen(req, timeout=30)
data = json.loads(resp.read().decode())
print(json.dumps(data, ensure_ascii=False, indent=2)[:3000])  # 限制输出
