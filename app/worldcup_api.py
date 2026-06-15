#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
World Cup 2026 API Routes - Football Quant OS (P0 安全修复版)
轻量认证：开发模式 localhost 免认证，生产模式强制认证
"""

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import date
import os

from app.auth import require_auth, validator
from core.config import config

from data.worldcup2026_data import get_team, get_group, get_all_teams, GROUPS
from data.worldcup_fixtures import get_fixtures_by_date, get_fixtures_by_group, get_all_fixtures
from core.worldcup_integrator import WorldCupPipeline, NationalTeamEvaluator

router = APIRouter(prefix="/worldcup", tags=["worldcup"])

pipeline = WorldCupPipeline(bankroll=10000)


class TeamResponse(BaseModel):
    code: str
    name_en: str
    name_cn: str
    fifa_rank: int
    elo_rating: float
    confederation: str
    is_host: bool
    is_debut: bool
    wc_titles: int
    wc_appearances: int
    notes: str


class MatchAnalysisRequest(BaseModel):
    home_code: str = Field(..., min_length=2, max_length=4, pattern=r'^[A-Za-z]+$')
    away_code: str = Field(..., min_length=2, max_length=4, pattern=r'^[A-Za-z]+$')
    market_odds: Optional[Dict[str, float]] = None
    bankroll: Optional[float] = Field(10000, ge=100)
    stage: Optional[str] = Field('group', pattern=r'^(group|knockout)$')
    match_notes: Optional[str] = Field("", max_length=200)


class MatchAnalysisResponse(BaseModel):
    home_team: Dict[str, Any]
    away_team: Dict[str, Any]
    model_probability: Dict[str, float]
    hybrid: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    kelly: Optional[Dict[str, Any]] = None
    model_recommendation: Optional[Dict[str, Any]] = None


class HybridDemoRequest(BaseModel):
    stage: Optional[str] = Field('group', pattern=r'^(group|knockout)$')
    bankroll: Optional[float] = Field(10000, ge=100)


@router.get("/teams/{team_code}", response_model=TeamResponse)
async def get_team_info(team_code: str, request: Request, _=Depends(require_auth)):
    team_code = validator.validate_team_code(team_code)
    team = get_team(team_code.upper())
    if not team:
        return {"error": f"Team {team_code} not found"}
    return TeamResponse(
        code=team.fifa_code, name_en=team.name_en, name_cn=team.name_cn,
        fifa_rank=team.fifa_rank, elo_rating=team.elo_rating,
        confederation=team.confederation.value, is_host=team.is_host,
        is_debut=team.is_debut, wc_titles=team.wc_titles,
        wc_appearances=team.wc_appearances, notes=team.notes
    )


@router.get("/groups/{group}")
async def get_group_info(group: str, request: Request, _=Depends(require_auth)):
    group = group.upper()
    if len(group) != 1 or group not in "ABCDEFGHIJKL":
        return {"error": "Group must be a single letter A-L"}
    teams = get_group(group)
    if not teams:
        return {"error": f"Group {group} not found"}
    return {
        "group": group,
        "teams": [{"code": t.fifa_code, "name": t.name_en, "rank": t.fifa_rank,
                   "elo": t.elo_rating} for t in teams],
        "fixtures": [
            {"date": f.match_date, "time": f.match_time, "home": f.home_team, "away": f.away_team}
            for f in get_fixtures_by_group(group)
        ]
    }


@router.get("/fixtures/{fixture_date}")
async def get_fixtures_by_date_endpoint(fixture_date: str, request: Request, _=Depends(require_auth)):
    fixture_date = validator.validate_date(fixture_date)
    fixtures = get_fixtures_by_date(fixture_date)
    if not fixtures:
        return {"date": fixture_date, "fixtures": [], "message": "No fixtures on this date"}
    return {
        "date": fixture_date,
        "fixtures": [
            {"match_id": f.match_id, "group": f.group, "matchday": f.matchday,
             "home": f.home_team, "away": f.away_team, "time": f.match_time,
             "venue": f.venue, "city": f.city, "country": f.country}
            for f in fixtures
        ]
    }


@router.get("/fixtures/today")
async def get_today_fixtures(request: Request, _=Depends(require_auth)):
    today = date.today().isoformat()
    return await get_fixtures_by_date_endpoint(today, request)


@router.post("/analyze", response_model=MatchAnalysisResponse)
async def analyze_match(request: MatchAnalysisRequest, req: Request, _=Depends(require_auth)):
    home = request.home_code.upper()
    away = request.away_code.upper()
    market_data = None
    if request.market_odds:
        market_data = {
            'market_odds': request.market_odds,
            'market_prob': {k: 1/v for k, v in request.market_odds.items()}
        }
    pipeline = WorldCupPipeline(bankroll=request.bankroll, stage=request.stage)
    result = pipeline.analyze_match(home, away, market_data, request.match_notes)
    return MatchAnalysisResponse(
        home_team=result.get('home_team', {}),
        away_team=result.get('away_team', {}),
        model_probability=result.get('model_probability', {}),
        hybrid=result.get('hybrid'),
        decision=result.get('decision'),
        kelly=result.get('kelly'),
        model_recommendation=result.get('model_recommendation')
    )


@router.post("/hybrid-demo")
async def hybrid_demo(request: HybridDemoRequest, req: Request, _=Depends(require_auth)):
    """A+B Hybrid 策略演示端点"""
    pipeline = WorldCupPipeline(bankroll=request.bankroll, stage=request.stage)
    
    matches = [
        ("FRA", "SEN", {'home': 1.55, 'draw': 3.80, 'away': 6.50}, "France already qualified, Senegal need to win"),
        ("BRA", "SCO", {'home': 1.30, 'draw': 4.50, 'away': 10.00}, "Brazil heavy favorite"),
        ("ARG", "ALG", {'home': 1.25, 'draw': 5.50, 'away': 12.00}, "Argentina heavy favorite"),
        ("ESP", "URU", {'home': 2.10, 'draw': 3.20, 'away': 3.60}, "Even match, Spain slight favorite"),
        ("ENG", "CRO", {'home': 1.90, 'draw': 3.40, 'away': 4.20}, "England home favorite"),
    ]
    
    results = []
    for m in matches:
        home, away = m[0], m[1]
        market_odds = m[2]
        notes = m[3] if len(m) > 3 else ""
        market_data = {
            'market_odds': market_odds,
            'market_prob': {k: 1/v for k, v in market_odds.items()},
        }
        result = pipeline.analyze_match(home, away, market_data, notes)
        results.append({
            'match': f"{home} vs {away}",
            'hybrid': result.get('hybrid'),
            'model_probability': result.get('model_probability'),
        })
    
    return {
        'stage': request.stage,
        'bankroll': request.bankroll,
        'strategy': 'A+B Hybrid (ELO + Motivation)',
        'validation': '2022: Tight 60% WR, +3.9% return, 10.4% utilization',
        'matches': results
    }


@router.get("/strategy-info")
async def strategy_info(request: Request, _=Depends(require_auth)):
    """返回 A+B 策略配置信息"""
    return {
        'strategy': 'A+B Hybrid',
        'description': 'Pure ELO with positive edge + Motivation factor',
        'components': {
            'A': 'ELO-based probability + Kelly conservative sizing',
            'B': 'Motivation factor (qualified/do-or-die/rotation)',
        },
        'group_stage': {
            'pd_threshold': 0.03,
            'edge_threshold': 0.05,
            'kelly_fraction': 0.45,
            'max_bet': '3%',
            'daily_limit': '15%',
        },
        'knockout_stage': {
            'pd_threshold': 0.015,
            'edge_threshold': 0.03,
            'kelly_fraction': 0.45,
            'max_bet': '3%',
            'daily_limit': '15%',
        },
        'motivation': {
            'already_qualified': -0.08,
            'reserves_rotation': -0.08,
            'need_to_win': +0.05,
            'must_win': +0.05,
        },
        '2022_validation': {
            'tight_hybrid': {'wr': '60.0%', 'return': '+3.9%', 'utilization': '10.4%'},
            'loose_hybrid': {'wr': '50.0%', 'return': '+0.4%', 'utilization': '16.7%'},
            'pure_elo': {'wr': '48.5%', 'return': '-1.9%', 'utilization': '68.8%'},
        },
        'auth': {
            'mode': config.AUTH_MODE,
            'dev_mode': config.is_dev_mode(),
            'prod_mode': config.is_prod_mode(),
        }
    }


@router.get("/all-teams")
async def get_all_teams_endpoint(request: Request, _=Depends(require_auth)):
    teams = get_all_teams()
    return {
        "total": len(teams),
        "teams": [{"code": t.fifa_code, "name": t.name_en, "name_cn": t.name_cn,
                   "rank": t.fifa_rank, "group": next((g for g, codes in GROUPS.items() 
                                                         if t.fifa_code in codes), "?")}
                  for t in teams]
    }
