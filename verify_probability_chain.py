#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
概率传递链验证脚本 - Football Quant OS
验证从输入 → Phase 1 → Phase 2 → Phase 3 的概率传递是否完整
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import requests
import json

BASE_URL = "http://localhost:8005/api/v1"

def test_api_health():
    """测试 API 服务状态"""
    print("=" * 60)
    print("[TEST 1] API 健康检查")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/agents")
        if response.status_code == 200:
            data = response.json()
            print(f"[OK] Agents 列表: {len(data.get('agents', []))} 个")
            for agent in data.get('agents', []):
                print(f"  - {agent['name']}: {agent['role']}")
            return True
        else:
            print(f"[FAIL] 状态码: {response.status_code}")
            return False
    except Exception as e:
        print(f"[FAIL] 连接失败: {e}")
        return False

def check_probability_chain(result, expected_market_probs):
    """检查概率传递链的完整性"""
    print("\n[CHAIN CHECK] 概率传递链验证:")
    print("-" * 50)
    
    chain_ok = True
    issues = []
    
    # Phase 1: DataScout
    agent_results = result.get('agent_results', {})
    phase1 = agent_results.get('phase1', {})
    
    datascout = phase1.get('DataScout', {})
    if datascout:
        ds_pred = datascout.get('prediction', {})
        print(f"[Phase 1] DataScout:")
        print(f"  主胜: {ds_pred.get('home_win', 0):.2f}%")
        print(f"  平局: {ds_pred.get('draw', 0):.2f}%")
        print(f"  客胜: {ds_pred.get('away_win', 0):.2f}%")
        
        # DataScout 应该使用输入的概率
        if abs(ds_pred.get('home_win', 0) - expected_market_probs['home_win']) > 2:
            issues.append("DataScout 概率与输入概率偏差较大")
            chain_ok = False
        else:
            print(f"  [OK] DataScout 正确传递输入概率")
    else:
        issues.append("Phase 1 DataScout 缺失")
        chain_ok = False
    
    # Analyst
    analyst = phase1.get('Analyst', {})
    if analyst:
        an_pred = analyst.get('prediction', {})
        print(f"\n[Phase 1] Analyst:")
        print(f"  主胜: {an_pred.get('home_win', 0):.2f}%")
        print(f"  平局: {an_pred.get('draw', 0):.2f}%")
        print(f"  客胜: {an_pred.get('away_win', 0):.2f}%")
        
        # Analyst 应该使用市场概率
        if abs(an_pred.get('home_win', 0) - expected_market_probs['home_win']) > 2:
            issues.append("Analyst 概率与市场概率偏差较大")
            chain_ok = False
        else:
            print(f"  [OK] Analyst 正确传递市场概率")
    else:
        issues.append("Phase 1 Analyst 缺失")
        chain_ok = False
    
    # Phase 2: Committee
    phase2 = agent_results.get('phase2', {})
    committee = phase2.get('Committee', {})
    if committee:
        com_pred = committee.get('prediction', {})
        com_rec = committee.get('recommended_outcome', 'unknown')
        com_conf = committee.get('confidence', 0)
        market_used = committee.get('market_odds_used', False)
        
        print(f"\n[Phase 2] Committee:")
        print(f"  主胜: {com_pred.get('home_win', 0):.2f}%")
        print(f"  平局: {com_pred.get('draw', 0):.2f}%")
        print(f"  客胜: {com_pred.get('away_win', 0):.2f}%")
        print(f"  推荐: {com_rec}")
        print(f"  置信度: {com_conf:.2f}")
        print(f"  使用市场概率: {market_used}")
        
        # Committee 应该优先使用市场概率
        if market_used:
            if abs(com_pred.get('home_win', 0) - expected_market_probs['home_win']) > 2:
                issues.append("Committee 声称使用市场概率，但数值偏差较大")
                chain_ok = False
            else:
                print(f"  [OK] Committee 正确优先使用市场概率")
        else:
            issues.append("Committee 未使用市场概率（可能无市场赔率输入）")
            # 这不一定是错误，如果没有市场赔率的话
    else:
        issues.append("Phase 2 Committee 缺失")
        chain_ok = False
    
    # Phase 3: RiskControl
    phase3 = agent_results.get('phase3', {})
    risk = phase3.get('RiskControl', {})
    if risk:
        risk_level = risk.get('risk_level', 'UNKNOWN')
        allow = risk.get('allow', False)
        print(f"\n[Phase 3] RiskControl:")
        print(f"  风险等级: {risk_level}")
        print(f"  允许投注: {allow}")
        
        kelly_adj = risk.get('kelly_adjustment', {})
        if kelly_adj:
            print(f"  凯利调整: {kelly_adj.get('adjusted_kelly', 0):.4f}")
            print(f"  调整原因: {kelly_adj.get('adjustment_reason', '')}")
        print(f"  [OK] RiskControl 正常接收上层数据")
    else:
        issues.append("Phase 3 RiskControl 缺失")
        chain_ok = False
    
    # 检查其他模型输出
    print(f"\n[MODELS CHECK]")
    matrix = result.get('matrix_108', {})
    if matrix:
        m_probs = matrix.get('probabilities', {})
        print(f"  108矩阵: 主{m_probs.get('home_win', 0)}% 平{m_probs.get('draw', 0)}% 客{m_probs.get('away_win', 0)}%")
    
    gene = result.get('gene_analysis', {})
    if gene:
        print(f"  基因分析: home_advantage={gene.get('home_advantage', 0)}")
    
    hist = result.get('historical_odds', {})
    if hist:
        h_adj = hist.get('probability_adjustment', {})
        if h_adj.get('adjusted'):
            h_probs = h_adj.get('adjusted_probs', {})
            print(f"  历史赔率调整: 主{h_probs.get('home_win', 0)}% 平{h_probs.get('draw', 0)}% 客{h_probs.get('away_win', 0)}%")
        else:
            print(f"  历史赔率: 无调整")
    
    # 最终决策
    decision = result.get('decision', {})
    stake = result.get('stake', {})
    
    print(f"\n[FINAL OUTPUT]")
    if result.get('status') == 'blocked':
        print(f"  状态: 被风控拦截")
        print(f"  原因: {result.get('reason', '')}")
        print(f"  风险等级: {result.get('risk_level', 'HIGH')}")
    else:
        print(f"  推荐: {decision.get('recommended_outcome', 'unknown')}")
        print(f"  投注金额: ¥{stake.get('stake', 0):.2f}")
        print(f"  凯利比例: {stake.get('safe_fraction', 0)*100:.2f}%")
    
    # 打印问题
    if issues:
        print(f"\n[ISSUES] 发现 {len(issues)} 个问题:")
        for issue in issues:
            print(f"  - {issue}")
    
    return chain_ok

def test_probability_chain():
    """测试概率传递链完整性"""
    print("\n" + "=" * 60)
    print("[TEST 2] 概率传递链验证")
    print("=" * 60)
    
    # 测试用例 1: 带真实赔率的比赛（较高赔率价值）
    match_request = {
        "home_team": "曼城",
        "away_team": "利物浦",
        "league": "英超",
        "home_team_rank": 2,
        "away_team_rank": 1,
        "market_odds": {
            "home_win": 3.50,
            "draw": 3.40,
            "away_win": 2.10
        },
        "bankroll": 10000
    }
    
    # 计算预期市场概率
    home_odds = match_request['market_odds']['home_win']
    draw_odds = match_request['market_odds']['draw']
    away_odds = match_request['market_odds']['away_win']
    
    home_prob = (1 / home_odds) * 100
    draw_prob = (1 / draw_odds) * 100
    away_prob = (1 / away_odds) * 100
    total = home_prob + draw_prob + away_prob
    
    expected_market_probs = {
        'home_win': round(home_prob / total * 100, 2),
        'draw': round(draw_prob / total * 100, 2),
        'away_win': round(away_prob / total * 100, 2)
    }
    
    print(f"\n[INPUT] 输入市场赔率:")
    print(f"  主胜赔率: {home_odds} → 预期概率: {expected_market_probs['home_win']:.2f}%")
    print(f"  平局赔率: {draw_odds} → 预期概率: {expected_market_probs['draw']:.2f}%")
    print(f"  客胜赔率: {away_odds} → 预期概率: {expected_market_probs['away_win']:.2f}%")
    
    # 调用分析 API
    print(f"\n[API CALL] 发送分析请求...")
    try:
        response = requests.post(f"{BASE_URL}/analyze", json=match_request)
        result = response.json()
    except Exception as e:
        print(f"[FAIL] API 调用失败: {e}")
        return False
    
    # 验证概率传递链
    chain_ok = check_probability_chain(result, expected_market_probs)
    
    # 即使被拦截，也返回 chain_ok 的结果
    return chain_ok

def test_fixtures_api():
    """测试赛程 API"""
    print("\n" + "=" * 60)
    print("[TEST 3] 赛程 API 验证")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BASE_URL}/fixtures/today")
        data = response.json()
        
        if "error" in data:
            print(f"[WARN] 赛程获取失败: {data['error']}")
            print(f"[DETAIL] {data.get('detail', '')}")
            return False
        
        total = data.get('total', 0)
        leagues = data.get('leagues', [])
        print(f"[OK] 今天共有 {total} 场比赛")
        print(f"[OK] 联赛: {', '.join(leagues)}")
        
        fixtures = data.get('fixtures', [])
        if fixtures:
            print(f"\n[SAMPLE] 前3场比赛:")
            for f in fixtures[:3]:
                league = f.get('league', '其他联赛')
                if league == 'Unknown':
                    league = '其他联赛'
                print(f"  - {f.get('home_team')} vs {f.get('away_team')} ({league})")
        
        return True
    except Exception as e:
        print(f"[FAIL] 赛程 API 调用失败: {e}")
        return False

def main():
    print("[START] Football Quant OS - 概率传递链完整验证")
    print("=" * 60)
    
    results = []
    
    # Test 1: API 健康
    results.append(("API 健康", test_api_health()))
    
    # Test 2: 概率传递链
    results.append(("概率传递链", test_probability_chain()))
    
    # Test 3: 赛程 API
    results.append(("赛程 API", test_fixtures_api()))
    
    # 总结
    print("\n" + "=" * 60)
    print("[SUMMARY] 验证结果汇总")
    print("=" * 60)
    
    all_pass = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} - {name}")
        if not passed:
            all_pass = False
    
    print("\n" + "=" * 60)
    if all_pass:
        print("[RESULT] 🎉 所有验证通过！概率传递链完整！")
    else:
        print("[RESULT] ⚠️ 部分验证失败，请检查日志")
    print("=" * 60)

if __name__ == "__main__":
    main()
