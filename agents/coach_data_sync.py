#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoachDataSync - 教练数据互联网实时抓取模块

数据源优先级：
1. FIFA官方 (权威) - 姓名、国籍、球队
2. Wikipedia (免费API) - 年龄、国籍、履历
3. Transfermarkt (爬虫) - 执教历史、战术偏好
4. FBref (免费API) - 比赛数据、进球统计
5. RSS/新闻源 (实时) - 突发事件、伤病、下课传闻

执行频率：
- 实时 (每15分钟): 新闻/RSS
- 每日: 比赛数据、阵容变化
- 每周: 教练履历、年龄更新
- 大赛前: FIFA官方数据刷新
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Tuple
try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    print("[WARNING] feedparser not installed. RSS features disabled.")
    print("  Install: pip install feedparser")

import re
from dataclasses import dataclass
from enum import Enum

# ============================================================
# 配置
# ============================================================

class DataSource(Enum):
    FIFA = "fifa"              # FIFA官方
    WIKIPEDIA = "wikipedia"    # 维基百科 (免费)
    TRANSFERMARKT = "tm"       # Transfermarkt (爬虫)
    FBREF = "fbref"            # FBref (免费API)
    RSS = "rss"                # 新闻RSS (实时)

# API端点
ENDPOINTS = {
    DataSource.WIKIPEDIA: "https://en.wikipedia.org/api/rest_v1/page/summary/",
    DataSource.FBREF: "https://fbref.com/en/coaches/",
}

# 用户代理 (必须设置，否则会被封)
HEADERS = {
    'User-Agent': 'CoachDataSync/1.0 (Research Purpose)',
    'Accept': 'application/json',
}

# 速率限制 (请求/分钟)
RATE_LIMITS = {
    DataSource.WIKIPEDIA: 100,   # 非常宽松
    DataSource.FBREF: 10,        # 严格限制
    DataSource.TRANSFERMARKT: 5, # 严格限制，需要延迟
    DataSource.RSS: 60,          # 通常宽松
}

# ============================================================
# 数据模型
# ============================================================

@dataclass
class CoachDataSnapshot:
    """教练数据快照"""
    name: str
    nationality: Optional[str] = None
    age: Optional[int] = None
    current_team: Optional[str] = None
    world_cup_experience: int = 0
    euro_experience: int = 0
    total_tournaments: int = 0
    knockout_wins: int = 0
    career_matches: Optional[int] = None
    preferred_formation: Optional[str] = None
    recent_results: List[str] = None
    news_mentions: int = 0
    last_updated: str = ""
    data_sources: List[str] = None

    def __post_init__(self):
        if self.recent_results is None:
            self.recent_results = []
        if self.data_sources is None:
            self.data_sources = []

# ============================================================
# 抓取器实现
# ============================================================

class WikipediaFetcher:
    """
    Wikipedia REST API - 免费，无需API Key
    
    提供数据：
    - 年龄 (birth date)
    - 国籍 (nationality)
    - 简要履历 (description)
    - 图片 (thumbnail)
    
    限制：
    - 100 requests/分钟 (非常宽松)
    - 只返回摘要信息，详细履历需要额外解析
    """
    
    BASE_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"
    
    def __init__(self):
        self.last_request = 0
        self.min_interval = 60 / RATE_LIMITS[DataSource.WIKIPEDIA]
    
    def _rate_limit(self):
        """速率限制"""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
    
    def fetch(self, coach_name: str) -> Optional[Dict]:
        """
        获取教练Wikipedia数据
        
        Args:
            coach_name: 教练英文全名 (e.g., "Lionel Scaloni")
        
        Returns:
            Dict with age, nationality, description, or None if not found
        """
        self._rate_limit()
        
        # 格式化URL (空格替换为下划线)
        url_name = coach_name.replace(' ', '_')
        url = f"{self.BASE_URL}{url_name}"
        
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 404:
                # 尝试变体搜索
                return self._search_variant(coach_name)
            
            response.raise_for_status()
            data = response.json()
            
            # 解析年龄
            age = self._extract_age(data.get('description', ''))
            if not age and 'birth_date' in data.get('content_urls', {}):
                age = self._calculate_age(data['content_urls']['birth_date'])
            
            return {
                'source': 'wikipedia',
                'name': data.get('title', coach_name),
                'description': data.get('description', ''),
                'extract': data.get('extract', ''),
                'age': age,
                'nationality': self._extract_nationality(data.get('extract', '')),
                'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
                'thumbnail': data.get('thumbnail', {}).get('source', ''),
                'timestamp': datetime.now().isoformat(),
            }
            
        except requests.exceptions.RequestException as e:
            print(f"[Wikipedia] Error fetching {coach_name}: {e}")
            return None
    
    def _search_variant(self, coach_name: str) -> Optional[Dict]:
        """尝试搜索变体名称"""
        # 常见变体：名+姓 -> 姓+名，或添加"(footballer)"
        variants = [
            f"{coach_name}_(footballer)",
            f"{coach_name}_(football_manager)",
        ]
        
        for variant in variants:
            self._rate_limit()
            url = f"{self.BASE_URL}{variant.replace(' ', '_')}"
            try:
                response = requests.get(url, headers=HEADERS, timeout=10)
                if response.status_code == 200:
                    return self._parse_response(response.json(), coach_name)
            except Exception:
                continue
        
        return None
    
    def _parse_response(self, data: Dict, original_name: str) -> Dict:
        """解析Wikipedia响应"""
        age = self._extract_age(data.get('description', ''))
        return {
            'source': 'wikipedia',
            'name': data.get('title', original_name),
            'description': data.get('description', ''),
            'extract': data.get('extract', ''),
            'age': age,
            'nationality': self._extract_nationality(data.get('extract', '')),
            'url': data.get('content_urls', {}).get('desktop', {}).get('page', ''),
            'timestamp': datetime.now().isoformat(),
        }
    
    @staticmethod
    def _extract_age(description: str) -> Optional[int]:
        """从描述中提取年龄"""
        # 匹配 "(born 1978)" 或 "age 46"
        patterns = [
            r'\(born\s+(\d{4})\)',
            r'age\s+(\d+)',
            r'aged\s+(\d+)',
        ]
        for pattern in patterns:
            match = re.search(pattern, description, re.IGNORECASE)
            if match:
                if len(match.group(1)) == 4:
                    return datetime.now().year - int(match.group(1))
                return int(match.group(1))
        return None
    
    @staticmethod
    def _extract_nationality(extract: str) -> Optional[str]:
        """从摘要中提取国籍"""
        # 简单匹配："is an Argentine" -> "Argentine"
        match = re.search(r'is an? (\w+) (?:football|coach|manager)', extract, re.IGNORECASE)
        if match:
            return match.group(1)
        return None


class TransfermarktFetcher:
    """
    Transfermarkt 爬虫 - 免费，需处理反爬
    
    提供数据：
    - 完整执教履历
    - 常用阵型
    - 执教球队历史
    - 转会/签约历史
    - 详细统计数据
    
    限制：
    - 5 requests/分钟 (严格)
    - 需要 User-Agent
    - 可能触发Cloudflare验证
    - 页面结构变化需要更新解析器
    """
    
    BASE_URL = "https://www.transfermarkt.com"
    SEARCH_URL = "https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche"
    
    def __init__(self):
        self.last_request = 0
        self.min_interval = 60 / RATE_LIMITS[DataSource.TRANSFERMARKT] + 2  # 额外延迟
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
    
    def _rate_limit(self):
        """严格速率限制"""
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
    
    def search_coach(self, name: str) -> Optional[str]:
        """
        搜索教练ID
        
        Returns:
            教练profile URL path, e.g., "/marcelo-bielsa/profil"
        """
        self._rate_limit()
        
        params = {'query': name, 'where': 'trainer'}
        try:
            response = self.session.get(self.SEARCH_URL, params=params, timeout=15)
            response.raise_for_status()
            
            # 解析搜索结果 (需要BeautifulSoup)
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找到第一个教练结果
            result = soup.find('td', class_='hauptlink')
            if result and result.find('a'):
                link = result.find('a')['href']
                return link
            
            return None
            
        except Exception as e:
            print(f"[Transfermarkt] Search error for {name}: {e}")
            return None
    
    def fetch_profile(self, profile_path: str) -> Optional[Dict]:
        """
        获取教练详细档案
        
        Returns:
            Dict with coaching history, stats, formations
        """
        self._rate_limit()
        
        url = f"{self.BASE_URL}{profile_path}"
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取基本信息
            data = {
                'source': 'transfermarkt',
                'url': url,
                'timestamp': datetime.now().isoformat(),
            }
            
            # 年龄和国籍
            info_table = soup.find('div', class_='info-table')
            if info_table:
                rows = info_table.find_all('div', class_='info-table__content')
                for row in rows:
                    label = row.find('div', class_='info-table__content--regular')
                    value = row.find('div', class_='info-table__content--bold')
                    if label and value:
                        label_text = label.text.strip().lower()
                        if 'age' in label_text:
                            data['age'] = self._extract_number(value.text)
                        elif 'nationality' in label_text:
                            data['nationality'] = value.text.strip()
            
            # 执教历史
            history = self._parse_coaching_history(soup)
            data['coaching_history'] = history
            data['total_teams'] = len(history)
            data['career_matches'] = sum(h.get('matches', 0) for h in history)
            
            # 当前球队
            current_team = soup.find('div', class_='data-header__club')
            if current_team:
                data['current_team'] = current_team.text.strip()
            
            return data
            
        except Exception as e:
            print(f"[Transfermarkt] Profile error: {e}")
            return None
    
    def _parse_coaching_history(self, soup) -> List[Dict]:
        """解析执教历史表格"""
        history = []
        table = soup.find('div', {'id': 'yw1'})
        if table:
            rows = table.find_all('tr', class_=['odd', 'even'])
            for row in rows:
                cols = row.find_all('td')
                if len(cols) >= 5:
                    history.append({
                        'team': cols[2].text.strip() if len(cols) > 2 else '',
                        'period': cols[3].text.strip() if len(cols) > 3 else '',
                        'matches': self._extract_number(cols[4].text) if len(cols) > 4 else 0,
                    })
        return history
    
    @staticmethod
    def _extract_number(text: str) -> int:
        """提取数字"""
        match = re.search(r'(\d+)', text)
        return int(match.group(1)) if match else 0


class FBrefFetcher:
    """
    FBref (Sports Reference) - 免费API，需申请API Key
    
    提供数据：
    - 详细比赛统计
    - 球队/球员数据
    - 历史对阵记录
    - 高级指标 (xG, possession, etc.)
    
    限制：
    - 10 requests/分钟 (严格)
    - 需要注册获取API Key
    - 数据粒度到比赛级别
    
    注册: https://www.sports-reference.com/api/
    """
    
    BASE_URL = "https://api.fbref.com/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.last_request = 0
        self.min_interval = 60 / RATE_LIMITS[DataSource.FBREF]
    
    def _rate_limit(self):
        elapsed = time.time() - self.last_request
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self.last_request = time.time()
    
    def fetch_team_stats(self, team_slug: str, season: int) -> Optional[Dict]:
        """
        获取球队赛季统计
        
        Args:
            team_slug: e.g., "9ca0593f" for Argentina
            season: e.g., 2024
        """
        self._rate_limit()
        
        url = f"{self.BASE_URL}/teams/{team_slug}/stats/{season}"
        headers = HEADERS.copy()
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return {
                'source': 'fbref',
                'data': response.json(),
                'timestamp': datetime.now().isoformat(),
            }
        except Exception as e:
            print(f"[FBref] Error: {e}")
            return None


class RSSNewsFetcher:
    """
    RSS新闻源 - 实时抓取
    
    提供数据：
    - 教练下课传闻
    - 伤病新闻
    - 战术变化
    - 突发事件
    
    优势：
    - 真正的实时数据
    - 反映市场情绪
    - 免费
    
    限制：
    - 需要过滤噪音
    - 可靠性参差不齐
    - 需要NLP处理
    """
    
    # 推荐RSS源
    FEEDS = {
        'espn': 'https://www.espn.com/espn/rss/soccer/news',
        'bbc_sport': 'https://feeds.bbci.co.uk/sport/football/rss.xml',
        'goal': 'https://www.goal.com/en/feeds/news?format=xml',
        'transfermarkt': 'https://www.transfermarkt.com/rss/news',
        'espn_fc': 'https://www.espn.com/soccer/rss',
    }
    
    def __init__(self):
        self.cache = {}
        self.cache_ttl = 900  # 15分钟缓存
    
    def fetch_feed(self, feed_name: str = 'bbc_sport') -> List[Dict]:
        """获取RSS新闻"""
        
        if not FEEDPARSER_AVAILABLE:
            print("[RSS] feedparser not installed. Skipping RSS fetch.")
            return []
        
        # 检查缓存
        if feed_name in self.cache:
            cached = self.cache[feed_name]
            if datetime.now() - cached['time'] < timedelta(seconds=self.cache_ttl):
                return cached['data']
        
        url = self.FEEDS.get(feed_name)
        if not url:
            return []
        
        try:
            feed = feedparser.parse(url)
            articles = []
            
            for entry in feed.entries[:20]:  # 最近20条
                articles.append({
                    'title': entry.get('title', ''),
                    'summary': entry.get('summary', ''),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'source': feed_name,
                })
            
            # 缓存
            self.cache[feed_name] = {
                'data': articles,
                'time': datetime.now(),
            }
            
            return articles
            
        except Exception as e:
            print(f"[RSS] Error fetching {feed_name}: {e}")
            return []
    
    def search_coach_mentions(self, coach_name: str, articles: List[Dict]) -> List[Dict]:
        """
        在新闻中搜索教练提及
        
        Returns:
            相关新闻列表，带相关性评分
        """
        mentions = []
        name_parts = coach_name.lower().split()
        
        for article in articles:
            text = f"{article['title']} {article['summary']}".lower()
            
            # 简单匹配：名字出现
            score = 0
            for part in name_parts:
                if part in text:
                    score += 1
            
            if score > 0:
                # 关键词加权
                keywords = ['sack', 'dismiss', 'appoint', 'hire', 'resign', 'injury', 'tactical', 'formation']
                for kw in keywords:
                    if kw in text:
                        score += 2
                
                article['relevance_score'] = score
                mentions.append(article)
        
        # 按相关性排序
        mentions.sort(key=lambda x: x['relevance_score'], reverse=True)
        return mentions


# ============================================================
# 数据融合器
# ============================================================

class CoachDataFusion:
    """
    多源数据融合
    
    策略：
    1. 客观数据 (年龄、比赛数) -> 取最新来源
    2. 枚举数据 (国籍) -> 取FIFA > Wikipedia > 其他
    3. 计数数据 (大赛经验) -> 取最大值 (可能有遗漏)
    4. 主观数据 -> 保留本地专家评估
    """
    
    SOURCE_PRIORITY = {
        'fifa': 100,
        'transfermarkt': 80,
        'wikipedia': 70,
        'fbref': 60,
        'rss': 10,  # 仅用于事件检测
    }
    
    def __init__(self):
        self.snapshot = CoachDataSnapshot(name="")
    
    def merge(self, sources: List[Dict]) -> CoachDataSnapshot:
        """
        合并多源数据
        
        Args:
            sources: List of data dicts from different fetchers
        """
        # 按来源优先级排序
        sources.sort(key=lambda x: self.SOURCE_PRIORITY.get(x.get('source', ''), 0), reverse=True)
        
        merged = {}
        for source in sources:
            for key, value in source.items():
                if key in ('source', 'timestamp', 'url'):
                    continue
                if value is not None:
                    if key not in merged:
                        merged[key] = value
                    elif key in ('world_cup_experience', 'euro_experience', 'career_matches'):
                        # 计数数据取最大值
                        merged[key] = max(merged[key], value)
        
        return CoachDataSnapshot(
            name=merged.get('name', ''),
            nationality=merged.get('nationality'),
            age=merged.get('age'),
            world_cup_experience=merged.get('world_cup_experience', 0),
            euro_experience=merged.get('euro_experience', 0),
            career_matches=merged.get('career_matches'),
            last_updated=datetime.now().isoformat(),
            data_sources=[s.get('source', 'unknown') for s in sources],
        )


# ============================================================
# 主控器
# ============================================================

class CoachDataSync:
    """
    教练数据同步主控器
    
    使用示例：
        sync = CoachDataSync()
        data = sync.sync_coach("Lionel Scaloni")
        print(data)
    """
    
    def __init__(self, fbref_api_key: Optional[str] = None):
        self.wiki = WikipediaFetcher()
        self.tm = TransfermarktFetcher()
        self.fbref = FBrefFetcher(api_key=fbref_api_key)
        self.rss = RSSNewsFetcher()
        self.fusion = CoachDataFusion()
    
    def sync_coach(self, coach_name: str, team_name: Optional[str] = None) -> CoachDataSnapshot:
        """
        同步单个教练数据
        
        流程：
        1. Wikipedia -> 基础信息 (年龄、国籍)
        2. Transfermarkt -> 详细履历 (执教历史、比赛数)
        3. RSS -> 近期新闻 (突发事件)
        4. 融合 -> 合并所有数据
        """
        sources = []
        
        # 1. Wikipedia (基础信息，快速)
        print(f"[Sync] Fetching Wikipedia for {coach_name}...")
        wiki_data = self.wiki.fetch(coach_name)
        if wiki_data:
            sources.append(wiki_data)
        
        # 2. Transfermarkt (详细履历，较慢)
        print(f"[Sync] Fetching Transfermarkt for {coach_name}...")
        tm_path = self.tm.search_coach(coach_name)
        if tm_path:
            tm_data = self.tm.fetch_profile(tm_path)
            if tm_data:
                sources.append(tm_data)
        
        # 3. RSS (实时新闻)
        print(f"[Sync] Checking RSS news for {coach_name}...")
        articles = self.rss.fetch_feed('bbc_sport')
        mentions = self.rss.search_coach_mentions(coach_name, articles)
        if mentions:
            sources.append({
                'source': 'rss',
                'news_mentions': len(mentions),
                'recent_news': mentions[:3],  # Top 3 relevant
                'timestamp': datetime.now().isoformat(),
            })
        
        # 4. 融合
        print(f"[Sync] Merging {len(sources)} sources...")
        snapshot = self.fusion.merge(sources)
        snapshot.name = coach_name
        if team_name:
            snapshot.current_team = team_name
        
        print(f"[Sync] Complete for {coach_name}")
        return snapshot
    
    def sync_all_coaches(self, coach_list: List[Tuple[str, str]]) -> Dict[str, CoachDataSnapshot]:
        """
        批量同步教练列表
        
        Args:
            coach_list: List of (coach_name, team_name) tuples
        
        Returns:
            Dict of team_name -> CoachDataSnapshot
        """
        results = {}
        
        for coach_name, team_name in coach_list:
            try:
                snapshot = self.sync_coach(coach_name, team_name)
                results[team_name] = snapshot
                
                # 避免速率限制，添加延迟
                time.sleep(3)
                
            except Exception as e:
                print(f"[Sync] Error syncing {coach_name}: {e}")
                continue
        
        return results
    
    def detect_changes(self, old_data: Dict, new_data: Dict) -> List[Dict]:
        """
        检测数据变化
        
        Returns:
            List of change dicts: {field, old_value, new_value, severity}
        """
        changes = []
        
        for team, new_snapshot in new_data.items():
            if team not in old_data:
                changes.append({
                    'team': team,
                    'field': 'new_coach',
                    'old': None,
                    'new': new_snapshot.name,
                    'severity': 'high',
                })
                continue
            
            old_snapshot = old_data[team]
            
            # 检查关键字段变化
            fields_to_check = ['name', 'age', 'current_team', 'world_cup_experience']
            for field in fields_to_check:
                old_val = getattr(old_snapshot, field, None)
                new_val = getattr(new_snapshot, field, None)
                if old_val != new_val and new_val is not None:
                    severity = 'high' if field == 'name' else 'medium'
                    changes.append({
                        'team': team,
                        'field': field,
                        'old': old_val,
                        'new': new_val,
                        'severity': severity,
                    })
        
        return changes


# ============================================================
# 演示
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CoachDataSync v1.0 - Internet Data Fetcher Demo")
    print("=" * 60)
    print()
    
    # 初始化
    sync = CoachDataSync()
    
    # 测试：获取单个教练
    test_coaches = [
        ("Lionel Scaloni", "Argentina"),
        ("Marcelo Bielsa", "Uruguay"),
        ("Graham Arnold", "Iraq"),  # FIFA官方确认
    ]
    
    print("[Demo] Testing 3 coaches...")
    print()
    
    for coach_name, team_name in test_coaches:
        print(f"--- {coach_name} ({team_name}) ---")
        
        try:
            data = sync.sync_coach(coach_name, team_name)
            
            print(f"  Name: {data.name}")
            print(f"  Age: {data.age}")
            print(f"  Nationality: {data.nationality}")
            print(f"  WC Experience: {data.world_cup_experience}")
            print(f"  Euro Experience: {data.euro_experience}")
            print(f"  Career Matches: {data.career_matches}")
            print(f"  News Mentions: {data.news_mentions}")
            print(f"  Sources: {', '.join(data.data_sources)}")
            print(f"  Last Updated: {data.last_updated}")
            print()
            
            # 速率限制
            time.sleep(2)
            
        except Exception as e:
            print(f"  Error: {e}")
            print()
    
    print("=" * 60)
    print("Demo Complete")
    print("=" * 60)
    print()
    print("Usage in production:")
    print("  from coach_data_sync import CoachDataSync")
    print("  sync = CoachDataSync()")
    print("  data = sync.sync_coach('Coach Name', 'Team Name')")
    print("  # Or batch: results = sync.sync_all_coaches(coach_list)")
