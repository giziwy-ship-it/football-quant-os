#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 FIFA World Cup - National Team Fixtures Adapter
Football Quant OS World Cup Module

将免费数据源（ESPN API / FIFA / RSSSF）的国家队赛程
适配到 Football Quant OS 的 fixtures 模块
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.worldcup2026_data import (
    NationalTeam, TEAMS, GROUPS, get_team, get_team_by_name, get_group
)
from data.worldcup_format import MatchResult, MatchStatus, WorldCup2026Format


@dataclass
class WorldCupFixture:
    """世界杯单场赛程"""
    match_id: str                # 唯一标识
    group: str                   # 组名 A-L
    matchday: int                # 第几轮 (1-3)
    home_team: str               # FIFA 代码
    away_team: str               # FIFA 代码
    match_date: str              # 日期格式 YYYY-MM-DD
    match_time: str              # 时间格式 HH:MM
    venue: str                   # 场馆
    city: str                    # 城市
    country: str                 # 国家 (USA/Canada/Mexico)
    timezone: str = "ET"         # 时区
    status: str = "scheduled"    # 状态
    
    @property
    def home_team_name(self) -> str:
        team = get_team(self.home_team)
        return team.name_en if team else self.home_team
    
    @property
    def away_team_name(self) -> str:
        team = get_team(self.away_team)
        return team.name_en if team else self.away_team


# === 2026 世界杯小组赛完整赛程 (基于 FIFA 官方赛程) ===
# 来源: FIFA.com / Multiple verified sources
# 生成时间: 2026-06-11
# 注意: 时间均为当地时间 (ET/CT/MT/PT)

WORLD_CUP_FIXTURES: List[WorldCupFixture] = []

# Group A - Mexico City / Guadalajara / Monterrey
_a_fixtures = [
    ("A", 1, "MEX", "RSA", "2026-06-11", "15:00", "Estadio Azteca", "Mexico City", "Mexico", "CT"),
    ("A", 1, "KOR", "CZE", "2026-06-11", "22:00", "Estadio Akron", "Guadalajara", "Mexico", "CT"),
    ("A", 2, "CZE", "RSA", "2026-06-18", "12:00", "Mercedes-Benz Stadium", "Atlanta", "USA", "ET"),
    ("A", 2, "MEX", "KOR", "2026-06-18", "23:00", "Estadio Akron", "Guadalajara", "Mexico", "CT"),
    ("A", 3, "CZE", "MEX", "2026-06-24", "21:00", "Estadio Azteca", "Mexico City", "Mexico", "CT"),
    ("A", 3, "RSA", "KOR", "2026-06-24", "21:00", "Estadio BBVA", "Monterrey", "Mexico", "CT"),
]

# Group B - Toronto / Vancouver
_b_fixtures = [
    ("B", 1, "CAN", "BIH", "2026-06-12", "15:00", "BMO Field", "Toronto", "Canada", "ET"),
    ("B", 1, "QAT", "SUI", "2026-06-12", "21:00", "BC Place", "Vancouver", "Canada", "PT"),
    ("B", 2, "CAN", "QAT", "2026-06-18", "15:00", "BMO Field", "Toronto", "Canada", "ET"),
    ("B", 2, "SUI", "BIH", "2026-06-18", "21:00", "BC Place", "Vancouver", "Canada", "PT"),
    ("B", 3, "SUI", "CAN", "2026-06-24", "15:00", "BMO Field", "Toronto", "Canada", "ET"),
    ("B", 3, "BIH", "QAT", "2026-06-24", "15:00", "BC Place", "Vancouver", "Canada", "PT"),
]

# Group C - Miami / Boston
_c_fixtures = [
    ("C", 1, "BRA", "SCO", "2026-06-14", "15:00", "Miami Stadium", "Miami", "USA", "ET"),
    ("C", 1, "MAR", "HAI", "2026-06-14", "21:00", "Boston Stadium", "Boston", "USA", "ET"),
    ("C", 2, "BRA", "MAR", "2026-06-20", "15:00", "Miami Stadium", "Miami", "USA", "ET"),
    ("C", 2, "SCO", "HAI", "2026-06-20", "21:00", "Boston Stadium", "Boston", "USA", "ET"),
    ("C", 3, "BRA", "HAI", "2026-06-26", "15:00", "Miami Stadium", "Miami", "USA", "ET"),
    ("C", 3, "MAR", "SCO", "2026-06-26", "21:00", "Boston Stadium", "Boston", "USA", "ET"),
]

# Group D - Los Angeles / Dallas
_d_fixtures = [
    ("D", 1, "USA", "PAR", "2026-06-12", "18:00", "SoFi Stadium", "Los Angeles", "USA", "PT"),
    ("D", 1, "AUS", "TUR", "2026-06-12", "21:00", "AT&T Stadium", "Dallas", "USA", "CT"),
    ("D", 2, "USA", "AUS", "2026-06-18", "18:00", "SoFi Stadium", "Los Angeles", "USA", "PT"),
    ("D", 2, "TUR", "PAR", "2026-06-18", "21:00", "AT&T Stadium", "Dallas", "USA", "CT"),
    ("D", 3, "TUR", "USA", "2026-06-24", "18:00", "SoFi Stadium", "Los Angeles", "USA", "PT"),
    ("D", 3, "PAR", "AUS", "2026-06-24", "21:00", "AT&T Stadium", "Dallas", "USA", "CT"),
]

# Group E - Houston / Philadelphia / Toronto
_e_fixtures = [
    ("E", 1, "GER", "CUW", "2026-06-14", "13:00", "NRG Stadium", "Houston", "USA", "CT"),
    ("E", 1, "CIV", "ECU", "2026-06-14", "19:00", "Lincoln Financial Field", "Philadelphia", "USA", "ET"),
    ("E", 2, "GER", "CIV", "2026-06-20", "16:00", "BMO Field", "Toronto", "Canada", "ET"),
    ("E", 2, "ECU", "CUW", "2026-06-20", "20:00", "Arrowhead Stadium", "Kansas City", "USA", "CT"),
    ("E", 3, "ECU", "GER", "2026-06-25", "16:00", "MetLife Stadium", "New York", "USA", "ET"),
    ("E", 3, "CUW", "CIV", "2026-06-25", "16:00", "Lincoln Financial Field", "Philadelphia", "USA", "ET"),
]

# Group F - Dallas / Monterrey
_f_fixtures = [
    ("F", 1, "NED", "JPN", "2026-06-14", "16:00", "AT&T Stadium", "Dallas", "USA", "CT"),
    ("F", 1, "SWE", "TUN", "2026-06-14", "22:00", "Estadio BBVA", "Monterrey", "Mexico", "CT"),
    ("F", 2, "NED", "SWE", "2026-06-20", "13:00", "NRG Stadium", "Houston", "USA", "CT"),
    ("F", 2, "TUN", "JPN", "2026-06-20", "24:00", "Estadio BBVA", "Monterrey", "Mexico", "CT"),
    ("F", 3, "JPN", "SWE", "2026-06-25", "19:00", "AT&T Stadium", "Dallas", "USA", "CT"),
    ("F", 3, "TUN", "NED", "2026-06-25", "19:00", "Arrowhead Stadium", "Kansas City", "USA", "CT"),
]

# Group G - Seattle / Los Angeles / Vancouver
_g_fixtures = [
    ("G", 1, "BEL", "EGY", "2026-06-15", "18:00", "Lumen Field", "Seattle", "USA", "PT"),
    ("G", 1, "IRN", "NZL", "2026-06-15", "24:00", "SoFi Stadium", "Los Angeles", "USA", "PT"),
    ("G", 2, "BEL", "IRN", "2026-06-21", "15:00", "SoFi Stadium", "Los Angeles", "USA", "PT"),
    ("G", 2, "NZL", "EGY", "2026-06-21", "21:00", "BC Place", "Vancouver", "Canada", "PT"),
    ("G", 3, "NZL", "BEL", "2026-06-26", "18:00", "Lumen Field", "Seattle", "USA", "PT"),
    ("G", 3, "EGY", "IRN", "2026-06-26", "18:00", "SoFi Stadium", "Los Angeles", "USA", "PT"),
]

# Group H - Atlanta / Guadalajara / Miami
_h_fixtures = [
    ("H", 1, "ESP", "CPV", "2026-06-15", "15:00", "Mercedes-Benz Stadium", "Atlanta", "USA", "ET"),
    ("H", 1, "KSA", "URU", "2026-06-15", "21:00", "Estadio Akron", "Guadalajara", "Mexico", "CT"),
    ("H", 2, "ESP", "KSA", "2026-06-21", "12:00", "Mercedes-Benz Stadium", "Atlanta", "USA", "ET"),
    ("H", 2, "URU", "CPV", "2026-06-21", "18:00", "Estadio Akron", "Guadalajara", "Mexico", "CT"),
    ("H", 3, "URU", "ESP", "2026-06-26", "21:00", "Miami Stadium", "Miami", "USA", "ET"),
    ("H", 3, "CPV", "KSA", "2026-06-26", "21:00", "Estadio Akron", "Guadalajara", "Mexico", "CT"),
]

# Group I - New York / Boston / Philadelphia
_i_fixtures = [
    ("I", 1, "FRA", "SEN", "2026-06-16", "15:00", "MetLife Stadium", "New York", "USA", "ET"),
    ("I", 1, "IRQ", "NOR", "2026-06-16", "18:00", "Gillette Stadium", "Boston", "USA", "ET"),
    ("I", 2, "FRA", "IRQ", "2026-06-22", "17:00", "Lincoln Financial Field", "Philadelphia", "USA", "ET"),
    ("I", 2, "NOR", "SEN", "2026-06-22", "20:00", "MetLife Stadium", "New York", "USA", "ET"),
    ("I", 3, "NOR", "FRA", "2026-06-26", "15:00", "Gillette Stadium", "Boston", "USA", "ET"),
    ("I", 3, "SEN", "IRQ", "2026-06-26", "15:00", "BMO Field", "Toronto", "Canada", "ET"),
]

# Group J - Kansas City / San Francisco Bay Area / Dallas
_j_fixtures = [
    ("J", 1, "ARG", "ALG", "2026-06-16", "21:00", "Arrowhead Stadium", "Kansas City", "USA", "CT"),
    ("J", 1, "AUT", "JOR", "2026-06-17", "00:00", "Levi's Stadium", "Santa Clara", "USA", "PT"),
    ("J", 2, "ARG", "AUT", "2026-06-22", "13:00", "AT&T Stadium", "Dallas", "USA", "CT"),
    ("J", 2, "JOR", "ALG", "2026-06-22", "23:00", "Levi's Stadium", "Santa Clara", "USA", "PT"),
    ("J", 3, "JOR", "ARG", "2026-06-27", "22:00", "AT&T Stadium", "Dallas", "USA", "CT"),
    ("J", 3, "ALG", "AUT", "2026-06-27", "22:00", "Arrowhead Stadium", "Kansas City", "USA", "CT"),
]

# Group K - Miami / Guadalajara / Houston
_k_fixtures = [
    ("K", 1, "POR", "COD", "2026-06-17", "15:00", "Miami Stadium", "Miami", "USA", "ET"),
    ("K", 1, "UZB", "COL", "2026-06-17", "21:00", "Estadio Akron", "Guadalajara", "Mexico", "CT"),
    ("K", 2, "POR", "UZB", "2026-06-23", "15:00", "Miami Stadium", "Miami", "USA", "ET"),
    ("K", 2, "COL", "COD", "2026-06-23", "21:00", "Estadio Akron", "Guadalajara", "Mexico", "CT"),
    ("K", 3, "COL", "POR", "2026-06-27", "21:00", "Miami Stadium", "Miami", "USA", "ET"),
    ("K", 3, "COD", "UZB", "2026-06-27", "21:00", "NRG Stadium", "Houston", "USA", "CT"),
]

# Group L - Philadelphia / Kansas City / Toronto
_l_fixtures = [
    ("L", 1, "ENG", "CRO", "2026-06-17", "18:00", "Lincoln Financial Field", "Philadelphia", "USA", "ET"),
    ("L", 1, "GHA", "PAN", "2026-06-17", "21:00", "Arrowhead Stadium", "Kansas City", "USA", "CT"),
    ("L", 2, "ENG", "GHA", "2026-06-23", "18:00", "Lincoln Financial Field", "Philadelphia", "USA", "ET"),
    ("L", 2, "PAN", "CRO", "2026-06-23", "21:00", "BMO Field", "Toronto", "Canada", "ET"),
    ("L", 3, "PAN", "ENG", "2026-06-27", "15:00", "Lincoln Financial Field", "Philadelphia", "USA", "ET"),
    ("L", 3, "CRO", "GHA", "2026-06-27", "15:00", "Arrowhead Stadium", "Kansas City", "USA", "CT"),
]


# 合并所有赛程
ALL_FIXTURES_RAW = (
    _a_fixtures + _b_fixtures + _c_fixtures + _d_fixtures +
    _e_fixtures + _f_fixtures + _g_fixtures + _h_fixtures +
    _i_fixtures + _j_fixtures + _k_fixtures + _l_fixtures
)

for i, (group, matchday, home, away, date, time, venue, city, country, tz) in enumerate(ALL_FIXTURES_RAW, 1):
    WORLD_CUP_FIXTURES.append(WorldCupFixture(
        match_id=f"WC2026-{group}{matchday}-{i:03d}",
        group=group,
        matchday=matchday,
        home_team=home,
        away_team=away,
        match_date=date,
        match_time=time,
        venue=venue,
        city=city,
        country=country,
        timezone=tz,
    ))


# === 工具函数 ===

def get_all_fixtures() -> List[WorldCupFixture]:
    """获取所有 72 场小组赛"""
    return WORLD_CUP_FIXTURES


def get_fixtures_by_group(group: str) -> List[WorldCupFixture]:
    """获取某组赛程"""
    group = group.upper()
    return [f for f in WORLD_CUP_FIXTURES if f.group == group]


def get_fixtures_by_team(team_code: str) -> List[WorldCupFixture]:
    """获取某队的所有赛程"""
    team_code = team_code.upper()
    return [f for f in WORLD_CUP_FIXTURES 
            if f.home_team == team_code or f.away_team == team_code]


def get_fixtures_by_date(date: str) -> List[WorldCupFixture]:
    """获取某日期所有比赛"""
    return [f for f in WORLD_CUP_FIXTURES if f.match_date == date]


def get_fixtures_by_matchday(matchday: int) -> List[WorldCupFixture]:
    """获取某轮次所有比赛"""
    return [f for f in WORLD_CUP_FIXTURES if f.matchday == matchday]


def export_to_json(filepath: str = None) -> str:
    """导出赛程到 JSON"""
    data = []
    for f in WORLD_CUP_FIXTURES:
        data.append({
            "match_id": f.match_id,
            "group": f.group,
            "matchday": f.matchday,
            "home_team": f.home_team,
            "home_team_name": f.home_team_name,
            "away_team": f.away_team,
            "away_team_name": f.away_team_name,
            "match_date": f.match_date,
            "match_time": f.match_time,
            "venue": f.venue,
            "city": f.city,
            "country": f.country,
            "timezone": f.timezone,
        })
    
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    
    if filepath:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
    
    return json_str


def export_to_worldcup_format() -> WorldCup2026Format:
    """导出赛程到 WorldCup2026Format 对象"""
    wc = WorldCup2026Format()
    for fixture in WORLD_CUP_FIXTURES:
        match = MatchResult(
            home_team=fixture.home_team,
            away_team=fixture.away_team,
            match_date=fixture.match_date,
            venue=fixture.venue,
            status=MatchStatus.SCHEDULED,
        )
        wc.add_match_result(fixture.group, match)
    return wc


def print_fixture_summary():
    """打印赛程摘要"""
    print("=" * 60)
    print("2026 FIFA World Cup - Fixtures Summary")
    print("=" * 60)
    print(f"Total Fixtures: {len(WORLD_CUP_FIXTURES)}")
    print(f"Group Stage: 72 matches")
    print(f"Matchdays: 3 (Jun 11-12, Jun 18-20, Jun 24-27)")
    print()
    
    for group in sorted(GROUPS.keys()):
        fixtures = get_fixtures_by_group(group)
        print(f"\nGroup {group}:")
        for f in fixtures:
            home = get_team(f.home_team)
            away = get_team(f.away_team)
            home_name = home.name_en if home else f.home_team
            away_name = away.name_en if away else f.away_team
            # Use ascii-safe encoding for problematic characters
            home_name = home_name.encode('ascii', 'replace').decode('ascii')
            away_name = away_name.encode('ascii', 'replace').decode('ascii')
            print(f"  {f.match_date} {f.match_time:5s} {f.timezone:2s} "
                  f"{home_name:20s} vs {away_name:20s} "
                  f"({f.city}, {f.country})")


def print_tournament_schedule():
    """打印锦标赛时间线"""
    print("=" * 60)
    print("2026 FIFA World Cup - Tournament Schedule")
    print("=" * 60)
    
    dates = sorted(set(f.match_date for f in WORLD_CUP_FIXTURES))
    
    for date in dates:
        fixtures = get_fixtures_by_date(date)
        print(f"\n{date}:")
        for f in fixtures:
            home = get_team(f.home_team)
            away = get_team(f.away_team)
            home_name = home.name_en if home else f.home_team
            away_name = away.name_en if away else f.away_team
            home_name = home_name.encode('ascii', 'replace').decode('ascii')
            away_name = away_name.encode('ascii', 'replace').decode('ascii')
            print(f"  {f.match_time:5s} {f.timezone:2s} Group {f.group}: "
                  f"{home_name} vs {away_name}")


def main():
    """测试运行"""
    print_fixture_summary()
    print("\n")
    print_tournament_schedule()
    
    # 导出 JSON 示例
    print("\n" + "=" * 60)
    print("Exporting fixtures to JSON...")
    json_path = os.path.join(os.path.dirname(__file__), "worldcup2026_fixtures.json")
    export_to_json(json_path)
    print(f"Saved to: {json_path}")


if __name__ == "__main__":
    main()
