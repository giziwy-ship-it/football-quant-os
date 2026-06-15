#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenFootball 数据集成脚本
P2 优先级：开源结构化数据
GitHub: https://github.com/openfootball
"""
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess


class OpenFootball:
    """OpenFootball 数据接口"""
    
    GITHUB_REPO = "https://github.com/openfootball/worldcup.git"
    
    def __init__(self, data_dir: str = "data/openfootball"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_data()
    
    def _ensure_data(self):
        """确保数据已下载"""
        worldcup_dir = self.data_dir / "worldcup"
        
        if not worldcup_dir.exists():
            print("[下载] 克隆 OpenFootball 数据...")
            try:
                subprocess.run([
                    "git", "clone", self.GITHUB_REPO, str(worldcup_dir)
                ], check=True, capture_output=True)
                print(f"[成功] 数据已克隆到: {worldcup_dir}")
            except subprocess.CalledProcessError as e:
                print(f"[失败] {e}")
            except FileNotFoundError:
                print("[失败] 找不到 git 命令")
    
    def load_tournament(self, year: str = "2022") -> Optional[Dict]:
        """
        加载指定年份的世界杯数据
        
        Returns:
            {
                "name": "FIFA World Cup 2022",
                "groups": {"a": [...], "b": [...]},
                "knockout": {"round_of_16": [...], "quarter_finals": [...]}
            }
        """
        worldcup_dir = self.data_dir / "worldcup"
        if not worldcup_dir.exists():
            print("[错误] 数据未下载")
            return None
        
        # 查找 YAML 文件
        yml_file = worldcup_dir / year / "cup.yml"
        if not yml_file.exists():
            # 尝试其他格式
            yml_file = worldcup_dir / f"{year}.yml"
        
        if not yml_file.exists():
            print(f"[错误] 找不到 {year} 的数据文件")
            return None
        
        try:
            with open(yml_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data
        except Exception as e:
            print(f"[错误] 解析 YAML 失败: {e}")
            return None
    
    def get_group_matches(self, year: str = "2022", group: str = "a") -> List[Dict]:
        """获取小组赛比赛"""
        data = self.load_tournament(year)
        if not data:
            return []
        
        groups = data.get("groups", {})
        group_matches = groups.get(group, [])
        
        matches = []
        for match in group_matches:
            if isinstance(match, list) and len(match) >= 4:
                matches.append({
                    "home": match[0],
                    "home_goals": match[1],
                    "away_goals": match[2],
                    "away": match[3]
                })
        
        return matches
    
    def get_knockout_matches(self, year: str = "2022", round_name: str = "round_of_16") -> List[Dict]:
        """获取淘汰赛比赛"""
        data = self.load_tournament(year)
        if not data:
            return []
        
        knockout = data.get("knockout", {})
        round_matches = knockout.get(round_name, [])
        
        matches = []
        for match in round_matches:
            if isinstance(match, dict):
                matches.append({
                    "home": match.get("home", "TBD"),
                    "away": match.get("away", "TBD"),
                    "home_goals": match.get("home_goals", None),
                    "away_goals": match.get("away_goals", None),
                    "winner": match.get("winner", None)
                })
        
        return matches
    
    def calculate_group_standings(self, year: str = "2022", group: str = "a") -> List[Dict]:
        """计算小组积分榜"""
        matches = self.get_group_matches(year, group)
        
        standings = {}
        for match in matches:
            home = match["home"]
            away = match["away"]
            home_goals = match["home_goals"]
            away_goals = match["away_goals"]
            
            # 初始化
            for team in [home, away]:
                if team not in standings:
                    standings[team] = {
                        "team": team,
                        "played": 0, "won": 0, "drawn": 0, "lost": 0,
                        "goals_for": 0, "goals_against": 0, "points": 0
                    }
            
            # 更新统计
            standings[home]["played"] += 1
            standings[away]["played"] += 1
            standings[home]["goals_for"] += home_goals
            standings[home]["goals_against"] += away_goals
            standings[away]["goals_for"] += away_goals
            standings[away]["goals_against"] += home_goals
            
            if home_goals > away_goals:
                standings[home]["won"] += 1
                standings[home]["points"] += 3
                standings[away]["lost"] += 1
            elif home_goals < away_goals:
                standings[away]["won"] += 1
                standings[away]["points"] += 3
                standings[home]["lost"] += 1
            else:
                standings[home]["drawn"] += 1
                standings[away]["drawn"] += 1
                standings[home]["points"] += 1
                standings[away]["points"] += 1
        
        # 排序
        sorted_standings = sorted(
            standings.values(),
            key=lambda x: (x["points"], x["goals_for"] - x["goals_against"]),
            reverse=True
        )
        
        return sorted_standings


def main():
    """示例：查看2022世界杯小组赛A组"""
    of = OpenFootball()
    
    # 获取A组比赛
    matches = of.get_group_matches("2022", "a")
    print("2022世界杯 A组比赛:")
    for match in matches:
        print(f"  {match['home']} {match['home_goals']}-{match['away_goals']} {match['away']}")
    
    # 计算积分榜
    standings = of.calculate_group_standings("2022", "a")
    print("\nA组积分榜:")
    for i, team in enumerate(standings, 1):
        gd = team["goals_for"] - team["goals_against"]
        print(f"  {i}. {team['team']:15} {team['points']}分 {team['won']}-{team['drawn']}-{team['lost']} 净胜球{gd:+d}")


if __name__ == "__main__":
    main()
