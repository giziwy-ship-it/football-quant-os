import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.chinese_sports_fetcher import ChineseSportsNewsFetcher

fetcher = ChineseSportsNewsFetcher()
chinese_data = fetcher.fetch_all(keyword='')

# Convert to intelligence manually
intelligence_items = []
for source_name, source_data in chinese_data.get('sources', {}).items():
    for item in source_data.get('items', []):
        intelligence_items.append({
            'match_id': 'USA_PAR',
            'source_key': 'sina_sports' if '新浪' in item.get('source', '') else 'netease_sports',
            'content': item.get('title', ''),
            'category': item.get('category', 'form'),
            'raw_text': item.get('title', ''),
            'sentiment_hint': None
        })

print(f'Converted {len(intelligence_items)} items from Chinese sources')
for i, item in enumerate(intelligence_items[:5]):
    print(f'  {i+1}. [{item["category"]}] {item["content"][:50]}')
