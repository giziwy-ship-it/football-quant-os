import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

# Read the file
with open('agents/free_intelligence_sources.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Lines 483-523 are the convert_to_intelligence method (0-indexed: 482-522)
start_line = 483  # 0-indexed
end_line = 523    # 0-indexed (exclusive)

new_method_lines = [
    '    def convert_to_intelligence(self, hub_data: Dict, match_id: str) -> List[Dict[str, Any]]:\n',
    '        """\n',
    '        Convert Hub data to IntelligenceAgent format\n',
    '        """\n',
    '        intelligence_items = []\n',
    '        \n',
    '        # RSS News -> Intelligence\n',
    '        for item in hub_data.get("sources", {}).get("rss_news", {}).get("items", []):\n',
    '            intelligence_items.append({\n',
    '                "match_id": match_id,\n',
    '                "source_key": "bbc_sport" if "BBC" in item.get("source", "") else "espn",\n',
    '                "content": f"{item.get(\'title\', \'\')}. {item.get(\'description\', \'\')}",\n',
    '                "category": item.get("category", "form"),\n',
    '                "raw_text": item.get("title", ""),\n',
    '                "sentiment_hint": None\n',
    '            })\n',
    '        \n',
    '        # Reddit -> Intelligence\n',
    '        for post in hub_data.get("sources", {}).get("reddit", {}).get("items", []):\n',
    '            intelligence_items.append({\n',
    '                "match_id": match_id,\n',
    '                "source_key": "reddit_soccer",\n',
    '                "content": f"{post.get(\'title\', \'\')}. {post.get(\'content\', \'\')}",\n',
    '                "category": post.get("category", "market"),\n',
    '                "raw_text": post.get("title", ""),\n',
    '                "sentiment_hint": None\n',
    '            })\n',
    '        \n',
    '        # Football-Data -> Intelligence\n',
    '        for team in hub_data.get("sources", {}).get("football_data", {}).get("items", []):\n',
    '            intelligence_items.append({\n',
    '                "match_id": match_id,\n',
    '                "source_key": "football_data",\n',
    '                "content": f"Team data: {team.get(\'name\', \'\')} ({team.get(\'tla\', \'\')})",\n',
    '                "category": "form",\n',
    '                "raw_text": team.get("name", ""),\n',
    '                "sentiment_hint": None\n',
    '            })\n',
    '        \n',
    '        # Chinese sports news -> Intelligence\n',
    '        chinese_data = hub_data.get("sources", {}).get("chinese_sports", {})\n',
    '        if chinese_data and isinstance(chinese_data, dict):\n',
    '            for source_name, source_data in chinese_data.get("sources", {}).items():\n',
    '                if isinstance(source_data, dict):\n',
    '                    for item in source_data.get("items", []):\n',
    '                        if isinstance(item, dict):\n',
    '                            intelligence_items.append({\n',
    '                                "match_id": match_id,\n',
    '                                "source_key": "sina_sports" if "sina" in source_name else "netease_sports",\n',
    '                                "content": item.get("title", ""),\n',
    '                                "category": item.get("category", "form"),\n',
    '                                "raw_text": item.get("title", ""),\n',
    '                                "sentiment_hint": None\n',
    '                            })\n',
    '        \n',
    '        return intelligence_items\n',
    '\n',
]

# Replace lines
new_lines = lines[:start_line] + new_method_lines + lines[end_line:]

with open('agents/free_intelligence_sources.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'Replaced lines {start_line} to {end_line}')
print('Done!')
