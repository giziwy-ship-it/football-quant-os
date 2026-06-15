#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
refresh_coaches.py - 一键刷新所有教练数据

用法：
    python scripts/refresh_coaches.py --preview    # 预览变化（不修改文件）
    python scripts/refresh_coaches.py --apply      # 应用变化（修改本地数据库）
    python scripts/refresh_coaches.py --team Argentina  # 刷新单个球队
    python scripts/refresh_coaches.py --report     # 生成当前状态报告

数据源：
    Wikipedia (免费) -> 年龄、国籍、履历
    Transfermarkt (爬虫) -> 执教历史、比赛数
    RSS (可选) -> 实时新闻

策略：
    - FIFA官方数据 (本地) -> 基准，永不被覆盖
    - 互联网数据 -> 补充客观字段（年龄、经验、比赛数）
    - 主观字段（情绪、心理）-> 保留不变
"""

import sys
import argparse
import json
from datetime import datetime

sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.coach_factor_bridge import CoachFactorDataBridge


def print_banner():
    print("=" * 60)
    print(" CoachFactor Data Refresh Tool v1.0")
    print("=" * 60)
    print(" Source: Wikipedia + Transfermarkt + RSS")
    print(" Strategy: Internet data supplements local FIFA database")
    print("=" * 60)
    print()


def preview_all():
    """预览所有48队的变化（不修改文件）"""
    print_banner()
    print("[MODE] Preview - No files will be modified")
    print()
    
    bridge = CoachFactorDataBridge()
    report = bridge.refresh_all(dry_run=True)
    
    # 保存报告
    report_file = f"data/refresh_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\n[Saved] Preview report: {report_file}")
    except Exception:
        print(f"\n[Report] Could not save to file, but report is above")
    
    return report


def apply_all():
    """应用所有变化到本地数据库"""
    print_banner()
    print("[MODE] LIVE UPDATE - Files will be modified!")
    print()
    
    # 先预览
    bridge = CoachFactorDataBridge()
    preview = bridge.refresh_all(dry_run=True)
    
    if preview['updated'] == 0 and preview['warnings'] == 0:
        print("No changes to apply.")
        return
    
    print()
    print(f"Changes to apply: {preview['updated']} teams")
    print(f"Warnings: {preview['warnings']}")
    print()
    
    # 确认
    confirm = input("Apply these changes? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Cancelled.")
        return
    
    # 执行更新
    print("\nApplying changes...")
    # TODO: 实现实际的文件更新逻辑
    print("[TODO] Implement file write logic")
    print("Done.")


def refresh_team(team_name: str):
    """刷新单个球队"""
    print_banner()
    print(f"[MODE] Refresh single team: {team_name}")
    print()
    
    bridge = CoachFactorDataBridge()
    result = bridge.refresh_coach(team_name)
    
    print()
    print("Result:")
    print(json.dumps(result, indent=2, default=str))


def generate_report():
    """生成当前数据库状态报告"""
    print_banner()
    print("[MODE] Database status report")
    print()
    
    from agents.worldcup_2026_full_coaches import WORLD_CUP_2026_FULL_COACHES
    
    print(f"Total teams: {len(WORLD_CUP_2026_FULL_COACHES)}")
    print()
    
    # 统计字段完整度
    field_stats = {}
    for field in ['age', 'nationality', 'world_cup_experience', 'euro_experience', 
                   'career_matches', 'emotional_stability', 'media_influence_susceptibility']:
        field_stats[field] = {'filled': 0, 'empty': 0}
    
    for team, coach in WORLD_CUP_2026_FULL_COACHES.items():
        for field in field_stats:
            val = getattr(coach, field, None)
            if val is not None and val != 0:
                field_stats[field]['filled'] += 1
            else:
                field_stats[field]['empty'] += 1
    
    print("Field completeness:")
    for field, stats in field_stats.items():
        pct = stats['filled'] / len(WORLD_CUP_2026_FULL_COACHES) * 100
        print(f"  {field:30} {stats['filled']:2}/{len(WORLD_CUP_2026_FULL_COACHES)} ({pct:5.1f}%)")
    
    print()
    print("Data sources:")
    print("  [FIFA]  Name, Nationality, Team (100% from FIFA PDF)")
    print("  [EST]   Age, Experience, Stats (estimated from public sources)")
    print("  [MANUAL] Emotional, Psychological (expert assessment)")


def main():
    parser = argparse.ArgumentParser(
        description='CoachFactor Data Refresh Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/refresh_coaches.py --preview          # 查看所有变化
  python scripts/refresh_coaches.py --apply            # 应用所有变化
  python scripts/refresh_coaches.py --team Argentina   # 刷新阿根廷
  python scripts/refresh_coaches.py --report            # 生成状态报告
        """
    )
    
    parser.add_argument('--preview', action='store_true', help='Preview all changes (dry run)')
    parser.add_argument('--apply', action='store_true', help='Apply changes to local database')
    parser.add_argument('--team', type=str, help='Refresh specific team')
    parser.add_argument('--report', action='store_true', help='Generate database status report')
    
    args = parser.parse_args()
    
    if args.preview:
        preview_all()
    elif args.apply:
        apply_all()
    elif args.team:
        refresh_team(args.team)
    elif args.report:
        generate_report()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
