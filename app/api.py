#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API路由 - Football Quant OS (P0 安全修复版)
轻量认证：开发模式 localhost 免认证，生产模式强制认证
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import date

from app.auth import require_auth, validator
from core.config import config
from app.tasks import run_match_task

router = APIRouter()


class MatchRequest(BaseModel):
    home_team: str = Field(..., min_length=1, max_length=50)
    away_team: str = Field(..., min_length=1, max_length=50)
    league: str = Field(..., min_length=1, max_length=50)
    home_team_rank: Optional[int] = Field(8, ge=1, le=100)
    away_team_rank: Optional[int] = Field(8, ge=1, le=100)
    home_recent_5: Optional[List[str]] = None
    away_recent_5: Optional[List[str]] = None
    home_team_genes: Optional[Dict[str, float]] = None
    away_team_genes: Optional[Dict[str, float]] = None
    market_odds: Dict[str, float]
    bankroll: Optional[float] = Field(10000, ge=100)
    # v5.2.0 Group Stage Context
    stage: Optional[str] = Field('group', description='比赛阶段: group/knockout/final')
    is_first_match: Optional[bool] = Field(False, description='是否首战')
    home_region: Optional[str] = Field('europe', description='主队区域')
    away_region: Optional[str] = Field('europe', description='客队区域')
    home_experience: Optional[str] = Field('experienced', description='主队经验')
    away_experience: Optional[str] = Field('experienced', description='客队经验')
    group_standings: Optional[Dict[str, Any]] = Field(None, description='小组赛积分榜')
    enable_v5: Optional[bool] = Field(True, description='优先使用 v5.2.0')
    agents: Optional[List[str]] = Field(None, description='v4.0智能体列表')


class BacktestRequest(BaseModel):
    dataset_path: Optional[str] = Field("data/backtest_dataset.json", max_length=200)
    bankroll: Optional[float] = Field(1000, ge=100)
    strategy: Optional[str] = Field("kelly_compressed", max_length=50)


# ===== 健康检查（免认证） =====

@router.get("/health")
async def health_check():
    """健康检查端点（永远免认证）"""
    return {
        "status": "ok",
        "version": config.VERSION,
        "auth_mode": config.AUTH_MODE,
        "system": config.SYSTEM_NAME
    }


# ===== Fixtures 赛程模块 =====

@router.get("/fixtures/today")
async def get_today_fixtures(request: Request, _=Depends(require_auth)):
    """获取今天所有比赛赛程"""
    from fixtures.espn_client import ESPNClient
    from fixtures.models import MatchFixtureResponse, FixturesResponse
    
    client = ESPNClient()
    try:
        fixtures = await client.fetch_fixtures()
        await client.close()
        
        fixture_responses = []
        leagues_set = set()
        
        for f in fixtures:
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
async def get_fixtures_by_date(query_date: str, request: Request, _=Depends(require_auth)):
    """获取指定日期的比赛赛程"""
    # 输入验证
    query_date = validator.validate_date(query_date)
    
    from fixtures.espn_client import ESPNClient
    from fixtures.models import MatchFixtureResponse, FixturesResponse
    
    client = ESPNClient()
    try:
        fixtures = await client.fetch_fixtures(query_date)
        await client.close()
        
        fixture_responses = []
        leagues_set = set()
        
        for f in fixtures:
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
async def analyze(match: MatchRequest, request: Request, _=Depends(require_auth)):
    """分析单场比赛"""
    result = await run_match_task(match.dict())
    return result


@router.post("/backtest")
async def backtest(request: BacktestRequest, req: Request, _=Depends(require_auth)):
    """运行回测"""
    from backtest.engine import BacktestEngine
    engine = BacktestEngine(bankroll=request.bankroll)
    result = engine.run(path=request.dataset_path)
    return result


@router.get("/matrix/108")
async def get_matrix_108(strength_gap: str, first_scorer: Optional[str] = None, request: Request = None, _=Depends(require_auth)):
    """查询108组合概率矩阵"""
    from models.matrix_108 import ProbabilityMatrix108
    matrix = ProbabilityMatrix108()
    result = matrix.apply_to_match(strength_gap, first_scorer)
    return result


@router.get("/agents")
async def list_agents(request: Request, _=Depends(require_auth)):
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
