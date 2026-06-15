import urllib.request, re

url = 'https://sports.sina.com.cn/global/'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req, timeout=10) as r:
    data = r.read()

# Try different encodings
for enc in ['gbk', 'gb2312', 'utf-8']:
    try:
        html = data.decode(enc, errors='strict')
        print(f'Encoding: {enc}')
        # Find news titles (common patterns in Chinese sports sites)
        # Pattern 1: <a href="...">title</a> where title is 10-80 chars
        pattern1 = r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]{10,80})</a>'
        titles1 = re.findall(pattern1, html)
        print(f'Pattern 1: {len(titles1)} matches')
        
        # Pattern 2: <h2><a href="...">title</a></h2>
        pattern2 = r'<h[1-6][^>]*>\s*<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]{10,80})</a>\s*</h[1-6]>'
        titles2 = re.findall(pattern2, html, re.IGNORECASE)
        print(f'Pattern 2: {len(titles2)} matches')
        
        # Pattern 3: specific classes (try common ones)
        # Look for <a> with specific text patterns
        all_titles = titles1 + titles2
        
        # Filter out non-news (nav links, ads, etc.)
        filtered = []
        for link, title in all_titles:
            title = title.strip()
            # Skip navigation, ads, short titles
            if len(title) < 10 or len(title) > 80:
                continue
            # Skip common non-news patterns
            skip_words = ['首页', '导航', '更多', '登录', '注册', '搜索', '返回', '下一页', '上一页', '频道', '专题', '广告', '视频', '图集', '评论']
            if any(w in title for w in skip_words):
                continue
            # Skip if URL is not a news article (too short, not .shtml or .html)
            if not any(ext in link.lower() for ext in ['.shtml', '.html', '.htm', '/doc/']):
                continue
            filtered.append((link, title))
        
        # Remove duplicates
        seen = set()
        unique = []
        for link, title in filtered:
            if title not in seen:
                seen.add(title)
                unique.append((link, title))
        
        print(f'Filtered unique news: {len(unique)}')
        for i, (link, title) in enumerate(unique[:10]):
            print(f'  {i+1}. {title}')
            print(f'     {link}')
        
        break
    except Exception as e:
        print(f'Encoding {enc} failed: {e}')
        continue
