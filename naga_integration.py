#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - Naga Core 集成模块
将 Football Quant OS v4.1 集成到 Naga Core v3.0 系统
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import os
import json
from pathlib import Path
from datetime import datetime, date

# Naga Core 路径
NAGA_CORE_PATH = Path(__file__).parent.parent / "skills" / "naga-core"

# Football Quant OS 路径
FQOS_PATH = Path(__file__).parent


class FQOSIntegration:
    """Football Quant OS 集成管理器"""
    
    def __init__(self):
        self.status = {
            "integrated": False,
            "version": "4.1.0",
            "components": {}
        }
    
    def check_integration(self) -> dict:
        """检查集成状态"""
        
        # 检查核心组件
        components = {
            "espn_client": (FQOS_PATH / "fixtures" / "espn_client.py").exists(),
            "odds_api": (FQOS_PATH / "odds_api.py").exists(),
            "config_loader": (FQOS_PATH / "core" / "config_loader.py").exists(),
            "workflow": (FQOS_PATH / "workflow_demo.py").exists(),
            "api_server": (FQOS_PATH / "app" / "main.py").exists(),
            "nine_agents": (FQOS_PATH / "agents").exists(),
            "models": (FQOS_PATH / "models").exists(),
        }
        
        self.status["components"] = components
        self.status["integrated"] = all(components.values())
        
        return self.status
    
    def get_system_info(self) -> dict:
        """获取系统集成信息"""
        
        info = {
            "system": "Football Quant OS",
            "version": "4.1.0",
            "naga_core_version": "3.0",
            "integration_date": "2026-05-05",
            "components": {
                "赛程获取": {
                    "status": "✅ 已集成",
                    "source": "ESPN API",
                    "leagues": "33+ 联赛",
                    "coverage": "全球主要联赛"
                },
                "赔率接入": {
                    "status": "✅ 已集成",
                    "primary": "The Odds API",
                    "backup": "Football-Data.org (待配置)",
                    "coverage": "欧洲主要联赛"
                },
                "预测分析": {
                    "status": "✅ 已集成",
                    "agents": "9 Agents",
                    "models": "108矩阵 + 凯利公式",
                    "framework": "3阶段流水线"
                },
                "风控系统": {
                    "status": "✅ 已集成",
                    "method": "Kelly Criterion",
                    "max_bet": "10% 资金",
                    "risk_level": "精算师级"
                },
                "配置管理": {
                    "status": "✅ 已集成",
                    "method": "统一 .env 配置",
                    "auto_load": "是",
                    "backup": "已备份"
                }
            },
            "workflow": {
                "step_1": "获取 ESPN 赛程",
                "step_2": "选择重点比赛",
                "step_3": "获取实时赔率",
                "step_4": "9 Agents 预测",
                "step_5": "Kelly 风控",
                "step_6": "输出投资建议"
            },
            "api_endpoints": {
                "fixtures_today": "GET /api/v1/fixtures/today",
                "fixtures_date": "GET /api/v1/fixtures/date/{YYYY-MM-DD}",
                "analyze": "POST /api/v1/analyze",
                "backtest": "POST /api/v1/backtest",
                "matrix_108": "GET /api/v1/matrix/108",
                "agents": "GET /api/v1/agents"
            }
        }
        
        return info
    
    def export_to_naga(self) -> bool:
        """导出集成信息到 Naga Core"""
        
        try:
            # 创建集成记录
            integration_record = {
                "timestamp": datetime.now().isoformat(),
                "system": "Football Quant OS",
                "version": "4.1.0",
                "status": "integrated",
                "components": self.check_integration()["components"]
            }
            
            # 保存到 Naga Core 数据目录
            naga_data = NAGA_CORE_PATH / "data"
            if naga_data.exists():
                record_path = naga_data / "fqos_integration.json"
                with open(record_path, 'w', encoding='utf-8') as f:
                    json.dump(integration_record, f, ensure_ascii=False, indent=2)
                print(f"[INFO] 集成记录已保存: {record_path}")
                return True
            else:
                print("[WARN] Naga Core 数据目录不存在")
                return False
                
        except Exception as e:
            print(f"[ERROR] 导出失败: {e}")
            return False


def main():
    """主函数"""
    print("="*60)
    print("Football Quant OS - Naga Core 集成检查")
    print("="*60)
    print()
    
    # 创建集成管理器
    integration = FQOSIntegration()
    
    # 检查集成状态
    print("[CHECK] 检查集成状态...")
    status = integration.check_integration()
    
    print(f"\n集成状态: {'✅ 已完成' if status['integrated'] else '❌ 未完成'}")
    print(f"系统版本: {status['version']}")
    print()
    
    # 显示组件状态
    print("组件状态:")
    for component, exists in status["components"].items():
        symbol = "✅" if exists else "❌"
        print(f"  {symbol} {component}")
    print()
    
    # 获取系统信息
    print("[INFO] 获取系统集成信息...")
    info = integration.get_system_info()
    
    print(f"\n系统: {info['system']} v{info['version']}")
    print(f"Naga Core: v{info['naga_core_version']}")
    print(f"集成日期: {info['integration_date']}")
    print()
    
    # 显示组件详情
    print("集成组件详情:")
    for name, details in info["components"].items():
        print(f"\n  【{name}】")
        for key, value in details.items():
            print(f"    {key}: {value}")
    
    # 显示工作流
    print("\n\n工作流:")
    for step, desc in info["workflow"].items():
        print(f"  {step}: {desc}")
    
    # 显示 API 端点
    print("\n\nAPI 端点:")
    for name, endpoint in info["api_endpoints"].items():
        print(f"  {name}: {endpoint}")
    
    # 导出到 Naga Core
    print("\n\n[EXPORT] 导出集成信息到 Naga Core...")
    if integration.export_to_naga():
        print("✅ 导出成功")
    else:
        print("⚠️ 导出失败（Naga Core 可能未安装）")
    
    print("\n" + "="*60)
    print("集成检查完成")
    print("="*60)


if __name__ == "__main__":
    main()
