#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API-Football 数据集成脚本
P1 优先级：实时数据 + 历史数据
需要 API Key (免费额度 100 requests/day)
"""
import requests
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import time


class APIFootball:
    """API-Football 数据接口"""
    
    BASE_URL = "https://v3.football.api-sports.io"
    
    # 联赛ID映射
    LEAGUES = {
        "WC": 1,       # 世界杯
        "EC": 4,       # 欧洲杯
        "CL": 2,       # 欧冠
        "PL": 39,      # 英超
        "LL": 140,     # 西甲
        "BL": 78,      # 德甲
        "SA": 135,     # 意甲
        "L1": 61,      # 法甲
    }
    
    def __init__(self, api_key: str, cache_dir: str = "data/api_football"):
        self.api_key = api_key
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "v3.football.api-sports.io"
        }
        self._request_count = 0
        self._max_requests = 100  # 免费额度
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """发送API请求，带缓存和限流"""
        if self._request_count >= self._max_requests:
            print("[警告] API请求额度已用完，请升级计划或等待明天")
            return None
        
        # 构建缓存键
        cache_key = f"{endpoint}_{json.dumps(params, sort_keys=True)}"
        cache_file = self.cache_dir / f"{hash(cache_key)}.json"
        
        # 检查缓存（24小时内有效）
        if cache_file.exists():
            mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
            if datetime.now() - mtime < timedelta(hours=24):
                with open(cache_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        
        # 发送请求
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # 保存缓存
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False)
            
            self._request_count += 1
            print(f"[API] {endpoint} | 剩余请求: {self._max_requests - self._request_count}")
            
            return data
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                print("[错误] API速率限制，请等待后重试")
            else:
                print(f"[错误] HTTP {response.status_code}: {e}")
            return None
        except Exception as e:
            print(f"[错误] {e}")
            return None
    
    def get_fixtures(self, league: str, season: int, round_str: str = None) -> List[Dict]:
        """
        获取比赛列表
        
        Args:
            league: 联赛代码 (WC, EC, PL, etc.)
            season: 赛季年份 (2022, 2024)
            round_str: 轮次 ("Group Stage - 1", "Round of 16", etc.)
        """
        league_id = self.LEAGUES.get(league)
        if not league_id:
            print(f"[错误] 未知联赛: {league}")
            return []
        
        params = {"league": league_id, "season": season}
        if round_str:
            params["round"] = round_str
        
        data = self._make_request("fixtures", params)
        if not data:
            return []
        
        return data.get("response", [])
    
    def get_fixture_statistics(self, fixture_id: int) -> Optional[Dict]:
        """
        获取比赛统计
        
        返回：xG, 射门, 射正, 控球率, 角球, 犯规, 黄牌, 红牌等
        """
        data = self._make_request("fixtures/statistics", {"fixture": fixture_id})
        if not data:
            return None
        
        return data.get("response", [])
    
    def get_fixture_events(self, fixture_id: int) -> List[Dict]:
        """获取比赛事件（进球、红黄牌、换人）"""
        data = self._make_request("fixtures/events", {"fixture": fixture_id})
        if not data:
            return []
        
        return data.get("response", [])
    
    def get_fixture_odds(self, fixture_id: int) -> List[Dict]:
        """获取比赛赔率（赛前）"""
        data = self._make_request("odds", {"fixture": fixture_id})
        if not data:
            return []
        
        return data.get("response", [])
    
    def get_team_statistics(self, team_id: int, league: str, season: int) -> Optional[Dict]:
        """获取球队统计（赛季累计）"""
        league_id = self.LEAGUES.get(league)
        if not league_id:
            return None
        
        data = self._make_request("teams/statistics", {
            "team": team_id,
            "league": league_id,
            "season": season
        })
        if not data:
            return None
        
        return data.get("response", {})
    
    def search_team(self, name: str) -> List[Dict]:
        """搜索球队"""
        data = self._make_request("teams", {"search": name})
        if not data:
            return []
        
        return data.get("response", [])
    
    def get_standings(self, league: str, season: int) -> List[Dict]:
        """获取积分榜"""
        league_id = self.LEAGUES.get(league)
        if not league_id:
            return []
        
        data = self._make_request("standings", {"league": league_id, "season": season})
        if not data:
            return []
        
        return data.get("response", [])


class FeatureExtractor:
    """从 API-Football 数据中提取特征"""
    
    @staticmethod
    def extract_xg(stats: List[Dict]) -> Dict[str, float]:
        """提取预期进球 (xG)"""
        xg = {"home": 0.0, "away": 0.0}
        
        for team_stats in stats:
            team = team_stats.get("team", {})
            team_name = team.get("name", "")
            statistics = team_stats.get("statistics", [])
            
            for stat in statistics:
                if stat.get("type") == "expected_goals":
                    value = stat.get("value")
                    if value:
                        # API-Football 返回 home team 第一个
                        if team_name == stats[0].get("team", {}).get("name"):
                            xg["home"] = float(value)
                        else:
                            xg["away"] = float(value)
        
        return xg
    
    @staticmethod
    def extract_shots(stats: List[Dict]) -> Dict[str, Dict]:
        """提取射门数据"""
        shots = {"home": {"total": 0, "on": 0}, "away": {"total": 0, "on": 0}}
        
        for team_stats in stats:
            team_name = team_stats.get("team", {}).get("name", "")
            statistics = team_stats.get("statistics", [])
            
            side = "home" if team_name == stats[0].get("team", {}).get("name") else "away"
            
            for stat in statistics:
                if stat.get("type") == "shots_on_goal":
                    shots[side]["on"] = int(stat.get("value", 0) or 0)
                elif stat.get("type") == "total_shots":
                    shots[side]["total"] = int(stat.get("value", 0) or 0)
        
        return shots
    
    @staticmethod
    def extract_possession(stats: List[Dict]) -> Dict[str, float]:
        """提取控球率"""
        possession = {"home": 50.0, "away": 50.0}
        
        for team_stats in stats:
            team_name = team_stats.get("team", {}).get("name", "")
            statistics = team_stats.get("statistics", [])
            
            side = "home" if team_name == stats[0].get("team", {}).get("name") else "away"
            
            for stat in statistics:
                if stat.get("type") == "ball_possession":
                    value = stat.get("value", "50%")
                    possession[side] = float(value.replace("%", ""))
        
        return possession


def main():
    """示例：获取2022世界杯巴西比赛数据"""
    # 需要替换为你的API Key
    API_KEY = "your_api_key_here"
    
    api = APIFootball(API_KEY)
    
    # 搜索巴西队
    teams = api.search_team("Brazil")
    if teams:
        brazil_id = teams[0]["team"]["id"]
        print(f"巴西队ID: {brazil_id}")
        
        # 获取世界杯小组赛
        fixtures = api.get_fixtures("WC", 2022, "Group Stage - 1")
        print(f"\n找到 {len(fixtures)} 场比赛")
        
        for fixture in fixtures[:3]:
            home = fixture["teams"]["home"]["name"]
            away = fixture["teams"]["away"]["name"]
            fixture_id = fixture["fixture"]["id"]
            print(f"\n{home} vs {away}")
            
            # 获取统计
            stats = api.get_fixture_statistics(fixture_id)
            if stats:
                xg = FeatureExtractor.extract_xg(stats)
                shots = FeatureExtractor.extract_shots(stats)
                possession = FeatureExtractor.extract_possession(stats)
                
                print(f"  xG: {home} {xg['home']:.2f} vs {xg['away']:.2f} {away}")
                print(f"  射门: {home} {shots['home']['on']}/{shots['home']['total']} vs {shots['away']['on']}/{shots['away']['total']} {away}")
                print(f"  控球率: {home} {possession['home']:.0f}% vs {possession['away']:.0f}% {away}")
    else:
        print("未找到巴西队，请检查API Key")


if __name__ == "__main__":
    main()
