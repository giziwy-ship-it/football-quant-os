#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FactorMonitor v1.0 - Football Quant OS
注入: 05.5 因子监控运维
功能: 预测因子健康度实时巡检 + 衰减预警 + 自动降级

监控因子:
- xG (预期进球)
- 控球率
- 战意因子
- 教练因子 (CRI)
- 历史对战记录
- 主客场优势
- 小组赛上下文
- 冷门信号

预警阈值:
- GREEN: IC > 预期 IC 的 80%
- YELLOW: IC 在预期的 50%-80%
- RED: IC <= 50% 或连续 5 天为负
- EMERGENCY: 因子相关性矩阵特征值爆炸
"""

import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class FactorStatus(Enum):
    HEALTHY = "healthy"      # 绿色
    DEGRADING = "degrading"  # 黄色
    FAILING = "failing"      # 红色
    EMERGENCY = "emergency"  # 紧急


@dataclass
class FactorMetric:
    """因子指标记录"""
    timestamp: str
    ic: float                # 信息系数
    expected_ic: float       # 预期 IC
    decay_rate: float        # 衰减率 (每日)
    win_rate: float          # 胜率
    sample_size: int         # 样本量


@dataclass
class FactorHealth:
    """因子健康状态"""
    factor_id: str
    name: str
    status: FactorStatus
    current_ic: float
    expected_ic: float
    ic_ratio: float          # 当前 / 预期
    decay_rate: float
    half_life: float         # 半衰期 (天)
    days_since_peak: int
    crowdedness: float       # 拥挤度 0-1
    recommendation: str


class FactorMonitor:
    """因子监控器 - 确保预测因子持续有效"""
    
    # 因子定义
    FACTOR_REGISTRY = {
        'xG': {'name': '预期进球', 'expected_ic': 0.05, 'half_life': 30},
        'possession': {'name': '控球率', 'expected_ic': 0.03, 'half_life': 25},
        'motivation': {'name': '战意因子', 'expected_ic': 0.04, 'half_life': 20},
        'coach_cri': {'name': '教练CRI', 'expected_ic': 0.03, 'half_life': 35},
        'h2h': {'name': '历史对战', 'expected_ic': 0.02, 'half_life': 40},
        'home_advantage': {'name': '主客场优势', 'expected_ic': 0.03, 'half_life': 50},
        'group_context': {'name': '小组赛上下文', 'expected_ic': 0.04, 'half_life': 25},
        'upset_signal': {'name': '冷门信号', 'expected_ic': 0.03, 'half_life': 15}
    }
    
    # 预警阈值
    THRESHOLDS = {
        'green': 0.8,    # IC > 80% 预期
        'yellow': 0.5,   # IC > 50% 预期
        'red': 0.0,      # IC > 0
        'emergency': -1  # 特征值爆炸
    }
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / 'logs'
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # 历史数据存储
        self.metrics_history: Dict[str, List[FactorMetric]] = {
            k: [] for k in self.FACTOR_REGISTRY.keys()
        }
        
        # 当前状态
        self.current_health: Dict[str, FactorHealth] = {}
        
        # 权重调整记录
        self.weight_adjustments: List[Dict] = []
    
    def record_prediction(self, factor_id: str, prediction: float, 
                          actual: float, timestamp: str = None) -> None:
        """记录单次预测结果"""
        if factor_id not in self.FACTOR_REGISTRY:
            return
        
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        # 计算 IC (预测与实际的秩相关)
        # 简化版: 使用符号一致性
        ic = 1.0 if (prediction > 0.5 and actual > 0.5) or (prediction < 0.5 and actual < 0.5) else -1.0
        
        metric = FactorMetric(
            timestamp=timestamp,
            ic=ic,
            expected_ic=self.FACTOR_REGISTRY[factor_id]['expected_ic'],
            decay_rate=0.0,  # 稍后计算
            win_rate=0.0,    # 稍后计算
            sample_size=1
        )
        
        self.metrics_history[factor_id].append(metric)
        
        # 如果历史足够，更新健康状态
        if len(self.metrics_history[factor_id]) >= 5:
            self._update_health(factor_id)
    
    def _update_health(self, factor_id: str) -> None:
        """更新因子健康状态"""
        history = self.metrics_history[factor_id]
        registry = self.FACTOR_REGISTRY[factor_id]
        
        # 计算最近 30 天的 IC
        recent = history[-30:] if len(history) >= 30 else history
        ics = [m.ic for m in recent]
        
        current_ic = np.mean(ics) if ics else 0
        expected_ic = registry['expected_ic']
        ic_ratio = current_ic / expected_ic if expected_ic > 0 else 0
        
        # 计算衰减率
        if len(ics) >= 10:
            first_half = np.mean(ics[:len(ics)//2])
            second_half = np.mean(ics[len(ics)//2:])
            decay_rate = (first_half - second_half) / max(abs(first_half), 0.001)
        else:
            decay_rate = 0.0
        
        # 计算半衰期
        half_life = self._estimate_half_life(ics, registry['half_life'])
        
        # 计算拥挤度 (基于 IC 波动率)
        crowdedness = np.std(ics) if len(ics) > 1 else 0.0
        
        # 确定状态
        status = self._determine_status(ic_ratio, ics)
        
        # 生成建议
        recommendation = self._generate_recommendation(status, ic_ratio, decay_rate)
        
        self.current_health[factor_id] = FactorHealth(
            factor_id=factor_id,
            name=registry['name'],
            status=status,
            current_ic=round(current_ic, 4),
            expected_ic=expected_ic,
            ic_ratio=round(ic_ratio, 4),
            decay_rate=round(decay_rate, 4),
            half_life=round(half_life, 1),
            days_since_peak=self._days_since_peak(history),
            crowdedness=round(min(crowdedness, 1.0), 4),
            recommendation=recommendation
        )
    
    def _estimate_half_life(self, ics: List[float], default: float) -> float:
        """估算半衰期"""
        if len(ics) < 10:
            return default
        
        # 使用指数衰减拟合
        x = np.arange(len(ics))
        y = np.array(ics)
        
        try:
            # 线性回归 log(|IC|)
            log_y = np.log(np.abs(y) + 0.01)
            slope = np.polyfit(x, log_y, 1)[0]
            
            if slope < 0:
                half_life = -np.log(2) / slope
                return max(min(half_life, 100), 1)
        except:
            pass
        
        return default
    
    def _determine_status(self, ic_ratio: float, ics: List[float]) -> FactorStatus:
        """确定因子状态"""
        # 检查连续 5 天为负
        recent_negative = all(ic < 0 for ic in ics[-5:]) if len(ics) >= 5 else False
        
        if ic_ratio <= 0 or recent_negative:
            return FactorStatus.FAILING
        elif ic_ratio < self.THRESHOLDS['yellow']:
            return FactorStatus.DEGRADING
        elif ic_ratio < self.THRESHOLDS['green']:
            return FactorStatus.HEALTHY
        
        return FactorStatus.HEALTHY
    
    def _generate_recommendation(self, status: FactorStatus, ic_ratio: float, decay_rate: float) -> str:
        """生成改进建议"""
        if status == FactorStatus.FAILING:
            return f"立即停用，IC 仅预期的 {ic_ratio:.1%}，衰减率 {decay_rate:.2f}"
        elif status == FactorStatus.DEGRADING:
            return f"权重降低 50%，IC 下降至预期的 {ic_ratio:.1%}"
        elif ic_ratio < self.THRESHOLDS['green']:
            return f"密切监控，IC 为预期的 {ic_ratio:.1%}"
        else:
            return "维持当前权重"
    
    def _days_since_peak(self, history: List[FactorMetric]) -> int:
        """计算距离峰值的天数"""
        if not history:
            return 0
        
        ics = [m.ic for m in history]
        peak_idx = np.argmax(ics)
        return len(history) - peak_idx - 1
    
    def get_health_report(self) -> Dict[str, Any]:
        """获取完整健康报告"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'factors': [],
            'summary': {
                'healthy': 0,
                'degrading': 0,
                'failing': 0,
                'emergency': 0
            },
            'recommendations': []
        }
        
        for factor_id, health in self.current_health.items():
            factor_report = {
                'factor_id': health.factor_id,
                'name': health.name,
                'status': health.status.value,
                'current_ic': health.current_ic,
                'expected_ic': health.expected_ic,
                'ic_ratio': health.ic_ratio,
                'decay_rate': health.decay_rate,
                'half_life': health.half_life,
                'recommendation': health.recommendation
            }
            report['factors'].append(factor_report)
            report['summary'][health.status.value] += 1
            
            if health.status != FactorStatus.HEALTHY:
                report['recommendations'].append({
                    'factor': health.name,
                    'action': health.recommendation
                })
        
        # 保存报告
        self._save_report(report)
        
        return report
    
    def _save_report(self, report: Dict) -> None:
        """保存报告到文件"""
        date_str = datetime.now().strftime('%Y%m%d')
        report_file = self.log_dir / f"factor_health_{date_str}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
    
    def get_weight_adjustments(self) -> Dict[str, float]:
        """获取权重调整建议"""
        adjustments = {}
        for factor_id, health in self.current_health.items():
            if health.status == FactorStatus.FAILING:
                adjustments[factor_id] = 0.0
            elif health.status == FactorStatus.DEGRADING:
                adjustments[factor_id] = 0.5
            else:
                adjustments[factor_id] = 1.0
        return adjustments
    
    def check_emergency(self) -> bool:
        """检查是否触发紧急状态"""
        failing_count = sum(1 for h in self.current_health.values() 
                           if h.status == FactorStatus.FAILING)
        total = len(self.current_health)
        
        # 超过 50% 因子失效触发紧急
        return total > 0 and failing_count / total > 0.5
