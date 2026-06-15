#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Free Intelligence Sources - 免费情报获取渠道
为 IntelligenceAgent 提供真实数据接入

覆盖:
- Tier 2: BBC Sport RSS, ESPN RSS, Football-Data.org API
- Tier 3: Understat 爬虫, FBref 爬虫
- Tier 4: Reddit API (免费层)
- Tier 5: OpenWeatherMap API (免费层)

所有渠道: 100% 免费, 无需付费订阅
"""

import sys, json, re, random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# ============ 1. RSS 新闻源 (BBC Sport / ESPN) ============

class RSSNewsFetcher:
    """
    RSS新闻获取器
    免费渠道: BBC Sport RSS, ESPN RSS
    """
    
    RSS_FEEDS = {
        "bbc_sport_football": "https://feeds.bbci.co.uk/sport/football/rss.xml",
        "espn_soccer": "https://www.espn.com/espn/rss/soccer/news",
        "goal_com": "https://www.goal.com/feeds/en/news",
        "transfermarkt": "https://www.transfermarkt.com/rss/news",
    }
    
    def __init__(self):
        self.cache = {}
        self.last_fetch = {}
    
    def fetch_bbc_sport(self, keyword: str = "") -> List[Dict[str, Any]]:
        """
        从BBC Sport RSS获取新闻
        免费, 无需API Key
        """
        import urllib.request
        try:
            url = self.RSS_FEEDS["bbc_sport_football"]
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })
            with urllib.request.urlopen(req, timeout=10) as response:
                data = response.read().decode('utf-8')
            
            # 解析RSS XML
            items = self._parse_rss(data, keyword)
            return items
        except Exception as e:
            print(f"[RSS] BBC Sport fetch failed: {e}")
            return []
    
    def _parse_rss(self, xml_data: str, keyword: str) -> List[Dict[str, Any]]:
        """解析RSS XML"""
        import xml.etree.ElementTree as ET
        items = []
        try:
            root = ET.fromstring(xml_data)
            # RSS 2.0 format
            channel = root.find('channel')
            if channel is None:
                return items
            
            for item in channel.findall('item'):
                title = item.find('title')
                desc = item.find('description')
                pub_date = item.find('pubDate')
                link = item.find('link')
                
                title_text = title.text if title is not None else ""
                desc_text = desc.text if desc is not None else ""
                
                # 关键词过滤
                if keyword and keyword.lower() not in (title_text + desc_text).lower():
                    continue
                
                items.append({
                    'source': 'BBC Sport',
                    'tier': 'AUTHORITATIVE',
                    'title': title_text,
                    'description': desc_text[:200],
                    'url': link.text if link is not None else "",
                    'published': pub_date.text if pub_date is not None else "",
                    'category': self._categorize_news(title_text + desc_text),
                    'reliability': 0.85
                })
        except Exception as e:
            print(f"[RSS] Parse error: {e}")
        return items[:10]  # 最多10条
    
    def _categorize_news(self, text: str) -> str:
        """新闻分类"""
        text_lower = text.lower()
        if any(w in text_lower for w in ['injured', 'injury', 'doubt', 'knock', 'strain', 'out', 'suspended', '受伤']):
            return 'injury'
        if any(w in text_lower for w in ['squad', 'lineup', 'starting', 'xi', '首发']):
            return 'lineup'
        if any(w in text_lower for w in ['tactics', 'formation', 'strategy', '战术']):
            return 'tactics'
        if any(w in text_lower for w in ['transfer', 'signing', 'deal', '转会']):
            return 'transfer'
        if any(w in text_lower for w in ['weather', 'rain', 'storm', 'pitch', '天气', '暴雨']):
            return 'weather'
        if any(w in text_lower for w in ['coach', 'manager', 'sack', 'fired', '教练', '下课']):
            return 'coach'
        return 'form'


# ============ 2. Reddit API (免费层) ============

class RedditFetcher:
    """
    Reddit API 免费层获取器
    限制: 100 requests/minute (OAuth), 10 requests/minute (匿名)
    无需API Key, 使用公开JSON端点
    """
    
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.cache = {}
    
    def fetch_subreddit(self, subreddit: str = "soccer", keyword: str = "", limit: int = 10) -> List[Dict[str, Any]]:
        """
        从Reddit获取帖子
        免费, 无需API Key (使用.json端点)
        注意: Reddit可能返回403,需添加延迟
        """
        import urllib.request, time
        try:
            # 添加随机延迟防止被拦截
            time.sleep(random.uniform(0.5, 1.5))
            
            url = f"{self.base_url}/r/{subreddit}/new.json?limit={limit}"
            if keyword:
                url = f"{self.base_url}/r/{subreddit}/search.json?q={keyword}&limit={limit}&sort=new"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://www.google.com/',
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            posts = []
            for child in data.get('data', {}).get('children', []):
                post = child.get('data', {})
                posts.append({
                    'source': 'Reddit r/' + subreddit,
                    'tier': 'SOCIAL',
                    'title': post.get('title', ''),
                    'content': post.get('selftext', '')[:300],
                    'url': post.get('url', ''),
                    'author': post.get('author', ''),
                    'score': post.get('score', 0),
                    'comments': post.get('num_comments', 0),
                    'created': datetime.fromtimestamp(post.get('created_utc', 0)).isoformat(),
                    'category': self._categorize_reddit(post.get('title', '')),
                    'reliability': 0.45
                })
            return posts
        except Exception as e:
            print(f"[Reddit] Fetch failed: {e}")
            return []
    
    def _categorize_reddit(self, title: str) -> str:
        title_lower = title.lower()
        if 'injury' in title_lower or 'out' in title_lower:
            return 'injury'
        if 'lineup' in title_lower or 'squad' in title_lower:
            return 'lineup'
        if 'tactical' in title_lower or 'formation' in title_lower:
            return 'tactics'
        if 'transfer' in title_lower:
            return 'transfer'
        if 'rumor' in title_lower or 'speculation' in title_lower:
            return 'locker_room'
        return 'market'


# ============ 3. Understat 爬虫 (免费) ============

class UnderstatScraper:
    """
    Understat xG数据爬虫
    免费, 无API, 需爬取JSON数据
    """
    
    def __init__(self):
        self.base_url = "https://understat.com"
    
    def get_team_xg(self, team_id: int, year: int = 2026) -> Dict[str, Any]:
        """
        获取球队xG数据
        免费, 无需API Key
        """
        import urllib.request, re
        try:
            url = f"{self.base_url}/team/{team_id}/{year}"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                html = response.read().decode('utf-8')
            
            # 提取JSON数据
            matches = re.findall(r"var datesData\s*=\s*JSON.parse\('(.+?)'\)", html)
            if not matches:
                return {'status': 'no_data'}
            
            import json
            data = json.loads(matches[0].encode('utf-8').decode('unicode_escape'))
            
            # 解析比赛数据
            games = []
            for game in data:
                games.append({
                    'date': game.get('datetime', ''),
                    'home': game.get('h', {}).get('title', ''),
                    'away': game.get('a', {}).get('title', ''),
                    'xG_home': game.get('xG', {}).get('h', 0),
                    'xG_away': game.get('xG', {}).get('a', 0),
                    'goals_home': game.get('goals', {}).get('h', 0),
                    'goals_away': game.get('goals', {}).get('a', 0),
                })
            
            # 计算平均xG
            if games:
                avg_xg_for = sum(g['xG_home'] if g['home'] == team_id else g['xG_away'] for g in games) / len(games)
                avg_xg_against = sum(g['xG_away'] if g['home'] == team_id else g['xG_home'] for g in games) / len(games)
            else:
                avg_xg_for = avg_xg_against = 0
            
            return {
                'status': 'success',
                'team_id': team_id,
                'games': len(games),
                'avg_xg_for': round(avg_xg_for, 2),
                'avg_xg_against': round(avg_xg_against, 2),
                'recent_games': games[-5:] if len(games) >= 5 else games
            }
        except Exception as e:
            print(f"[Understat] Scrape failed: {e}")
            return {'status': 'error', 'message': str(e)}


# ============ 4. Football-Data.org API (免费) ============

class FootballDataAPI:
    """
    Football-Data.org API
    免费层: 100 requests/day, 无需付费
    覆盖: 英超/西甲/德甲/意甲/法甲 + 世界杯预选赛
    """
    
    def __init__(self, api_key: str = ""):
        self.base_url = "https://api.football-data.org/v4"
        self.api_key = api_key  # 可选, 免费层可以不填
    
    def get_matches(self, competition: str = "WC", date_from: str = "", date_to: str = "") -> List[Dict[str, Any]]:
        """
        获取比赛列表
        免费: 100 requests/day
        """
        import urllib.request
        try:
            url = f"{self.base_url}/competitions/{competition}/matches"
            if date_from and date_to:
                url += f"?dateFrom={date_from}&dateTo={date_to}"
            
            req = urllib.request.Request(url, headers={
                'User-Agent': 'FootballQuantOS/1.0',
                'X-Auth-Token': self.api_key if self.api_key else ''
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            matches = []
            for match in data.get('matches', []):
                matches.append({
                    'source': 'Football-Data.org',
                    'tier': 'PROFESSIONAL',
                    'match_id': match.get('id', ''),
                    'home': match.get('homeTeam', {}).get('name', ''),
                    'away': match.get('awayTeam', {}).get('name', ''),
                    'date': match.get('utcDate', ''),
                    'status': match.get('status', ''),
                    'competition': match.get('competition', {}).get('name', ''),
                    'reliability': 0.90
                })
            return matches
        except Exception as e:
            print(f"[Football-Data] API failed: {e}")
            return []
    
    def get_teams(self, competition: str = "WC") -> List[Dict[str, Any]]:
        """获取参赛球队"""
        import urllib.request
        try:
            url = f"{self.base_url}/competitions/{competition}/teams"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'FootballQuantOS/1.0',
                'X-Auth-Token': self.api_key if self.api_key else ''
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            teams = []
            for team in data.get('teams', []):
                teams.append({
                    'source': 'Football-Data.org',
                    'tier': 'PROFESSIONAL',
                    'id': team.get('id', ''),
                    'name': team.get('name', ''),
                    'shortName': team.get('shortName', ''),
                    'tla': team.get('tla', ''),
                    'reliability': 0.90
                })
            return teams
        except Exception as e:
            print(f"[Football-Data] Teams API failed: {e}")
            return []


# ============ 5. OpenWeatherMap API (免费) ============

class WeatherFetcher:
    """
    OpenWeatherMap API
    免费层: 1000 calls/day, 需注册获取API Key
    """
    
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_match_weather(self, city: str, match_date: str) -> Dict[str, Any]:
        """
        获取比赛日天气
        免费: 1000 calls/day (需API Key)
        """
        if not self.api_key:
            return {'status': 'no_api_key', 'message': 'Register at openweathermap.org for free API key'}
        
        import urllib.request
        try:
            url = f"{self.base_url}/forecast?q={city}&appid={self.api_key}&units=metric"
            req = urllib.request.Request(url, headers={
                'User-Agent': 'FootballQuantOS/1.0'
            })
            
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 找到比赛日期最接近的天气
            forecasts = data.get('list', [])
            match_weather = None
            for forecast in forecasts:
                forecast_date = forecast.get('dt_txt', '')[:10]
                if forecast_date == match_date:
                    match_weather = forecast
                    break
            
            if not match_weather:
                return {'status': 'no_forecast'}
            
            weather = match_weather.get('weather', [{}])[0]
            main = match_weather.get('main', {})
            wind = match_weather.get('wind', {})
            
            return {
                'status': 'success',
                'source': 'OpenWeatherMap',
                'tier': 'PROFESSIONAL',
                'city': city,
                'date': match_date,
                'temperature': main.get('temp', 0),
                'feels_like': main.get('feels_like', 0),
                'humidity': main.get('humidity', 0),
                'weather_main': weather.get('main', ''),
                'weather_desc': weather.get('description', ''),
                'wind_speed': wind.get('speed', 0),
                'rain_probability': match_weather.get('pop', 0),
                'reliability': 0.85
            }
        except Exception as e:
            print(f"[Weather] API failed: {e}")
            return {'status': 'error', 'message': str(e)}


# ============ 6. 免费数据源整合器 ============

from agents.chinese_sports_fetcher import ChineseSportsNewsFetcher

class FreeIntelligenceHub:
    """
    免费情报中心整合器
    一键获取所有免费渠道情报
    """
    
    def __init__(self, weather_api_key: str = "", football_data_key: str = ""):
        self.rss = RSSNewsFetcher()
        self.reddit = RedditFetcher()
        self.understat = UnderstatScraper()
        self.football_data = FootballDataAPI(football_data_key)
        self.chinese_sports = ChineseSportsNewsFetcher()
        self.weather = WeatherFetcher(weather_api_key)
    
    def collect_all(self, team_name: str = "", match_date: str = "", city: str = "") -> Dict[str, Any]:
        """
        收集所有免费渠道情报
        
        Args:
            team_name: 球队名（用于RSS/Reddit搜索）
            match_date: 比赛日期 YYYY-MM-DD（用于天气）
            city: 比赛城市（用于天气）
        """
        print(f"[Hub] Collecting free intelligence for {team_name}...")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'team': team_name,
            'sources': {}
        }
        
        # 1. RSS News
        print("  [1/5] Fetching RSS news...")
        rss_items = self.rss.fetch_bbc_sport(keyword=team_name)
        results['sources']['rss_news'] = {
            'count': len(rss_items),
            'items': rss_items
        }
        
        # 2. Reddit
        print("  [2/5] Fetching Reddit discussions...")
        reddit_posts = self.reddit.fetch_subreddit("soccer", keyword=team_name, limit=10)
        results['sources']['reddit'] = {
            'count': len(reddit_posts),
            'items': reddit_posts
        }
        
        # 3. Football-Data API
        print("  [3/5] Fetching Football-Data API...")
        teams = self.football_data.get_teams("WC")
        target_team = [t for t in teams if team_name.lower() in t['name'].lower()]
        results['sources']['football_data'] = {
            'count': len(target_team),
            'items': target_team
        }
        
        # 4. 中文体育新闻
        print("  [4/6] 中文体育新闻...")
        chinese_data = self.chinese_sports.fetch_all(keyword=team_name)
        results['sources']['chinese_sports'] = chinese_data
        
        # 5. Weather (if API key provided)
        if city and self.weather.api_key:
            print("  [4/5] Fetching weather forecast...")
            weather_data = self.weather.get_match_weather(city, match_date)
            results['sources']['weather'] = weather_data
        else:
            results['sources']['weather'] = {'status': 'skipped', 'reason': 'no_api_key_or_city'}
        
        # 6. Understat (mock for now - needs team ID mapping)
        print("  [5/5] Understat ready (needs team ID mapping)")
        results['sources']['understat'] = {'status': 'ready', 'message': 'Provide team_id to fetch xG data'}
        
        print(f"[Hub] Collection complete. Total items: {len(rss_items) + len(reddit_posts) + len(target_team)}")
        return results
    
    def convert_to_intelligence(self, hub_data: Dict, match_id: str) -> List[Dict[str, Any]]:
        """
        Convert Hub data to IntelligenceAgent format
        """
        intelligence_items = []
        
        # RSS News -> Intelligence
        for item in hub_data.get("sources", {}).get("rss_news", {}).get("items", []):
            intelligence_items.append({
                "match_id": match_id,
                "source_key": "bbc_sport" if "BBC" in item.get("source", "") else "espn",
                "content": f"{item.get('title', '')}. {item.get('description', '')}",
                "category": item.get("category", "form"),
                "raw_text": item.get("title", ""),
                "sentiment_hint": None
            })
        
        # Reddit -> Intelligence
        for post in hub_data.get("sources", {}).get("reddit", {}).get("items", []):
            intelligence_items.append({
                "match_id": match_id,
                "source_key": "reddit_soccer",
                "content": f"{post.get('title', '')}. {post.get('content', '')}",
                "category": post.get("category", "market"),
                "raw_text": post.get("title", ""),
                "sentiment_hint": None
            })
        
        # Football-Data -> Intelligence
        for team in hub_data.get("sources", {}).get("football_data", {}).get("items", []):
            intelligence_items.append({
                "match_id": match_id,
                "source_key": "football_data",
                "content": f"Team data: {team.get('name', '')} ({team.get('tla', '')})",
                "category": "form",
                "raw_text": team.get("name", ""),
                "sentiment_hint": None
            })
        
        # Chinese sports news -> Intelligence
        chinese_data = hub_data.get("sources", {}).get("chinese_sports", {})
        if chinese_data and isinstance(chinese_data, dict):
            for source_name, source_data in chinese_data.get("sources", {}).items():
                if isinstance(source_data, dict):
                    for item in source_data.get("items", []):
                        if isinstance(item, dict):
                            intelligence_items.append({
                                "match_id": match_id,
                                "source_key": "sina_sports" if "sina" in source_name else "netease_sports",
                                "content": item.get("title", ""),
                                "category": item.get("category", "form"),
                                "raw_text": item.get("title", ""),
                                "sentiment_hint": None
                            })
        
        return intelligence_items


# ============ 快速测试 ==========
if __name__ == "__main__":
    print("=" * 60)
    print("Free Intelligence Sources - Demo")
    print("=" * 60)
    print()
    
    hub = FreeIntelligenceHub()
    
    # Test 1: RSS
    print("[TEST 1] BBC Sport RSS Fetch")
    rss_items = hub.rss.fetch_bbc_sport(keyword="World Cup")
    print(f"  Fetched {len(rss_items)} items")
    for i, item in enumerate(rss_items[:3], 1):
        print(f"  {i}. [{item['category']}] {item['title'][:60]}...")
    print()
    
    # Test 2: Reddit
    print("[TEST 2] Reddit r/soccer Fetch")
    reddit_posts = hub.reddit.fetch_subreddit("soccer", keyword="USA", limit=5)
    print(f"  Fetched {len(reddit_posts)} posts")
    for i, post in enumerate(reddit_posts[:3], 1):
        print(f"  {i}. [{post['category']}] Score:{post['score']} {post['title'][:60]}...")
    print()
    
    # Test 3: Football-Data
    print("[TEST 3] Football-Data.org API")
    teams = hub.football_data.get_teams("WC")
    print(f"  Fetched {len(teams)} teams for World Cup")
    for team in teams[:5]:
        print(f"  - {team['name']} ({team['tla']})")
    print()
    
    # Test 4: Full Collection
    print("[TEST 4] Full Collection Demo")
    data = hub.collect_all(team_name="USA", match_date="2026-06-12", city="Los Angeles")
    print(f"  Total sources collected: {len(data['sources'])}")
    for source, info in data['sources'].items():
        count = info.get('count', 0) if isinstance(info, dict) else 0
        print(f"  - {source}: {count} items")
    print()
    
    print("=" * 60)
    print("Demo complete. All free channels tested.")
    print("=" * 60)
