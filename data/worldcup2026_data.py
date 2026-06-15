#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 FIFA World Cup - 48 Teams Database
Football Quant OS World Cup Module

Source: FIFA Official / Multiple verified sources
Generated: 2026-06-11
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Confederation(Enum):
    """足球联合会"""
    UEFA = "UEFA"       # 欧洲
    CONMEBOL = "CONMEBOL"  # 南美
    CAF = "CAF"         # 非洲
    AFC = "AFC"         # 亚洲
    CONCACAF = "CONCACAF"  # 中北美及加勒比
    OFC = "OFC"         # 大洋洲


@dataclass
class NationalTeam:
    """国家队数据结构"""
    fifa_code: str              # FIFA 3位代码
    name_en: str                # 英文名
    name_cn: str                # 中文名
    fifa_rank: int              # FIFA 排名 (2026-06)
    elo_rating: float           # Elo 评级 (估计值)
    confederation: Confederation
    is_host: bool = False       # 是否东道主
    is_debut: bool = False      # 是否首次参赛
    wc_titles: int = 0          # 世界杯冠军次数
    wc_appearances: int = 0     # 世界杯参赛次数
    notes: str = ""             # 备注


# === 48 支参赛国家队 ===

TEAMS: Dict[str, NationalTeam] = {
    # ===== Group A =====
    "MEX": NationalTeam("MEX", "Mexico", "墨西哥", 15, 1800.0, Confederation.CONCACAF, 
                        is_host=True, wc_titles=0, wc_appearances=18, 
                        notes="Host, 3-time host nation"),
    "RSA": NationalTeam("RSA", "South Africa", "南非", 60, 1580.0, Confederation.CAF, 
                        wc_titles=0, wc_appearances=4, 
                        notes=""),
    "KOR": NationalTeam("KOR", "Korea Republic", "韩国", 25, 1760.0, Confederation.AFC, 
                        wc_titles=0, wc_appearances=12, 
                        notes="Best result: 4th place 2002"),
    "CZE": NationalTeam("CZE", "Czechia", "捷克", 40, 1700.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=10, 
                        notes="Former Czechoslovakia: 2x finalist"),

    # ===== Group B =====
    "CAN": NationalTeam("CAN", "Canada", "加拿大", 42, 1680.0, Confederation.CONCACAF, 
                        is_host=True, wc_titles=0, wc_appearances=3, 
                        notes="Host"),
    "BIH": NationalTeam("BIH", "Bosnia & Herzegovina", "波黑", 55, 1620.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=2, 
                        notes="Eliminated Italy in playoffs"),
    "QAT": NationalTeam("QAT", "Qatar", "卡塔尔", 50, 1640.0, Confederation.AFC, 
                        wc_titles=0, wc_appearances=2, 
                        notes="2022 Host"),
    "SUI": NationalTeam("SUI", "Switzerland", "瑞士", 30, 1740.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=13, 
                        notes=""),

    # ===== Group C =====
    "BRA": NationalTeam("BRA", "Brazil", "巴西", 6, 1950.0, Confederation.CONMEBOL, 
                        wc_titles=5, wc_appearances=23, 
                        notes="5x Champion, only team in every WC"),
    "MAR": NationalTeam("MAR", "Morocco", "摩洛哥", 8, 1850.0, Confederation.CAF, 
                        wc_titles=0, wc_appearances=7, 
                        notes="2022 Semi-finalist"),
    "HAI": NationalTeam("HAI", "Haiti", "海地", 85, 1400.0, Confederation.CONCACAF, 
                        wc_titles=0, wc_appearances=2, 
                        notes="2nd appearance since 1974"),
    "SCO": NationalTeam("SCO", "Scotland", "苏格兰", 43, 1700.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=9, 
                        notes="First since 1998, never past group stage"),

    # ===== Group D =====
    "USA": NationalTeam("USA", "USA", "美国", 16, 1790.0, Confederation.CONCACAF, 
                        is_host=True, wc_titles=0, wc_appearances=12, 
                        notes="Host"),
    "PAR": NationalTeam("PAR", "Paraguay", "巴拉圭", 45, 1690.0, Confederation.CONMEBOL, 
                        wc_titles=0, wc_appearances=8, 
                        notes=""),
    "AUS": NationalTeam("AUS", "Australia", "澳大利亚", 35, 1720.0, Confederation.AFC, 
                        wc_titles=0, wc_appearances=6, 
                        notes="Moved from OFC to AFC 2006"),
    "TUR": NationalTeam("TUR", "Türkiye", "土耳其", 38, 1710.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=3, 
                        notes="Best result: 3rd place 2002"),

    # ===== Group E =====
    "GER": NationalTeam("GER", "Germany", "德国", 5, 1920.0, Confederation.UEFA, 
                        wc_titles=4, wc_appearances=21, 
                        notes="4x Champion (1954, 1974, 1990, 2014)"),
    "CUW": NationalTeam("CUW", "Curaçao", "库拉索", 90, 1350.0, Confederation.CONCACAF, 
                        is_debut=True, wc_titles=0, wc_appearances=0, 
                        notes="Debut"),
    "CIV": NationalTeam("CIV", "Ivory Coast", "科特迪瓦", 48, 1680.0, Confederation.CAF, 
                        wc_titles=0, wc_appearances=4, 
                        notes=""),
    "ECU": NationalTeam("ECU", "Ecuador", "厄瓜多尔", 32, 1730.0, Confederation.CONMEBOL, 
                        wc_titles=0, wc_appearances=4, 
                        notes=""),

    # ===== Group F =====
    "NED": NationalTeam("NED", "Netherlands", "荷兰", 10, 1840.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=12, 
                        notes="3x Runner-up (1974, 1978, 2010, 2022)"),
    "JPN": NationalTeam("JPN", "Japan", "日本", 18, 1780.0, Confederation.AFC, 
                        wc_titles=0, wc_appearances=8, 
                        notes="Round of 16 in 2002, 2010, 2018, 2022"),
    "SWE": NationalTeam("SWE", "Sweden", "瑞典", 38, 1710.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=13, 
                        notes="Best result: Runner-up 1958"),
    "TUN": NationalTeam("TUN", "Tunisia", "突尼斯", 52, 1650.0, Confederation.CAF, 
                        wc_titles=0, wc_appearances=7, 
                        notes=""),

    # ===== Group G =====
    "BEL": NationalTeam("BEL", "Belgium", "比利时", 4, 1920.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=15, 
                        notes="3rd place 2018"),
    "EGY": NationalTeam("EGY", "Egypt", "埃及", 36, 1720.0, Confederation.CAF, 
                        wc_titles=0, wc_appearances=4, 
                        notes=""),
    "IRN": NationalTeam("IRN", "Iran", "伊朗", 28, 1750.0, Confederation.AFC, 
                        wc_titles=0, wc_appearances=7, 
                        notes=""),
    "NZL": NationalTeam("NZL", "New Zealand", "新西兰", 85, 1400.0, Confederation.OFC, 
                        wc_titles=0, wc_appearances=3, 
                        notes="Unbeaten 2010 but 3 draws = exit"),

    # ===== Group H =====
    "ESP": NationalTeam("ESP", "Spain", "西班牙", 2, 1980.0, Confederation.UEFA, 
                        wc_titles=1, wc_appearances=17, 
                        notes="2010 Champion, Euro 2024 Champion"),
    "CPV": NationalTeam("CPV", "Cape Verde", "佛得角", 75, 1500.0, Confederation.CAF, 
                        is_debut=True, wc_titles=0, wc_appearances=0, 
                        notes="Debut"),
    "KSA": NationalTeam("KSA", "Saudi Arabia", "沙特阿拉伯", 55, 1620.0, Confederation.AFC, 
                        wc_titles=0, wc_appearances=7, 
                        notes=""),
    "URU": NationalTeam("URU", "Uruguay", "乌拉圭", 17, 1800.0, Confederation.CONMEBOL, 
                        wc_titles=2, wc_appearances=15, 
                        notes="2x Champion (1930, 1950)"),

    # ===== Group I =====
    "FRA": NationalTeam("FRA", "France", "法国", 1, 2000.0, Confederation.UEFA, 
                        wc_titles=2, wc_appearances=16, 
                        notes="2018 Champion, 2022 Runner-up"),
    "SEN": NationalTeam("SEN", "Senegal", "塞内加尔", 14, 1820.0, Confederation.CAF, 
                        wc_titles=0, wc_appearances=4, 
                        notes="Round of 16 2018, Quarter-final 2022"),
    "IRQ": NationalTeam("IRQ", "Iraq", "伊拉克", 65, 1580.0, Confederation.AFC, 
                        wc_titles=0, wc_appearances=2, 
                        notes="Intercontinental playoff winner"),
    "NOR": NationalTeam("NOR", "Norway", "挪威", 25, 1760.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=4, 
                        notes="Haaland's team"),

    # ===== Group J =====
    "ARG": NationalTeam("ARG", "Argentina", "阿根廷", 3, 1990.0, Confederation.CONMEBOL, 
                        wc_titles=3, wc_appearances=19, 
                        notes="Defending Champion (2022, 1978, 1986)"),
    "ALG": NationalTeam("ALG", "Algeria", "阿尔及利亚", 45, 1690.0, Confederation.CAF, 
                        wc_titles=0, wc_appearances=5, 
                        notes=""),
    "AUT": NationalTeam("AUT", "Austria", "奥地利", 28, 1750.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=8, 
                        notes="Best result: 3rd place 1954"),
    "JOR": NationalTeam("JOR", "Jordan", "约旦", 80, 1450.0, Confederation.AFC, 
                        is_debut=True, wc_titles=0, wc_appearances=0, 
                        notes="Debut"),

    # ===== Group K =====
    "POR": NationalTeam("POR", "Portugal", "葡萄牙", 9, 1850.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=9, 
                        notes="Euro 2016 Champion"),
    "COD": NationalTeam("COD", "Congo DR", "刚果民主共和国", 70, 1550.0, Confederation.CAF, 
                        wc_titles=0, wc_appearances=2, 
                        notes="Intercontinental playoff winner"),
    "UZB": NationalTeam("UZB", "Uzbekistan", "乌兹别克斯坦", 70, 1550.0, Confederation.AFC, 
                        is_debut=True, wc_titles=0, wc_appearances=0, 
                        notes="Debut"),
    "COL": NationalTeam("COL", "Colombia", "哥伦比亚", 13, 1830.0, Confederation.CONMEBOL, 
                        wc_titles=0, wc_appearances=7, 
                        notes="Quarter-final 2014"),

    # ===== Group L =====
    "ENG": NationalTeam("ENG", "England", "英格兰", 7, 1940.0, Confederation.UEFA, 
                        wc_titles=1, wc_appearances=17, 
                        notes="1966 Champion, Runner-up 2022"),
    "CRO": NationalTeam("CRO", "Croatia", "克罗地亚", 12, 1840.0, Confederation.UEFA, 
                        wc_titles=0, wc_appearances=7, 
                        notes="Runner-up 2018, 3rd place 2022"),
    "GHA": NationalTeam("GHA", "Ghana", "加纳", 58, 1600.0, Confederation.CAF, 
                        wc_titles=0, wc_appearances=5, 
                        notes="Quarter-final 2010"),
    "PAN": NationalTeam("PAN", "Panama", "巴拿马", 65, 1550.0, Confederation.CONCACAF, 
                        wc_titles=0, wc_appearances=2, 
                        notes=""),
}


# === 12 组配置 ===
GROUPS: Dict[str, List[str]] = {
    "A": ["MEX", "RSA", "KOR", "CZE"],
    "B": ["CAN", "BIH", "QAT", "SUI"],
    "C": ["BRA", "MAR", "HAI", "SCO"],
    "D": ["USA", "PAR", "AUS", "TUR"],
    "E": ["GER", "CUW", "CIV", "ECU"],
    "F": ["NED", "JPN", "SWE", "TUN"],
    "G": ["BEL", "EGY", "IRN", "NZL"],
    "H": ["ESP", "CPV", "KSA", "URU"],
    "I": ["FRA", "SEN", "IRQ", "NOR"],
    "J": ["ARG", "ALG", "AUT", "JOR"],
    "K": ["POR", "COD", "UZB", "COL"],
    "L": ["ENG", "CRO", "GHA", "PAN"],
}


# === 大洲系数 (用于 Elo 修正) ===
CONTINENTAL_COEFFICIENTS: Dict[Confederation, float] = {
    Confederation.UEFA: 1.00,      # 基准
    Confederation.CONMEBOL: 0.98,  # 南美接近欧洲
    Confederation.CAF: 0.90,       # 非洲
    Confederation.AFC: 0.88,       # 亚洲
    Confederation.CONCACAF: 0.85,  # 中北美
    Confederation.OFC: 0.80,       # 大洋洲
}


# === 东道主优势系数 ===
HOST_ADVANTAGE = 1.05  # 主场优势约 5% Elo 提升


# === 国家队 Elo 评级 vs 俱乐部差异系数 ===
# 国家队比赛强度系数 (相比俱乐部)
NATIONAL_TEAM_INTENSITY_FACTOR = 0.92  # 国家队磨合时间少，默契度低于俱乐部


# === 特殊因子配置 ===
WORLD_CUP_2026_FACTORS = {
    "altitude_factor": {           # 高原因素 (墨西哥城海拔 2240m)
        "Mexico City": 0.03,     # 高原球队优势 +3%
        "default": 0.0,
    },
    "climate_factor": {          # 气候因素
        "hot_humid": -0.02,      # 湿热环境 (墨西哥/美国南部)
        "mild": 0.0,             # 温和环境 (美国北部/加拿大)
        "hot_dry": 0.01,         # 干热环境 (美国西部)
    },
    "time_zone_factor": {        # 时差因素
        "Europe_to_NAmerica": -0.03,  # 欧洲球队跨大西洋时差
        "Asia_to_NAmerica": -0.04,   # 亚洲球队跨太平洋时差
        "SA_to_NAmerica": 0.0,        # 南美时差较小
        "local": 0.02,                # 东道主/北美球队优势
    },
}


# === 赛制参数 ===
FORMAT_2026 = {
    "total_teams": 48,
    "groups": 12,
    "teams_per_group": 4,
    "matches_per_group": 6,
    "group_matches_total": 72,
    "auto_advance": 2,           # 每组前 2 自动晋级
    "best_third_advance": 8,     # 8 个最好第三晋级
    "knockout_teams": 32,        # 32 强
    "round_of_32": True,         # 新增 32 强轮
    "total_matches": 104,        # 总比赛数
}


# === 晋级规则 ===
ADVANCEMENT_RULES = {
    "tiebreakers_third_place": [
        "points",
        "goal_difference",
        "goals_scored",
        "fair_play_points",
        "drawing_of_lots",
    ],
    "round_of_32_seeding": {
        "group_1st_2nd": "fixed_bracket",  # 24 队固定位置
        "third_place_teams": "predetermined_map",  # 8 第三按预定对阵表
    },
    "no_rematch_rule": True,  # Round of 32 不安排同组再遇
}


# === 实用函数 ===

def get_team(fifa_code: str) -> Optional[NationalTeam]:
    """通过 FIFA 代码获取国家队信息"""
    return TEAMS.get(fifa_code.upper())


def get_team_by_name(name: str) -> Optional[NationalTeam]:
    """通过英文或中文名获取国家队信息"""
    name = name.strip().lower()
    for team in TEAMS.values():
        if name == team.name_en.lower() or name == team.name_cn:
            return team
        # 模糊匹配
        if name in team.name_en.lower() or name in team.name_cn:
            return team
    return None


def get_group(group: str) -> List[NationalTeam]:
    """获取某组的所有球队信息"""
    group = group.upper()
    codes = GROUPS.get(group, [])
    return [TEAMS[code] for code in codes if code in TEAMS]


def get_all_teams() -> List[NationalTeam]:
    """获取所有 48 支球队"""
    return list(TEAMS.values())


def get_teams_by_confederation(conf: Confederation) -> List[NationalTeam]:
    """按联合会筛选球队"""
    return [t for t in TEAMS.values() if t.confederation == conf]


def get_teams_by_fifa_rank(min_rank: int = 1, max_rank: int = 100) -> List[NationalTeam]:
    """按 FIFA 排名范围筛选"""
    return [t for t in TEAMS.values() if min_rank <= t.fifa_rank <= max_rank]


def get_host_teams() -> List[NationalTeam]:
    """获取东道主球队"""
    return [t for t in TEAMS.values() if t.is_host]


def get_debut_teams() -> List[NationalTeam]:
    """获取首次参赛球队"""
    return [t for t in TEAMS.values() if t.is_debut]


def calculate_adjusted_elo(team: NationalTeam, venue: str = None, 
                            opponent_conf: Confederation = None) -> float:
    """
    计算修正后的 Elo 评级 (考虑东道主、大洲、气候等因素)
    """
    base_elo = team.elo_rating
    
    # 大洲系数调整
    conf_coeff = CONTINENTAL_COEFFICIENTS.get(team.confederation, 1.0)
    adjusted = base_elo * conf_coeff
    
    # 东道主加成
    if team.is_host:
        adjusted *= HOST_ADVANTAGE
    
    #  venue 高原加成 (如适用)
    if venue and "Mexico City" in venue:
        if team.fifa_code == "MEX":
            adjusted *= (1 + WORLD_CUP_2026_FACTORS["altitude_factor"]["Mexico City"])
    
    return adjusted


def print_team_summary():
    """打印球队摘要"""
    print("=" * 60)
    print("2026 FIFA World Cup - 48 Teams Summary")
    print("=" * 60)
    
    for group, codes in GROUPS.items():
        print(f"\nGroup {group}:")
        for code in codes:
            team = TEAMS[code]
            host = " [HOST]" if team.is_host else ""
            debut = " [DEBUT]" if team.is_debut else ""
            print(f"  {code:3s} - {team.name_en:25s} "
                  f"FIFA#{team.fifa_rank:2d} Elo={team.elo_rating:.0f}{host}{debut}")
    
    print("\n" + "=" * 60)
    print(f"Total: {len(TEAMS)} teams | {len(GROUPS)} groups | "
          f"Hosts: {len(get_host_teams())} | Debutants: {len(get_debut_teams())}")
    print("=" * 60)


if __name__ == "__main__":
    print_team_summary()
