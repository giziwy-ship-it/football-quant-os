#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FastAPI v4.0 路由 - 物理AI交易操作系统 REST API

Endpoints:
- POST /v4/predict       - 单场比赛预测
- POST /v4/analyze       - 市场微结构分析
- POST /v4/signal        - 交易信号生成
- POST /v4/execute       - 风控检查 + 执行
- GET  /v4/portfolio     - 组合状态
- GET  /v4/diagnose      - 系统诊断
- POST /v4/evolve        - 权重进化

Author: Naga Core Team
Version: 4.0.0
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime

# v4 核心引擎
from v4.core.physical_ai import PhysicalAI, TeamState, MarketState
from v4.core.market_micro import MarketMicrostructure, OddsSnapshot
from v4.core.trade_engine import TradingEngine
from v4.core.risk_engine_v4 import RiskEngine, Position, BankrollState
from v4.core.evolution import SelfEvolution


# ============ Pydantic Models ============

class TeamInput(BaseModel):
    name: str
    attack: float = 0.5
    defense: float = 0.5
    form: float = 0.5
    fatigue: float = 0.0
    morale: float = 0.5
    home_advantage: float = 0.0
    elo: float = 1500.0
    xg_for: float = 1.0
    xg_against: float = 1.0
    coach_factor: float = 0.0
    tournament_gene: float = 0.5


class OddsInput(BaseModel):
    home: float = 2.0
    draw: float = 3.5
    away: float = 2.0


class PredictRequest(BaseModel):
    match_id: str
    home_team: TeamInput
    away_team: TeamInput
    odds: OddsInput
    sentiment: float = 0.0
    money_flow: float = 0.0
    weather: float = 0.0


class MarketAnalyzeRequest(BaseModel):
    model_probs: Dict[str, float]
    market_probs: Dict[str, float]
    odds_history: List[Dict[str, Any]] = []
    bookmaker_odds: List[Dict[str, Any]] = None
    volume: float = 0.0


class SignalRequest(BaseModel):
    match_id: str
    probs: Dict[str, float]
    odds: Dict[str, float]
    upset_score: float = 0.0
    market_bias: str = "balanced"
    confidence: float = 0.7


class ExecuteRequest(BaseModel):
    match_id: str
    direction: str
    odds: float
    model_prob: float
    expected_value: float
    correlation: float = 0.0


class EvolveRequest(BaseModel):
    results: List[Dict[str, Any]]


# ============ Global State ============

app = FastAPI(title="Football Quant OS v4.0", version="4.0.0")

# 初始化引擎 (单例)
physical_ai = PhysicalAI()
market_micro = MarketMicrostructure()
trade_engine = TradingEngine()
risk_engine = RiskEngine(initial_bankroll=10000.0)
evolution = SelfEvolution()


# ============ Endpoints ============

@app.post("/v4/predict")
async def predict(request: PredictRequest):
    """
    物理AI预测
    
    输入球队数据，输出胜平负概率 + 冷门信号 + 大比分信号
    """
    try:
        home = TeamState(
            attack=request.home_team.attack,
            defense=request.home_team.defense,
            form=request.home_team.form,
            fatigue=request.home_team.fatigue,
            morale=request.home_team.morale,
            home_advantage=request.home_team.home_advantage,
            elo=request.home_team.elo,
            xg_for=request.home_team.xg_for,
            xg_against=request.home_team.xg_against,
            coach_factor=request.home_team.coach_factor,
            tournament_gene=request.home_team.tournament_gene
        )
        
        away = TeamState(
            attack=request.away_team.attack,
            defense=request.away_team.defense,
            form=request.away_team.form,
            fatigue=request.away_team.fatigue,
            morale=request.away_team.morale,
            home_advantage=0.0,
            elo=request.away_team.elo,
            xg_for=request.away_team.xg_for,
            xg_against=request.away_team.xg_against,
            coach_factor=request.away_team.coach_factor,
            tournament_gene=request.away_team.tournament_gene
        )
        
        market = MarketState(
            home_odds=request.odds.home,
            draw_odds=request.odds.draw,
            away_odds=request.odds.away
        )
        
        result = physical_ai.predict(
            home, away, market,
            sentiment=request.sentiment,
            money_flow=request.money_flow,
            weather=request.weather
        )
        
        return {
            "match_id": request.match_id,
            "timestamp": datetime.now().isoformat(),
            **result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v4/analyze")
async def analyze_market(request: MarketAnalyzeRequest):
    """
    市场微结构分析
    
    分析赔率变动、聪明钱流向、市场偏向
    """
    try:
        # 加载历史赔率
        for snapshot_data in request.odds_history:
            snapshot = OddsSnapshot(
                timestamp=datetime.fromisoformat(snapshot_data["timestamp"]),
                home_odds=snapshot_data["odds"]["home"],
                draw_odds=snapshot_data["odds"]["draw"],
                away_odds=snapshot_data["odds"]["away"]
            )
            market_micro.add_snapshot(snapshot)
        
        signal = market_micro.analyze(
            model_probs=request.model_probs,
            market_probs=request.market_probs,
            bookmaker_odds=request.bookmaker_odds,
            volume=request.volume
        )
        
        return {
            "timestamp": datetime.now().isoformat(),
            **signal.to_dict()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v4/signal")
async def generate_signal(request: SignalRequest):
    """
    生成交易信号
    
    综合模型概率和市场信号，输出交易决策
    """
    try:
        result = trade_engine.signal(
            probs=request.probs,
            odds=request.odds,
            upset_score=request.upset_score,
            market_bias=request.market_bias,
            confidence=request.confidence
        )
        
        return {
            "match_id": request.match_id,
            "timestamp": datetime.now().isoformat(),
            **result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v4/execute")
async def execute_trade(request: ExecuteRequest):
    """
    执行交易 (风控检查 + 执行)
    
    1. 风控检查
    2. 如果通过，记录持仓
    3. 返回结果
    """
    try:
        # 风控检查
        check = risk_engine.check(
            match_id=request.match_id,
            direction=request.direction,
            odds=request.odds,
            model_prob=request.model_prob,
            expected_value=request.expected_value,
            correlation_with_existing=request.correlation
        )
        
        executed = False
        if check.allowed:
            # 创建持仓
            position = Position(
                match_id=request.match_id,
                direction=request.direction,
                odds=request.odds,
                stake=check.position_size,
                model_prob=request.model_prob,
                expected_value=request.expected_value,
                timestamp=datetime.now()
            )
            executed = risk_engine.execute_bet(position, check)
        
        return {
            "match_id": request.match_id,
            "executed": executed,
            "risk_check": check.to_dict(),
            "portfolio": risk_engine.get_portfolio_summary()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v4/settle")
async def settle_trade(match_id: str, result: str):
    """
    结算交易
    
    Args:
        match_id: 比赛ID
        result: "home", "draw", "away" - 实际结果
    """
    try:
        # 检查是否有该比赛的持仓
        position = None
        for p in risk_engine.positions:
            if p.match_id == match_id:
                position = p
                break
        
        if not position:
            return {"error": f"No open position for match {match_id}"}
        
        won = position.direction == result
        pnl = risk_engine.settle_bet(match_id, won)
        
        # 记录到进化引擎
        evolution.record_result(
            "combined",
            {"home": position.model_prob if position.direction == "home" else 0,
             "draw": 0.33, "away": 0.33},  # 简化
            result,
            stake=position.stake,
            pnl=pnl
        )
        
        return {
            "match_id": match_id,
            "settled": True,
            "won": won,
            "pnl": round(pnl, 2),
            "bankroll": risk_engine.get_portfolio_summary()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v4/portfolio")
async def get_portfolio():
    """获取当前组合状态"""
    return risk_engine.get_portfolio_summary()


@app.get("/v4/diagnose")
async def diagnose():
    """系统诊断"""
    return {
        "timestamp": datetime.now().isoformat(),
        "physical_ai_version": physical_ai.VERSION,
        "market_micro_version": market_micro.VERSION,
        "trade_engine_version": trade_engine.VERSION,
        "risk_engine_version": risk_engine.VERSION,
        "evolution_version": evolution.VERSION,
        "evolution": evolution.diagnose(),
        "portfolio": risk_engine.get_portfolio_summary()
    }


@app.post("/v4/evolve")
async def evolve(request: EvolveRequest):
    """
    权重进化
    
    输入最近的比赛结果，更新模型权重
    """
    try:
        # 记录结果
        for r in request.results:
            evolution.record_result(
                r.get("model", "combined"),
                r.get("predicted_probs", {}),
                r.get("actual_result", ""),
                r.get("odds", {}),
                r.get("stake", 0),
                r.get("pnl", 0)
            )
        
        # 更新权重
        new_weights = evolution.update_weights()
        
        # 更新物理AI权重
        physical_ai.layer_weights.update(new_weights)
        
        return {
            "timestamp": datetime.now().isoformat(),
            "new_weights": {k: round(v, 4) for k, v in new_weights.items()},
            "diagnosis": evolution.diagnose()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 主入口 ============

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
