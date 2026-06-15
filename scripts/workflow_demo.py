#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 完整工作流示例
从赛程获取 → 比赛选择 → 9 Agents 预测 → 投资建议
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

# 加载统一配置（必须在其他导入之前）
from core.config_loader import ensure_config, get_config
ensure_config()

import asyncio
import requests
from typing import List, Dict, Any
from datetime import date

# 导入赔率模块
from odds_api import get_match_odds

# API 基础 URL
BASE_URL = "http://localhost:8005/api/v1"


async def get_today_fixtures() -> List[Dict[str, Any]]:
    """获取今天所有比赛"""
    response = requests.get(f"{BASE_URL}/fixtures/today")
    data = response.json()
    
    if "error" in data:
        print(f"[ERROR] 获取赛程失败: {data['error']}")
        return []
    
    fixtures = data.get("fixtures", [])
    print(f"[INFO] 今天共有 {len(fixtures)} 场比赛")
    print(f"[INFO] 联赛: {', '.join(data.get('leagues', []))}")
    print()
    
    return fixtures


def select_key_matches(fixtures: List[Dict[str, Any]], top_n: int = 3) -> List[Dict[str, Any]]:
    """选择重点比赛（基于联赛级别和球队知名度）"""
    
    # 联赛优先级
    league_priority = {
        "欧冠": 100,
        "英超": 90,
        "西甲": 85,
        "意甲": 80,
        "德甲": 75,
        "法甲": 70,
        "欧联": 65,
    }
    
    # 为每场比赛打分
    scored_matches = []
    for match in fixtures:
        league = match.get("league", "")
        score = league_priority.get(league, 50)
        
        # 知名球队加分
        famous_teams = ["皇家马德里", "巴塞罗那", "曼城", "利物浦", "拜仁慕尼黑", 
                       "巴黎圣日耳曼", "尤文图斯", "AC米兰", "国际米兰", "切尔西", "阿森纳"]
        
        home_team = match.get("home_team", "")
        away_team = match.get("away_team", "")
        
        if any(team in home_team or team in away_team for team in famous_teams):
            score += 20
        
        scored_matches.append((score, match))
    
    # 按分数排序，取前 N 场
    scored_matches.sort(key=lambda x: x[0], reverse=True)
    selected = [match for _, match in scored_matches[:top_n]]
    
    return selected


async def analyze_match(match: Dict[str, Any]) -> Dict[str, Any]:
    """分析单场比赛"""
    
    home_team = match.get("home_team", "")
    away_team = match.get("away_team", "")
    league = match.get("league", "Unknown")
    
    # 获取实时赔率（使用统一配置）
    real_odds = await get_match_odds(home_team, away_team, league)
    if real_odds:
        source = real_odds.get("source", "unknown")
        print(f"[ODDS] 赔率来源: {source}")
        print(f"[ODDS] 主{real_odds['home_win']} | 平{real_odds['draw']} | 客{real_odds['away_win']}")
        market_odds = {
            "home_win": real_odds["home_win"],
            "draw": real_odds["draw"],
            "away_win": real_odds["away_win"]
        }
    else:
        print(f"[ODDS] 使用默认赔率")
        market_odds = {
            "home_win": 2.0,
            "draw": 3.2,
            "away_win": 3.5
        }
    
    # 准备分析请求
    match_request = {
        "home_team": home_team,
        "away_team": away_team,
        "league": league,
        "home_team_rank": 8,
        "away_team_rank": 8,
        "market_odds": market_odds,
        "bankroll": int(get_config("DEFAULT_BANKROLL", "10000"))
    }
    
    # 显示真实赔率转换的概率
    if real_odds and 'source' in real_odds and real_odds['source'] == 'the-odds-api':
        # 计算隐含概率
        home_odds = real_odds['home_win']
        draw_odds = real_odds['draw']
        away_odds = real_odds['away_win']
        
        home_prob = (1 / home_odds) * 100
        draw_prob = (1 / draw_odds) * 100
        away_prob = (1 / away_odds) * 100
        
        total = home_prob + draw_prob + away_prob
        home_win_pct = round(home_prob / total * 100, 1)
        draw_pct = round(draw_prob / total * 100, 1)
        away_win_pct = round(away_prob / total * 100, 1)
        
        print(f"[MARKET] 市场概率: 主{home_win_pct}% 平{draw_pct}% 客{away_win_pct}%")
    
    print(f"[ANALYZE] {match_request['home_team']} vs {match_request['away_team']}")
    
    response = requests.post(f"{BASE_URL}/analyze", json=match_request)
    result = response.json()
    
    return result


def print_analysis_result(result: Dict[str, Any], market_probs: Dict[str, float] = None):
    """打印分析结果"""
    
    if result.get("status") == "blocked":
        print(f"[BLOCKED] 被风控拦截: {result.get('reason', '')}")
        print(f"[RISK] 风险等级: {result.get('risk_level', 'HIGH')}")
        return
    
    match_info = result.get("match", {})
    decision = result.get("decision", {})
    stake = result.get("stake", {})
    
    # 确保联赛名显示正确
    league = match_info.get('league', '其他联赛')
    if league == 'Unknown':
        league = '其他联赛'
    
    print(f"\n[RESULT] 分析结果:")
    print(f"  比赛: {match_info.get('home_team')} vs {match_info.get('away_team')}")
    print(f"  联赛: {league}")
    
    # 优先显示市场概率（如果有）
    if market_probs:
        print(f"\n[MARKET] 市场概率（推荐参考）:")
        print(f"  主胜概率: {market_probs.get('home_win', 0):.1f}%")
        print(f"  平局概率: {market_probs.get('draw', 0):.1f}%")
        print(f"  客胜概率: {market_probs.get('away_win', 0):.1f}%")
    
    # 显示 9 Agents 预测（仅供参考）
    recommended = decision.get("recommended_outcome", "unknown")
    prediction = decision.get("prediction", {})
    
    print(f"\n[AGENTS] 9 Agents 预测（仅供参考）:")
    print(f"  推荐: {recommended}")
    print(f"  主胜概率: {prediction.get('home_win', 0):.1f}%")
    print(f"  平局概率: {prediction.get('draw', 0):.1f}%")
    print(f"  客胜概率: {prediction.get('away_win', 0):.1f}%")
    
    # 投注建议
    if stake:
        print(f"\n[STAKE] 投注建议:")
        print(f"  投注金额: ¥{stake.get('stake', 0):.2f}")
        print(f"  凯利比例: {stake.get('safe_fraction', 0)*100:.2f}%")
        print(f"  预期价值: {stake.get('expected_value', 0):.2f}%")
    
    # 风控信息
    risk = result.get("risk_control", {})
    if risk:
        print(f"\n[RISK] 风控:")
        print(f"  风险等级: {risk.get('risk_level', 'UNKNOWN')}")
        if risk.get("warnings"):
            print(f"  警告: {', '.join(risk['warnings'])}")
    
    print("\n" + "="*50)


async def main():
    """主工作流"""
    print("[START] Football Quant OS - 完整预测工作流")
    print("="*50)
    print()
    
    # 步骤 1: 获取今天比赛
    fixtures = await get_today_fixtures()
    if not fixtures:
        print("[ERROR] 今天没有比赛或获取失败")
        return
    
    # 步骤 2: 选择重点比赛
    print("[SELECT] 选择重点比赛...")
    key_matches = select_key_matches(fixtures, top_n=3)
    
    print(f"[INFO] 选中 {len(key_matches)} 场重点比赛:")
    for i, match in enumerate(key_matches, 1):
        league = match.get('league', '其他联赛')
        if league == 'Unknown':
            league = '其他联赛'
        print(f"  {i}. {match.get('home_team')} vs {match.get('away_team')} ({league})")
    print()
    
    # 步骤 3: 分析每场比赛
    print("[PREDICT] 启动 9 Agents 预测分析...")
    print("="*50)
    
    for match in key_matches:
        # 计算市场概率
        market_probs = None
        real_odds = await get_match_odds(
            match.get('home_team', ''), 
            match.get('away_team', ''), 
            match.get('league', 'Unknown')
        )
        if real_odds and 'home_win' in real_odds:
            home_odds = real_odds['home_win']
            draw_odds = real_odds['draw']
            away_odds = real_odds['away_win']
            
            home_prob = (1 / home_odds) * 100
            draw_prob = (1 / draw_odds) * 100
            away_prob = (1 / away_odds) * 100
            
            total = home_prob + draw_prob + away_prob
            market_probs = {
                'home_win': round(home_prob / total * 100, 1),
                'draw': round(draw_prob / total * 100, 1),
                'away_win': round(away_prob / total * 100, 1)
            }
        
        result = await analyze_match(match)
        print_analysis_result(result, market_probs)
        await asyncio.sleep(1)  # 避免请求过快
    
    print("\n[DONE] 分析完成！")
    print("[ADVICE] 请根据以上分析做出投资决策")


if __name__ == "__main__":
    asyncio.run(main())
