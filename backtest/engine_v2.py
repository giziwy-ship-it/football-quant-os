#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BacktestEngine v2.0 - Football Quant OS
注入: 02 文艺复兴回测引擎
增强: Walk-forward + 蒙特卡洛 + 偏差控制 + 统计显著性
"""

import json
import os
import numpy as np
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
from models.kelly import Kelly
from scipy import stats


class BiasChecker:
    """偏差检测器 - Renaissance 级严谨性"""
    
    def __init__(self):
        self.issues = []
    
    def validate(self, data: List[Dict], strategy_info: Dict = None) -> Dict[str, Any]:
        """全面偏差检测"""
        result = {
            'look_ahead_bias': False,
            'survivorship_bias': False,
            'data_snooping': False,
            'issues': [],
            'recommendations': []
        }
        
        # 1. 前视偏差检测
        for match in data:
            if 'xG' in match and match.get('date'):
                if match.get('xG_source') == 'post_match':
                    result['look_ahead_bias'] = True
                    result['issues'].append("xG 数据可能来自赛后，存在前视偏差风险")
        
        # 2. 幸存者偏差检测
        teams_in_data = set()
        for match in data:
            teams_in_data.add(match.get('home'))
            teams_in_data.add(match.get('away'))
        
        if len(teams_in_data) < 48 and len(data) > 10:
            result['survivorship_bias'] = True
            result['issues'].append(f"仅 {len(teams_in_data)} 支球队，可能缺失淘汰球队数据")
        
        # 3. 数据窥探检测
        if strategy_info and strategy_info.get('optimized_params', False):
            result['data_snooping'] = True
            result['issues'].append("策略参数经过优化，可能存在数据窥探偏差")
        
        if result['look_ahead_bias']:
            result['recommendations'].append("使用赛前 xG 预测值，而非赛后实际 xG")
        if result['survivorship_bias']:
            result['recommendations'].append("确保包含所有参赛球队，包括被淘汰球队")
        if result['data_snooping']:
            result['recommendations'].append("使用单次验证集或 walk-forward 验证")
        
        return result


class WalkForwardValidator:
    """Walk-forward 验证器"""
    
    def __init__(self, train_pct: float = 0.6, val_pct: float = 0.2):
        self.train_pct = train_pct
        self.val_pct = val_pct
    
    def split(self, data: List[Dict]) -> Dict[str, List[Dict]]:
        """时间序列分割"""
        sorted_data = sorted(data, key=lambda x: x.get('date', '1900-01-01'))
        n = len(sorted_data)
        train_end = int(n * self.train_pct)
        val_end = int(n * (self.train_pct + self.val_pct))
        
        return {
            'train': sorted_data[:train_end],
            'validation': sorted_data[train_end:val_end],
            'test': sorted_data[val_end:]
        }


class MonteCarloSimulator:
    """蒙特卡洛模拟器"""
    
    def __init__(self, n_paths: int = 10000):
        self.n_paths = n_paths
    
    def simulate(self, returns: List[float], initial_bankroll: float = 1000) -> Dict[str, Any]:
        """路径重采样蒙特卡洛"""
        if not returns:
            return {}
        
        returns = np.array(returns)
        paths = []
        final_values = []
        sharpes = []
        max_dds = []
        
        for _ in range(self.n_paths):
            sampled = np.random.choice(returns, size=len(returns), replace=True)
            path = [initial_bankroll]
            for r in sampled:
                path.append(path[-1] * (1 + r))
            
            paths.append(path)
            final_values.append(path[-1])
            
            sharpe = np.mean(sampled) / np.std(sampled) if np.std(sampled) > 0 else 0
            sharpes.append(sharpe)
            
            peak = initial_bankroll
            max_dd = 0
            for val in path:
                if val > peak:
                    peak = val
                dd = (peak - val) / peak
                if dd > max_dd:
                    max_dd = dd
            max_dds.append(max_dd)
        
        return {
            'paths': paths[:100],
            'final_values': final_values,
            'percentiles': {
                '5th': float(np.percentile(final_values, 5)),
                '50th': float(np.percentile(final_values, 50)),
                '95th': float(np.percentile(final_values, 95))
            },
            'sharpe_distribution': {
                'mean': float(np.mean(sharpes)),
                '5th': float(np.percentile(sharpes, 5)),
                '95th': float(np.percentile(sharpes, 95))
            },
            'max_drawdown_distribution': {
                'mean': float(np.mean(max_dds)),
                '95th': float(np.percentile(max_dds, 95))
            }
        }


class StatisticalTests:
    """统计显著性测试"""
    
    @staticmethod
    def sharpe_significance(returns: List[float], risk_free: float = 0.0) -> Dict[str, float]:
        """夏普比率显著性测试"""
        returns = np.array(returns)
        n = len(returns)
        if n < 2:
            return {'sharpe': 0, 't_stat': 0, 'p_value': 1.0, 'significant': False}
        
        excess = returns - risk_free
        sharpe = np.mean(excess) / np.std(excess, ddof=1) if np.std(excess) > 0 else 0
        t_stat = sharpe * np.sqrt(n)
        p_value = 2 * (1 - stats.norm.cdf(abs(t_stat)))
        
        return {
            'sharpe': float(sharpe),
            't_stat': float(t_stat),
            'p_value': float(p_value),
            'significant': p_value < 0.05
        }
    
    @staticmethod
    def benchmark_comparison(returns: List[float], benchmark: List[float]) -> Dict[str, float]:
        """与基准的对比检验"""
        if not returns or not benchmark or len(returns) != len(benchmark):
            return {'t_stat': 0, 'p_value': 1.0, 'significant': False}
        
        diff = np.array(returns) - np.array(benchmark)
        t_stat, p_value = stats.ttest_1samp(diff, 0)
        
        return {
            't_stat': float(t_stat),
            'p_value': float(p_value),
            'significant': p_value < 0.05,
            'mean_excess': float(np.mean(diff))
        }


class BacktestEngineV2:
    """回测引擎 v2.0 - 机构级无偏差回测"""
    
    def __init__(self, bankroll: float = 1000, strategy: str = "kelly_compressed"):
        self.initial_bankroll = bankroll
        self.bankroll = bankroll
        self.strategy = strategy
        self.history = []
        self.trades = []
        self.returns = []
        
        self.bias_checker = BiasChecker()
        self.walk_forward = WalkForwardValidator()
        self.monte_carlo = MonteCarloSimulator()
        self.stat_tests = StatisticalTests()
    
    def run(self, path: str = "data/backtest_dataset.json", strategy_info: Dict = None) -> Dict[str, Any]:
        """运行完整回测流程"""
        data = self._load_data(path)
        bias_report = self.bias_checker.validate(data, strategy_info)
        splits = self.walk_forward.split(data)
        test_results = self._run_on_data(splits['test'])
        mc_results = self.monte_carlo.simulate(self.returns, self.initial_bankroll)
        sharpe_test = self.stat_tests.sharpe_significance(self.returns)
        
        return self._generate_report(test_results, bias_report, mc_results, sharpe_test, splits)
    
    def _load_data(self, path: str) -> List[Dict]:
        if not os.path.exists(path):
            base_dir = os.path.dirname(os.path.dirname(__file__))
            path = os.path.join(base_dir, path)
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _run_on_data(self, data: List[Dict]) -> Dict[str, Any]:
        kelly = Kelly(bankroll=self.bankroll)
        
        for match in data:
            prob = match["prob"]
            odds = match["odds"]
            result = match["result"]
            
            if self.strategy == "flat":
                stake = self.initial_bankroll * 0.02
            else:
                bet_info = kelly.calculate(prob, odds, self.bankroll)
                if self.strategy == "kelly_half":
                    stake = self.bankroll * bet_info["half_kelly"]
                elif self.strategy == "kelly_full":
                    stake = self.bankroll * bet_info["kelly_fraction"]
                else:
                    stake = bet_info["stake"]
            
            stake = min(stake, self.bankroll)
            
            if result == "win":
                profit = stake * (odds - 1)
                self.bankroll += profit
                trade_return = (odds - 1) * (stake / self.initial_bankroll)
                trade_result = "win"
            else:
                self.bankroll -= stake
                trade_return = -stake / self.initial_bankroll
                trade_result = "loss"
            
            self.trades.append({
                "match_id": match.get("match_id"),
                "stake": round(stake, 2),
                "odds": odds,
                "prob": prob,
                "result": trade_result,
                "return": round(trade_return, 4),
                "bankroll_after": round(self.bankroll, 2)
            })
            self.history.append(round(self.bankroll, 2))
            self.returns.append(trade_return)
        
        return self._generate_basic_report()
    
    def _generate_basic_report(self) -> Dict[str, Any]:
        wins = len([t for t in self.trades if t["result"] == "win"])
        losses = len([t for t in self.trades if t["result"] == "loss"])
        total = len(self.trades)
        win_rate = wins / total if total > 0 else 0
        roi = (self.bankroll - self.initial_bankroll) / self.initial_bankroll
        
        peak = self.initial_bankroll
        max_drawdown = 0
        for val in self.history:
            if val > peak:
                peak = val
            dd = (peak - val) / peak
            if dd > max_drawdown:
                max_drawdown = dd
        
        returns = np.array(self.returns)
        sharpe = np.mean(returns) / np.std(returns, ddof=1) * np.sqrt(len(returns)) if np.std(returns) > 0 else 0
        
        return {
            "total_trades": total,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 4),
            "roi": round(roi, 4),
            "final_bankroll": round(self.bankroll, 2),
            "max_drawdown": round(max_drawdown, 4),
            "sharpe": round(sharpe, 4)
        }
    
    def _generate_report(self, basic: Dict, bias: Dict, mc: Dict, sharpe_test: Dict, splits: Dict) -> Dict[str, Any]:
        return {
            'version': '2.0',
            'timestamp': datetime.now().isoformat(),
            'basic_metrics': basic,
            'bias_analysis': bias,
            'walk_forward': {
                'train_size': len(splits['train']),
                'val_size': len(splits['validation']),
                'test_size': len(splits['test'])
            },
            'monte_carlo': mc,
            'statistical_tests': sharpe_test,
            'trades': self.trades,
            'history': self.history
        }
