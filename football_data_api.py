#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football-Data.org API 客户端 - Football Quant OS
免费备选方案，提供赛程和赔率数据
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
from datetime import datetime


@dataclass
class MatchData:
    """标准化比赛数据"""
    match_id: str
    home_team: str
    away_team: str
    home_team_en: str
    away_team_en: str
    league: str
    league_en: str
    match_time: str
    status: str
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    odds: Optional[Dict[str, float]] = None


class FootballDataClient:
    """Football-Data.org API 客户端"""
    
    BASE_URL = "https://api.football-data.org/v4"
    
    # 联赛代码映射
    LEAGUE_CODES = {
        "英超": "PL",
        "EPL": "PL",
        "西甲": "PD",
        "La Liga": "PD",
        "意甲": "SA",
        "Serie A": "SA",
        "德甲": "BL1",
        "Bundesliga": "BL1",
        "法甲": "FL1",
        "Ligue 1": "FL1",
        "欧冠": "CL",
        "Champions League": "CL",
        "欧联": "EL",
        "Europa League": "EL",
    }
    
    # 球队名映射（简化版）
    TEAM_NAME_MAP = {
        "Arsenal": "阿森纳",
        "Aston Villa": "阿斯顿维拉",
        "Chelsea": "切尔西",
        "Liverpool": "利物浦",
        "Manchester City": "曼城",
        "Manchester United": "曼联",
        "Tottenham": "热刺",
        "Newcastle": "纽卡斯尔",
        "Brighton": "布莱顿",
        "West Ham": "西汉姆联",
        "Crystal Palace": "水晶宫",
        "Brentford": "布伦特福德",
        "Fulham": "富勒姆",
        "Everton": "埃弗顿",
        "Nottingham Forest": "诺丁汉森林",
        "Bournemouth": "伯恩茅斯",
        "Wolves": "狼队",
        "Burnley": "伯恩利",
        "Sheffield United": "谢菲尔德联",
        "Luton": "卢顿",
        
        "Real Madrid": "皇家马德里",
        "Barcelona": "巴塞罗那",
        "Atletico Madrid": "马德里竞技",
        "Atletico": "马德里竞技",
        "Sevilla": "塞维利亚",
        "Real Sociedad": "皇家社会",
        "Real Betis": "皇家贝蒂斯",
        "Villarreal": "比利亚雷亚尔",
        "Athletic Club": "毕尔巴鄂竞技",
        "Valencia": "瓦伦西亚",
        "Getafe": "赫塔菲",
        "Celta Vigo": "塞尔塔",
        "Osasuna": "奥萨苏纳",
        "Rayo Vallecano": "巴列卡诺",
        "Mallorca": "马略卡",
        "Alaves": "阿拉维斯",
        "Las Palmas": "拉斯帕尔马斯",
        "Granada": "格拉纳达",
        "Cadiz": "加的斯",
        "Almeria": "阿尔梅里亚",
        
        "Inter": "国际米兰",
        "Milan": "AC米兰",
        "Juventus": "尤文图斯",
        "Napoli": "那不勒斯",
        "Roma": "罗马",
        "Lazio": "拉齐奥",
        "Atalanta": "亚特兰大",
        "Fiorentina": "佛罗伦萨",
        "Bologna": "博洛尼亚",
        "Torino": "都灵",
        "Monza": "蒙扎",
        "Genoa": "热那亚",
        "Sassuolo": "萨索洛",
        "Frosinone": "弗罗西诺内",
        "Lecce": "莱切",
        "Udinese": "乌迪内斯",
        "Empoli": "恩波利",
        "Verona": "维罗纳",
        "Cagliari": "卡利亚里",
        "Salernitana": "萨勒尼塔纳",
        
        "Bayern Munich": "拜仁慕尼黑",
        "Borussia Dortmund": "多特蒙德",
        "RB Leipzig": "莱比锡",
        "Leverkusen": "勒沃库森",
        "Eintracht Frankfurt": "法兰克福",
        "Wolfsburg": "沃尔夫斯堡",
        "Freiburg": "弗赖堡",
        "Stuttgart": "斯图加特",
        "Gladbach": "门兴格拉德巴赫",
        "Mainz": "美因茨",
        "Augsburg": "奥格斯堡",
        "Hoffenheim": "霍芬海姆",
        "Werder Bremen": "云达不莱梅",
        "Heidenheim": "海登海姆",
        "Darmstadt": "达姆施塔特",
        "Union Berlin": "柏林联合",
        "Bochum": "波鸿",
        "Koln": "科隆",
        
        "Paris Saint-Germain": "巴黎圣日耳曼",
        "PSG": "巴黎圣日耳曼",
        "Monaco": "摩纳哥",
        "Nice": "尼斯",
        "Lille": "里尔",
        "Rennes": "雷恩",
        "Marseille": "马赛",
        "Lens": "朗斯",
        "Reims": "兰斯",
        "Montpellier": "蒙彼利埃",
        "Strasbourg": "斯特拉斯堡",
        "Nantes": "南特",
        "Brest": "布雷斯特",
        "Le Havre": "勒阿弗尔",
        "Metz": "梅斯",
        "Lorient": "洛里昂",
        "Toulouse": "图卢兹",
        "Clermont": "克莱蒙",
        "Lyon": "里昂",
    }
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_key = get_api_key("football_data")
    
    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            headers = {
                "User-Agent": "Football-Quant-OS/4.1",
                "X-Auth-Token": self.api_key  # Football-Data.org 使用这个 header
            }
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=15)
            )
        return self.session
    
    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()
    
    def _translate_team(self, en_name: str) -> str:
        """将英文球队名翻译为中文"""
        return self.TEAM_NAME_MAP.get(en_name, en_name)
    
    def _translate_league(self, code: str) -> str:
        """将联赛代码翻译为中文"""
        reverse_map = {v: k for k, v in self.LEAGUE_CODES.items()}
        return reverse_map.get(code, code)
    
    async def get_matches(self, date_from: str = None, date_to: str = None) -> List[MatchData]:
        """
        获取比赛列表
        
        Args:
            date_from: 开始日期 YYYY-MM-DD
            date_to: 结束日期 YYYY-MM-DD
        """
        if not self.api_key:
            print("[WARN] Football-Data API 密钥未配置")
            return []
        
        session = await self._get_session()
        
        # 获取所有主要联赛的比赛
        all_matches = []
        
        # 主要联赛代码
        major_leagues = ["PL", "PD", "SA", "BL1", "FL1", "CL", "EL"]
        
        for league_code in major_leagues:
            try:
                url = f"{self.BASE_URL}/competitions/{league_code}/matches"
                params = {}
                if date_from:
                    params["dateFrom"] = date_from
                if date_to:
                    params["dateTo"] = date_to
                
                async with session.get(url, params=params) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        matches = self._parse_matches(data, league_code)
                        all_matches.extend(matches)
                        print(f"[INFO] {league_code}: 获取 {len(matches)} 场比赛")
                    elif resp.status == 400:
                        # API 400 错误，可能是日期格式问题或免费版限制
                        error_text = await resp.text()
                        print(f"[WARN] {league_code}: API 400 - {error_text[:100]}")
                    elif resp.status == 429:
                        print(f"[WARN] {league_code}: 请求频率限制，等待...")
                        await asyncio.sleep(2)
                    elif resp.status == 403:
                        print(f"[WARN] {league_code}: API 403 - 可能需要升级套餐")
                    else:
                        print(f"[WARN] {league_code}: API 错误 {resp.status}")
                
                # 避免请求过快
                await asyncio.sleep(0.5)
                
            except Exception as e:
                print(f"[WARN] {league_code}: 获取失败 - {e}")
                continue
        
        return all_matches
    
    def _parse_matches(self, data: Dict, league_code: str) -> List[MatchData]:
        """解析比赛数据"""
        matches = []
        
        for match in data.get("matches", []):
            try:
                home_team_en = match.get("homeTeam", {}).get("name", "")
                away_team_en = match.get("awayTeam", {}).get("name", "")
                
                home_team_cn = self._translate_team(home_team_en)
                away_team_cn = self._translate_team(away_team_en)
                
                # 获取比分
                home_score = None
                away_score = None
                score = match.get("score", {})
                if score:
                    full_time = score.get("fullTime", {})
                    home_score = full_time.get("home")
                    away_score = full_time.get("away")
                
                # 构建比赛数据
                match_data = MatchData(
                    match_id=str(match.get("id", "")),
                    home_team=home_team_cn,
                    away_team=away_team_cn,
                    home_team_en=home_team_en,
                    away_team_en=away_team_en,
                    league=self._translate_league(league_code),
                    league_en=league_code,
                    match_time=match.get("utcDate", ""),
                    status=match.get("status", "SCHEDULED"),
                    home_score=home_score,
                    away_score=away_score
                )
                
                matches.append(match_data)
                
            except Exception as e:
                print(f"[WARN] 解析比赛失败: {e}")
                continue
        
        return matches
    
    async def get_odds(self, match_id: str) -> Optional[Dict[str, float]]:
        """
        获取比赛赔率
        
        Args:
            match_id: 比赛 ID
        """
        if not self.api_key:
            return None
        
        session = await self._get_session()
        
        try:
            url = f"{self.BASE_URL}/matches/{match_id}"
            
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    
                    # 提取赔率
                    odds = data.get("odds", {})
                    if odds:
                        home_win = odds.get("homeWin", 0)
                        draw = odds.get("draw", 0)
                        away_win = odds.get("awayWin", 0)
                        
                        if home_win and draw and away_win:
                            return {
                                "home_win": float(home_win),
                                "draw": float(draw),
                                "away_win": float(away_win)
                            }
                
                return None
                
        except Exception as e:
            print(f"[WARN] 获取赔率失败: {e}")
            return None


# 全局客户端实例
football_data_client = FootballDataClient()


async def get_today_matches() -> List[Dict[str, Any]]:
    """获取今天比赛的便捷函数"""
    from datetime import date, timedelta
    
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    matches = await football_data_client.get_matches(
        date_from=today.isoformat(),
        date_to=tomorrow.isoformat()
    )
    
    # 转换为字典列表
    result = []
    for match in matches:
        match_dict = {
            "match_id": match.match_id,
            "home_team": match.home_team,
            "away_team": match.away_team,
            "home_team_en": match.home_team_en,
            "away_team_en": match.away_team_en,
            "league": match.league,
            "league_en": match.league_en,
            "match_time": match.match_time,
            "status": match.status,
            "home_score": match.home_score,
            "away_score": match.away_score,
        }
        
        # 获取赔率
        odds = await football_data_client.get_odds(match.match_id)
        if odds:
            match_dict["odds"] = odds
        
        result.append(match_dict)
    
    await football_data_client.close()
    return result


# ============ 测试 ============

async def test_football_data():
    """测试 Football-Data.org API"""
    print("=== 测试 Football-Data.org API ===\n")
    
    # 检查 API 密钥
    api_key = get_api_key("football_data")
    if api_key:
        print(f"[INFO] API 密钥已配置: {api_key[:10]}...")
    else:
        print("[WARN] API 密钥未配置，请在 .env 文件中设置 FOOTBALL_DATA_API_KEY")
        print("[INFO] 获取免费 API 密钥: https://www.football-data.org/")
        return
    
    print()
    
    # 获取今天比赛
    from datetime import date, timedelta
    today = date.today()
    tomorrow = today + timedelta(days=1)
    
    print(f"[INFO] 获取 {today} 的比赛...\n")
    
    matches = await football_data_client.get_matches(
        date_from=today.isoformat(),
        date_to=tomorrow.isoformat()
    )
    
    print(f"\n[INFO] 共获取 {len(matches)} 场比赛\n")
    
    # 显示前 5 场
    for i, match in enumerate(matches[:5], 1):
        print(f"{i}. {match.home_team} vs {match.away_team}")
        print(f"   联赛: {match.league} ({match.league_en})")
        print(f"   时间: {match.match_time}")
        
        # 获取赔率
        odds = await football_data_client.get_odds(match.match_id)
        if odds:
            print(f"   赔率: 主{odds['home_win']} | 平{odds['draw']} | 客{odds['away_win']}")
        else:
            print(f"   赔率: 暂无")
        print()
    
    await football_data_client.close()
    print("测试完成！")


if __name__ == "__main__":
    asyncio.run(test_football_data())
