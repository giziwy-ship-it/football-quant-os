#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务执行入口 - Football Quant OS (修复版)
整合所有 Agent、模型和调度器
修复: 资金信号映射、GeneEngine变量名、冗余运行、数据传递
"""

import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')

from typing import Dict, Any

from core.scheduler import PipelineScheduler, AsyncScheduler
from core.event_bus import event_bus, CHANNELS
from core.config import config

from agents.datascout_v2 import DataScout
from agents.gene_engine import TeamEvaluator, GeneEngine
from agents.analyst_v2 import Analyst
from agents.committee_v2 import Committee
from agents.risk_control_v2 import RiskControl

from models.matrix_108 import ProbabilityMatrix108
from models.kelly import Kelly
from models.historical_odds import HistoricalOddsFactor


# 资金信号映射（中文 → 英文）
SIGNAL_MAP = {
    "强烈看好主胜": "strong_home",
    "看好主胜": "home_win",
    "看好平局": "draw",
    "看好客胜": "away_win",
    "强烈看好客胜": "strong_away",
    "中性": "neutral"
}


async def run_match_task(match: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行完整比赛分析任务
    
    三阶段流水线：
    Phase 1: DataScout + Analyst (并行)
    Phase 2: Committee (综合)
    Phase 3: RiskControl (风控)
    """
    
    bankroll = match.get('bankroll', config.DEFAULT_BANKROLL)
    home_team = match.get('home_team', '')
    away_team = match.get('away_team', '')
    league = match.get('league', 'Unknown')
    
    # ===== 预处理：新系统 =====
    
    # 1. 实力评定
    evaluator = TeamEvaluator()
    evaluator.evaluate(
        home_team, league,
        match.get('home_team_rank', 8),
        match.get('home_recent_5')
    )
    evaluator.evaluate(
        away_team, league,
        match.get('away_team_rank', 8),
        match.get('away_recent_5')
    )
    strength_matchup = evaluator.matchup(home_team, away_team)
    
    # 2. 108矩阵
    matrix = ProbabilityMatrix108()
    matrix_gap = strength_matchup.get('matrix_gap', 'even')
    matrix_result = matrix.apply_to_match(matrix_gap)
    
    # 3. 基因分析
    gene_engine = GeneEngine()
    gene_engine.evaluate(home_team, manual_scores=match.get('home_team_genes'))
    gene_engine.evaluate(away_team, manual_scores=match.get('away_team_genes'))
    gene_matchup = gene_engine.analyze_matchup(home_team, away_team)
    
    # 4. 历史赔率因素分析
    historical_odds = HistoricalOddsFactor()
    odds = match.get('market_odds', {})
    historical_result = historical_odds.run({
        "home_team": home_team,
        "away_team": away_team,
        "market_odds": odds,
        "league": league,
        "base_probs": matrix_result.get('probabilities', {"home_win": 40, "draw": 30, "away_win": 30}),
        "money_flow_signal": "neutral"
    })
    
    # 将矩阵概率注入 match_data 作为基础概率
    if 'probabilities' in matrix_result:
        probs = matrix_result['probabilities']
        match['home_win'] = probs.get('home_win', 40)
        match['draw'] = probs.get('draw', 30)
        match['away_win'] = probs.get('away_win', 30)
    
    # ===== 优先级1: 真实赔率概率（最高优先级）=====
    market_odds = match.get('market_odds', {})
    if market_odds and all(k in market_odds for k in ['home_win', 'draw', 'away_win']):
        # 赔率转概率
        home_odds = market_odds['home_win']
        draw_odds = market_odds['draw']
        away_odds = market_odds['away_win']
        
        home_prob = (1 / home_odds) * 100
        draw_prob = (1 / draw_odds) * 100
        away_prob = (1 / away_odds) * 100
        
        total = home_prob + draw_prob + away_prob
        match['home_win'] = round(home_prob / total * 100, 2)
        match['draw'] = round(draw_prob / total * 100, 2)
        match['away_win'] = round(away_prob / total * 100, 2)
        
        print(f"[Tasks] 优先级1 - 真实赔率概率: 主{match['home_win']}% 平{match['draw']}% 客{match['away_win']}%")
    
    # ===== 优先级2: 历史赔率调整（次优先级，不覆盖真实赔率）=====
    elif historical_result.get('probability_adjustment', {}).get('adjusted'):
        adj_probs = historical_result['probability_adjustment']['adjusted_probs']
        match['home_win'] = adj_probs.get('home_win', match.get('home_win', 40))
        match['draw'] = adj_probs.get('draw', match.get('draw', 30))
        match['away_win'] = adj_probs.get('away_win', match.get('away_win', 30))
        print(f"[Tasks] 优先级2 - 历史赔率调整: 主{match['home_win']}% 平{match['draw']}% 客{match['away_win']}%")
    
    # ===== 优先级3: 108矩阵概率（默认）=====
    else:
        print(f"[Tasks] 优先级3 - 108矩阵概率: 主{match['home_win']}% 平{match['draw']}% 客{match['away_win']}%")
    
    # ===== Phase 1: Agent 并行分析 =====
    scheduler = PipelineScheduler()
    scheduler.add_phase1([
        DataScout(),
        Analyst()
    ])
    scheduler.add_phase2(Committee())
    scheduler.add_phase3([RiskControl()])
    
    # 确保 match 中包含真实赔率概率（传递给 Agents）
    print(f"[Tasks] 传入 Agents 的概率: 主{match.get('home_win', 40)}% 平{match.get('draw', 30)}% 客{match.get('away_win', 30)}%")
    
    pipeline_result = await scheduler.run(match)
    
    # 提取资金信号传递给Committee（修复：使用正确的变量名和信号映射）
    phase1_results = pipeline_result.get('phase1', {})
    analyst_result = phase1_results.get('Analyst', {})
    
    # 收集所有Agent观点（修复：使用正确的变量名 gene_matchup）
    opinions = []
    for agent_name, agent_result in phase1_results.items():
        if isinstance(agent_result, dict) and 'prediction' in agent_result:
            opinions.append(agent_result)
    
    # 添加基因引擎观点（修复：使用 gene_matchup 而非 gene_analysis）
    if 'gene_matchup' in locals() and gene_matchup:
        opinions.append({
            "agent": "GeneEngine",
            "prediction": {
                "home_win": gene_matchup.get('home_advantage', 50),
                "draw": 30,
                "away_win": 70 - gene_matchup.get('home_advantage', 50)
            },
            "confidence": 0.75
        })
    
    # 添加108矩阵观点
    if 'matrix_result' in locals() and 'probabilities' in matrix_result:
        opinions.append({
            "agent": "Matrix108",
            "prediction": matrix_result['probabilities'],
            "confidence": 0.8
        })
    
    # 添加历史赔率因素观点
    if 'historical_result' in locals() and historical_result:
        hist_adj = historical_result.get('probability_adjustment', {})
        if hist_adj.get('adjusted'):
            opinions.append({
                "agent": "HistoricalOdds",
                "prediction": hist_adj['adjusted_probs'],
                "confidence": historical_result.get('pattern', {}).get('confidence', 0.7),
                "key_factors": historical_result.get('key_factors', [])
            })
    
    # 如果有资金流向分析，传递给Committee（修复：使用信号映射）
    if 'money_flow_analysis' in analyst_result:
        money_flow = analyst_result['money_flow_analysis']
        
        # 创建新的 Committee 对象（带资金信号）
        committee_obj = Committee()
        committee_obj.receive_other_opinions(opinions)
        
        # 转换资金信号格式（修复：使用 SIGNAL_MAP）
        raw_signal = money_flow.get('signal', 'NEUTRAL')
        signal_type = SIGNAL_MAP.get(raw_signal, raw_signal.lower().replace(' ', '_'))
        
        committee_obj.receive_fund_signals([{
            "signal_type": signal_type,
            "confidence": money_flow.get('confidence', 0.5),
            "direction": money_flow.get('direction', 'neutral'),
            "strength": money_flow.get('strength', 'neutral'),
            "source": "money_flow",
            "weight": 1.0
        }])
        
        # 重新运行 Committee 决策（带资金信号）
        committee_result = committee_obj.run(match)
        pipeline_result['phase2']['Committee'] = committee_result
    
    # ===== 决策与执行 =====
    committee_result = pipeline_result['phase2'].get('Committee', {})
    
    # 组装完整数据给 RiskControl
    risk_input = {
        **match,
        "committee_prediction": committee_result.get('prediction', {}),
        "recommended_outcome": committee_result.get('recommended_outcome', 'home_win')
    }
    
    # 如果有资金流向分析，传递给 RiskControl
    if 'money_flow_analysis' in analyst_result:
        risk_input["money_flow_analysis"] = analyst_result['money_flow_analysis']
    
    # 运行 RiskControl
    risk_control = RiskControl()
    risk_result = risk_control.run(risk_input)
    pipeline_result['phase3']['RiskControl'] = risk_result
    
    if not risk_result.get('allow', True):
        event_bus.publish(CHANNELS['RISK_ALERT'], {
            'match': f"{home_team} vs {away_team}",
            'reason': risk_result.get('warnings', [])
        })
        return {
            "status": "blocked",
            "reason": "risk control",
            "risk_level": risk_result.get('risk_level', 'HIGH'),
            "warnings": risk_result.get('warnings', []),
            "match": {
                "home_team": home_team,
                "away_team": away_team,
                "league": league
            },
            "team_strengths": strength_matchup,
            "matrix_108": matrix_result,
            "gene_analysis": gene_matchup,
            "historical_odds": historical_result,
            "agent_results": pipeline_result,
            "decision": committee_result,
            "risk_control": risk_result
        }
    
    # 凯利计算（使用市场概率或 Committee 概率）
    recommended = committee_result.get('recommended_outcome', 'home_win')
    
    # 优先使用市场概率（如果有真实赔率）
    if market_odds and all(k in market_odds for k in ['home_win', 'draw', 'away_win']):
        # 计算市场概率
        home_odds = market_odds['home_win']
        draw_odds = market_odds['draw']
        away_odds = market_odds['away_win']
        
        home_prob = (1 / home_odds) * 100
        draw_prob = (1 / draw_odds) * 100
        away_prob = (1 / away_odds) * 100
        
        total = home_prob + draw_prob + away_prob
        market_probs = {
            'home_win': round(home_prob / total * 100, 2),
            'draw': round(draw_prob / total * 100, 2),
            'away_win': round(away_prob / total * 100, 2)
        }
        
        probability = market_probs.get(recommended, 50) / 100
        print(f"[Tasks] 使用市场概率计算凯利: {recommended} = {probability*100:.1f}%")
    else:
        # 使用 Committee 预测概率
        probability = committee_result.get('prediction', {}).get(recommended, 50) / 100
        print(f"[Tasks] 使用Committee概率计算凯利: {recommended} = {probability*100:.1f}%")
    
    odds = match.get('market_odds', {}).get(recommended, 2.0)
    
    # 基础凯利计算
    kelly = Kelly(bankroll=bankroll)
    base_stake = kelly.calculate(probability, odds)
    
    # 应用 RiskControl 的资金流调整
    final_stake = base_stake.copy()
    if 'kelly_adjustment' in risk_result:
        ka = risk_result['kelly_adjustment']
        adjusted_fraction = ka.get('adjusted_kelly', base_stake['safe_fraction'])
        final_stake['safe_fraction'] = adjusted_fraction
        final_stake['stake'] = bankroll * adjusted_fraction
        final_stake['adjustment_reason'] = ka.get('adjustment_reason', '')
    
    stake_result = final_stake
    
    # 发布事件
    event_bus.publish(CHANNELS['MATCH_ANALYZED'], {
        'match': f"{home_team} vs {away_team}",
        'decision': recommended,
        'stake': stake_result['stake']
    })
    
    return {
        "status": "success",
        "match": {
            "home_team": home_team,
            "away_team": away_team,
            "league": league
        },
        "team_strengths": strength_matchup,
        "matrix_108": matrix_result,
        "gene_analysis": gene_matchup,
        "historical_odds": historical_result,
        "agent_results": pipeline_result,
        "decision": committee_result,
        "risk_control": risk_result,
        "stake": stake_result
    }
