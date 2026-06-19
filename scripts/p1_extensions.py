#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1 Extensions for predict_v6.py
自进化引擎 + 市场微结构分析

用法:
    from p1_extensions import apply_p1_extensions
    apply_p1_extensions(PredictorV6)
"""

from datetime import datetime
from pathlib import Path
import json
from typing import Dict, Any

project_root = Path(__file__).parent.parent


def _apply_evolution(self, match_info: Dict) -> Dict[str, Any]:
    """自进化权重调整 - SelfEvolutionEngine"""
    try:
        # 加载历史预测日志
        history_file = project_root / 'logs' / 'prediction_history.json'
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
            self.evolution_engine.load_history(history)
        
        # 调整模型权重
        adjusted_weights = self.evolution_engine.adjust_weights(self.models_used)
        
        if adjusted_weights and len(adjusted_weights) == len(self.ensemble._models):
            original = self.ensemble._weights.copy()
            for i, w in enumerate(adjusted_weights):
                self.ensemble._weights[i] = w
            
            return {
                'status': 'adjusted',
                'original_weights': [round(w, 3) for w in original],
                'adjusted_weights': [round(w, 3) for w in adjusted_weights],
                'adjustment_reason': 'historical_performance'
            }
        
        return {'status': 'no_adjustment', 'reason': 'insufficient_history'}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def _analyze_market_micro(self, match_info: Dict) -> Dict[str, Any]:
    """市场微结构分析 - MarketMicrostructureEngine"""
    try:
        # 加载历史数据
        history_file = project_root / 'logs' / 'market_micro_history.json'
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
            self.market_micro.load_history(history)
        
        # 创建赔率快照
        snapshot = self.market_micro.create_snapshot({
            'match_id': f"{match_info.get('home', '')}_vs_{match_info.get('away', '')}",
            'odds': {
                'home': match_info.get('odds_home', 2.0),
                'draw': match_info.get('odds_draw', 3.0),
                'away': match_info.get('odds_away', 3.0)
            },
            'timestamp': datetime.now().isoformat()
        })
        
        # 检测诱盘信号
        signals = self.market_micro.detect_traps(snapshot)
        
        # 检测资金动向
        steam = self.market_micro.detect_steam(snapshot)
        
        return {
            'status': 'analyzed',
            'snapshot_id': snapshot.get('id', 'unknown'),
            'trap_signals': signals,
            'steam_signals': steam,
            'market_sentiment': self.market_micro.get_sentiment(snapshot),
            'warnings': [s['description'] for s in signals if s.get('severity') == 'high']
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}


def _load_prediction_history(self) -> None:
    """加载历史预测日志"""
    try:
        history_file = project_root / 'logs' / 'prediction_history.json'
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
            self.evolution_engine.load_history(history)
    except Exception:
        pass


def _load_market_micro_history(self) -> None:
    """加载市场微结构历史数据"""
    try:
        history_file = project_root / 'logs' / 'market_micro_history.json'
        if history_file.exists():
            with open(history_file, 'r') as f:
                history = json.load(f)
            self.market_micro.load_history(history)
    except Exception:
        pass


def apply_p1_extensions(PredictorV6Class):
    """将P1扩展方法应用到PredictorV6类"""
    PredictorV6Class._apply_evolution = _apply_evolution
    PredictorV6Class._analyze_market_micro = _analyze_market_micro
    PredictorV6Class._load_prediction_history = _load_prediction_history
    PredictorV6Class._load_market_micro_history = _load_market_micro_history
