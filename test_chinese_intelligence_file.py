import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.chinese_sports_fetcher import ChineseSportsNewsFetcher

fetcher = ChineseSportsNewsFetcher()
chinese_data = fetcher.fetch_all(keyword='')

with open('chinese_intelligence_output.txt', 'w', encoding='utf-8') as f:
    f.write('=' * 60 + '\n')
    f.write('Chinese Sports News - Intelligence Conversion Test\n')
    f.write('=' * 60 + '\n\n')
    
    # Convert to intelligence
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
    
    f.write(f'Total converted: {len(intelligence_items)} items\n\n')
    
    for i, item in enumerate(intelligence_items, 1):
        f.write(f'{i}. [{item["source_key"]} | {item["category"]}]\n')
        f.write(f'   {item["content"]}\n\n')
    
    f.write('=' * 60 + '\n')

print('Output written to chinese_intelligence_output.txt')
