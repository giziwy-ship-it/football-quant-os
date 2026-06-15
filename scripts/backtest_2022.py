#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2022 FIFA World Cup Backtest
Football Quant OS - World Cup Module

使用真实2022世界杯数据回测模型预测能力
数据来源：FIFA官方记录
"""

import sys
import os
import json
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from core.worldcup_integrator import NationalTeamEvaluator


# 2022 球队 FIFA 排名映射 (用于 Elo 近似)
TEAM_ELO_2022 = {
    "BRA": 1980, "BEL": 1960, "ARG": 1950, "FRA": 1930, "ENG": 1900, "ESP": 1880,
    "NED": 1870, "POR": 1860, "GER": 1840, "URU": 1820, "CRO": 1800, "DEN": 1790,
    "MEX": 1760, "SUI": 1750, "USA": 1740, "SEN": 1730, "WAL": 1720, "IRN": 1700,
    "SRB": 1690, "MAR": 1680, "JPN": 1670, "POL": 1660, "KOR": 1650, "TUN": 1630,
    "AUS": 1620, "CAN": 1600, "CMR": 1580, "ECU": 1570, "KSA": 1560, "QAT": 1550,
    "GHA": 1540, "CRC": 1530,
}

TEAM_NAMES = {
    "QAT": "Qatar", "ECU": "Ecuador", "SEN": "Senegal", "NED": "Netherlands",
    "ENG": "England", "IRN": "Iran", "USA": "USA", "WAL": "Wales",
    "ARG": "Argentina", "KSA": "Saudi Arabia", "MEX": "Mexico", "POL": "Poland",
    "FRA": "France", "AUS": "Australia", "DEN": "Denmark", "TUN": "Tunisia",
    "ESP": "Spain", "CRC": "Costa Rica", "GER": "Germany", "JPN": "Japan",
    "BEL": "Belgium", "CAN": "Canada", "MAR": "Morocco", "CRO": "Croatia",
    "BRA": "Brazil", "SRB": "Serbia", "SUI": "Switzerland", "CMR": "Cameroon",
    "POR": "Portugal", "GHA": "Ghana", "URU": "Uruguay", "KOR": "South Korea",
}


class MatchOutcome(Enum):
    HOME_WIN = "home_win"
    DRAW = "draw"
    AWAY_WIN = "away_win"


@dataclass
class MatchRecord:
    """单场比赛记录"""
    match_id: str
    group: str
    date: str
    home: str
    away: str
    home_score: int
    away_score: int
    home_pen: int = 0  # 点球
    away_pen: int = 0
    
    @property
    def outcome(self) -> MatchOutcome:
        if self.home_score > self.away_score:
            return MatchOutcome.HOME_WIN
        elif self.home_score < self.away_score:
            return MatchOutcome.AWAY_WIN
        else:
            return MatchOutcome.DRAW
    
    @property
    def is_draw(self) -> bool:
        return self.home_score == self.away_score


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, data_path: str = None):
        self.data_path = data_path or os.path.join(
            os.path.dirname(__file__), "data", "worldcup2022_data.json"
        )
        self.matches: List[MatchRecord] = []
        self.evaluator = NationalTeamEvaluator()
        # Override 2022 Elo ratings
        self.evaluator.teams = []
        
        self.results = {
            "total": 0,
            "correct_direction": 0,  # 正确预测胜负方向（非平局）
            "correct_exact": 0,      # 正确预测具体结果（胜负平）
            "draws_predicted": 0,    # 预测平局数
            "draws_actual": 0,       # 实际平局数
            "upsets": 0,             # 爆冷场次
            "upsets_correct": 0,     # 预测到爆冷
            "favorites_won": 0,      # 热门获胜
            "favorites_lost": 0,     # 热门失利
            "by_group": {},
            "by_stage": {
                "group": {"total": 0, "correct": 0, "upsets": 0},
                "round_of_16": {"total": 0, "correct": 0, "upsets": 0},
                "quarterfinals": {"total": 0, "correct": 0, "upsets": 0},
                "semifinals": {"total": 0, "correct": 0, "upsets": 0},
                "third_place": {"total": 0, "correct": 0, "upsets": 0},
                "final": {"total": 0, "correct": 0, "upsets": 0},
            },
            "upset_details": [],
            "match_details": [],
        }
    
    def load_data(self):
        """加载2022数据"""
        with open(self.data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 小组赛
        for m in data.get("group_stage", []):
            self.matches.append(MatchRecord(
                m["match_id"], m["group"], m["date"],
                m["home"], m["away"], m["home_score"], m["away_score"]
            ))
        
        # 淘汰赛
        for stage, matches in data.get("knockout", {}).items():
            if stage == "final":
                m = matches
                self.matches.append(MatchRecord(
                    m["match_id"], "F", m["date"], m["home"], m["away"],
                    m["home_score"], m["away_score"], m.get("home_pen", 0), m.get("away_pen", 0)
                ))
            elif stage == "third_place":
                m = matches
                self.matches.append(MatchRecord(
                    m["match_id"], "3P", m["date"], m["home"], m["away"],
                    m["home_score"], m["away_score"]
                ))
            else:
                for m in matches:
                    self.matches.append(MatchRecord(
                        m["match_id"], stage[:3].upper(), m["date"],
                        m["home"], m["away"], m["home_score"], m["away_score"],
                        m.get("home_pen", 0), m.get("away_pen", 0)
                    ))
        
        print(f"Loaded {len(self.matches)} matches from 2022 World Cup")
    
    def predict_match(self, home: str, away: str) -> Dict[str, Any]:
        """用Elo模型预测单场比赛"""
        # 使用2022 Elo近似
        home_elo = TEAM_ELO_2022.get(home, 1600)
        away_elo = TEAM_ELO_2022.get(away, 1600)
        
        # 世界杯中性场地，无主场优势
        elo_diff = home_elo - away_elo
        prob_home = 1 / (1 + 10 ** (-elo_diff / 400))
        prob_away = 1 - prob_home
        
        # 平局概率（根据实力差距）
        draw_prob = 0.25 - abs(prob_home - 0.5) * 0.2
        draw_prob = max(0.15, min(0.30, draw_prob))
        
        # 归一化
        total = prob_home + draw_prob + prob_away
        
        return {
            "home": prob_home / total,
            "draw": draw_prob / total,
            "away": prob_away / total,
            "home_elo": home_elo,
            "away_elo": away_elo,
            "elo_diff": elo_diff,
        }
    
    def get_predicted_outcome(self, probs: Dict[str, float]) -> MatchOutcome:
        """从概率预测结果"""
        home = probs["home"]
        draw = probs["draw"]
        away = probs["away"]
        
        if home > draw and home > away:
            return MatchOutcome.HOME_WIN
        elif away > draw and away > home:
            return MatchOutcome.AWAY_WIN
        else:
            return MatchOutcome.DRAW
    
    def is_upset(self, match: MatchRecord, probs: Dict[str, float]) -> Tuple[bool, str]:
        """判断是否爆冷"""
        actual = match.outcome
        
        # 确定热门方
        if probs["home"] > probs["away"]:
            favorite = "home"
            fav_prob = probs["home"]
            underdog = "away"
        else:
            favorite = "away"
            fav_prob = probs["away"]
            underdog = "home"
        
        # 热门概率 > 60% 且失利 = 爆冷
        if fav_prob > 0.55:
            if favorite == "home" and actual == MatchOutcome.AWAY_WIN:
                return True, f"{match.home} ({fav_prob:.1%}) lost to {match.away}"
            elif favorite == "away" and actual == MatchOutcome.HOME_WIN:
                return True, f"{match.away} ({fav_prob:.1%}) lost to {match.home}"
        
        return False, ""
    
    def get_stage(self, match: MatchRecord) -> str:
        """判断比赛阶段"""
        if match.group in "ABCDEFGH":
            return "group"
        elif match.group in ["R16", "R16-1", "R16-2", "R16-3", "R16-4", "R16-5", "R16-6", "R16-7", "R16-8"]:
            return "round_of_16"
        elif match.group in ["QF", "QF-1", "QF-2", "QF-3", "QF-4"]:
            return "quarterfinals"
        elif match.group in ["SF", "SF-1", "SF-2"]:
            return "semifinals"
        elif match.group == "F":
            return "final"
        elif match.group == "3P":
            return "third_place"
        return "group"
    
    def run_backtest(self):
        """执行回测"""
        print("\n" + "=" * 60)
        print("2022 FIFA World Cup - Backtest Running")
        print("=" * 60)
        
        for match in self.matches:
            probs = self.predict_match(match.home, match.away)
            predicted = self.get_predicted_outcome(probs)
            actual = match.outcome
            
            # 统计
            self.results["total"] += 1
            stage = self.get_stage(match)
            self.results["by_stage"][stage]["total"] += 1
            
            # 预测胜负方向（非平局）
            if predicted == actual:
                self.results["correct_exact"] += 1
                self.results["by_stage"][stage]["correct"] += 1
            
            # 方向正确（忽略平局）
            if actual != MatchOutcome.DRAW:
                if (predicted == MatchOutcome.HOME_WIN and actual == MatchOutcome.HOME_WIN) or \
                   (predicted == MatchOutcome.AWAY_WIN and actual == MatchOutcome.AWAY_WIN):
                    self.results["correct_direction"] += 1
            
            # 平局统计
            if actual == MatchOutcome.DRAW:
                self.results["draws_actual"] += 1
            if predicted == MatchOutcome.DRAW:
                self.results["draws_predicted"] += 1
            
            # 爆冷检测
            is_upset, upset_reason = self.is_upset(match, probs)
            if is_upset:
                self.results["upsets"] += 1
                self.results["upset_details"].append({
                    "match_id": match.match_id,
                    "home": match.home,
                    "away": match.away,
                    "score": f"{match.home_score}-{match.away_score}",
                    "reason": upset_reason,
                    "prob_home": probs["home"],
                    "prob_away": probs["away"],
                })
                self.results["by_stage"][stage]["upsets"] += 1
            
            # 热门统计
            if probs["home"] > 0.55 or probs["away"] > 0.55:
                if predicted == actual:
                    self.results["favorites_won"] += 1
                else:
                    self.results["favorites_lost"] += 1
            
            # 详细记录
            self.results["match_details"].append({
                "match_id": match.match_id,
                "home": match.home,
                "away": match.away,
                "score": f"{match.home_score}-{match.away_score}",
                "prob_home": probs["home"],
                "prob_draw": probs["draw"],
                "prob_away": probs["away"],
                "predicted": predicted.value,
                "actual": actual.value,
                "correct": predicted == actual,
                "elo_diff": probs["elo_diff"],
            })
    
    def print_report(self):
        """打印回测报告"""
        r = self.results
        total = r["total"]
        
        print("\n" + "=" * 60)
        print("2022 FIFA World Cup - Backtest Report")
        print("=" * 60)
        
        print(f"\nTotal Matches: {total}")
        print(f"Correct Predictions (Exact): {r['correct_exact']}/{total} ({r['correct_exact']/total*100:.1f}%)")
        print(f"Correct Direction (Win/Loss): {r['correct_direction']}/{total - r['draws_actual']} ({r['correct_direction']/(total - r['draws_actual'])*100:.1f}%)")
        print(f"Draws Predicted: {r['draws_predicted']}, Actual: {r['draws_actual']}")
        
        print(f"\nUpsets: {r['upsets']} ({r['upsets']/total*100:.1f}%)")
        print(f"Favorites Won: {r['favorites_won']}, Favorites Lost: {r['favorites_lost']}")
        if r['favorites_won'] + r['favorites_lost'] > 0:
            fav_rate = r['favorites_won'] / (r['favorites_won'] + r['favorites_lost'])
            print(f"Favorite Win Rate: {fav_rate*100:.1f}%")
        
        print(f"\nBy Stage:")
        for stage, stats in r["by_stage"].items():
            if stats["total"] > 0:
                acc = stats["correct"] / stats["total"] * 100
                print(f"  {stage:15s}: {stats['correct']:2d}/{stats['total']:2d} ({acc:5.1f}%) | Upsets: {stats['upsets']}")
        
        print(f"\nTop 5 Upsets (Biggest Surprises):")
        sorted_upsets = sorted(r["upset_details"], 
                               key=lambda x: max(x["prob_home"], x["prob_away"]), 
                               reverse=True)[:5]
        for u in sorted_upsets:
            fav_prob = max(u["prob_home"], u["prob_away"])
            print(f"  {u['home']} vs {u['away']:10s}: {u['score']:5s} | "
                  f"Favorite prob: {fav_prob:.1%} | {u['reason']}")
        
        print(f"\nTop 5 Correct Predictions (High Confidence):")
        correct_matches = [m for m in r["match_details"] if m["correct"]]
        sorted_correct = sorted(correct_matches, 
                                key=lambda x: max(x["prob_home"], x["prob_away"]), 
                                reverse=True)[:5]
        for m in sorted_correct:
            fav_prob = max(m["prob_home"], m["prob_away"])
            print(f"  {m['home']} vs {m['away']:10s}: {m['score']:5s} | "
                  f"Confidence: {fav_prob:.1%}")
        
        print(f"\nWorst 5 Misses (High Confidence Wrong):")
        wrong_matches = [m for m in r["match_details"] if not m["correct"]]
        sorted_wrong = sorted(wrong_matches, 
                             key=lambda x: max(x["prob_home"], x["prob_away"]), 
                             reverse=True)[:5]
        for m in sorted_wrong:
            fav_prob = max(m["prob_home"], m["prob_away"])
            print(f"  {m['home']} vs {m['away']:10s}: {m['score']:5s} | "
                  f"Predicted: {m['predicted']}, Actual: {m['actual']}, Confidence: {fav_prob:.1%}")
        
        print("\n" + "=" * 60)
        print("Backtest Complete")
        print("=" * 60)
    
    def export_results(self, filepath: str = None):
        """导出详细结果到JSON"""
        if not filepath:
            filepath = os.path.join(os.path.dirname(__file__), 
                                   "data", "backtest_2022_results.json")
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        print(f"\nResults exported to: {filepath}")


def main():
    engine = BacktestEngine()
    engine.load_data()
    engine.run_backtest()
    engine.print_report()
    engine.export_results()


if __name__ == "__main__":
    main()
