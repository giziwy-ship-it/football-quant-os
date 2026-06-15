#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chinese Sports News Fetcher - 中国体育新闻获取器 v2.0
覆盖: 新浪体育 + 网易体育 + 腾讯体育 (网页爬取)
替代失效的RSS源
"""

import urllib.request
import urllib.parse
import re
from datetime import datetime
from typing import Dict, List, Any

class ChineseSportsNewsFetcher:
    """
    中国体育新闻获取器
    使用网页爬取获取新浪体育、网易体育、腾讯体育的新闻
    """
    
    SOURCES = {
        "sina_global": {
            "name": "新浪体育-国际足球",
            "url": "https://sports.sina.com.cn/global/",
            "tier": "AUTHORITATIVE",
            "reliability": 0.80,
            "category": "form",
        },
        "netease_world": {
            "name": "网易体育-世界足球",
            "url": "https://sports.163.com/world/",
            "tier": "AUTHORITATIVE",
            "reliability": 0.80,
            "category": "form",
        },
    }
    
    # 需要过滤掉的非新闻关键词
    SKIP_WORDS = [
        '首页', '导航', '更多', '登录', '注册', '搜索', '返回', '下一页', '上一页',
        '频道', '专题', '广告', '视频', '图集', '评论', '滚动', '热点', '推荐',
        '排行', '排行', '商城', '彩票', '投注', '直播', '积分榜', '赛程', '数据',
        '手机', '客户端', 'APP', '下载', '微博', '微信', '分享', '收藏', '打印',
        '中国', '正文', '标题', '来源', '编辑', '时间', '日期', '相关',
    ]
    
    def __init__(self):
        self.cache = {}
        self.last_fetch = {}
    
    def _fetch_html(self, url: str) -> str:
        """获取网页HTML内容"""
        try:
            req = urllib.request.Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            })
            
            with urllib.request.urlopen(req, timeout=15) as response:
                data = response.read()
            
            # 尝试不同编码
            for enc in ['utf-8', 'gbk', 'gb2312']:
                try:
                    return data.decode(enc, errors='strict')
                except UnicodeDecodeError:
                    continue
            return data.decode('utf-8', errors='replace')
        except Exception as e:
            print(f"[Fetch] Failed: {url} -> {e}")
            return ""
    
    def _extract_news(self, html: str, source_name: str, base_url: str) -> List[Dict[str, Any]]:
        """从HTML中提取新闻标题和链接"""
        items = []
        seen = set()
        
        # 通用模式：提取链接和标题
        patterns = [
            # 模式1: <a href="...">标题</a>
            r'<a[^>]*href=["\']([^"\']+)["\'][^>]*>([^<]{15,80})</a>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for link, title in matches:
                title = title.strip()
                
                # 过滤条件
                if len(title) < 15 or len(title) > 80:
                    continue
                
                # 跳过模板数据（JavaScript模板）
                if '{{' in title or '}}' in title or 'value.' in title or 'comment_' in title:
                    continue
                
                # 跳过非新闻
                if any(w in title for w in self.SKIP_WORDS):
                    continue
                    continue
                
                # 跳过重复
                if title in seen:
                    continue
                seen.add(title)
                
                # 修复链接
                if link.startswith('//'):
                    link = 'https:' + link
                elif link.startswith('/'):
                    link = base_url.rstrip('/') + link
                elif not link.startswith('http'):
                    link = base_url + link
                
                # 分类
                category = self._categorize_chinese_news(title)
                
                items.append({
                    'source': source_name,
                    'tier': 'AUTHORITATIVE',
                    'title': title,
                    'description': '',
                    'url': link,
                    'published': '',
                    'category': category,
                    'reliability': 0.80,
                    'language': 'zh',
                })
        
        return items
    
    def _categorize_chinese_news(self, text: str) -> str:
        """中文新闻分类"""
        text_lower = text.lower()
        
        if any(w in text_lower for w in ['伤病', '受伤', '停赛', '缺阵', '复出', '伤愈', '缺席']):
            return 'injury'
        if any(w in text_lower for w in ['首发', '阵容', '大名单', '名单', ' lineup']):
            return 'lineup'
        if any(w in text_lower for w in ['战术', '阵型', '打法', '策略']):
            return 'tactics'
        if any(w in text_lower for w in ['转会', '签约', '加盟', '离队']):
            return 'transfer'
        if any(w in text_lower for w in ['天气', '暴雨', '大雪', '场地']):
            return 'weather'
        if any(w in text_lower for w in ['教练', '下课', '主帅', '解雇', '任命']):
            return 'coach'
        if any(w in text_lower for w in ['更衣室', '矛盾', '冲突', '内讧', '不和']):
            return 'locker_room'
        if any(w in text_lower for w in ['赔率', '盘口', '投注', '市场', '赢指']):
            return 'market'
        if any(w in text_lower for w in ['出线', '生死战', '晋级', '淘汰', '荣誉']):
            return 'motivation'
        return 'form'
    
    def fetch_sina_global(self, keyword: str = "") -> List[Dict[str, Any]]:
        """新浪体育国际足球"""
        html = self._fetch_html(self.SOURCES["sina_global"]["url"])
        if not html:
            return []
        
        items = self._extract_news(html, "新浪体育", "https://sports.sina.com.cn")
        
        # 关键词过滤
        if keyword:
            items = [i for i in items if keyword.lower() in i['title'].lower()]
        
        return items[:15]
    
    def fetch_netease_world(self, keyword: str = "") -> List[Dict[str, Any]]:
        """网易体育世界足球"""
        html = self._fetch_html(self.SOURCES["netease_world"]["url"])
        if not html:
            return []
        
        items = self._extract_news(html, "网易体育", "https://sports.163.com")
        
        # 关键词过滤
        if keyword:
            items = [i for i in items if keyword.lower() in i['title'].lower()]
        
        return items[:15]
    
    def fetch_all(self, keyword: str = "") -> Dict[str, Any]:
        """获取所有中文体育新闻"""
        print(f"[Chinese Sports] Fetching sources for keyword: {keyword}")
        
        results = {
            'timestamp': datetime.now().isoformat(),
            'keyword': keyword,
            'sources': {}
        }
        
        # 1. 新浪体育
        print("  [1/2] 新浪体育国际足球...")
        sina_items = self.fetch_sina_global(keyword)
        results['sources']['sina_global'] = {
            'count': len(sina_items),
            'items': sina_items
        }
        
        # 2. 网易体育
        print("  [2/2] 网易体育世界足球...")
        netease_items = self.fetch_netease_world(keyword)
        results['sources']['netease_world'] = {
            'count': len(netease_items),
            'items': netease_items
        }
        
        total = len(sina_items) + len(netease_items)
        print(f"[Chinese Sports] Total fetched: {total} items")
        return results
    
    def convert_to_intelligence(self, fetcher_data: Dict, match_id: str) -> List[Dict[str, Any]]:
        """转换为 IntelligenceAgent 格式"""
        intelligence_items = []
        
        for source_name, source_data in fetcher_data.get('sources', {}).items():
            for item in source_data.get('items', []):
                intelligence_items.append({
                    'match_id': match_id,
                    'source_key': 'sina_sports' if '新浪' in item['source'] else 'netease_sports',
                    'content': item['title'],
                    'category': item['category'],
                    'raw_text': item['title'],
                    'sentiment_hint': None,
                })
        
        return intelligence_items


# ========== 快速测试 ==========
if __name__ == "__main__":
    print("=" * 60)
    print("Chinese Sports News Fetcher v2.0 - Test")
    print("=" * 60)
    print()
    
    fetcher = ChineseSportsNewsFetcher()
    
    # Test 1: 新浪体育
    print("[TEST 1] 新浪体育国际足球")
    items = fetcher.fetch_sina_global(keyword="")
    print(f"  Fetched {len(items)} items")
    for i, item in enumerate(items[:5], 1):
        print(f"  {i}. [{item['category']}] {item['title'][:50]}")
    print()
    
    # Test 2: 关键词过滤
    print("[TEST 2] 关键词过滤: 美国")
    items = fetcher.fetch_sina_global(keyword="美国")
    print(f"  Fetched {len(items)} items with keyword")
    for i, item in enumerate(items[:5], 1):
        print(f"  {i}. [{item['category']}] {item['title']}")
    print()
    
    # Test 3: 全部获取
    print("[TEST 3] 全部中文体育新闻")
    data = fetcher.fetch_all(keyword="")
    for source, info in data['sources'].items():
        print(f"  {source}: {info['count']} items")
    print()
    
    print("=" * 60)
    print("Test complete.")
    print("=" * 60)
