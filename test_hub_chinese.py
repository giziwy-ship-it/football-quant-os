import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.free_intelligence_sources import FreeIntelligenceHub

hub = FreeIntelligenceHub()

print('Testing FreeIntelligenceHub with Chinese keyword...')
data = hub.collect_all(team_name='美国')

print()
print('Source counts:')
for source, info in data['sources'].items():
    if isinstance(info, dict) and 'count' in info:
        print(f'  {source}: {info["count"]} items')
    elif isinstance(info, dict) and 'sources' in info:
        total = sum(s['count'] for s in info['sources'].values())
        print(f'  {source}: {total} items')
    else:
        print(f'  {source}: available')

print()
print('Chinese sports news sample:')
chinese = data['sources'].get('chinese_sports', {})
for src_name, src_data in chinese.get('sources', {}).items():
    for item in src_data.get('items', [])[:3]:
        print(f'  [{item["category"]}] {item["title"][:50]}')

print()
print('Converting to IntelligenceAgent format...')
items = hub.convert_to_intelligence(data, match_id='USA_PAR')
print(f'Converted {len(items)} intelligence items')
for i, item in enumerate(items[:5]):
    print(f'  {i+1}. [{item["source_key"]}] {item["content"][:50]}')
