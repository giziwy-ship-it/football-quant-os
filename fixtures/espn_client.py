#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ESPN 赛程数据源客户端
Football Quant OS - Fixtures Module
"""

import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class MatchFixture:
    """标准化赛程数据模型"""
    match_id: str
    home_team: str
    away_team: str
    home_team_en: str
    away_team_en: str
    league: str
    league_en: str
    match_time: str
    status: str
    venue: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None


# 球队名中英文映射表
TEAM_NAME_MAP = {
    # 英超
    "Arsenal": "阿森纳",
    "Aston Villa": "阿斯顿维拉",
    "Brentford": "布伦特福德",
    "Brighton & Hove Albion": "布莱顿",
    "Burnley": "伯恩利",
    "Chelsea": "切尔西",
    "Crystal Palace": "水晶宫",
    "Everton": "埃弗顿",
    "Fulham": "富勒姆",
    "Liverpool": "利物浦",
    "Luton Town": "卢顿",
    "Manchester City": "曼城",
    "Manchester United": "曼联",
    "Newcastle United": "纽卡斯尔",
    "Nottingham Forest": "诺丁汉森林",
    "Sheffield United": "谢菲尔德联",
    "Tottenham Hotspur": "热刺",
    "West Ham United": "西汉姆联",
    "Wolverhampton Wanderers": "狼队",
    # 西甲
    "Alavés": "阿拉维斯",
    "Almería": "阿尔梅里亚",
    "Athletic Bilbao": "毕尔巴鄂竞技",
    "Atlético Madrid": "马德里竞技",
    "Barcelona": "巴塞罗那",
    "Cádiz": "加的斯",
    "Celta de Vigo": "塞尔塔",
    "Getafe": "赫塔菲",
    "Girona": "赫罗纳",
    "Granada": "格拉纳达",
    "Las Palmas": "拉斯帕尔马斯",
    "Mallorca": "马略卡",
    "Osasuna": "奥萨苏纳",
    "Rayo Vallecano": "巴列卡诺",
    "Real Betis": "皇家贝蒂斯",
    "Real Madrid": "皇家马德里",
    "Real Sociedad": "皇家社会",
    "Sevilla": "塞维利亚",
    "Valencia": "瓦伦西亚",
    "Villarreal": "比利亚雷亚尔",
    # 意甲
    "Atalanta": "亚特兰大",
    "Bologna": "博洛尼亚",
    "Cagliari": "卡利亚里",
    "Empoli": "恩波利",
    "Fiorentina": "佛罗伦萨",
    "Frosinone": "弗罗西诺内",
    "Genoa": "热那亚",
    "Hellas Verona": "维罗纳",
    "Inter": "国际米兰",
    "Juventus": "尤文图斯",
    "Lazio": "拉齐奥",
    "Lecce": "莱切",
    "Milan": "AC米兰",
    "Monza": "蒙扎",
    "Napoli": "那不勒斯",
    "Roma": "罗马",
    "Salernitana": "萨勒尼塔纳",
    "Sassuolo": "萨索洛",
    "Torino": "都灵",
    "Udinese": "乌迪内斯",
    # 德甲
    "Augsburg": "奥格斯堡",
    "Bayer Leverkusen": "勒沃库森",
    "Bayern Munich": "拜仁慕尼黑",
    "Bochum": "波鸿",
    "Borussia Dortmund": "多特蒙德",
    "Borussia Mönchengladbach": "门兴格拉德巴赫",
    "Darmstadt 98": "达姆施塔特",
    "Eintracht Frankfurt": "法兰克福",
    "Freiburg": "弗赖堡",
    "Heidenheim": "海登海姆",
    "Hoffenheim": "霍芬海姆",
    "Köln": "科隆",
    "Mainz 05": "美因茨",
    "RB Leipzig": "莱比锡",
    "Stuttgart": "斯图加特",
    "Union Berlin": "柏林联合",
    "Werder Bremen": "云达不莱梅",
    "Wolfsburg": "沃尔夫斯堡",
    # 法甲
    "Brest": "布雷斯特",
    "Clermont Foot": "克莱蒙",
    "Le Havre": "勒阿弗尔",
    "Lens": "朗斯",
    "Lille": "里尔",
    "Lorient": "洛里昂",
    "Lyon": "里昂",
    "Marseille": "马赛",
    "Metz": "梅斯",
    "Monaco": "摩纳哥",
    "Montpellier": "蒙彼利埃",
    "Nantes": "南特",
    "Nice": "尼斯",
    "Paris Saint-Germain": "巴黎圣日耳曼",
    "Reims": "兰斯",
    "Rennes": "雷恩",
    "Strasbourg": "斯特拉斯堡",
    "Toulouse": "图卢兹",
    # 欧冠
    "Benfica": "本菲卡",
    "Braga": "布拉加",
    "Copenhagen": "哥本哈根",
    "Galatasaray": "加拉塔萨雷",
    "Porto": "波尔图",
    "PSV": "埃因霍温",
    "RB Salzburg": "萨尔茨堡红牛",
    "Shakhtar Donetsk": "顿涅茨克矿工",
    "Young Boys": "伯尔尼年轻人",
    # 其他常见
    "Ajax": "阿贾克斯",
    "Feyenoord": "费耶诺德",
    "Celtic": "凯尔特人",
    "Rangers": "流浪者",
    "Dinamo Zagreb": "萨格勒布迪纳摩",
    "Olympiacos": "奥林匹亚科斯",
    "PAOK": "塞萨洛尼基",
    "Sparta Prague": "布拉格斯巴达",
    "Slavia Prague": "布拉格斯拉维亚",
    "Red Star Belgrade": "贝尔格莱德红星",
    "Ludogorets": "卢多戈雷茨",
    "Qarabağ": "卡拉巴赫",
    "Maccabi Haifa": "海法马卡比",
    "Hapoel Be'er Sheva": "贝尔谢巴工人",
}

# 联赛名映射（ESPN uid 到中文联赛名）
LEAGUE_UID_MAP = {
    "l:770": "英超",
    "l:766": "西甲",
    "l:768": "意甲",
    "l:778": "德甲",
    "l:771": "法甲",
    "l:775": "欧冠",
    "l:773": "欧联",
    "l:772": "欧协联",
    "l:783": "沙特联",
    "l:805": "解放者杯",
    "l:840": "南美杯",
    "l:779": "足总杯",
    "l:781": "联赛杯",
    "l:767": "国王杯",
    "l:769": "意大利杯",
    "l:782": "德国杯",
    "l:774": "法国杯",
    "l:776": "世俱杯",
    "l:777": "欧超杯",
    "l:780": "社区盾",
    "l:784": "亚冠",
    "l:785": "美职联",
    "l:786": "墨超",
    "l:787": "巴甲",
    "l:788": "阿甲",
    "l:789": "葡超",
    "l:790": "荷甲",
    "l:791": "比甲",
    "l:792": "苏超",
    "l:793": "俄超",
    "l:794": "土超",
    "l:795": "希腊超",
    "l:796": "丹超",
    "l:797": "瑞典超",
    "l:798": "挪超",
    "l:799": "芬超",
}

# 联赛名映射（英文到中文）
LEAGUE_NAME_MAP = {
    "English Premier League": "英超",
    "Spanish LaLiga": "西甲",
    "Italian Serie A": "意甲",
    "German Bundesliga": "德甲",
    "French Ligue 1": "法甲",
    "UEFA Champions League": "欧冠",
    "UEFA Europa League": "欧联",
    "UEFA Europa Conference League": "欧协联",
    "FA Cup": "足总杯",
    "Carabao Cup": "联赛杯",
    "Copa del Rey": "国王杯",
    "Coppa Italia": "意大利杯",
    "DFB-Pokal": "德国杯",
    "Coupe de France": "法国杯",
    "Saudi Pro League": "沙特联",
    "Copa Libertadores": "解放者杯",
    "Copa Sudamericana": "南美杯",
    "FIFA Club World Cup": "世俱杯",
    "UEFA Super Cup": "欧超杯",
    "FA Community Shield": "社区盾",
    "AFC Champions League": "亚冠",
    "Major League Soccer": "美职联",
    "Liga MX": "墨超",
    "Campeonato Brasileiro": "巴甲",
    "Argentine Primera División": "阿甲",
    "Primeira Liga": "葡超",
    "Eredivisie": "荷甲",
    "Belgian Pro League": "比甲",
    "Scottish Premiership": "苏超",
    "Russian Premier League": "俄超",
    "Süper Lig": "土超",
    "Super League Greece": "希腊超",
    "Danish Superliga": "丹超",
    "Allsvenskan": "瑞典超",
    "Eliteserien": "挪超",
    "Veikkausliiga": "芬超",
}


def translate_team_name(en_name: str) -> str:
    """将英文球队名翻译为中文"""
    return TEAM_NAME_MAP.get(en_name, en_name)


def translate_league_name(en_name: str) -> str:
    """将英文联赛名翻译为中文"""
    # 先检查完整映射
    if en_name in LEAGUE_NAME_MAP:
        return LEAGUE_NAME_MAP[en_name]
    
    # 检查是否已经是中文
    if any(en_name == cn for cn in LEAGUE_NAME_MAP.values()):
        return en_name
    
    # 尝试部分匹配
    en_lower = en_name.lower()
    for eng_name, cn_name in LEAGUE_NAME_MAP.items():
        if eng_name.lower() in en_lower or en_lower in eng_name.lower():
            return cn_name
    
    return en_name


class ESPNClient:
    """ESPN API 客户端"""
    
    BASE_URL = "https://site.api.espn.com/apis/site/v2/sports"
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                headers={"User-Agent": "Football-Quant-OS/4.1"},
                timeout=aiohttp.ClientTimeout(total=15)
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    async def fetch_fixtures(self, date: Optional[str] = None) -> List[MatchFixture]:
        """
        获取赛程列表
        
        Args:
            date: 日期格式 YYYY-MM-DD，None则获取今天
        
        Returns:
            List[MatchFixture]: 标准化赛程列表
        """
        session = await self._get_session()
        
        # ESPN soccer API endpoint
        url = f"{self.BASE_URL}/soccer/all/scoreboard"
        
        params = {}
        if date:
            params["dates"] = date.replace("-", "")
        
        try:
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    print(f"ESPN API Error: {resp.status}")
                    return []
                
                data = await resp.json()
                return self._parse_events(data.get("events", []))
                
        except Exception as e:
            print(f"ESPN fetch error: {e}")
            return []
    
    def _parse_events(self, events: List[Dict]) -> List[MatchFixture]:
        """解析 ESPN 事件数据"""
        fixtures = []
        
        for event in events:
            try:
                match_id = str(event.get("id", ""))
                name = event.get("name", "")
                
                # 解析球队名 "Home Team at Away Team" 或 "Home Team vs Away Team"
                teams = self._parse_match_name(name)
                if not teams:
                    continue
                
                home_en, away_en = teams
                home_cn = translate_team_name(home_en)
                away_cn = translate_team_name(away_en)
                
                # 获取联赛信息 - 从 competitions 中提取
                competitions = event.get("competitions", [])
                league_en = "Unknown"
                league_cn = "Unknown"
                
                if competitions and len(competitions) > 0:
                    comp = competitions[0]
                    
                    # 尝试多种路径获取联赛名
                    # 1. 从 competition 对象获取
                    competition_obj = comp.get("competition", {})
                    if competition_obj:
                        league_en = competition_obj.get("name", "")
                        # 尝试从 parent 获取
                        if not league_en:
                            league_en = competition_obj.get("parent", {}).get("name", "")
                    
                    # 2. 直接从 competition 获取
                    if not league_en:
                        league_en = comp.get("name", "")
                    
                    # 3. 从 type 获取
                    if not league_en:
                        league_en = comp.get("type", {}).get("name", "")
                    
                    # 4. 从 genre 获取
                    if not league_en:
                        league_en = comp.get("genre", "")
                    
                    # 5. 从 notes 获取（有时 ESPN 会把联赛名放在 notes 里）
                    if not league_en:
                        notes = comp.get("notes", [])
                        if notes and len(notes) > 0:
                            league_en = notes[0].get("headline", "")
                
                # 从 uid 解析联赛信息 (备用方案)
                if not league_en or league_en == "Unknown":
                    uid = event.get("uid", "")
                    
                    # 检查 uid 中的联赛标识
                    for uid_key, league_name in LEAGUE_UID_MAP.items():
                        if uid_key in uid:
                            league_cn = league_name
                            league_en = LEAGUE_NAME_MAP.get(league_name, league_name)
                            break
                    
                    # 如果还是 Unknown，尝试从 uid 提取数字
                    if not league_cn or league_cn == "Unknown":
                        import re
                        match = re.search(r'l:(\d+)', uid)
                        if match:
                            league_id = match.group(1)
                            uid_key = f"l:{league_id}"
                            if uid_key in LEAGUE_UID_MAP:
                                league_cn = LEAGUE_UID_MAP[uid_key]
                                league_en = LEAGUE_NAME_MAP.get(league_cn, league_cn)
                
                # 确保 league_en 是字符串
                if not isinstance(league_en, str):
                    league_en = str(league_en)
                if not isinstance(league_cn, str):
                    league_cn = str(league_cn)
                
                # 最终处理
                if not league_en:
                    league_en = "Unknown"
                if not league_cn or league_cn == "Unknown":
                    # 尝试从英文名翻译
                    if league_en != "Unknown":
                        league_cn = translate_league_name(league_en)
                    else:
                        league_cn = "未知联赛"
                
                # 确保 league_cn 不为 Unknown
                if league_cn == "Unknown" or league_cn == "未知联赛":
                    # 最后尝试：检查 event 的其他字段
                    season = event.get("season", {})
                    if season:
                        season_type = season.get("type", "")
                        if season_type:
                            # 强制转换为字符串
                            season_type_str = str(season_type)
                            league_cn = f"赛季{season_type_str}"
                            league_en = season_type_str
                
                # 最终安全检查：确保 league_en 是字符串
                if not isinstance(league_en, str):
                    league_en = str(league_en)
                if not isinstance(league_cn, str):
                    league_cn = str(league_cn)
                
                # 获取比赛时间
                date_str = event.get("date", "")
                match_time = self._format_time(date_str)
                
                # 获取状态
                status_info = event.get("status", {})
                status = status_info.get("type", {}).get("description", "Unknown")
                
                # 获取比分（如果比赛进行中或已结束）
                home_score = None
                away_score = None
                if competitions and len(competitions) > 0:
                    competitors = competitions[0].get("competitors", [])
                    for c in competitors:
                        if c.get("homeAway") == "home":
                            home_score = c.get("score")
                        elif c.get("homeAway") == "away":
                            away_score = c.get("score")
                
                # 获取场地
                venue = None
                if competitions and len(competitions) > 0:
                    venue = competitions[0].get("venue", {}).get("fullName")
                
                fixture = MatchFixture(
                    match_id=match_id,
                    home_team=home_cn,
                    away_team=away_cn,
                    home_team_en=home_en,
                    away_team_en=away_en,
                    league=league_cn,
                    league_en=league_en,
                    match_time=match_time,
                    status=status,
                    venue=venue,
                    home_score=int(home_score) if home_score is not None else None,
                    away_score=int(away_score) if away_score is not None else None
                )
                
                fixtures.append(fixture)
                
            except Exception as e:
                print(f"Parse event error: {e}")
                continue
        
        return fixtures
    
    def _parse_match_name(self, name: str) -> Optional[tuple]:
        """解析比赛名称，提取主客队"""
        if " at " in name:
            parts = name.split(" at ")
            return (parts[1].strip(), parts[0].strip())  # (home, away)
        elif " vs " in name:
            parts = name.split(" vs ")
            return (parts[0].strip(), parts[1].strip())
        return None
    
    def _format_time(self, iso_time: str) -> str:
        """格式化ISO时间为本地时间"""
        try:
            # 解析 UTC 时间
            dt = datetime.fromisoformat(iso_time.replace("Z", "+00:00"))
            # 转换为北京时间 (UTC+8)
            dt_local = dt + timedelta(hours=8)
            return dt_local.strftime("%Y-%m-%d %H:%M")
        except:
            return iso_time


async def test_client():
    """测试客户端"""
    client = ESPNClient()
    
    print("=== 测试 ESPN 赛程拉取 ===")
    print()
    
    # 获取今天的比赛
    fixtures = await client.fetch_fixtures()
    
    print(f"获取到 {len(fixtures)} 场比赛")
    print()
    
    # 按联赛分组显示
    leagues = {}
    for f in fixtures:
        league = f.league if f.league else "Unknown"
        if league not in leagues:
            leagues[league] = []
        leagues[league].append(f)
    
    for league, matches in leagues.items():
        print(f"【{league}】")
        for m in matches[:3]:  # 只显示前3场
            score_str = ""
            if m.home_score is not None and m.away_score is not None:
                score_str = f" [{m.home_score}-{m.away_score}]"
            print(f"  {m.match_time} | {m.home_team} vs {m.away_team}{score_str} ({m.status})")
        if len(matches) > 3:
            print(f"  ... 还有 {len(matches) - 3} 场")
        print()
    
    await client.close()


if __name__ == "__main__":
    asyncio.run(test_client())
