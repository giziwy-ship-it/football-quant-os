#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AttributionAgent v1.0 - Football Quant OS
注入: 13.5 绩效归因分析师
功能: 预测准确率归因 + 收益归因 + 成本归因 + 改进建议

归因维度:
- 每个因子贡献了多少准确率
- 每个策略贡献了多少收益
- 每个成本项的分解
- 运气 vs 技能判断
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import numpy as np


@dataclass
class FactorAttribution:
    """因子归因记录"""
    factor_id: str
    name: str
    predictions: int
    correct: int
    accuracy: float
    contribution: float  # 对总准确率的贡献
    expected_accuracy: float
    vs_expected: float


@dataclass
class StrategyAttribution:
    """策略归因记录"""
    strategy_id: str
    name: str
    total_return: float
    risk_adjusted_return: float
    sharpe: float
    max_drawdown: float
    contribution_pct: float
    trades: int


@dataclass
class CostAttribution:
    """成本归因记录"""
    cost_type: str
    amount: float
    percentage: float
    vs_baseline: float
    recommendation: str


class AttributionEngine:
    """归因引擎"""
    
    def __init__(self):
        self.factor_history: List[Dict] = []
        self.strategy_history: List[Dict] = []
        self.cost_history: List[Dict] = []
    
    def record_factor_prediction(self, factor_id: str, factor_name: str,
                                  predicted: float, actual: float,
                                  expected_accuracy: float = 0.33) -> None:
        """记录因子预测结果"""
        self.factor_history.append({
            'timestamp': datetime.now().isoformat(),
            'factor_id': factor_id,
            'factor_name': factor_name,
            'predicted': predicted,
            'actual': actual,
            'correct': abs(predicted - actual) < 0.5,
            'expected_accuracy': expected_accuracy
        })
    
    def record_strategy_result(self, strategy_id: str, strategy_name: str,
                                return_pct: float, risk: float,
                                max_dd: float) -> None:
        """记录策略结果"""
        self.strategy_history.append({
            'timestamp': datetime.now().isoformat(),
            'strategy_id': strategy_id,
            'strategy_name': strategy_name,
            'return': return_pct,
            'risk': risk,
            'max_drawdown': max_dd
        })
    
    def record_cost(self, cost_type: str, amount: float, 
                   total_volume: float) -> None:
        """记录成本"""
        self.cost_history.append({
            'timestamp': datetime.now().isoformat(),
            'cost_type': cost_type,
            'amount': amount,
            'percentage': amount / total_volume if total_volume > 0 else 0
        })
    
    def calculate_factor_attribution(self) -> Dict[str, Any]:
        """计算因子归因"""
        if not self.factor_history:
            return {'status': 'NO_DATA'}
        
        # 按因子分组
        factor_groups = {}
        for record in self.factor_history:
            fid = record['factor_id']
            if fid not in factor_groups:
                factor_groups[fid] = []
            factor_groups[fid].append(record)
        
        attributions = []
        total_correct = sum(1 for r in self.factor_history if r['correct'])
        total = len(self.factor_history)
        
        for factor_id, records in factor_groups.items():
            correct = sum(1 for r in records if r['correct'])
            accuracy = correct / len(records) if records else 0
            expected = records[0]['expected_accuracy'] if records else 0.33
            
            # 贡献度 = (该因子准确率 - 随机) / (总准确率 - 随机)
            total_accuracy = total_correct / total if total > 0 else 0
            contribution = (accuracy - expected) / max(total_accuracy - expected, 0.01) if total_accuracy > expected else 0
            
            attributions.append(FactorAttribution(
                factor_id=factor_id,
                name=records[0]['factor_name'] if records else factor_id,
                predictions=len(records),
                correct=correct,
                accuracy=round(accuracy, 4),
                contribution=round(contribution, 4),
                expected_accuracy=expected,
                vs_expected=round(accuracy - expected, 4)
            ))
        
        return {
            'factors': [
                {
                    'factor_id': a.factor_id,
                    'name': a.name,
                    'predictions': a.predictions,
                    'accuracy': a.accuracy,
                    'contribution': a.contribution,
                    'vs_expected': a.vs_expected
                } for a in sorted(attributions, key=lambda x: x.contribution, reverse=True)
            ],
            'total_accuracy': round(total_correct / total, 4) if total > 0 else 0,
            'total_predictions': total
        }
    
    def calculate_strategy_attribution(self) -> Dict[str, Any]:
        """计算策略归因"""
        if not self.strategy_history:
            return {'status': 'NO_DATA'}
        
        # 按策略分组
        strategy_groups = {}
        for record in self.strategy_history:
            sid = record['strategy_id']
            if sid not in strategy_groups:
                strategy_groups[sid] = []
            strategy_groups[sid].append(record)
        
        total_return = sum(r['return'] for r in self.strategy_history)
        
        attributions = []
        for strategy_id, records in strategy_groups.items():
            avg_return = np.mean([r['return'] for r in records])
            avg_risk = np.mean([r['risk'] for r in records])
            max_dd = max([r['max_drawdown'] for r in records])
            sharpe = avg_return / max(avg_risk, 0.001)
            
            contribution = avg_return / max(total_return, 0.001) if total_return != 0 else 0
            
            attributions.append(StrategyAttribution(
                strategy_id=strategy_id,
                name=records[0]['strategy_name'] if records else strategy_id,
                total_return=round(avg_return, 4),
                risk_adjusted_return=round(avg_return / max(avg_risk, 0.001), 4),
                sharpe=round(sharpe, 4),
                max_drawdown=round(max_dd, 4),
                contribution_pct=round(contribution, 4),
                trades=len(records)
            ))
        
        return {
            'strategies': [
                {
                    'strategy_id': a.strategy_id,
                    'name': a.name,
                    'total_return': a.total_return,
                    'sharpe': a.sharpe,
                    'contribution_pct': a.contribution_pct,
                    'trades': a.trades
                } for a in sorted(attributions, key=lambda x: x.contribution_pct, reverse=True)
            ],
            'total_return': round(total_return, 4)
        }
    
    def calculate_cost_attribution(self) -> Dict[str, Any]:
        """计算成本归因"""
        if not self.cost_history:
            return {'status': 'NO_DATA'}
        
        # 按成本类型分组
        cost_groups = {}
        for record in self.cost_history:
            ctype = record['cost_type']
            if ctype not in cost_groups:
                cost_groups[ctype] = []
            cost_groups[ctype].append(record)
        
        total_cost = sum(r['amount'] for r in self.cost_history)
        total_volume = sum(r['amount'] / r['percentage'] if r['percentage'] > 0 else 0 for r in self.cost_history)
        
        attributions = []
        for cost_type, records in cost_groups.items():
            total = sum(r['amount'] for r in records)
            avg_pct = np.mean([r['percentage'] for r in records])
            
            # 与行业基准对比
            baseline = {
                'commission': 0.03,
                'slippage': 0.05,
                'impact': 0.02,
                'opportunity': 0.01
            }.get(cost_type, 0.05)
            
            attributions.append(CostAttribution(
                cost_type=cost_type,
                amount=round(total, 2),
                percentage=round(avg_pct, 4),
                vs_baseline=round(avg_pct - baseline, 4),
                recommendation='优化' if avg_pct > baseline * 1.5 else '正常'
            ))
        
        return {
            'costs': [
                {
                    'cost_type': c.cost_type,
                    'amount': c.amount,
                    'percentage': c.percentage,
                    'vs_baseline': c.vs_baseline,
                    'recommendation': c.recommendation
                } for c in sorted(attributions, key=lambda x: x.amount, reverse=True)
            ],
            'total_cost': round(total_cost, 2),
            'total_cost_pct': round(total_cost / total_volume, 4) if total_volume > 0 else 0
        }
    
    def luck_vs_skill(self, n_trials: int = 100) -> Dict[str, Any]:
        """判断运气 vs 技能"""
        if not self.factor_history:
            return {'status': 'NO_DATA'}
        
        actual_accuracy = sum(1 for r in self.factor_history if r['correct']) / len(self.factor_history)
        expected = 0.33  # 随机准确率
        
        # 蒙特卡洛模拟
        random_accuracies = []
        for _ in range(n_trials):
            random_correct = sum(np.random.random() < expected for _ in range(len(self.factor_history)))
            random_accuracies.append(random_correct / len(self.factor_history))
        
        percentile = sum(1 for a in random_accuracies if a < actual_accuracy) / n_trials
        
        return {
            'actual_accuracy': round(actual_accuracy, 4),
            'random_accuracy': round(expected, 4),
            'percentile': round(percentile, 4),
            'skill_confidence': 'HIGH' if percentile > 0.95 else 'MEDIUM' if percentile > 0.80 else 'LOW',
            'conclusion': '技能' if percentile > 0.90 else '运气+技能' if percentile > 0.70 else '运气'
        }
    
    def generate_full_report(self) -> Dict[str, Any]:
        """生成完整归因报告"""
        return {
            'timestamp': datetime.now().isoformat(),
            'factor_attribution': self.calculate_factor_attribution(),
            'strategy_attribution': self.calculate_strategy_attribution(),
            'cost_attribution': self.calculate_cost_attribution(),
            'luck_vs_skill': self.luck_vs_skill(),
            'improvement_recommendations': self._generate_recommendations()
        }
    
    def _generate_recommendations(self) -> List[Dict[str, str]]:
        """生成改进建议"""
        recommendations = []
        
        # 基于因子归因
        factor_attr = self.calculate_factor_attribution()
        if factor_attr.get('status') != 'NO_DATA':
            worst_factor = min(factor_attr['factors'], key=lambda x: x['accuracy'])
            if worst_factor['accuracy'] < worst_factor['expected_accuracy']:
                recommendations.append({
                    'area': 'factor',
                    'issue': f"{worst_factor['name']} 准确率低于预期",
                    'suggestion': f"考虑降低 {worst_factor['name']} 权重或重新校准"
                })
        
        # 基于成本归因
        cost_attr = self.calculate_cost_attribution()
        if cost_attr.get('status') != 'NO_DATA':
            high_cost = max(cost_attr['costs'], key=lambda x: x['percentage'])
            if high_cost['vs_baseline'] > 0:
                recommendations.append({
                    'area': 'cost',
                    'issue': f"{high_cost['cost_type']} 成本高于基准",
                    'suggestion': "优化执行算法或选择更低成本平台"
                })
        
        return recommendations


class AttributionAgent:
    """AttributionAgent v1.0 - 绩效归因"""
    
    def __init__(self):
        self.engine = AttributionEngine()
    
    def record(self, record_type: str, **kwargs) -> None:
        """记录数据"""
        if record_type == 'factor':
            self.engine.record_factor_prediction(**kwargs)
        elif record_type == 'strategy':
            self.engine.record_strategy_result(**kwargs)
        elif record_type == 'cost':
            self.engine.record_cost(**kwargs)
    
    def get_report(self) -> Dict[str, Any]:
        """获取完整报告"""
        return self.engine.generate_full_report()
    
    def get_factor_breakdown(self) -> Dict[str, Any]:
        """获取因子分解"""
        return self.engine.calculate_factor_attribution()
    
    def get_strategy_breakdown(self) -> Dict[str, Any]:
        """获取策略分解"""
        return self.engine.calculate_strategy_attribution()
    
    def get_cost_breakdown(self) -> Dict[str, Any]:
        """获取成本分解"""
        return self.engine.calculate_cost_attribution()
    
    def get_luck_vs_skill(self) -> Dict[str, Any]:
        """获取运气 vs 技能分析"""
        return self.engine.luck_vs_skill()


__all__ = ['AttributionAgent', 'AttributionEngine']
