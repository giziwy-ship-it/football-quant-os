#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一赔率数据客户端 - Football Quant OS (P1 修复)
整合多个数据源：The Odds API + ESPN + 网页抓取
"""

import sys
import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
import httpx
from core.config import config


@dataclass
class OddsData:
    """统一赔率数据结构"""
    source: str
    match_id: str
    home_team: str
    away_team: str
    match_time: str
    home_odds: float
    draw_odds: float
    away_odds: float
    home_prob: float
    draw_prob: float
    away_prob: float
    league: str
    bookmaker: str
    last_update: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "match_id": self.match_id,
            "home_team": self.home_team,
            "away_team": self.away_team,
            "match_time": self.match_time,
            "odds": {"home": self.home_odds, "draw": self.draw_odds, "away": self.away_odds},
            "probabilities": {"home": self.home_prob, "draw": self.draw_prob, "away": self.away_prob},
            "league": self.league,
            "bookmaker": self.bookmaker,
            "last_update": self.last_update,
        }


class TheOddsAPIClient:
    """The Odds API 官方客户端 (https://the-odds-api.com/)"""
    
    BASE_URL = "https://api.the-odds-api.com/v4"
    
    # 运动代码映射
    SPORTS = {
        "epl": "soccer_epl",
        "la_liga": "soccer_spain_la_liga",
        "bundesliga": "soccer_germany_bundesliga",
        "serie_a": "soccer_italy_serie_a",
        "ligue_1": "soccer_france_ligue_one",
        "champions_league": "soccer_uefa_champs_league",
        "world_cup": "soccer_fifa_world_cup",
        "europa_league": "soccer_uefa_europa_league",
    }
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or config.THE_ODDS_API_KEY
        self.client = httpx.AsyncClient(timeout=30.0)
        self._last_request_time = None
        self._min_interval = 0.5  # 最小请求间隔（秒）
    
    async def _rate_limit(self):
        """速率限制"""
        if self._last_request_time:
            elapsed = (datetime.now() - self._last_request_time).total_seconds()
            if elapsed < self._min_interval:
                await asyncio.sleep(self._min_interval - elapsed)
        self._last_request_time = datetime.now()
    
    async def get_sports(self) -> List[Dict[str, str]]:
        """获取支持的运动列表"""
        await self._rate_limit()
        url = f"{self.BASE_URL}/sports"
        params = {"apiKey": self.api_key}
        
        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPError as e:
            print(f"[TheOddsAPI] 获取运动列表失败: {e}")
            return []
    
    async def get_odds(
        self,
        sport: str = "soccer_epl",
        regions: str = "eu",  # eu, uk, us, au
        markets: str = "h2h",  # h2h, spreads, totals
        odds_format: str = "decimal",
        date_format: str = "iso",
    ) -> List[Dict[str, Any]]:
        """
        获取赔率数据
        
        Args:
            sport: 运动代码 (e.g. soccer_epl)
            regions: 地区代码
            markets: 市场类型 h2h=胜负平
            odds_format: 赔率格式 decimal=欧洲盘
        """
        await self._rate_limit()
        url = f"{self.BASE_URL}/sports/{sport}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": odds_format,
            "dateFormat": date_format,
        }
        
        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
            
            # 解析为标准格式
            results = []
            for match in data:
                parsed = self._parse_match(match, sport)
                if parsed:
                    results.append(parsed)
            
            return results
        except httpx.HTTPError as e:
            print(f"[TheOddsAPI] 获取赔率失败 [{sport}]: {e}")
            return []
    
    def _parse_match(self, match: Dict, sport: str) -> Optional[OddsData]:
        """解析单场比赛数据"""
        try:
            home = match.get("home_team", "")
            away = match.get("away_team", "")
            match_id = match.get("id", "")
            match_time = match.get("commence_time", "")
            
            # 获取第一个 bookmaker 的赔率
            bookmakers = match.get("bookmakers", [])
            if not bookmakers:
                return None
            
            # 优先选择 Pinnacle (最 sharp)
            preferred = None
            for bm in bookmakers:
                if bm.get("key") in ["pinnacle", "betfair_ex", "bet365"]:
                    preferred = bm
                    break
            
            if not preferred:
                preferred = bookmakers[0]
            
            # 提取 h2h 赔率
            h2h = None
            for market in preferred.get("markets", []):
                if market.get("key") == "h2h":
                    h2h = market
                    break
            
            if not h2h:
                return None
            
            outcomes = {o["name"]: o["price"] for o in h2h.get("outcomes", [])}
            
            # 足球通常是 Home/Draw/Away
            home_odds = outcomes.get(home, 0)
            away_odds = outcomes.get(away, 0)
            draw_odds = outcomes.get("Draw", 0)
            
            if not all([home_odds, draw_odds, away_odds]):
                return None
            
            # 计算概率（去水）
            total = 1/home_odds + 1/draw_odds + 1/away_odds
            home_prob = (1/home_odds) / total
            draw_prob = (1/draw_odds) / total
            away_prob = (1/away_odds) / total
            
            return OddsData(
                source="the_odds_api",
                match_id=match_id,
                home_team=home,
                away_team=away,
                match_time=match_time,
                home_odds=home_odds,
                draw_odds=draw_odds,
                away_odds=away_odds,
                home_prob=round(home_prob, 4),
                draw_prob=round(draw_prob, 4),
                away_prob=round(away_prob, 4),
                league=sport,
                bookmaker=preferred.get("title", "unknown"),
                last_update=datetime.now().isoformat(),
            )
        except Exception as e:
            print(f"[TheOddsAPI] 解析比赛失败: {e}")
            return None
    
    async def get_usage(self) -> Dict[str, Any]:
        """获取 API 使用情况（检查剩余请求次数）"""
        await self._rate_limit()
        url = f"{self.BASE_URL}/sports"
        params = {"apiKey": self.api_key}
        
        try:
            resp = await self.client.get(url, params=params)
            # 从响应头中提取使用信息
            headers = dict(resp.headers)
            return {
                "remaining_requests": headers.get("x-requests-remaining", "unknown"),
                "used_requests": headers.get("x-requests-used", "unknown"),
            }
        except Exception as e:
            print(f"[TheOddsAPI] 获取使用量失败: {e}")
            return {"error": str(e)}
    
    async def close(self):
        await self.client.aclose()


class ESPNClient:
    """ESPN 免费 API 客户端（无密钥）"""
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"
    
    async def get_fixtures(self, date: str = None) -> List[Dict[str, Any]]:
        """获取赛程"""
        url = f"{self.BASE_URL}/soccer/all/scoreboard"
        params = {"dates": date.replace("-", "")} if date else {}
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                
                events = data.get("events", [])
                results = []
                for event in events:
                    parsed = self._parse_event(event)
                    if parsed:
                        results.append(parsed)
                return results
            except Exception as e:
                print(f"[ESPN] 获取赛程失败: {e}")
                return []
    
    def _parse_event(self, event: Dict) -> Optional[Dict[str, Any]]:
        """解析 ESPN 事件数据"""
        try:
            home = event["competitions"][0]["competitors"][0]["team"]["abbreviation"]
            away = event["competitions"][0]["competitors"][1]["team"]["abbreviation"]
            status = event["status"]["type"]["description"]
            
            return {
                "match_id": event.get("id", ""),
                "home_team": home,
                "away_team": away,
                "match_time": event.get("date", ""),
                "status": status,
                "league": event.get("league", {}).get("name", ""),
            }
        except (KeyError, IndexError):
            return None


class OddsScraper500:
    """500.com 网页抓取（备用方案）"""
    
    URL_TEMPLATE = "https://odds.500.com/fenxi/daxiao-{match_id}.shtml"
    
    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )
    
    async def fetch_odds(self, match_id: str) -> Optional[Dict[str, Any]]:
        """
        抓取 500.com 赔率数据
        
        注意：网页结构可能变化，需要定期维护
        """
        url = self.URL_TEMPLATE.format(match_id=match_id)
        
        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            html = resp.text
            
            # 简单的正则解析（实际应该用 BeautifulSoup）
            # 这里提供一个框架，实际使用时需要适配页面结构
            import re
            
            # 尝试提取百家欧赔
            odds_pattern = re.compile(r'([\d.]+)\s+([\d.]+)\s+([\d.]+)')
            matches = odds_pattern.findall(html)
            
            if matches:
                # 取第一个匹配（通常是主流公司）
                home, draw, away = map(float, matches[0])
                
                total = 1/home + 1/draw + 1/away
                return {
                    "source": "500.com",
                    "match_id": match_id,
                    "home_odds": home,
                    "draw_odds": draw,
                    "away_odds": away,
                    "home_prob": round((1/home)/total, 4),
                    "draw_prob": round((1/draw)/total, 4),
                    "away_prob": round((1/away)/total, 4),
                }
            
            return None
        except Exception as e:
            print(f"[500.com] 抓取失败: {e}")
            return None
    
    async def close(self):
        await self.client.aclose()


class UnifiedOddsClient:
    """
    统一赔率客户端
    
    优先级：
    1. The Odds API（官方数据，最可靠）
    2. ESPN（免费，赛程为主）
    3. 500.com 抓取（备用）
    """
    
    def __init__(self):
        self.the_odds = TheOddsAPIClient()
        self.espn = ESPNClient()
        self.scraper = OddsScraper500()
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 分钟缓存
    
    def _get_cache_key(self, sport: str, source: str) -> str:
        return f"{source}:{sport}:{datetime.now().strftime('%Y%m%d%H%M')}"
    
    def _get_cached(self, key: str) -> Optional[Any]:
        if key in self._cache:
            data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                return data
            del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        self._cache[key] = (data, datetime.now())
    
    async def get_odds(
        self,
        sport: str = "soccer_epl",
        use_cache: bool = True,
    ) -> List[OddsData]:
        """
        获取赔率数据（自动选择最佳源）
        
        Args:
            sport: 运动代码
            use_cache: 是否使用缓存
        
        Returns:
            赔率数据列表
        """
        cache_key = self._get_cache_key(sport, "odds")
        
        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                print(f"[UnifiedOdds] 使用缓存 [{sport}]")
                return cached
        
        # 尝试 The Odds API
        results = await self.the_odds.get_odds(sport=sport)
        
        if results:
            print(f"[UnifiedOdds] The Odds API 成功 [{sport}]: {len(results)} 场")
            self._set_cache(cache_key, results)
            return results
        
        # 备用：ESPN（无赔率，只有赛程）
        print(f"[UnifiedOdds] The Odds API 失败，尝试 ESPN [{sport}]")
        # ESPN 不提供赔率，所以这里返回空
        
        return []
    
    async def get_world_cup_odds(self) -> List[OddsData]:
        """获取世界杯赔率"""
        return await self.get_odds("soccer_fifa_world_cup")
    
    async def get_match_odds(self, match_id: str, source: str = "auto") -> Optional[Dict[str, Any]]:
        """
        获取单场比赛赔率
        
        Args:
            match_id: 比赛 ID
            source: 数据源（auto/the_odds/500）
        """
        if source in ("auto", "500"):
            return await self.scraper.fetch_odds(match_id)
        return None
    
    async def get_usage(self) -> Dict[str, Any]:
        """获取 API 使用情况"""
        return await self.the_odds.get_usage()
    
    async def close(self):
        await self.the_odds.close()
        await self.scraper.close()


async def test_client():
    """测试客户端"""
    client = UnifiedOddsClient()
    
    # 检查 API 使用情况
    usage = await client.get_usage()
    print(f"API 使用: {usage}")
    
    # 获取 EPL 赔率
    odds = await client.get_odds("soccer_epl")
    print(f"\n获取到 {len(odds)} 场比赛赔率")
    
    for o in odds[:3]:
        print(f"\n{o.home_team} vs {o.away_team}")
        print(f"  赔率: H={o.home_odds} D={o.draw_odds} A={o.away_odds}")
        print(f"  概率: H={o.home_prob:.1%} D={o.draw_prob:.1%} A={o.away_prob:.1%}")
        print(f"  来源: {o.bookmaker}")
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(test_client())
