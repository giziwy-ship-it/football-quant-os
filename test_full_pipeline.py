import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.free_intelligence_sources import FreeIntelligenceHub
from agents.intelligence import IntelligenceAgent, IntelCategory

hub = FreeIntelligenceHub()

print('Collecting intelligence for USA vs Paraguay...')
data = hub.collect_all(team_name='USA')

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
print('Converting to IntelligenceAgent format...')
items = hub.convert_to_intelligence(data, match_id='USA_PAR')
print(f'Converted {len(items)} intelligence items')

print()
print('Top 5 intelligence items:')
for i, item in enumerate(items[:5]):
    print(f'  {i+1}. [{item["source_key"]} | {item["category"]}]')
    print(f'     {item["content"][:80]}')

print()
print('Creating IntelligenceAgent and adding items...')
agent = IntelligenceAgent()
for item in items:
    try:
        agent.add_intelligence(**item)
    except Exception as e:
        print(f'  Error adding item: {e}')

print()
print('Generating pre-match briefing...')
briefing = agent.generate_pre_match_briefing('USA_PAR')
print(briefing[:1000])
print('...')
