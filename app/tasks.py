#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
任务执行入口 - Football Quant OS v5.2.0 整合版
支持 v5.2.0 run_prediction() + v4.0 PipelineScheduler fallback
Group Stage Context 已整合
"""

import sys
import os
import json
import asyncio
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path for v5.2.0 imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from core.config import config
from core.logger import logger
from core.config_loader import load_config

# v5.2.0 imports
from scripts.predict import run_prediction as v5_predict
from models.kelly_integration import get_kelly_recommendations

# v4.0 fallback imports
from core.scheduler import PipelineScheduler
from core.config_loader import load_config


def _map_team_name(team_name: str) -> str:
    """Map Chinese team names to English for v5.2.0 model"""
    name_map = {
        '捷克': 'Czechia', '南非': 'South Africa',
        '墨西哥': 'Mexico', '韩国': 'Korea Republic',
        '加拿大': 'Canada', '卡塔尔': 'Qatar',
        '瑞士': 'Switzerland', '波黑': 'Bosnia & Herzegovina',
        '法国': 'France', '塞内加尔': 'Senegal',
        '伊拉克': 'Iraq', '挪威': 'Norway',
        '阿根廷': 'Argentina', '阿尔及利亚': 'Algeria',
        '奥地利': 'Austria', '约旦': 'Jordan',
        '葡萄牙': 'Portugal', '刚果(金)': 'Congo DR',
        '英格兰': 'England', '克罗地亚': 'Croatia',
        '加纳': 'Ghana', '巴拿马': 'Panama',
        '乌兹别克斯坦': 'Uzbekistan', '哥伦比亚': 'Colombia',
    }
    return name_map.get(team_name, team_name)


def _extract_odds(market_odds: dict) -> tuple:
    """Extract 1X2 and OU odds from market_odds dict"""
    home_odds = market_odds.get('home', market_odds.get('1', 2.0))
    draw_odds = market_odds.get('draw', market_odds.get('X', 3.0))
    away_odds = market_odds.get('away', market_odds.get('2', 3.0))
    over_odds = market_odds.get('over', 1.80)
    under_odds = market_odds.get('under', 2.05)
    ou_line = market_odds.get('ou_line', 2.5)
    return home_odds, draw_odds, away_odds, ou_line, over_odds, under_odds


def _run_v5_prediction(match_data: dict) -> dict:
    """Run v5.2.0 prediction with group_stage_context support"""
    home = _map_team_name(match_data.get('home_team', ''))
    away = _map_team_name(match_data.get('away_team', ''))
    
    home_odds, draw_odds, away_odds, ou_line, over_odds, under_odds = _extract_odds(
        match_data.get('market_odds', {})
    )
    
    # Extract xG if available, else estimate from rank
    home_rank = match_data.get('home_team_rank', 50)
    away_rank = match_data.get('away_team_rank', 50)
    home_xg = match_data.get('home_xg', max(0.8, 2.0 - home_rank/50))
    away_xg = match_data.get('away_xg', max(0.5, 1.5 - away_rank/50))
    
    # Extract region/experience
    home_region = match_data.get('home_region', 'europe')
    away_region = match_data.get('away_region', 'europe')
    home_exp = match_data.get('home_experience', 'experienced')
    away_exp = match_data.get('away_experience', 'experienced')
    
    # Stage and group standings
    stage = match_data.get('stage', 'group')
    is_first = match_data.get('is_first_match', False)
    group_standings = match_data.get('group_standings', None)
    
    # Run v5.2.0 prediction
    result = v5_predict(
        home=home, away=away,
        odds_home=home_odds, odds_draw=draw_odds, odds_away=away_odds,
        stage=stage, ou_line=ou_line,
        odds_over=over_odds, odds_under=under_odds,
        home_xg=home_xg, away_xg=away_xg,
        home_poss=match_data.get('home_possession', 50),
        away_poss=match_data.get('away_possession', 50),
        is_first_match=is_first,
        home_region=home_region, away_region=away_region,
        home_experience=home_exp, away_experience=away_exp,
        group_standings=group_standings,
        bankroll=match_data.get('bankroll', 100000),
        kelly_fraction=match_data.get('kelly_fraction', 0.25)
    )
    
    # Extract simplified recommendations for API response
    markets = result.get('markets', {})
    m1x2 = markets.get('1x2', {})
    ou = markets.get('over_under', {})
    
    model_probs = m1x2.get('model', {}) if isinstance(m1x2.get('model'), dict) else {}
    home_prob = model_probs.get('home', 0.33)
    draw_prob = model_probs.get('draw', 0.33)
    away_prob = model_probs.get('away', 0.33)
    
    if home_prob >= draw_prob and home_prob >= away_prob:
        pred_1x2 = '主胜'
    elif away_prob >= home_prob and away_prob >= draw_prob:
        pred_1x2 = '客胜'
    else:
        pred_1x2 = '平局'
    
    ou_rec = ou.get('recommendation', 'N/A')
    
    # Kelly
    kelly = result.get('kelly', {})
    kelly_recs = kelly.get('recommendations', [])
    
    return {
        'version': '5.2.0',
        'system': 'Football Quant OS v5.2.0 (XGBoost Ensemble + Poisson + Heuristic)',
        'match': f"{home} vs {away}",
        'prediction': {
            '1x2': {
                'probabilities': {
                    'home': round(home_prob, 4),
                    'draw': round(draw_prob, 4),
                    'away': round(away_prob, 4)
                },
                'recommendation': pred_1x2,
                'confidence': result.get('confidence', 0)
            },
            'over_under': {
                'line': ou_line,
                'recommendation': ou_rec,
                'lambda': ou.get('lambda', 'N/A')
            },
            'kelly': kelly_recs
        },
        'group_context': result.get('group_context', {}),
        'group_context_display': result.get('group_context_display', ''),
        'upset_score': result.get('upset_score', 0),
        'recommendations': result.get('recommendations', []),
        'raw_result': result  # Full result for advanced users
    }


async def _run_v4_fallback(match_data: dict) -> dict:
    """v4.0 fallback using PipelineScheduler"""
    scheduler = PipelineScheduler(
        bankroll=match_data.get('bankroll', 10000)
    )
    
    # Build pipeline config
    pipeline_config = load_config()
    
    # Run pipeline
    result = await scheduler.execute(
        match_data=match_data,
        config=pipeline_config,
        agents=match_data.get('agents', None)
    )
    
    return {
        'version': '4.0',
        'system': 'Football Quant OS v4.0 (PipelineScheduler)',
        'result': result
    }


async def run_match_task(match_data: dict) -> dict:
    """
    主执行入口 - 优先使用 v5.2.0，失败时 fallback 到 v4.0
    """
    task_id = match_data.get('task_id', 'unknown')
    logger.info(f"[Task {task_id}] Starting prediction task")
    
    # Try v5.2.0 first
    try:
        logger.info(f"[Task {task_id}] Trying v5.2.0 prediction with group_stage_context")
        result = _run_v5_prediction(match_data)
        logger.info(f"[Task {task_id}] v5.2.0 prediction succeeded")
        return result
    except Exception as e:
        logger.warning(f"[Task {task_id}] v5.2.0 failed: {e}, falling back to v4.0")
    
    # Fallback to v4.0
    try:
        result = await _run_v4_fallback(match_data)
        logger.info(f"[Task {task_id}] v4.0 fallback succeeded")
        return result
    except Exception as e:
        logger.error(f"[Task {task_id}] v4.0 fallback also failed: {e}")
        return {
            'error': 'Both v5.2.0 and v4.0 failed',
            'v5_error': str(e) if 'e' in dir() else 'unknown',
            'v4_error': str(e)
        }


# For direct testing
if __name__ == '__main__':
    # Test v5.2.0 integration
    test_data = {
        'home_team': '捷克',
        'away_team': '南非',
        'market_odds': {'home': 1.80, 'draw': 3.30, 'away': 4.10, 'over': 1.00, 'under': 0.80, 'ou_line': 2.25},
        'home_team_rank': 45,
        'away_team_rank': 60,
        'stage': 'group',
        'group_standings': {
            'Czechia': {'points': 0, 'played': 1, 'goal_diff': -1},
            'South Africa': {'points': 0, 'played': 1, 'goal_diff': -2}
        }
    }
    result = asyncio.run(run_match_task(test_data))
    print(json.dumps(result, ensure_ascii=False, indent=2))
