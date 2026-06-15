import urllib.request, re

url = 'https://sports.sina.com.cn/global/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as r:
    data = r.read()

html = data.decode('utf-8', errors='replace')

# Find news titles -新浪体育新闻标题通常在特定结构中
# Look for news links with Chinese titles
pattern = r'<a[^\u003e]*href=["\']([^"\']+)["\'][^\u003e]*\u003e([^\u003c]{15,80})\u003c/a\u003e'
matches = re.findall(pattern, html)

# Filter news items
filtered = []
seen = set()
for link, title in matches:
    title = title.strip()
    if len(title) < 15 or len(title) > 80:
        continue
    skip_words = ['首页', '导航', '更多', '登录', '注册', '搜索', '返回', '下一页', '上一页', '频道', '专题', '广告', '视频', '图集', '评论', '滚动', '热点', '推荐']
    if any(w in title for w in skip_words):
        continue
    if title in seen:
        continue
    seen.add(title)
    filtered.append((link, title))

# Write to file to avoid encoding issues
with open('sina_news_output.txt', 'w', encoding='utf-8') as f:
    f.write(f'Found {len(filtered)} unique news items\n\n')
    for i, (link, title) in enumerate(filtered[:20]):
        f.write(f'{i+1}. {title}\n')
        f.write(f'   Link: {link}\n\n')

print(f'Written {min(len(filtered), 20)} items to sina_news_output.txt')
