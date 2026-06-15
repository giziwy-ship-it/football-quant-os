#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 FIFA World Cup Format Adapter
Football Quant OS World Cup Module

适配 12 组 × 4 队 → 32 强的新赛制
"""

from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.worldcup2026_data import (
    NationalTeam, TEAMS, GROUPS, FORMAT_2026, 
    ADVANCEMENT_RULES, get_team, get_group
)


class MatchStatus(Enum):
    """比赛状态"""
    SCHEDULED = "scheduled"
    LIVE = "live"
    FINISHED = "finished"
    POSTPONED = "postponed"


@dataclass
class MatchResult:
    """单场比赛结果"""
    home_team: str           # FIFA 代码
    away_team: str
    home_score: int = 0
    away_score: int = 0
    status: MatchStatus = MatchStatus.SCHEDULED
    match_date: str = ""
    venue: str = ""
    
    # 衍生数据
    home_points: int = field(init=False)
    away_points: int = field(init=False)
    
    def __post_init__(self):
        if self.status == MatchStatus.FINISHED:
            if self.home_score > self.away_score:
                self.home_points = 3
                self.away_points = 0
            elif self.home_score < self.away_score:
                self.home_points = 0
                self.away_points = 3
            else:
                self.home_points = 1
                self.away_points = 1
        else:
            self.home_points = 0
            self.away_points = 0


@dataclass
class GroupStandings:
    """小组积分榜"""
    team_code: str
    played: int = 0
    wins: int = 0
    draws: int = 0
    losses: int = 0
    goals_for: int = 0
    goals_against: int = 0
    points: int = 0
    
    @property
    def goal_difference(self) -> int:
        return self.goals_for - self.goals_against
    
    @property
    def position(self) -> int:
        """由外部计算后填充"""
        return 0


class WorldCup2026Format:
    """
    2026 世界杯 48 队赛制适配器
    
    核心功能：
    1. 12 组小组赛管理 (每队 3 场)
    2. 8 个最好第三晋级计算
    3. 32 强对阵表生成
    4. 淘汰赛阶段管理
    """
    
    def __init__(self):
        self.total_teams = FORMAT_2026["total_teams"]          # 48
        self.num_groups = FORMAT_2026["groups"]                 # 12
        self.teams_per_group = FORMAT_2026["teams_per_group"]  # 4
        self.auto_advance = FORMAT_2026["auto_advance"]        # 2
        self.best_third_advance = FORMAT_2026["best_third_advance"]  # 8
        self.knockout_teams = FORMAT_2026["knockout_teams"]    # 32
        
        # 比赛数据存储
        self.group_matches: Dict[str, List[MatchResult]] = {}  # group -> matches
        self.knockout_matches: Dict[str, List[MatchResult]] = {}  # round -> matches
        
        # 初始化小组赛空数据结构
        for group in GROUPS.keys():
            self.group_matches[group] = []
    
    def get_group_fixtures(self, group: str) -> List[Tuple[str, str]]:
        """
        生成某组的 6 场比赛对阵
        
        4 队单循环：C(4,2) = 6 场
        对阵顺序：保证最后一轮同时开球
        """
        teams = GROUPS.get(group.upper(), [])
        if len(teams) != 4:
            raise ValueError(f"Group {group} must have exactly 4 teams")
        
        # 标准 4 队单循环赛程
        # Round 1: A vs B, C vs D
        # Round 2: A vs C, B vs D
        # Round 3: A vs D, B vs C
        fixtures = [
            (teams[0], teams[1]),  # Match 1
            (teams[2], teams[3]),  # Match 2
            (teams[0], teams[2]),  # Match 3
            (teams[1], teams[3]),  # Match 4
            (teams[0], teams[3]),  # Match 5
            (teams[1], teams[2]),  # Match 6
        ]
        return fixtures
    
    def add_match_result(self, group: str, match: MatchResult):
        """添加比赛结果"""
        group = group.upper()
        if group not in self.group_matches:
            self.group_matches[group] = []
        self.group_matches[group].append(match)
    
    def calculate_group_standings(self, group: str) -> List[GroupStandings]:
        """计算某组积分榜"""
        group = group.upper()
        teams = GROUPS.get(group, [])
        
        # 初始化
        standings = {code: GroupStandings(code) for code in teams}
        
        # 汇总比赛结果
        for match in self.group_matches.get(group, []):
            if match.status != MatchStatus.FINISHED:
                continue
            
            home = standings[match.home_team]
            away = standings[match.away_team]
            
            home.played += 1
            away.played += 1
            home.goals_for += match.home_score
            home.goals_against += match.away_score
            away.goals_for += match.away_score
            away.goals_against += match.home_score
            home.points += match.home_points
            away.points += match.away_points
            
            if match.home_points == 3:
                home.wins += 1
                away.losses += 1
            elif match.away_points == 3:
                away.wins += 1
                home.losses += 1
            else:
                home.draws += 1
                away.draws += 1
        
        # 排序：积分 → 净胜球 → 进球数
        sorted_standings = sorted(
            standings.values(),
            key=lambda x: (x.points, x.goal_difference, x.goals_for),
            reverse=True
        )
        
        return sorted_standings
    
    def get_all_group_standings(self) -> Dict[str, List[GroupStandings]]:
        """获取所有 12 组积分榜"""
        return {group: self.calculate_group_standings(group) 
                for group in GROUPS.keys()}
    
    def calculate_best_third_placed(self) -> List[GroupStandings]:
        """
        计算 8 个最好的第三晋级球队
        
        从 12 个小组第三中选取 8 个最好的
        排序：积分 → 净胜球 → 进球数 → 公平竞赛分
        """
        all_standings = self.get_all_group_standings()
        
        third_placed = []
        for group, standings in all_standings.items():
            if len(standings) >= 3:
                third = standings[2]  # 第三名 (index 2)
                third_placed.append(third)
        
        # 排序选取前 8
        third_placed.sort(
            key=lambda x: (x.points, x.goal_difference, x.goals_for),
            reverse=True
        )
        
        return third_placed[:8]  # 取前 8
    
    def get_advancement_teams(self) -> Dict[str, List[str]]:
        """
        获取所有晋级 32 强的球队
        
        Returns:
            {
                "group_1st": [...],      # 12 组第一
                "group_2nd": [...],      # 12 组第二
                "best_3rd": [...],        # 8 个最好第三
                "knockout_32": [...],     # 全部 32 强
            }
        """
        all_standings = self.get_all_group_standings()
        
        group_1st = []
        group_2nd = []
        
        for group, standings in all_standings.items():
            if len(standings) >= 1:
                group_1st.append(standings[0].team_code)
            if len(standings) >= 2:
                group_2nd.append(standings[1].team_code)
        
        best_3rd = [t.team_code for t in self.calculate_best_third_placed()]
        
        knockout_32 = group_1st + group_2nd + best_3rd
        
        return {
            "group_1st": group_1st,
            "group_2nd": group_2nd,
            "best_3rd": best_3rd,
            "knockout_32": knockout_32,
        }
    
    def generate_knockout_bracket(self) -> List[Tuple[str, str, str]]:
        """
        生成 Round of 32 对阵表
        
        32 强对阵表结构 (基于 FIFA 官方对阵图):
        - 24 个小组前 2 名固定位置
        - 8 个第三根据预定对阵表填入
        
        Returns:
            [(match_id, team_A, team_B), ...]
        """
        advancement = self.get_advancement_teams()
        
        # 这里需要根据 FIFA 官方对阵表实现
        # 简化版：先返回占位符
        # 实际实现需要参考 FIFA 官方 bracket map
        
        bracket = []
        # Round of 32: 16 场比赛
        # Match 1: 1A vs 3C/3D/3E/3F (之一)
        # ...
        
        # TODO: 实现完整对阵表
        return bracket
    
    def print_group_standings(self, group: str):
        """打印某组积分榜"""
        group = group.upper()
        standings = self.calculate_group_standings(group)
        
        print(f"\n{'='*50}")
        print(f"Group {group} Standings")
        print(f"{'='*50}")
        print(f"{'Pos':<4} {'Team':<8} {'P':<3} {'W':<3} {'D':<3} {'L':<3} "
              f"{'GF':<3} {'GA':<3} {'GD':<4} {'Pts':<4}")
        print("-"*50)
        
        for i, s in enumerate(standings, 1):
            team = get_team(s.team_code)
            name = team.name_en if team else s.team_code
            name = name.encode('ascii', 'replace').decode('ascii')
            advance = " [Q]" if i <= 2 else ""
            print(f"{i:<4} {name:<20} {s.played:<3} {s.wins:<3} {s.draws:<3} "
                  f"{s.losses:<3} {s.goals_for:<3} {s.goals_against:<3} "
                  f"{s.goal_difference:+3d} {s.points:<4}{advance}")
        
        # 标注第三是否有机会
        if len(standings) >= 3:
            print(f"\n* 3rd place: {standings[2].team_code} "
                  f"(Pts={standings[2].points}, GD={standings[2].goal_difference})")
    
    def print_all_standings(self):
        """打印所有组积分榜"""
        for group in sorted(GROUPS.keys()):
            self.print_group_standings(group)
        
        # 打印第三晋级预测
        best_third = self.calculate_best_third_placed()
        print(f"\n{'='*50}")
        print("8 Best 3rd-Place Teams (Predicted)")
        print(f"{'='*50}")
        for i, t in enumerate(best_third, 1):
            team = get_team(t.team_code)
            name = team.name_cn if team else t.team_code
            print(f"{i:2d}. {name:<8} (Pts={t.points}, GD={t.goal_difference})")
    
    def print_tournament_info(self):
        """打印锦标赛信息"""
        print(f"\n{'='*60}")
        print("2026 FIFA World Cup - Format Information")
        print(f"{'='*60}")
        print(f"Total Teams:       {self.total_teams}")
        print(f"Groups:            {self.num_groups}")
        print(f"Teams per Group:   {self.teams_per_group}")
        print(f"Group Matches:     {FORMAT_2026['group_matches_total']}")
        print(f"Auto Advance:      Top {self.auto_advance} per group")
        print(f"Best 3rd Advance:  {self.best_third_advance} teams")
        print(f"Knockout Teams:    {self.knockout_teams}")
        print(f"Total Matches:     {FORMAT_2026['total_matches']}")
        print(f"{'='*60}")
        
        # 大洲分布
        from data.worldcup2026_data import Confederation
        conf_count = {}
        for team in TEAMS.values():
            conf = team.confederation.value
            conf_count[conf] = conf_count.get(conf, 0) + 1
        
        print("\nConfederation Distribution:")
        for conf, count in sorted(conf_count.items()):
            print(f"  {conf}: {count} teams")
        
        print(f"\nHost Teams:  {len([t for t in TEAMS.values() if t.is_host])}")
        print(f"Debutants:   {len([t for t in TEAMS.values() if t.is_debut])}")
        print(f"Champions:   {len([t for t in TEAMS.values() if t.wc_titles > 0])}")


def main():
    """测试运行"""
    wc = WorldCup2026Format()
    wc.print_tournament_info()
    
    # 演示：添加模拟比赛结果
    print("\n[Demo] Simulated Group C Results:")
    
    # 模拟 Group C 结果
    wc.add_match_result("C", MatchResult("BRA", "SCO", 3, 1, MatchStatus.FINISHED, "Jun 14"))
    wc.add_match_result("C", MatchResult("MAR", "HAI", 2, 0, MatchStatus.FINISHED, "Jun 14"))
    wc.add_match_result("C", MatchResult("BRA", "MAR", 2, 1, MatchStatus.FINISHED, "Jun 20"))
    wc.add_match_result("C", MatchResult("SCO", "HAI", 1, 1, MatchStatus.FINISHED, "Jun 20"))
    wc.add_match_result("C", MatchResult("BRA", "HAI", 4, 0, MatchStatus.FINISHED, "Jun 26"))
    wc.add_match_result("C", MatchResult("MAR", "SCO", 1, 0, MatchStatus.FINISHED, "Jun 26"))
    
    wc.print_group_standings("C")
    
    # 模拟更多组
    print("\n[Demo] Simulated Best 3rd-Place Calculation:")
    # Group A 模拟
    wc.add_match_result("A", MatchResult("MEX", "RSA", 2, 0, MatchStatus.FINISHED, "Jun 11"))
    wc.add_match_result("A", MatchResult("KOR", "CZE", 1, 1, MatchStatus.FINISHED, "Jun 11"))
    wc.add_match_result("A", MatchResult("MEX", "KOR", 1, 1, MatchStatus.FINISHED, "Jun 18"))
    wc.add_match_result("A", MatchResult("CZE", "RSA", 2, 1, MatchStatus.FINISHED, "Jun 18"))
    wc.add_match_result("A", MatchResult("MEX", "CZE", 2, 0, MatchStatus.FINISHED, "Jun 24"))
    wc.add_match_result("A", MatchResult("RSA", "KOR", 0, 2, MatchStatus.FINISHED, "Jun 24"))
    
    # Group B 模拟
    wc.add_match_result("B", MatchResult("CAN", "QAT", 1, 0, MatchStatus.FINISHED, "Jun 12"))
    wc.add_match_result("B", MatchResult("BIH", "SUI", 0, 2, MatchStatus.FINISHED, "Jun 12"))
    wc.add_match_result("B", MatchResult("CAN", "BIH", 1, 1, MatchStatus.FINISHED, "Jun 18"))
    wc.add_match_result("B", MatchResult("SUI", "QAT", 2, 0, MatchStatus.FINISHED, "Jun 18"))
    wc.add_match_result("B", MatchResult("CAN", "SUI", 0, 1, MatchStatus.FINISHED, "Jun 24"))
    wc.add_match_result("B", MatchResult("QAT", "BIH", 1, 1, MatchStatus.FINISHED, "Jun 24"))
    
    wc.print_all_standings()


if __name__ == "__main__":
    main()
