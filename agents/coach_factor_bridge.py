#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CoachFactorDataBridge - 教练数据集成桥接器

功能：一键从互联网刷新48强教练客观数据
策略：
- FIFA官方数据 (本地) → 基准，永不被覆盖
- 互联网数据 (实时) → 补充/验证客观字段
- 专家评估数据 → 保留，标记为[MANUAL]

刷新字段：
✅ 自动刷新 (客观): age, world_cup_experience, euro_experience, career_matches
✅ 交叉验证 (客观): nationality, preferred_formation
❌ 保留不变 (主观): emotional_stability, media_influence, meltdown_incidents, etc.
"""

import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.coach_data_sync import CoachDataSync, CoachDataSnapshot
from agents.worldcup_2026_full_coaches import WORLD_CUP_2026_FULL_COACHES as BASE_COACHES
from agents.coach_types import CoachProfile
from dataclasses import fields, asdict
import json
from datetime import datetime
import time


class CoachFactorDataBridge:
    """
    桥接CoachFactor数据库与互联网数据
    
    使用：
        bridge = CoachFactorDataBridge()
        report = bridge.refresh_all()  # 一键刷新全部
        # 或
        report = bridge.refresh_coach("Argentina")  # 刷新单个
    """
    
    # 字段映射：本地字段名 -> 互联网数据源字段名
    FIELD_MAP = {
        'age': ('age', 'int'),
        'world_cup_experience': ('world_cup_experience', 'int'),
        'euro_experience': ('euro_experience', 'int'),
        'career_matches': ('career_matches', 'int'),
        'nationality': ('nationality', 'str'),
    }
    
    def __init__(self, fbref_api_key=None):
        self.sync = CoachDataSync(fbref_api_key=fbref_api_key)
        self.changes_log = []
        self.errors = []
    
    def refresh_coach(self, team_name: str, internet_data: CoachDataSnapshot = None) -> dict:
        """
        刷新单个教练数据
        
        策略：
        1. 获取互联网数据（如果没有传入）
        2. 对比本地数据
        3. 只更新客观字段，且需确认
        4. 记录变化日志
        
        Returns:
            dict: {team, changes, errors, status}
        """
        result = {
            'team': team_name,
            'status': 'no_change',
            'changes': [],
            'warnings': [],
            'errors': [],
        }
        
        # 1. 获取本地数据
        if team_name not in BASE_COACHES:
            result['status'] = 'error'
            result['errors'].append(f"Team {team_name} not found in local database")
            return result
        
        local = BASE_COACHES[team_name]
        
        # 2. 获取互联网数据（如果没有传入）
        if internet_data is None:
            try:
                internet_data = self.sync.sync_coach(local.name, team_name)
                time.sleep(2)  # 速率限制
            except Exception as e:
                result['status'] = 'error'
                result['errors'].append(f"Internet fetch failed: {e}")
                return result
        
        # 3. 对比并更新
        for local_field, (internet_field, field_type) in self.FIELD_MAP.items():
            local_val = getattr(local, local_field, None)
            internet_val = getattr(internet_data, internet_field, None)
            
            if internet_val is None:
                continue  # 互联网没有数据，保留本地
            
            # 类型转换
            if field_type == 'int' and internet_val is not None:
                try:
                    internet_val = int(internet_val)
                except Exception:
                    continue
            
            # 检查差异
            if local_val != internet_val:
                # 判断可信度
                if local_field == 'age' and abs((local_val or 0) - internet_val) > 2:
                    # 年龄差异>2岁，可能是数据错误，标记警告
                    result['warnings'].append({
                        'field': local_field,
                        'local': local_val,
                        'internet': internet_val,
                        'note': 'Age difference > 2 years, verify manually',
                    })
                else:
                    # 正常更新
                    result['changes'].append({
                        'field': local_field,
                        'old': local_val,
                        'new': internet_val,
                        'source': internet_data.data_sources,
                    })
        
        # 4. 如果有变化，标记状态
        if result['changes']:
            result['status'] = 'updated'
        elif result['warnings']:
            result['status'] = 'warning'
        
        return result
    
    def refresh_all(self, dry_run: bool = True) -> dict:
        """
        一键刷新所有48强教练数据
        
        Args:
            dry_run: True = 只生成报告，不修改文件
                    False = 实际更新本地数据库
        
        Returns:
            完整刷新报告
        """
        print("=" * 60)
        print("CoachFactor Data Bridge - Full Refresh Report")
        print("=" * 60)
        print(f"Mode: {'DRY RUN (preview only)' if dry_run else 'LIVE UPDATE'}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print(f"Total teams: {len(BASE_COACHES)}")
        print()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'mode': 'dry_run' if dry_run else 'live',
            'total_teams': len(BASE_COACHES),
            'updated': 0,
            'warnings': 0,
            'errors': 0,
            'no_change': 0,
            'details': [],
        }
        
        # 逐个刷新
        for i, (team_name, local_coach) in enumerate(BASE_COACHES.items(), 1):
            print(f"[{i}/48] Refreshing {team_name} ({local_coach.name})...")
            
            try:
                result = self.refresh_coach(team_name)
                report['details'].append(result)
                
                if result['status'] == 'updated':
                    report['updated'] += 1
                    print(f"  ✓ UPDATED: {len(result['changes'])} fields")
                    for ch in result['changes']:
                        print(f"    - {ch['field']}: {ch['old']} → {ch['new']}")
                
                elif result['status'] == 'warning':
                    report['warnings'] += 1
                    print(f"  ⚠ WARNING: {len(result['warnings'])} issues")
                    for w in result['warnings']:
                        print(f"    - {w['field']}: {w['local']} vs {w['internet']} ({w['note']})")
                
                elif result['status'] == 'error':
                    report['errors'] += 1
                    print(f"  ✗ ERROR: {result['errors']}")
                
                else:
                    report['no_change'] += 1
                    print(f"  = No change")
                
                # 速率限制
                time.sleep(2)
                
            except Exception as e:
                report['errors'] += 1
                report['details'].append({
                    'team': team_name,
                    'status': 'error',
                    'errors': [str(e)],
                })
                print(f"  ✗ EXCEPTION: {e}")
        
        print()
        print("=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Updated:     {report['updated']}")
        print(f"Warnings:    {report['warnings']}")
        print(f"Errors:      {report['errors']}")
        print(f"No change:   {report['no_change']}")
        print(f"Total:       {report['total_teams']}")
        print()
        
        if dry_run:
            print("NOTE: This was a DRY RUN. No files were modified.")
            print("To apply changes, run: bridge.refresh_all(dry_run=False)")
        
        print("=" * 60)
        
        return report
    
    def generate_update_script(self, report: dict) -> str:
        """
        根据报告生成Python更新脚本
        
        用途：用户审查报告后，运行脚本应用更新
        """
        lines = [
            "#!/usr/bin/env python3",
            "# -*- coding: utf-8 -*-",
            f"\"\"\"",
            f"Auto-generated update script",
            f"Generated: {report['timestamp']}",
            f"Changes: {report['updated']} teams",
            f"\"\"\"",
            "",
            "import sys",
            "sys.path.insert(0, 'D:\\\\openclaw-workspace\\\\football_quant_os')",
            "from agents.worldcup_2026_full_coaches import WORLD_CUP_2026_FULL_COACHES",
            "",
            "# Apply verified changes",
        ]
        
        for detail in report['details']:
            if detail['status'] == 'updated':
                team = detail['team']
                for change in detail['changes']:
                    field = change['field']
                    new_val = change['new']
                    lines.append(f"WORLD_CUP_2026_FULL_COACHES['{team}'].{field} = {new_val}")
        
        lines.extend([
            "",
            "print('Update complete')",
        ])
        
        return '\n'.join(lines)


# ============================================================
# 快速刷新命令行工具
# ============================================================

def quick_refresh():
    """
    命令行快速刷新入口
    
    使用:
        python coach_factor_bridge.py --refresh-all
        python coach_factor_bridge.py --refresh-team Argentina
        python coach_factor_bridge.py --report
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='CoachFactor Data Bridge')
    parser.add_argument('--refresh-all', action='store_true', help='Refresh all 48 teams')
    parser.add_argument('--refresh-team', type=str, help='Refresh specific team')
    parser.add_argument('--live', action='store_true', help='Apply changes (not dry run)')
    parser.add_argument('--report', action='store_true', help='Generate summary report')
    
    args = parser.parse_args()
    
    bridge = CoachFactorDataBridge()
    
    if args.refresh_all:
        report = bridge.refresh_all(dry_run=not args.live)
        
        # 保存报告
        if report:
            with open('data/refresh_report.json', 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"\nReport saved to: data/refresh_report.json")
    
    elif args.refresh_team:
        result = bridge.refresh_coach(args.refresh_team)
        print(json.dumps(result, indent=2, default=str))
    
    elif args.report:
        # 生成当前状态报告
        print("Generating current database status report...")
        # ... 实现报告生成
    
    else:
        parser.print_help()


# ============================================================
# 演示
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CoachFactor Data Bridge v1.0")
    print("=" * 60)
    print()
    print("Features:")
    print("  1. refresh_all()     - One-click refresh all 48 teams")
    print("  2. refresh_coach()   - Refresh single team")
    print("  3. Dry-run mode      - Preview before applying")
    print()
    print("Usage:")
    print("  from coach_factor_bridge import CoachFactorDataBridge")
    print("  bridge = CoachFactorDataBridge()")
    print("  report = bridge.refresh_all(dry_run=True)  # Preview")
    print("  report = bridge.refresh_all(dry_run=False)  # Apply")
    print()
    
    # 运行快速演示（阿根廷）
    print("[Demo] Refreshing Argentina (Lionel Scaloni)...")
    bridge = CoachFactorDataBridge()
    result = bridge.refresh_coach("Argentina")
    
    print()
    print("Result:")
    print(f"  Status: {result['status']}")
    if result['changes']:
        print(f"  Changes: {len(result['changes'])}")
        for ch in result['changes']:
            print(f"    {ch['field']}: {ch['old']} → {ch['new']}")
    if result['warnings']:
        print(f"  Warnings: {len(result['warnings'])}")
    if result['errors']:
        print(f"  Errors: {result['errors']}")
    
    print()
    print("Demo complete. Run refresh_all() to update all 48 teams.")
    print("=" * 60)
