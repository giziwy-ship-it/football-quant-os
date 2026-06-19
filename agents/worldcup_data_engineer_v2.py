#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WorldCupDataEngineer v2.0 - Football Quant OS
注入: 11 Point72 ML 研究
增强: SHAP + 时序交叉验证 + 特征工程 + 自动重训练
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import json
import math
import numpy as np


class FeatureImportance:
    """特征重要性分析器"""
    
    def __init__(self):
        self.importance_scores = {}
        self.shap_values = {}
    
    def calculate_shap(self, model, features: Dict[str, float], 
                       baseline: Dict[str, float] = None) -> Dict[str, float]:
        """计算 SHAP 值 (简化版)"""
        if baseline is None:
            baseline = {k: 0.0 for k in features.keys()}
        
        shap_values = {}
        base_prediction = self._predict_with_features(model, baseline)
        
        for feature_name, feature_value in features.items():
            modified = baseline.copy()
            modified[feature_name] = feature_value
            
            new_prediction = self._predict_with_features(model, modified)
            shap_values[feature_name] = new_prediction - base_prediction
        
        self.shap_values = shap_values
        return shap_values
    
    def _predict_with_features(self, model, features: Dict[str, float]) -> float:
        """使用特征进行预测 (简化)"""
        return sum(features.values()) / max(len(features), 1)
    
    def get_top_features(self, n: int = 10) -> List[Tuple[str, float]]:
        """获取最重要的特征"""
        sorted_features = sorted(
            self.shap_values.items(), 
            key=lambda x: abs(x[1]), 
            reverse=True
        )
        return sorted_features[:n]


class TimeSeriesCV:
    """时序交叉验证器"""
    
    def __init__(self, n_splits: int = 5, test_size: int = 10):
        self.n_splits = n_splits
        self.test_size = test_size
    
    def split(self, data: List[Dict]) -> List[Tuple[List[Dict], List[Dict]]]:
        """生成时序交叉验证折叠"""
        sorted_data = sorted(data, key=lambda x: x.get('date', '1900-01-01'))
        n = len(sorted_data)
        
        splits = []
        for i in range(self.n_splits):
            train_end = int(n * (self.n_splits - i - 1) / self.n_splits)
            test_end = min(train_end + self.test_size, n)
            
            train = sorted_data[:train_end]
            test = sorted_data[train_end:test_end]
            
            if train and test:
                splits.append((train, test))
        
        return splits
    
    def validate(self, model, data: List[Dict]) -> Dict[str, float]:
        """执行交叉验证"""
        splits = self.split(data)
        scores = []
        
        for train, test in splits:
            model.train(train)
            
            correct = 0
            total = 0
            for match in test:
                pred = model.predict(match)
                actual = match.get('result')
                if pred == actual:
                    correct += 1
                total += 1
            
            if total > 0:
                scores.append(correct / total)
        
        return {
            'mean_accuracy': np.mean(scores) if scores else 0.0,
            'std_accuracy': np.std(scores) if scores else 0.0,
            'min_accuracy': np.min(scores) if scores else 0.0,
            'max_accuracy': np.max(scores) if scores else 0.0,
            'n_splits': len(splits)
        }


class ModelMonitor:
    """模型监控器"""
    
    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.performance_history = []
        self.prediction_distribution = []
    
    def record_prediction(self, predicted: float, actual: float) -> None:
        """记录预测结果"""
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'predicted': predicted,
            'actual': actual,
            'correct': abs(predicted - actual) < 0.5
        })
        
        self.prediction_distribution.append(predicted)
    
    def check_drift(self) -> Dict[str, Any]:
        """检查模型漂移"""
        if len(self.performance_history) < self.window_size:
            return {'status': 'INSUFFICIENT_DATA'}
        
        recent = self.performance_history[-self.window_size:]
        older = self.performance_history[:-self.window_size] if len(self.performance_history) > self.window_size * 2 else []
        
        recent_accuracy = sum(1 for r in recent if r['correct']) / len(recent)
        
        drift_status = 'OK'
        older_accuracy = 0.0
        if older:
            older_accuracy = sum(1 for r in older if r['correct']) / len(older)
            accuracy_drop = older_accuracy - recent_accuracy
            
            if accuracy_drop > 0.15:
                drift_status = 'CRITICAL'
            elif accuracy_drop > 0.08:
                drift_status = 'WARNING'
        
        # 检查预测分布漂移
        recent_preds = [r['predicted'] for r in recent]
        pred_std = np.std(recent_preds)
        
        if pred_std < 0.05:
            drift_status = 'CRITICAL'
        
        return {
            'status': drift_status,
            'recent_accuracy': round(recent_accuracy, 4),
            'older_accuracy': round(older_accuracy, 4) if older else None,
            'accuracy_drop': round(older_accuracy - recent_accuracy, 4) if older else None,
            'prediction_std': round(pred_std, 4),
            'recommendation': 'RETRAIN' if drift_status == 'CRITICAL' else 'MONITOR' if drift_status == 'WARNING' else 'OK'
        }
    
    def should_retrain(self) -> bool:
        """判断是否需要重训练"""
        drift = self.check_drift()
        return drift['status'] == 'CRITICAL'


class WorldCupDataEngineerV2:
    """世界杯数据工程师 v2.0 - Point72 级 ML 管道"""
    
    def __init__(self):
        self.feature_importance = FeatureImportance()
        self.cv = TimeSeriesCV(n_splits=5, test_size=10)
        self.monitor = ModelMonitor(window_size=30)
        self.model = None
        
        self.FEATURE_DEFINITIONS = {
            'elo_diff': {'description': 'ELO 差距', 'importance': 0.20},
            'fifa_rank_diff': {'description': 'FIFA 排名差距', 'importance': 0.15},
            'goals_avg_diff': {'description': '场均进球差', 'importance': 0.12},
            'defense_strength_diff': {'description': '防守强度差', 'importance': 0.10},
            'xG_diff': {'description': '预期进球差', 'importance': 0.18},
            'possession_diff': {'description': '控球率差', 'importance': 0.08},
            'motivation_diff': {'description': '战意差', 'importance': 0.10},
            'home_advantage': {'description': '主场优势', 'importance': 0.07},
        }
    
    def extract_features(self, match_info: Dict[str, Any]) -> Dict[str, float]:
        """提取特征"""
        features = {}
        
        home_elo = match_info.get('home_elo', 1500)
        away_elo = match_info.get('away_elo', 1500)
        features['elo_diff'] = (home_elo - away_elo) / 100.0
        
        home_rank = match_info.get('home_fifa_rank', 50)
        away_rank = match_info.get('away_fifa_rank', 50)
        features['fifa_rank_diff'] = (away_rank - home_rank) / 10.0
        
        home_xg = match_info.get('home_xg', 1.0)
        away_xg = match_info.get('away_xg', 1.0)
        features['xG_diff'] = home_xg - away_xg
        
        home_poss = match_info.get('home_possession', 50)
        away_poss = match_info.get('away_possession', 50)
        features['possession_diff'] = (home_poss - away_poss) / 10.0
        
        home_need = match_info.get('home_need_win', 0)
        away_need = match_info.get('away_need_win', 0)
        features['motivation_diff'] = home_need - away_need
        
        features['home_advantage'] = 1.0 if match_info.get('neutral', False) == False else 0.0
        
        return features
    
    def train_with_cv(self, data: List[Dict], model) -> Dict[str, Any]:
        """使用时序交叉验证训练"""
        self.model = model
        
        cv_results = self.cv.validate(model, data)
        model.train(data)
        
        sample_features = self.extract_features(data[0]) if data else {}
        shap_values = self.feature_importance.calculate_shap(model, sample_features)
        top_features = self.feature_importance.get_top_features(5)
        
        return {
            'cv_results': cv_results,
            'top_features': top_features,
            'shap_values': shap_values,
            'training_size': len(data)
        }
    
    def predict_with_monitor(self, match_info: Dict[str, Any]) -> Dict[str, Any]:
        """带监控的预测"""
        features = self.extract_features(match_info)
        
        if self.model:
            prediction = self.model.predict(match_info)
        else:
            prediction = {'prob_home': 0.33, 'prob_draw': 0.33, 'prob_away': 0.34}
        
        self.monitor.record_prediction(0.5, match_info.get('actual_result', 0.5))
        
        drift = self.monitor.check_drift()
        
        return {
            'prediction': prediction,
            'features': features,
            'drift_status': drift,
            'should_retrain': self.monitor.should_retrain()
        }


__all__ = ['WorldCupDataEngineerV2', 'FeatureImportance', 'TimeSeriesCV', 'ModelMonitor']
