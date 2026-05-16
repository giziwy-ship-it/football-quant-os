#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由 - Football Quant OS
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from datetime import date
from app.tasks import run_match_task

router = APIRouter()


class MatchRequest(BaseModel):
    home_team: str
    away_team: str
    league: str
    home_team_rank: Optional[int] = 8
    away_team_rank: Optional[int] = 8
    home_recent_5: Optional[List[str]] = None
    away_recent_5: Optional[List[str]] = None
    home_team_genes: Optional[Dict[str, float]] = None
    away_team_genes: Optional[Dict[str, float]] = None
    market_odds: Dict[str, float]
    bankroll: Optional[float] = 10000


class BacktestRequest(BaseModel):
    dataset_path: Optional[str] = "data/backtest_dataset.json"
    bankroll: Optional[float] = 1000
    strategy: Optional[str] = "kelly_compressed"


# ===== Fixtures 赛程模块 =====

@router.get("/fixtures/today")
async def get_today_fixtures():
    """获取今天所有比赛赛程"""
    from fixtures.espn_client import ESPNClient
    from fixtures.models import MatchFixtureResponse, FixturesResponse
    
    client = ESPNClient()
    try:
        fixtures = await client.fetch_fixtures()
        await client.close()
        
        # 转换为响应模型
        fixture_responses = []
        leagues_set = set()
        
        for f in fixtures:
            # 确保联赛名不为空或 Unknown
            league = f.league if f.league and f.league != "Unknown" else "其他联赛"
            league_en = f.league_en if f.league_en and f.league_en != "Unknown" else "Other"
            
            fixture_responses.append(MatchFixtureResponse(
                match_id=f.match_id,
                home_team=f.home_team,
                away_team=f.away_team,
                home_team_en=f.home_team_en,
                away_team_en=f.away_team_en,
                league=league,
                league_en=league_en,
                match_time=f.match_time,
                status=f.status,
                venue=f.venue,
                home_score=f.home_score,
                away_score=f.away_score
            ))
            leagues_set.add(league)
        
        today = date.today().isoformat()
        
        return FixturesResponse(
            date=today,
            total=len(fixture_responses),
            leagues=list(leagues_set),
            fixtures=fixture_responses
        ).dict()
        
    except Exception as e:
        await client.close()
        return {"error": "Failed to fetch fixtures", "detail": str(e)}


@router.get("/fixtures/date/{query_date}")
async def get_fixtures_by_date(query_date: str):
    """
    获取指定日期的比赛赛程
    
    Args:
        query_date: 日期格式 YYYY-MM-DD (例如: 2026-05-05)
    """
    from fixtures.espn_client import ESPNClient
    from fixtures.models import MatchFixtureResponse, FixturesResponse
    
    # 验证日期格式
    try:
        validated_date = date.fromisoformat(query_date)
    except ValueError:
        return {"error": "Invalid date format", "detail": "Use YYYY-MM-DD format"}
    
    client = ESPNClient()
    try:
        fixtures = await client.fetch_fixtures(query_date)
        await client.close()
        
        fixture_responses = []
        leagues_set = set()
        
        for f in fixtures:
            # 确保联赛名不为空或 Unknown
            league = f.league if f.league and f.league != "Unknown" else "其他联赛"
            league_en = f.league_en if f.league_en and f.league_en != "Unknown" else "Other"
            
            fixture_responses.append(MatchFixtureResponse(
                match_id=f.match_id,
                home_team=f.home_team,
                away_team=f.away_team,
                home_team_en=f.home_team_en,
                away_team_en=f.away_team_en,
                league=league,
                league_en=league_en,
                match_time=f.match_time,
                status=f.status,
                venue=f.venue,
                home_score=f.home_score,
                away_score=f.away_score
            ))
            leagues_set.add(league)
        
        return FixturesResponse(
            date=query_date,
            total=len(fixture_responses),
            leagues=list(leagues_set),
            fixtures=fixture_responses
        ).dict()
        
    except Exception as e:
        await client.close()
        return {"error": "Failed to fetch fixtures", "detail": str(e)}


# ===== 原有分析模块 =====

@router.post("/analyze")
async def analyze(match: MatchRequest):
    """分析单场比赛"""
    result = await run_match_task(match.dict())
    return result


@router.post("/backtest")
async def backtest(request: BacktestRequest):
    """运行回测"""
    from backtest.engine import BacktestEngine
    engine = BacktestEngine(bankroll=request.bankroll)
    result = engine.run(path=request.dataset_path)
    return result


@router.get("/matrix/108")
async def get_matrix_108(strength_gap: str, first_scorer: Optional[str] = None):
    """查询108组合概率矩阵"""
    from models.matrix_108 import ProbabilityMatrix108
    matrix = ProbabilityMatrix108()
    result = matrix.apply_to_match(strength_gap, first_scorer)
    return result


@router.get("/agents")
async def list_agents():
    """列出所有Agent"""
    return {
        "agents": [
            {"name": "DataScout", "role": "数据侦察"},
            {"name": "GeneEngine", "role": "基因分析"},
            {"name": "Analyst", "role": "深度分析"},
            {"name": "Arbitrage", "role": "套利发现"},
            {"name": "TeamValue", "role": "球队估值"},
            {"name": "Committee", "role": "委员会决策"},
            {"name": "RiskControl", "role": "风险控制"},
            {"name": "Execution", "role": "执行交易"},
            {"name": "Evolution", "role": "进化学习"}
        ]
    }
