#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
一键刷新演示 - 48强教练数据互联网同步

使用方法:
    python scripts/demo_refresh.py
"""

import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.worldcup_2026_full_coaches import WORLD_CUP_2026_FULL_COACHES as COACHES
from agents.coach_factor_bridge import CoachFactorDataBridge

def demo_refresh():
    print("=" * 60)
    print(" CoachFactor One-Click Refresh Demo")
    print("=" * 60)
    print()
    
    # 显示当前状态
    print("Current Database Status:")
    print(f"  Teams: {len(COACHES)}")
    
    missing_wc = sum(1 for c in COACHES.values() if c.world_cup_experience == 0)
    missing_euro = sum(1 for c in COACHES.values() if c.euro_experience == 0)
    
    print(f"  Missing WC experience: {missing_wc}/48")
    print(f"  Missing Euro experience: {missing_euro}/48")
    print()
    
    # 演示：刷新3个关键球队
    bridge = CoachFactorDataBridge()
    
    demo_teams = [
        ('Argentina', 'Lionel Scaloni'),
        ('France', 'Didier Deschamps'),
        ('England', 'Thomas Tuchel'),
    ]
    
    print("Demo: Refreshing 3 key teams from internet...")
    print()
    
    for team, coach_name in demo_teams:
        print(f"--- {team} ({coach_name}) ---")
        result = bridge.refresh_coach(team)
        
        if result['status'] == 'updated':
            print(f"  [OK] Found {len(result['changes'])} updates:")
            for ch in result['changes']:
                print(f"    {ch['field']}: {ch['old']} -> {ch['new']}")
        elif result['warnings']:
            print(f"  [!] {len(result['warnings'])} warnings")
        else:
            print(f"  [=] No changes (data matches)")
        print()
    
    print("=" * 60)
    print("Demo complete.")
    print()
    print("To refresh ALL 48 teams:")
    print("  python scripts/refresh_coaches.py --preview")
    print()
    print("To apply changes:")
    print("  python scripts/refresh_coaches.py --apply")
    print("=" * 60)

if __name__ == '__main__':
    demo_refresh()
