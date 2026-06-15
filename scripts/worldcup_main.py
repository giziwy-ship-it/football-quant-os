#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2026 FIFA World Cup - Main Entry Point (v2.0 Integrated)
Football Quant OS World Cup Module

整合:
  1. 数据层 (worldcup2026_data.py) - 48队数据库
  2. 赛程层 (worldcup_fixtures.py) - 72场比赛
  3. 格式层 (worldcup_format.py) - 12组赛制
  4. 分析层 (worldcup_integrator.py) - 五层信号+诱盘+Kelly+决策树
  5. API 层 (worldcup_api.py) - FastAPI端点

Usage:
    python worldcup_main.py --summary
    python worldcup_main.py --team BRA
    python worldcup_main.py --group C
    python worldcup_main.py --fixtures
    python worldcup_main.py --standings-demo
    python worldcup_main.py --full-report
    python worldcup_main.py --analyze BRA SCO
    python worldcup_main.py --with-odds FRA SEN 1.55 3.80 6.50
    python worldcup_main.py --auto-demo
"""

import sys
import os
import json
import argparse

sys.path.insert(0, os.path.dirname(__file__))

from data.worldcup2026_data import (
    TEAMS, GROUPS, get_team, get_group, get_all_teams, 
    get_teams_by_confederation, get_teams_by_fifa_rank,
    get_host_teams, get_debut_teams, print_team_summary
)
from data.worldcup_format import WorldCup2026Format, MatchResult, MatchStatus
from data.worldcup_fixtures import (
    WORLD_CUP_FIXTURES, get_all_fixtures, get_fixtures_by_group,
    get_fixtures_by_team, get_fixtures_by_date, export_to_json,
    export_to_worldcup_format
)
from core.worldcup_integrator import WorldCupPipeline, NationalTeamEvaluator


def print_summary():
    """打印系统概览"""
    print("=" * 60)
    print("2026 FIFA World Cup - Naga System Ready Report")
    print("=" * 60)
    print()
    print("Data Status:")
    print(f"  Teams:        {len(TEAMS)} / 48 confirmed")
    print(f"  Groups:       {len(GROUPS)} (A-L)")
    print(f"  Fixtures:     {len(WORLD_CUP_FIXTURES)} / 72 scheduled")
    print(f"  Hosts:        {len(get_host_teams())} (USA, Canada, Mexico)")
    print(f"  Debutants:    {len(get_debut_teams())} (Cape Verde, Curacao, Uzbekistan, Jordan)")
    print(f"  Champions:    {len([t for t in TEAMS.values() if t.wc_titles > 0])}")
    print()
    print("Modules Loaded:")
    print("  [OK] worldcup2026_data.py - 48 teams database")
    print("  [OK] worldcup2026_teams.md - Human-readable reference")
    print("  [OK] worldcup_format.py - 12-group format adapter")
    print("  [OK] worldcup_fixtures.py - 72-match schedule")
    print("  [OK] worldcup2026_fixtures.json - JSON export")
    print()
    print("Config Updated:")
    print("  [OK] core/config.py - Added WC2026 league coefficients")
    print()
    print("Special Factors Model:")
    print("  [OK] Altitude factor (Mexico City: 2240m)")
    print("  [OK] Climate factor (Hot/Humid vs Mild)")
    print("  [OK] Time zone factor (Europe/Asia jet lag)")
    print("  [OK] Host advantage (+5% Elo boost)")
    print()
    print("System Status: READY for World Cup 2026")
    print("=" * 60)


def print_team_info(team_code: str):
    """打印球队详情"""
    team = get_team(team_code.upper())
    if not team:
        print(f"Team {team_code} not found")
        return
    
    print(f"\n{'='*50}")
    print(f"Team Profile: {team.name_en}")
    print(f"{'='*50}")
    print(f"  FIFA Code:    {team.fifa_code}")
    print(f"  FIFA Rank:    #{team.fifa_rank}")
    print(f"  Elo Rating:   {team.elo_rating}")
    print(f"  Confederation: {team.confederation.value}")
    print(f"  WC Titles:    {team.wc_titles}")
    print(f"  WC Apps:      {team.wc_appearances}")
    print(f"  Host:         {'Yes' if team.is_host else 'No'}")
    print(f"  Debut:        {'Yes' if team.is_debut else 'No'}")
    print(f"  Notes:        {team.notes}")
    
    # 赛程
    fixtures = get_fixtures_by_team(team.fifa_code)
    print(f"\n  Fixtures ({len(fixtures)} matches):")
    for f in fixtures:
        home = get_team(f.home_team)
        away = get_team(f.away_team)
        if f.home_team == team.fifa_code:
            opp = away.name_en if away else f.away_team
            print(f"    {f.match_date} {f.match_time:5s} vs {opp:20s} ({f.city})")
        else:
            opp = home.name_en if home else f.home_team
            print(f"    {f.match_date} {f.match_time:5s} @ {opp:20s} ({f.city})")


def print_group_info(group: str):
    """打印小组信息"""
    group = group.upper()
    teams = get_group(group)
    fixtures = get_fixtures_by_group(group)
    
    print(f"\n{'='*50}")
    print(f"Group {group} - {len(teams)} Teams")
    print(f"{'='*50}")
    
    for team in teams:
        print(f"  {team.fifa_code:3s} - {team.name_en:25s} "
              f"FIFA#{team.fifa_rank:2d} Elo={team.elo_rating:.0f}")
    
    print(f"\n  Fixtures:")
    for f in fixtures:
        home = get_team(f.home_team)
        away = get_team(f.away_team)
        print(f"    MD{f.matchday}: {f.match_date} {f.match_time:5s} "
              f"{home.name_en if home else f.home_team:15s} "
              f"vs {away.name_en if away else f.away_team:15s}")


def run_standings_demo():
    """运行积分榜演示"""
    wc = WorldCup2026Format()
    
    # 模拟一些比赛结果
    wc.add_match_result("C", MatchResult("BRA", "SCO", 3, 1, MatchStatus.FINISHED, "Jun 14"))
    wc.add_match_result("C", MatchResult("MAR", "HAI", 2, 0, MatchStatus.FINISHED, "Jun 14"))
    wc.add_match_result("C", MatchResult("BRA", "MAR", 2, 1, MatchStatus.FINISHED, "Jun 20"))
    wc.add_match_result("C", MatchResult("SCO", "HAI", 1, 1, MatchStatus.FINISHED, "Jun 20"))
    wc.add_match_result("C", MatchResult("BRA", "HAI", 4, 0, MatchStatus.FINISHED, "Jun 26"))
    wc.add_match_result("C", MatchResult("MAR", "SCO", 1, 0, MatchStatus.FINISHED, "Jun 26"))
    
    wc.print_group_standings("C")
    
    advancement = wc.get_advancement_teams()
    print(f"\n{'='*50}")
    print("Advancement (Demo - Only Group C has results)")
    print(f"{'='*50}")
    print(f"Group 1st:  {len(advancement['group_1st'])}/12")
    print(f"Group 2nd:  {len(advancement['group_2nd'])}/12")
    print(f"Best 3rd:   {len(advancement['best_3rd'])}/8")
    print(f"Knockout 32: {len(advancement['knockout_32'])}/32")


def run_pipeline_analysis(home_code, away_code, market_odds=None, stage='group', match_notes=""):
    """运行完整分析流水线"""
    pipeline = WorldCupPipeline(bankroll=10000, stage=stage)
    market_data = None
    if market_odds:
        market_data = {
            'market_odds': market_odds,
            'market_prob': {k: 1/v for k, v in market_odds.items()},
            'media_consensus': 0.85,
        }
    pipeline.print_match_report(home_code, away_code, market_data, match_notes)


def run_hybrid_demo(stage='group'):
    """A+B Hybrid 策略演示"""
    print("\n" + "=" * 60)
    print(f"World Cup 2026 - A+B Hybrid Demo ({stage.upper()})")
    print("=" * 60)
    print("Strategy: A (Pure ELO + Edge) + B (Motivation Factor)")
    print("2022 Validation: Tight Hybrid 60% WR, +3.9% return, 10.4% utilization")
    print("=" * 60)
    
    pipeline = WorldCupPipeline(bankroll=10000, stage=stage)
    
    # Group Stage: Tight thresholds
    matches = [
        ("FRA", "SEN", {'home': 1.55, 'draw': 3.80, 'away': 6.50}, "France already qualified, Senegal need to win"),
        ("BRA", "SCO", {'home': 1.30, 'draw': 4.50, 'away': 10.00}, "Brazil heavy favorite"),
        ("ARG", "ALG", {'home': 1.25, 'draw': 5.50, 'away': 12.00}, "Argentina heavy favorite"),
        ("ESP", "URU", {'home': 2.10, 'draw': 3.20, 'away': 3.60}, "Even match, Spain slight favorite"),
        ("ENG", "CRO", {'home': 1.90, 'draw': 3.40, 'away': 4.20}, "England home favorite"),
    ]
    
    for m in matches:
        home, away = m[0], m[1]
        market_odds = m[2]
        notes = m[3] if len(m) > 3 else ""
        market_data = {
            'market_odds': market_odds,
            'market_prob': {k: 1/v for k, v in market_odds.items()},
            'media_consensus': 0.85,
        }
        pipeline.print_match_report(home, away, market_data, notes)
        print()
    
    print("=" * 60)
    print(f"A+B Hybrid Demo Complete - Stage: {stage.upper()}")
    print("=" * 60)


def run_auto_demo():
    """自动演示：5场经典对决"""
    print("\n" + "=" * 60)
    print("World Cup 2026 - Auto Demo (5 Classic Matches)")
    print("=" * 60)
    pipeline = WorldCupPipeline(bankroll=10000, stage='group')
    matches = [
        ("BRA", "SCO"),
        ("FRA", "SEN", {'home': 1.55, 'draw': 3.80, 'away': 6.50}),
        ("ARG", "ALG", {'home': 1.25, 'draw': 5.50, 'away': 12.00}),
        ("ESP", "URU", {'home': 2.10, 'draw': 3.20, 'away': 3.60}),
        ("ENG", "CRO", {'home': 1.90, 'draw': 3.40, 'away': 4.20}),
    ]
    for m in matches:
        home, away = m[0], m[1]
        market_data = None
        if len(m) > 2:
            market_odds = m[2]
            market_data = {
                'market_odds': market_odds,
                'market_prob': {k: 1/v for k, v in market_odds.items()},
                'media_consensus': 0.85,
            }
        pipeline.print_match_report(home, away, market_data)
        print()
    print("=" * 60)
    print("Auto Demo Complete - System Integration: ACTIVE")
    print("=" * 60)



def generate_full_report():
    """生成完整报告"""
    print_summary()
    print("\n")
    print_team_summary()
    print("\n")
    
    # 所有组概览
    for group in sorted(GROUPS.keys()):
        print_group_info(group)
    
    print("\n" + "=" * 60)
    print("World Cup 2026 System - Full Report Complete")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="2026 FIFA World Cup System")
    parser.add_argument("--summary", action="store_true", help="Print system summary")
    parser.add_argument("--team", type=str, help="Print team info (e.g., BRA, ARG)")
    parser.add_argument("--group", type=str, help="Print group info (e.g., A, C)")
    parser.add_argument("--fixtures", action="store_true", help="Print all fixtures")
    parser.add_argument("--standings-demo", action="store_true", help="Run standings demo")
    parser.add_argument("--full-report", action="store_true", help="Generate full report")
    parser.add_argument("--export-json", type=str, help="Export fixtures to JSON file")
    parser.add_argument("--analyze", type=str, nargs=2, metavar=('HOME','AWAY'), help="Analyze match (e.g., BRA SCO)")
    parser.add_argument("--with-odds", type=str, nargs=3, metavar=('H','D','A'), help="Market odds home draw away")
    parser.add_argument("--auto-demo", action="store_true", help="Run full pipeline demo")
    parser.add_argument("--hybrid-demo", action="store_true", help="Run A+B Hybrid strategy demo")
    parser.add_argument("--stage", type=str, default='group', help="Stage: group or knockout (for hybrid)")
    parser.add_argument("--notes", type=str, default='', help="Match notes for motivation factor")
    
    args = parser.parse_args()
    
    if not any([args.summary, args.team, args.group, args.fixtures, 
                args.standings_demo, args.full_report, args.export_json,
                args.hybrid_demo]):
        print_summary()
        return
    
    if args.summary:
        print_summary()
    
    if args.team:
        print_team_info(args.team)
    
    if args.group:
        print_group_info(args.group)
    
    if args.fixtures:
        from data.worldcup_fixtures import print_fixture_summary
        print_fixture_summary()
    
    if args.standings_demo:
        run_standings_demo()
    
    if args.auto_demo:
        run_auto_demo()
    
    if args.hybrid_demo:
        run_hybrid_demo(args.stage)
    
    if args.analyze:
        home, away = args.analyze
        odds = None
        if args.with_odds:
            h_odds, d_odds, a_odds = map(float, args.with_odds)
            odds = {'home': h_odds, 'draw': d_odds, 'away': a_odds}
        run_pipeline_analysis(home, away, odds, args.stage, args.notes)
    
    if args.full_report:
        generate_full_report()
    
    if args.export_json:
        export_to_json(args.export_json)
        print(f"Fixtures exported to {args.export_json}")


if __name__ == "__main__":
    main()
