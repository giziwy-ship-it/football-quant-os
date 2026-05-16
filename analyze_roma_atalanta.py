#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""罗马 vs 亚特兰大 比赛分析 - 修正API路径"""

import requests
import json
import sys

# 设置UTF-8输出
sys.stdout.reconfigure(encoding='utf-8')

# 罗马 vs 亚特兰大 - 意甲焦点战
payload = {
    'home_team': '罗马',
    'away_team': '亚特兰大',
    'league': '意甲',
    'home_team_rank': 6,
    'away_team_rank': 3,
    'market_odds': {
        'home_win': 2.40,
        'draw': 3.40,
        'away_win': 2.80
    }
}

print("=" * 60)
print("   娜迦足球量化决策系统 v4.1")
print("   比赛分析: 罗马 vs 亚特兰大")
print("   日期: 2026-04-19 | 联赛: 意甲")
print("=" * 60)
print("")

try:
    # 使用正确的API路径 /api/v1/analyze
    r = requests.post('http://127.0.0.1:8000/api/v1/analyze', json=payload, timeout=30)
    result = r.json()
    
    # 检查是否有错误
    if r.status_code != 200:
        print(f"API错误 (状态码 {r.status_code}):")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        # 成功响应，格式化输出
        print("[比赛信息]")
        print(f"  主队: {result.get('home_team', '罗马')}")
        print(f"  客队: {result.get('away_team', '亚特兰大')}")
        print(f"  联赛: {result.get('league', '意甲')}")
        print("")
        
        # 实力对比
        print("[实力评估]")
        strength = result.get('strength_analysis', {})
        print(f"  实力差距: {strength.get('gap', '中')}")
        print(f"  主队评级: {strength.get('home_rating', '中等')}")
        print(f"  客队评级: {strength.get('away_rating', '中等')}")
        print("")
        
        # 概率预测
        print("[概率预测 - 108组合矩阵]")
        probs = result.get('probabilities', {})
        print(f"  主胜: {probs.get('home_win', 'N/A')}")
        print(f"  平局: {probs.get('draw', 'N/A')}")
        print(f"  客胜: {probs.get('away_win', 'N/A')}")
        print("")
        
        # 投资建议
        print("[投资建议 - 凯利风控]")
        rec = result.get('recommendation', {})
        print(f"  建议方向: {rec.get('action', '观望')}")
        print(f"  信心指数: {rec.get('confidence', 'N/A')}")
        print(f"  建议仓位: {rec.get('position_size', '0%')}")
        print("")
        
        # 详细分析
        if 'full_analysis' in result:
            print("[深度分析]")
            print(result['full_analysis'])
            print("")
        
        print("=" * 60)
        print("  系统状态: 正常 | 风控模式: 精算师凯利(≤5%)")
        print("=" * 60)

except Exception as e:
    print(f"系统错误: {e}")
    import traceback
    traceback.print_exc()
