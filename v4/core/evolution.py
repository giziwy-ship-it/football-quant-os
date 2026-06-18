#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Self-Evolution Engine (SEE) v4.0
自进化引擎 - 让系统自己变聪明

核心机制：
1. 贝叶斯在线学习: P(model_i | results) ∝ P(results | model_i) × P(model_i)
2. 滚动窗口回测: 每周重新校准权重
3. 梯度下降更新: 用实际结果对权重做带正则的 SGD

Author: Naga Core Team
Version: 4.0.0
"""

import json
import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime, timedelta


@dataclass
class ModelPerformance:
    """模型性能记录"""
    model_name: str
    predictions: List[Dict] = field(default_factory=list)
    accuracy: float = 0.0
    roi: float = 0.0
    brier_score: float = 1.0
    log_loss: float = 1.0
    sample_count: int = 0
    
    def update(
        self,
        predicted_probs: Dict[str, float],
        actual_result: str,  # "home", "draw", "away"
        odds: Dict[str, float],
        stake: float = 0.0,
        pnl: float = 0.0
    ):
        """更新性能指标"""
        self.sample_count += 1
        
        # 准确率 (是否正确预测了结果)
        predicted_best = max(predicted_probs, key=predicted_probs.get)
        correct = 1 if predicted_best == actual_result else 0
        self.accuracy = (self.accuracy * (self.sample_count - 1) + correct) / self.sample_count
        
        # Brier Score (概率校准度)
        actual_vec = {k: 1.0 if k == actual_result else 0.0 for k in predicted_probs}
        brier = sum((predicted_probs[k] - actual_vec[k]) ** 2 for k in predicted_probs) / len(predicted_probs)
        self.brier_score = (self.brier_score * (self.sample_count - 1) + brier) / self.sample_count
        
        # ROI
        if stake > 0:
            roi_contrib = pnl / stake
            self.roi = (self.roi * (self.sample_count - 1) + roi_contrib) / self.sample_count
        
        self.predictions.append({
            "probs": predicted_probs,
            "actual": actual_result,
            "pnl": pnl,
            "timestamp": datetime.now().isoformat()
        })


class SelfEvolution:
    """
    自进化引擎 v4.0
    
    不是简单的启发式规则，而是基于概率框架的权重更新：
    
    1. 贝叶斯框架:
       w_i(t+1) ∝ w_i(t) × exp(-β × loss_i)
       其中 loss_i = Brier Score 或 负对数似然
    
    2. 指数加权移动平均:
       最近的样本权重更高
    
    3. 正则化:
       防止单个模型权重过高
    """
    
    VERSION = "4.0.0"
    
    def __init__(
        self,
        model_names: List[str] = None,
        learning_rate: float = 0.05,
        beta: float = 2.0,
        regularization: float = 0.1,
        window_size: int = 50
    ):
        self.model_names = model_names or ["mechanics", "field", "entropy", "coach", "market"]
        self.learning_rate = learning_rate
        self.beta = beta
        self.regularization = regularization
        self.window_size = window_size
        
        # 模型权重 (softmax 前的 logits)
        self.logits = {name: 0.0 for name in self.model_names}
        
        # 性能记录
        self.performance: Dict[str, ModelPerformance] = {
            name: ModelPerformance(model_name=name)
            for name in self.model_names
        }
        
        # 历史权重
        self.weight_history: List[Dict[str, float]] = []
        
        # 综合性能
        self.overall_accuracy = 0.5
        self.overall_roi = 0.0
    
    @property
    def weights(self) -> Dict[str, float]:
        """当前权重 (softmax)"""
        exp_logits = {k: np.exp(v) for k, v in self.logits.items()}
        total = sum(exp_logits.values())
        return {k: v / total for k, v in exp_logits.items()}
    
    def record_result(
        self,
        model_name: str,
        predicted_probs: Dict[str, float],
        actual_result: str,
        odds: Dict[str, float] = None,
        stake: float = 0.0,
        pnl: float = 0.0
    ):
        """记录单场比赛结果"""
        if model_name not in self.performance:
            self.performance[model_name] = ModelPerformance(model_name=model_name)
        
        self.performance[model_name].update(
            predicted_probs, actual_result, odds or {}, stake, pnl
        )
    
    def update_weights(self) -> Dict[str, float]:
        """
        更新权重 (贝叶斯梯度下降)
        
        对每个模型:
        1. 计算最近 window_size 场的平均 Brier Score
        2. 计算梯度: ∇ = -β × (performance - baseline)
        3. 更新: logits += lr × ∇
        4. 正则化: logits -= reg × logits
        5. Softmax → 权重
        """
        gradients = {}
        
        for name in self.model_names:
            perf = self.performance[name]
            
            if perf.sample_count < 5:
                # 样本不足，不更新
                gradients[name] = 0.0
                continue
            
            # 最近 window 的表现
            recent = perf.predictions[-self.window_size:]
            if not recent:
                gradients[name] = 0.0
                continue
            
            # 计算最近平均 Brier Score
            recent_briers = []
            for pred in recent:
                actual = pred["actual"]
                probs = pred["probs"]
                actual_vec = {k: 1.0 if k == actual else 0.0 for k in probs}
                brier = sum((probs[k] - actual_vec[k]) ** 2 for k in probs) / len(probs)
                recent_briers.append(brier)
            
            avg_brier = np.mean(recent_briers)
            
            # 梯度: Brier越低 → 梯度越正 → 权重越高
            # baseline Brier = 0.22 (随机猜测)
            baseline = 0.22
            gradient = -self.beta * (avg_brier - baseline)
            
            # ROI 加成
            if perf.roi != 0:
                gradient += perf.roi * 2  # ROI 正 → 权重提升
            
            gradients[name] = gradient
        
        # 更新 logits
        for name in self.model_names:
            self.logits[name] += self.learning_rate * gradients.get(name, 0)
            # 正则化 (防止爆炸)
            self.logits[name] -= self.regularization * self.logits[name]
            # 裁剪
            self.logits[name] = np.clip(self.logits[name], -3, 3)
        
        # 记录历史
        current_weights = self.weights
        self.weight_history.append({
            "timestamp": datetime.now().isoformat(),
            "weights": current_weights.copy(),
            "logits": self.logits.copy()
        })
        
        return current_weights
    
    def get_model_ranking(self) -> List[Tuple[str, float, float]]:
        """
        获取模型排名
        
        Returns:
            [(model_name, weight, accuracy), ...] 按权重排序
        """
        weights = self.weights
        ranking = []
        
        for name in self.model_names:
            perf = self.performance[name]
            ranking.append((name, weights[name], perf.accuracy, perf.roi))
        
        ranking.sort(key=lambda x: x[1], reverse=True)
        return ranking
    
    def diagnose(self) -> Dict[str, Any]:
        """系统诊断"""
        weights = self.weights
        ranking = self.get_model_ranking()
        
        # 检测权重失衡
        max_weight = max(weights.values())
        is_imbalanced = max_weight > 0.5
        
        # 检测模型失效
        failing_models = []
        for name, perf in self.performance.items():
            if perf.sample_count > 10 and perf.accuracy < 0.45:
                failing_models.append(name)
        
        # 建议
        recommendations = []
        if is_imbalanced:
            recommendations.append(f"权重失衡: {ranking[0][0]} 占比 {max_weight:.1%} → 增加正则化")
        if failing_models:
            recommendations.append(f"模型失效: {failing_models} → 检查特征工程或重新训练")
        if self.overall_roi < 0:
            recommendations.append(f"整体亏损: ROI={self.overall_roi:.1%} → 收紧信号阈值")
        if not recommendations:
            recommendations.append("系统运行正常")
        
        return {
            "weights": {k: round(v, 4) for k, v in weights.items()},
            "logits": {k: round(v, 4) for k, v in self.logits.items()},
            "ranking": [
                {"name": r[0], "weight": round(r[1], 4), "accuracy": round(r[2], 4), "roi": round(r[3], 4)}
                for r in ranking
            ],
            "performance_summary": {
                name: {
                    "accuracy": round(perf.accuracy, 4),
                    "roi": round(perf.roi, 4),
                    "brier_score": round(perf.brier_score, 4),
                    "samples": perf.sample_count
                }
                for name, perf in self.performance.items()
            },
            "diagnosis": {
                "is_imbalanced": is_imbalanced,
                "failing_models": failing_models,
                "recommendations": recommendations
            },
            "overall": {
                "accuracy": round(self.overall_accuracy, 4),
                "roi": round(self.overall_roi, 4)
            }
        }
    
    def save(self, path: str):
        """保存进化状态"""
        state = {
            "logits": self.logits,
            "performance": {
                name: {
                    "accuracy": perf.accuracy,
                    "roi": perf.roi,
                    "brier_score": perf.brier_score,
                    "sample_count": perf.sample_count
                }
                for name, perf in self.performance.items()
            },
            "weight_history": self.weight_history[-100:],  # 最近100条
            "overall_accuracy": self.overall_accuracy,
            "overall_roi": self.overall_roi,
            "version": self.VERSION,
            "timestamp": datetime.now().isoformat()
        }
        
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(state, f, indent=2)
    
    def load(self, path: str):
        """加载进化状态"""
        if not Path(path).exists():
            return
        
        with open(path, 'r') as f:
            state = json.load(f)
        
        self.logits = state.get("logits", self.logits)
        self.overall_accuracy = state.get("overall_accuracy", 0.5)
        self.overall_roi = state.get("overall_roi", 0.0)
        
        # 恢复性能记录
        for name, perf_data in state.get("performance", {}).items():
            if name in self.performance:
                self.performance[name].accuracy = perf_data.get("accuracy", 0.0)
                self.performance[name].roi = perf_data.get("roi", 0.0)
                self.performance[name].brier_score = perf_data.get("brier_score", 1.0)
                self.performance[name].sample_count = perf_data.get("sample_count", 0)


# ============ 快速测试 ============
if __name__ == "__main__":
    evo = SelfEvolution()
    
    # 模拟几场比赛结果
    print("=== 模拟训练 ===")
    
    # 模型1 (mechanics) - 表现好
    for i in range(20):
        evo.record_result(
            "mechanics",
            {"home": 0.6, "draw": 0.25, "away": 0.15},
            "home" if i % 2 == 0 else "draw",
            stake=100, pnl=15 if i % 2 == 0 else -100
        )
    
    # 模型2 (entropy) - 表现差
    for i in range(20):
        evo.record_result(
            "entropy",
            {"home": 0.5, "draw": 0.3, "away": 0.2},
            "home" if i % 3 == 0 else "away",
            stake=100, pnl=-30
        )
    
    # 更新权重
    weights = evo.update_weights()
    print("更新后权重:")
    for name, w in weights.items():
        print(f"  {name}: {w:.2%}")
    
    # 诊断
    print("\n=== 系统诊断 ===")
    diag = evo.diagnose()
    print(f"推荐: {diag['diagnosis']['recommendations']}")
    print(f"排名:")
    for r in diag['ranking']:
        print(f"  {r['name']}: 权重={r['weight']:.1%} 准确率={r['accuracy']:.1%} ROI={r['roi']:.1%}")
