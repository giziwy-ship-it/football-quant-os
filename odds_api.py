#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实时赔率接入模块 - Football Quant OS
支持多赔率源：Bet365、William Hill、Pinnacle 等
"""

import os
import sys
sys.stdout.reconfigure(encoding='utf-8')

# 加载统一配置
from core.config_loader import ensure_config, get_api_key
ensure_config()

import asyncio
import aiohttp
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class MatchOdds:
    """标准化赔率数据"""
    home_win: float
    draw: float
    away_win: float
    source: str
    timestamp: str
    
    def to_dict(self) -> Dict[str, float]:
        return {
            "home_win": self.home_win,
            "draw": self.draw,
            "away_win": self.away_win,
            "source": self.source,
            "timestamp": self.timestamp
        }


class OddsAPIClient:
    """赔率 API 客户端"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_key = get_api_key("the_odds")
        self.base_url = "https://api.the-odds-api.com/v4"
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "Football-Quant-OS/4.1"},
                timeout=aiohttp.ClientTimeout(total=10)
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_odds(self, home_team: str, away_team: str, league: str) -> Optional[MatchOdds]:
        """
        获取比赛赔率
        
        使用 The Odds API 获取真实赔率数据
        搜索所有可用联赛，不只是指定的联赛
        """
        if not self.api_key:
            print("[WARN] THE_ODDS_API_KEY 未配置，使用模拟数据")
            return self._get_mock_odds(home_team, away_team, league)
        
        session = await self._get_session()
        
        # 尝试多个联赛搜索
        # 首先尝试指定联赛，然后尝试所有主要联赛
        sport_keys = self._get_search_priority(league)
        
        for sport_key in sport_keys:
            try:
                url = f"{self.base_url}/sports/{sport_key}/odds"
                params = {
                    "apiKey": self.api_key,
                    "regions": "eu",  # 欧洲赔率
                    "markets": "h2h",  # 胜负平
                    "oddsFormat": "decimal"
                }
                
                async with session.get(url, params=params) as resp:
                    if resp.status != 200:
                        continue
                    
                    data = await resp.json()
                    
                    # 查找匹配的比赛
                    for event in data:
                        event_home = event.get("home_team", "")
                        event_away = event.get("away_team", "")
                        
                        # 使用增强的模糊匹配
                        if self._team_match(home_team, event_home) and \
                           self._team_match(away_team, event_away):
                            
                            # 提取赔率
                            bookmakers = event.get("bookmakers", [])
                            if bookmakers:
                                # 使用第一个 bookmaker 的赔率
                                markets = bookmakers[0].get("markets", [])
                                for market in markets:
                                    if market.get("key") == "h2h":
                                        outcomes = market.get("outcomes", [])
                                        odds = {}
                                        for outcome in outcomes:
                                            name = outcome.get("name", "")
                                            price = outcome.get("price", 0)
                                            if name == event_home:
                                                odds["home_win"] = price
                                            elif name == event_away:
                                                odds["away_win"] = price
                                            elif name == "Draw":
                                                odds["draw"] = price
                                        
                                        if len(odds) == 3:
                                            print(f"[INFO] 找到真实赔率: {home_team} vs {away_team} ({sport_key})")
                                            return MatchOdds(
                                                home_win=odds["home_win"],
                                                draw=odds["draw"],
                                                away_win=odds["away_win"],
                                                source="the-odds-api",
                                                timestamp=event.get("commence_time", "")
                                            )
                
            except Exception as e:
                print(f"[WARN] 搜索 {sport_key} 失败: {e}")
                continue
        
        # 未找到匹配比赛，使用模拟数据
        print(f"[WARN] 未找到 {home_team} vs {away_team} 的真实赔率，使用模拟数据")
        return self._get_mock_odds(home_team, away_team, league)
    
    def _get_search_priority(self, league: str) -> List[str]:
        """获取搜索优先级列表"""
        # 主要联赛代码
        all_leagues = [
            "soccer_epl",           # 英超
            "soccer_uefa_champs_league",  # 欧冠
            "soccer_la_liga",       # 西甲
            "soccer_serie_a",       # 意甲
            "soccer_bundesliga",    # 德甲
            "soccer_ligue_one",     # 法甲
            "soccer_uefa_europa_league",  # 欧联
            "soccer_fa_cup",        # 足总杯
            "soccer_carabao_cup",   # 联赛杯
            "soccer_copa_del_rey",  # 国王杯
            "soccer_coppa_italia",  # 意大利杯
            "soccer_dfb_pokal",     # 德国杯
            "soccer_saudi_pro_league",  # 沙特联
        ]
        
        # 联赛映射
        league_mapping = {
            "英超": "soccer_epl",
            "EPL": "soccer_epl",
            "西甲": "soccer_la_liga",
            "意甲": "soccer_serie_a",
            "德甲": "soccer_bundesliga",
            "法甲": "soccer_ligue_one",
            "欧冠": "soccer_uefa_champs_league",
            "欧联": "soccer_uefa_europa_league",
        }
        
        # 优先搜索指定联赛
        priority = []
        if league in league_mapping:
            priority.append(league_mapping[league])
        
        # 然后搜索所有其他联赛
        for l in all_leagues:
            if l not in priority:
                priority.append(l)
        
        return priority
    
    def _team_match(self, team1: str, team2: str) -> bool:
        """模糊匹配球队名（增强版）"""
        # 标准化处理
        team1_lower = team1.lower().strip()
        team2_lower = team2.lower().strip()
        
        # 直接匹配
        if team1_lower == team2_lower:
            return True
        
        # 中文名匹配
        if team1 in team2 or team2 in team1:
            return True
        
        # 完整的球队名映射表
        name_map = {
            # 英超
            "arsenal": ["阿森纳", "arsenal", "gunners"],
            "aston villa": ["阿斯顿维拉", "aston villa", "villa"],
            "brentford": ["布伦特福德", "brentford", "bees"],
            "brighton": ["布莱顿", "brighton", "seagulls"],
            "burnley": ["伯恩利", "burnley", "clarets"],
            "chelsea": ["切尔西", "chelsea", "blues"],
            "crystal palace": ["水晶宫", "crystal palace", "eagles"],
            "everton": ["埃弗顿", "everton", "toffees"],
            "fulham": ["富勒姆", "fulham", "cottagers"],
            "liverpool": ["利物浦", "liverpool", "reds"],
            "luton": ["卢顿", "luton", "hatters"],
            "manchester city": ["曼城", "manchester city", "man city", "city"],
            "manchester united": ["曼联", "manchester united", "man utd", "united", "red devils"],
            "newcastle": ["纽卡斯尔", "newcastle", "magpies"],
            "nottingham forest": ["诺丁汉森林", "nottingham forest", "forest"],
            "sheffield united": ["谢菲尔德联", "sheffield united", "blades"],
            "tottenham": ["热刺", "tottenham", "spurs"],
            "west ham": ["西汉姆联", "west ham", "hammers"],
            "wolves": ["狼队", "wolverhampton", "wolves"],
            
            # 西甲
            "alaves": ["阿拉维斯", "alaves", "alavés"],
            "almeria": ["阿尔梅里亚", "almeria", "almería"],
            "athletic bilbao": ["毕尔巴鄂竞技", "athletic bilbao", "bilbao", "athletic club"],
            "atletico madrid": ["马德里竞技", "atletico madrid", "atletico", "atlético", "atleti"],
            "barcelona": ["巴塞罗那", "barcelona", "barça", "barca"],
            "cadiz": ["加的斯", "cadiz", "cádiz"],
            "celta vigo": ["塞尔塔", "celta vigo", "celta"],
            "getafe": ["赫塔菲", "getafe"],
            "girona": ["赫罗纳", "girona"],
            "granada": ["格拉纳达", "granada"],
            "las palmas": ["拉斯帕尔马斯", "las palmas"],
            "mallorca": ["马略卡", "mallorca"],
            "osasuna": ["奥萨苏纳", "osasuna"],
            "rayo vallecano": ["巴列卡诺", "rayo vallecano", "rayo"],
            "real betis": ["皇家贝蒂斯", "real betis", "betis"],
            "real madrid": ["皇家马德里", "real madrid", "madrid"],
            "real sociedad": ["皇家社会", "real sociedad", "sociedad"],
            "sevilla": ["塞维利亚", "sevilla"],
            "valencia": ["瓦伦西亚", "valencia"],
            "villarreal": ["比利亚雷亚尔", "villarreal"],
            
            # 意甲
            "atalanta": ["亚特兰大", "atalanta"],
            "bologna": ["博洛尼亚", "bologna"],
            "cagliari": ["卡利亚里", "cagliari"],
            "empoli": ["恩波利", "empoli"],
            "fiorentina": ["佛罗伦萨", "fiorentina", "viola"],
            "frosinone": ["弗罗西诺内", "frosinone"],
            "genoa": ["热那亚", "genoa"],
            "hellas verona": ["维罗纳", "hellas verona", "verona"],
            "inter": ["国际米兰", "inter", "inter milan"],
            "juventus": ["尤文图斯", "juventus", "juve"],
            "lazio": ["拉齐奥", "lazio"],
            "lecce": ["莱切", "lecce"],
            "milan": ["ac米兰", "milan", "ac milan", "rossoneri"],
            "monza": ["蒙扎", "monza"],
            "napoli": ["那不勒斯", "napoli"],
            "roma": ["罗马", "roma"],
            "salernitana": ["萨勒尼塔纳", "salernitana"],
            "sassuolo": ["萨索洛", "sassuolo"],
            "torino": ["都灵", "torino"],
            "udinese": ["乌迪内斯", "udinese"],
            
            # 德甲
            "augsburg": ["奥格斯堡", "augsburg"],
            "bayer leverkusen": ["勒沃库森", "bayer leverkusen", "leverkusen"],
            "bayern munich": ["拜仁慕尼黑", "bayern munich", "bayern", "fc bayern"],
            "bochum": ["波鸿", "bochum"],
            "borussia dortmund": ["多特蒙德", "borussia dortmund", "dortmund", "bvb"],
            "borussia monchengladbach": ["门兴格拉德巴赫", "borussia monchengladbach", "gladbach", "monchengladbach"],
            "darmstadt": ["达姆施塔特", "darmstadt", "darmstadt 98"],
            "eintracht frankfurt": ["法兰克福", "eintracht frankfurt", "frankfurt"],
            "freiburg": ["弗赖堡", "freiburg"],
            "heidenheim": ["海登海姆", "heidenheim"],
            "hoffenheim": ["霍芬海姆", "hoffenheim"],
            "koln": ["科隆", "koln", "köln", "cologne"],
            "mainz": ["美因茨", "mainz", "mainz 05"],
            "rb leipzig": ["莱比锡", "rb leipzig", "leipzig"],
            "stuttgart": ["斯图加特", "stuttgart"],
            "union berlin": ["柏林联合", "union berlin"],
            "werder bremen": ["云达不莱梅", "werder bremen", "bremen"],
            "wolfsburg": ["沃尔夫斯堡", "wolfsburg"],
            
            # 法甲
            "brest": ["布雷斯特", "brest"],
            "clermont": ["克莱蒙", "clermont", "clermont foot"],
            "le havre": ["勒阿弗尔", "le havre"],
            "lens": ["朗斯", "lens"],
            "lille": ["里尔", "lille"],
            "lorient": ["洛里昂", "lorient"],
            "lyon": ["里昂", "lyon", "olympique lyonnais"],
            "marseille": ["马赛", "marseille", "olympique marseille"],
            "metz": ["梅斯", "metz"],
            "monaco": ["摩纳哥", "monaco", "as monaco"],
            "montpellier": ["蒙彼利埃", "montpellier"],
            "nantes": ["南特", "nantes"],
            "nice": ["尼斯", "nice"],
            "paris saint-germain": ["巴黎圣日耳曼", "paris saint-germain", "psg", "paris sg"],
            "reims": ["兰斯", "reims"],
            "rennes": ["雷恩", "rennes"],
            "strasbourg": ["斯特拉斯堡", "strasbourg"],
            "toulouse": ["图卢兹", "toulouse"],
            
            # 欧冠常见球队
            "benfica": ["本菲卡", "benfica"],
            "braga": ["布拉加", "braga"],
            "porto": ["波尔图", "porto", "fc porto"],
            "psv": ["埃因霍温", "psv", "psv eindhoven"],
            "ajax": ["阿贾克斯", "ajax"],
            "feyenoord": ["费耶诺德", "feyenoord"],
            "celtic": ["凯尔特人", "celtic"],
            "rangers": ["流浪者", "rangers"],
            "galatasaray": ["加拉塔萨雷", "galatasaray"],
            "fenerbahce": ["费内巴切", "fenerbahce"],
            "besiktas": ["贝西克塔斯", "besiktas"],
            "shakhtar": ["顿涅茨克矿工", "shakhtar", "shakhtar donetsk"],
            "dynamo kyiv": ["基辅迪纳摩", "dynamo kyiv"],
            "red bull salzburg": ["萨尔茨堡红牛", "red bull salzburg", "rb salzburg", "salzburg"],
            "young boys": ["伯尔尼年轻人", "young boys"],
            "copenhagen": ["哥本哈根", "copenhagen", "fc copenhagen"],
            "molde": ["莫尔德", "molde"],
            "bodo glimt": ["博德闪耀", "bodo glimt", "bodø glimt"],
        }
        
        # 检查所有映射
        for names in name_map.values():
            # 检查 team1 是否匹配任何别名
            team1_match = any(alias in team1_lower or team1_lower in alias for alias in names)
            # 检查 team2 是否匹配任何别名
            team2_match = any(alias in team2_lower or team2_lower in alias for alias in names)
            
            # 如果两个球队都匹配同一个映射组
            if team1_match and team2_match:
                return True
        
        # 特殊处理：检查是否包含共同的关键词
        common_keywords = ["madrid", "manchester", "liverpool", "arsenal", "chelsea", 
                          "tottenham", "bayern", "dortmund", "juventus", "milan", 
                          "inter", "roma", "napoli", "barcelona", "valencia", "sevilla",
                          "lyon", "marseille", "monaco", "psg", "lille"]
        
        for keyword in common_keywords:
            if keyword in team1_lower and keyword in team2_lower:
                return True
        
        return False
    
    def _get_mock_odds(self, home_team: str, away_team: str, league: str) -> MatchOdds:
        """生成模拟赔率"""
        
        # 强队列表
        strong_teams = ["曼城", "利物浦", "皇家马德里", "巴塞罗那", "拜仁慕尼黑", 
                       "巴黎圣日耳曼", "阿森纳", "切尔西", "马德里竞技"]
        
        # 判断主客队实力
        home_strong = any(team in home_team for team in strong_teams)
        away_strong = any(team in away_team for team in strong_teams)
        
        if home_strong and not away_strong:
            return MatchOdds(home_win=1.45, draw=4.20, away_win=7.50, source="mock", timestamp="")
        elif away_strong and not home_strong:
            return MatchOdds(home_win=4.50, draw=3.60, away_win=1.75, source="mock", timestamp="")
        elif home_strong and away_strong:
            return MatchOdds(home_win=2.40, draw=3.30, away_win=2.90, source="mock", timestamp="")
        else:
            return MatchOdds(home_win=2.20, draw=3.20, away_win=3.40, source="mock", timestamp="")


# 全局客户端实例
odds_client = OddsAPIClient()


async def get_match_odds(home_team: str, away_team: str, league: str) -> Optional[Dict[str, float]]:
    """
    获取比赛赔率的便捷函数
    """
    odds = await odds_client.fetch_odds(home_team, away_team, league)
    if odds:
        return odds.to_dict()
    return None


# ============ 测试 ============

async def test_odds_api():
    """测试赔率 API"""
    print("=== 测试实时赔率接入 ===\n")
    
    # 检查 API 密钥
    api_key = get_api_key("the_odds")
    if api_key:
        print(f"[INFO] API 密钥已配置: {api_key[:10]}...")
    else:
        print("[WARN] API 密钥未配置，将使用模拟数据")
    print()
    
    test_matches = [
        ("阿森纳", "马德里竞技", "欧冠"),
        ("曼城", "利物浦", "英超"),
        ("巴塞罗那", "皇家马德里", "西甲"),
    ]
    
    for home, away, league in test_matches:
        odds = await get_match_odds(home, away, league)
        source = odds.get("source", "unknown") if odds else "none"
        print(f"{home} vs {away} ({league}) - 来源: {source}:")
        if odds:
            print(f"  主胜: {odds['home_win']}")
            print(f"  平局: {odds['draw']}")
            print(f"  客胜: {odds['away_win']}")
        print()
    
    await odds_client.close()
    print("测试完成！")


if __name__ == "__main__":
    asyncio.run(test_odds_api())
