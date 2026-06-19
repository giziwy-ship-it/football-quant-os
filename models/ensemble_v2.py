from typing import Dict, Any, List, Optional
import numpy as np
from .base_model import BaseModel


class ModelEnsembleV2(BaseModel):
    """
    模型融合 v2.0 - 注入 AQR 因子模型
    增强: 风险平价权重分配 + IC加权 + 动态调整 + 因子敞口监控
    
    相比 v1.0:
    - 风险平价: 每个模型对组合风险贡献相等
    - IC加权: 根据近期预测准确率动态调整权重
    - 动态再平衡: 定期根据表现调整权重
    - 因子敞口: 监控组合对各预测因子的暴露度
    """
    
    def __init__(self, models: List[BaseModel] = None, weights: List[float] = None,
                 weighting_method: str = 'risk_parity'):
        self._models = models or []
        self._base_weights = weights or []
        self.weighting_method = weighting_method
        self._current_weights = []
        self._ic_history = {i: [] for i in range(len(models))} if models else {}
        self._performance_history = []
        
        # 如果未指定权重，使用等权重
        if self._models and not self._base_weights:
            self._base_weights = [1.0 / len(self._models)] * len(self._models)
        
        self._normalize_weights()
    
    @property
    def name(self) -> str:
        return "ModelEnsembleV2"
    
    @property
    def version(self) -> str:
        return "2.0"
    
    def _normalize_weights(self):
        """归一化权重"""
        if self._base_weights:
            total = sum(self._base_weights)
            self._current_weights = [w / total for w in self._base_weights]
    
    def add_model(self, model: BaseModel, weight: float = 1.0):
        """添加子模型"""
        self._models.append(model)
        self._base_weights.append(weight)
        self._ic_history[len(self._models) - 1] = []
        self._normalize_weights()
    
    def predict(self, match_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行多模型融合预测"""
        if not self._models:
            return {'error': 'No models in ensemble'}
        
        # 收集所有子模型预测
        predictions = []
        valid_indices = []
        for i, model in enumerate(self._models):
            try:
                pred = model.predict(match_info, **kwargs)
                if 'error' not in pred:
                    predictions.append(pred)
                    valid_indices.append(i)
            except Exception as e:
                continue
        
        if not predictions:
            return {'error': 'All models failed to predict'}
        
        # 根据方法选择权重
        weights = self._calculate_weights(valid_indices, predictions)
        
        # 融合预测结果
        fused_markets = self._fuse_markets(predictions, weights)
        
        # 计算综合置信度
        confidences = [p.get('confidence', 0.5) for p in predictions]
        avg_confidence = sum(c * w for c, w in zip(confidences, weights))
        
        # 因子敞口分析
        factor_exposure = self._calculate_factor_exposure(predictions, weights)
        
        return {
            'model_name': self.name,
            'version': self.version,
            'markets': fused_markets,
            'confidence': round(avg_confidence, 3),
            'weighting_method': self.weighting_method,
            'factor_exposure': factor_exposure,
            'metadata': {
                'models_used': [p['model_name'] for p in predictions],
                'weights': [round(w, 3) for w in weights],
                'individual_predictions': predictions
            }
        }
    
    def _calculate_weights(self, valid_indices: List[int], 
                          predictions: List[Dict]) -> List[float]:
        """根据策略计算权重"""
        if self.weighting_method == 'equal':
            return [1.0 / len(predictions)] * len(predictions)
        
        elif self.weighting_method == 'ic_weighted':
            # IC 加权: 近期 IC 高的模型权重更高
            ics = []
            for idx in valid_indices:
                ic_history = self._ic_history.get(idx, [])
                if len(ic_history) >= 5:
                    recent_ic = np.mean(ic_history[-10:])
                    ics.append(max(recent_ic, 0.01))
                else:
                    ics.append(0.5)
            
            total_ic = sum(ics)
            return [ic / total_ic for ic in ics]
        
        elif self.weighting_method == 'risk_parity':
            # 风险平价: 每个模型贡献相等的风险
            # 简化实现: 根据预测方差的倒数加权
            variances = []
            for pred in predictions:
                conf = pred.get('confidence', 0.5)
                variance = (1 - conf) ** 2
                variances.append(1.0 / max(variance, 0.01))
            
            total_var = sum(variances)
            return [v / total_var for v in variances]
        
        elif self.weighting_method == 'performance':
            # 表现加权: 根据近期夏普比率
            sharpes = []
            for idx in valid_indices:
                perf = self._performance_history
                if perf:
                    recent_perf = perf[-min(10, len(perf)):]
                    sharpe = np.mean(recent_perf) / max(np.std(recent_perf), 0.001)
                    sharpes.append(max(sharpe, 0.01))
                else:
                    sharpes.append(0.5)
            
            total_sharpe = sum(sharpes)
            return [s / total_sharpe for s in sharpes]
        
        else:
            # 默认使用基础权重
            weights = [self._current_weights[i] for i in valid_indices]
            total = sum(weights)
            return [w / total for w in weights]
    
    def _fuse_markets(self, predictions: List[Dict], weights: List[float]) -> Dict[str, Any]:
        """融合多个模型的市场预测"""
        fused = {}
        
        # 收集所有市场类型
        all_markets = set()
        for pred in predictions:
            all_markets.update(pred.get('markets', {}).keys())
        
        for market in all_markets:
            market_preds = []
            market_weights = []
            
            for i, pred in enumerate(predictions):
                if market in pred.get('markets', {}):
                    market_preds.append(pred['markets'][market])
                    market_weights.append(weights[i])
            
            if not market_preds:
                continue
            
            # 归一化市场权重
            total_weight = sum(market_weights)
            normalized_weights = [w / total_weight for w in market_weights]
            
            # 融合概率分布
            if market == '1x2':
                fused[market] = self._fuse_1x2(market_preds, normalized_weights)
            elif market == 'over_under':
                fused[market] = self._fuse_over_under(market_preds, normalized_weights)
            elif market == 'upset_score':
                fused[market] = self._fuse_upset_score(market_preds, normalized_weights)
            else:
                fused[market] = self._fuse_generic(market_preds, normalized_weights)
        
        return fused
    
    def _fuse_1x2(self, preds: List[Dict], weights: List[float]) -> Dict:
        """融合 1X2 预测"""
        probs = {'home': [], 'draw': [], 'away': []}
        
        for pred, weight in zip(preds, weights):
            if 'probabilities' in pred:
                for key in probs:
                    probs[key].append(pred['probabilities'].get(key, 0.33) * weight)
        
        fused = {k: sum(v) for k, v in probs.items()}
        total = sum(fused.values())
        if total > 0:
            fused = {k: round(v / total, 3) for k, v in fused.items()}
        
        return {'probabilities': fused}
    
    def _fuse_over_under(self, preds: List[Dict], weights: List[float]) -> Dict:
        """融合大小球预测"""
        lambdas = []
        for pred, weight in zip(preds, weights):
            if 'lambda' in pred:
                lambdas.append(pred['lambda'] * weight)
        
        return {'lambda': round(sum(lambdas), 3)} if lambdas else {}
    
    def _fuse_upset_score(self, preds: List[Dict], weights: List[float]) -> Dict:
        """融合冷门评分"""
        scores = []
        for pred, weight in zip(preds, weights):
            if 'score' in pred:
                scores.append(pred['score'] * weight)
        
        return {'score': round(sum(scores), 2)} if scores else {}
    
    def _fuse_generic(self, preds: List[Dict], weights: List[float]) -> Dict:
        """通用融合"""
        return preds[0] if preds else {}
    
    def _calculate_factor_exposure(self, predictions: List[Dict], weights: List[float]) -> Dict[str, float]:
        """计算因子敞口"""
        # 简化: 根据模型类型推断因子敞口
        exposure = {}
        for pred, weight in zip(predictions, weights):
            model_name = pred.get('model_name', '')
            if 'Heuristic' in model_name:
                exposure['heuristic'] = exposure.get('heuristic', 0) + weight
            elif 'Poisson' in model_name:
                exposure['poisson'] = exposure.get('poisson', 0) + weight
            elif 'XGBoost' in model_name:
                exposure['xgboost'] = exposure.get('xgboost', 0) + weight
        
        return exposure
    
    def record_performance(self, model_idx: int, actual_result: float) -> None:
        """记录模型表现用于权重调整"""
        self._performance_history.append(actual_result)
        
        # 更新 IC
        if model_idx in self._ic_history:
            self._ic_history[model_idx].append(actual_result)
    
    def rebalance_weights(self, method: str = 'ic') -> Dict[str, Any]:
        """重新平衡权重"""
        if method == 'ic':
            self.weighting_method = 'ic_weighted'
        elif method == 'risk_parity':
            self.weighting_method = 'risk_parity'
        elif method == 'performance':
            self.weighting_method = 'performance'
        
        return {
            'method': method,
            'new_weights': [round(w, 3) for w in self._current_weights],
            'rebalance_time': datetime.now().isoformat()
        }


__all__ = ['ModelEnsembleV2']
