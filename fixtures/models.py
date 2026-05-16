#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
赛程模块数据模型
Football Quant OS - Fixtures Module
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import date


class MatchFixtureResponse(BaseModel):
    """API响应模型 - 单场比赛"""
    match_id: str
    home_team: str
    away_team: str
    home_team_en: str
    away_team_en: str
    league: str
    league_en: str
    match_time: str
    status: str
    venue: Optional[str] = None
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "match_id": "12345",
                "home_team": "阿森纳",
                "away_team": "切尔西",
                "home_team_en": "Arsenal",
                "away_team_en": "Chelsea",
                "league": "英超",
                "league_en": "English Premier League",
                "match_time": "2026-05-05 22:00",
                "status": "Scheduled",
                "venue": "Emirates Stadium",
                "home_score": None,
                "away_score": None
            }
        }


class FixturesResponse(BaseModel):
    """API响应模型 - 赛程列表"""
    date: str
    total: int
    leagues: List[str]
    fixtures: List[MatchFixtureResponse]
    
    class Config:
        json_schema_extra = {
            "example": {
                "date": "2026-05-05",
                "total": 15,
                "leagues": ["英超", "西甲", "意甲"],
                "fixtures": []
            }
        }


class FixturesErrorResponse(BaseModel):
    """API错误响应"""
    error: str
    detail: Optional[str] = None
