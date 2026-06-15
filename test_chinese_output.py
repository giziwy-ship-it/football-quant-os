import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.chinese_sports_fetcher import ChineseSportsNewsFetcher

fetcher = ChineseSportsNewsFetcher()

with open('chinese_sports_output.txt', 'w', encoding='utf-8') as f:
    f.write('=' * 60 + '\n')
    f.write('Chinese Sports News Fetcher v2.0 - Test Output\n')
    f.write('=' * 60 + '\n\n')
    
    # Test 1: 新浪体育
    f.write('[TEST 1] 新浪体育国际足球\n')
    items = fetcher.fetch_sina_global(keyword="")
    f.write(f'Fetched {len(items)} items\n\n')
    for i, item in enumerate(items, 1):
        f.write(f'{i}. [{item["category"]}] {item["title"]}\n')
        f.write(f'   URL: {item["url"]}\n\n')
    
    # Test 2: 关键词过滤
    f.write('\n[TEST 2] 关键词过滤: 美国\n')
    items = fetcher.fetch_sina_global(keyword="美国")
    f.write(f'Fetched {len(items)} items with keyword\n\n')
    for i, item in enumerate(items, 1):
        f.write(f'{i}. [{item["category"]}] {item["title"]}\n')
        f.write(f'   URL: {item["url"]}\n\n')
    
    f.write('=' * 60 + '\n')
    f.write('Test complete.\n')
    f.write('=' * 60 + '\n')

print('Output written to chinese_sports_output.txt')
