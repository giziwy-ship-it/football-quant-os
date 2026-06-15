import re

with open('agents/free_intelligence_sources.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the method boundaries
lines = content.split('\n')
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if 'def convert_to_intelligence(self, hub_data' in line:
        start_idx = i
    if start_idx is not None and 'return intelligence_items' in line:
        end_idx = i
        break

if start_idx and end_idx:
    new_method = '''    def convert_to_intelligence(self, hub_data: Dict, match_id: str) -> List[Dict[str, Any]]:
        """
        将Hub数据转换为 IntelligenceAgent 格式
        """
        intelligence_items = []
        
        # RSS News -> Intelligence
        for item in hub_data.get('sources', {}).get('rss_news', {}).get('items', []):
            intelligence_items.append({
                'match_id': match_id,
                'source_key': 'bbc_sport' if 'BBC' in item.get('source', '') else 'espn',
                'content': f"{item.get('title', '')}. {item.get('description', '')}",
                'category': item.get('category', 'form'),
                'raw_text': item.get('title', ''),
                'sentiment_hint': None
            })
        
        # Reddit -> Intelligence
        for post in hub_data.get('sources', {}).get('reddit', {}).get('items', []):
            intelligence_items.append({
                'match_id': match_id,
                'source_key': 'reddit_soccer',
                'content': f"{post.get('title', '')}. {post.get('content', '')}",
                'category': post.get('category', 'market'),
                'raw_text': post.get('title', ''),
                'sentiment_hint': None
            })
        
        # Football-Data -> Intelligence
        for team in hub_data.get('sources', {}).get('football_data', {}).get('items', []):
            intelligence_items.append({
                'match_id': match_id,
                'source_key': 'football_data',
                'content': f"Team data: {team.get('name', '')} ({team.get('tla', '')})",
                'category': 'form',
                'raw_text': team.get('name', ''),
                'sentiment_hint': None
            })
        
        # Chinese sports news -> Intelligence
        chinese_data = hub_data.get('sources', {}).get('chinese_sports', {})
        if chinese_data and isinstance(chinese_data, dict):
            for source_name, source_data in chinese_data.get('sources', {}).items():
                if isinstance(source_data, dict):
                    for item in source_data.get('items', []):
                        if isinstance(item, dict):
                            intelligence_items.append({
                                'match_id': match_id,
                                'source_key': 'sina_sports' if '新浪' in item.get('source', '') else 'netease_sports',
                                'content': item.get('title', ''),
                                'category': item.get('category', 'form'),
                                'raw_text': item.get('title', ''),
                                'sentiment_hint': None
                            })
        
        return intelligence_items'''
    
    new_lines = lines[:start_idx] + new_method.split('\n') + lines[end_idx+1:]
    new_content = '\n'.join(new_lines)
    
    with open('agents/free_intelligence_sources.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f'Replaced lines {start_idx} to {end_idx}')
    print('Done')
else:
    print('Could not find method boundaries')
