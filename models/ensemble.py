from typing import Dict, Any, List, Optional
from .base_model import BaseModel


class ModelEnsemble(BaseModel):
    """
    模型融合 (Model Ensemble) - v1.0
    
    支持多模型融合预测，通过加权平均或投票机制整合多个模型的预测结果。
    """
    
    def __init__(self, models: List[BaseModel] = None, weights: List[float] = None):
        self._models = models or []
        self._weights = weights or []
        
        # 如果未指定权重，使用等权重
        if self._models and not self._weights:
            self._weights = [1.0 / len(self._models)] * len(self._models)
        
        # 归一化权重
        if self._weights:
            total = sum(self._weights)
            self._weights = [w / total for w in self._weights]
    
    @property
    def name(self) -> str:
        return "ModelEnsemble"
    
    @property
    def version(self) -> str:
        return "1.0"
    
    @property
    def supported_markets(self) -> List[str]:
        """返回所有子模型支持市场的并集"""
        markets = set()
        for model in self._models:
            markets.update(model.supported_markets)
        return list(markets)
    
    def add_model(self, model: BaseModel, weight: float = 1.0):
        """添加子模型"""
        self._models.append(model)
        self._weights.append(weight)
        
        # 重新归一化
        total = sum(self._weights)
        self._weights = [w / total for w in self._weights]
    
    def predict(self, match_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """执行多模型融合预测"""
        if not self._models:
            return {'error': 'No models in ensemble'}
        
        # 收集所有子模型预测
        predictions = []
        for model in self._models:
            try:
                pred = model.predict(match_info, **kwargs)
                if 'error' not in pred:
                    predictions.append(pred)
            except Exception as e:
                continue
        
        if not predictions:
            return {'error': 'All models failed to predict'}
        
        # 融合预测结果
        fused_markets = self._fuse_markets(predictions, self._weights[:len(predictions)])
        
        # 计算综合置信度
        confidences = [p.get('confidence', 0.5) for p in predictions]
        avg_confidence = sum(c * w for c, w in zip(confidences, self._weights[:len(predictions)]))
        
        return {
            'model_name': self.name,
            'version': self.version,
            'markets': fused_markets,
            'confidence': round(avg_confidence, 3),
            'metadata': {
                'models_used': [p['model_name'] for p in predictions],
                'weights': [round(w, 3) for w in self._weights[:len(predictions)]],
                'individual_predictions': predictions
            }
        }
    
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
            total_w = sum(market_weights)
            market_weights = [w / total_w for w in market_weights]
            
            # 融合逻辑
            if market == '1x2':
                fused[market] = self._fuse_1x2(market_preds, market_weights)
            elif market == 'over_under':
                fused[market] = self._fuse_over_under(market_preds, market_weights)
            elif market == 'upset_score':
                fused[market] = self._fuse_upset_score(market_preds, market_weights)
            else:
                # 默认融合：取第一个
                fused[market] = market_preds[0]
        
        return fused
    
    def _fuse_1x2(self, preds: List[Dict], weights: List[float]) -> Dict[str, Any]:
        """融合1X2预测"""
        # Handle both HeuristicModel (model.home) and XGBoostPredictor (home directly) formats
        model_home = []
        model_draw = []
        model_away = []
        
        for p in preds:
            if 'model' in p:
                model_home.append(p['model']['home'])
                model_draw.append(p['model']['draw'])
                model_away.append(p['model']['away'])
            elif 'home' in p and 'draw' in p and 'away' in p:
                model_home.append(p['home'])
                model_draw.append(p['draw'])
                model_away.append(p['away'])
            else:
                model_home.append(0.33)
                model_draw.append(0.33)
                model_away.append(0.34)
        
        # 加权平均模型概率
        avg_home = sum(m * w for m, w in zip(model_home, weights))
        avg_draw = sum(m * w for m, w in zip(model_draw, weights))
        avg_away = sum(m * w for m, w in zip(model_away, weights))
        
        # 归一化
        total = avg_home + avg_draw + avg_away
        if total > 0:
            avg_home /= total
            avg_draw /= total
            avg_away /= total
        
        # 使用第一个的implied作为基准 (if available)
        implied = preds[0].get('implied', {'home': 0.33, 'draw': 0.33, 'away': 0.34})
        
        edge_home = avg_home - implied['home']
        edge_draw = avg_draw - implied['draw']
        edge_away = avg_away - implied['away']
        
        recommendations = []
        if edge_home > 0.02:
            recommendations.append(f"主胜 ({edge_home:+.1%})")
        if edge_draw > 0.02:
            recommendations.append(f"平局 ({edge_draw:+.1%})")
        if edge_away > 0.02:
            recommendations.append(f"客胜 ({edge_away:+.1%})")
        
        return {
            'market': '1X2',
            'implied': implied,
            'model': {
                'home': round(avg_home, 3),
                'draw': round(avg_draw, 3),
                'away': round(avg_away, 3)
            },
            'edge': {
                'home': round(edge_home, 3),
                'draw': round(edge_draw, 3),
                'away': round(edge_away, 3)
            },
            'recommendations': recommendations,
            'fusion_method': 'weighted_average'
        }
    
    def _fuse_over_under(self, preds: List[Dict], weights: List[float]) -> Dict[str, Any]:
        """融合大小球预测"""
        # Handle both PoissonModel (over_prob/under_prob/lambda) and XGBoostPredictor formats
        over_probs = []
        under_probs = []
        lambdas = []
        
        for p in preds:
            if 'over_prob' in p and 'under_prob' in p:
                over_probs.append(p['over_prob'])
                under_probs.append(p['under_prob'])
            elif 'over_2_5' in p and 'under_2_5' in p:
                over_probs.append(p['over_2_5'])
                under_probs.append(p['under_2_5'])
            else:
                over_probs.append(0.5)
                under_probs.append(0.5)
            
            lambdas.append(p.get('lambda', 2.5))
        
        # 加权平均lambda
        avg_lambda = sum(l * w for l, w in zip(lambdas, weights))
        
        # 加权平均概率
        avg_over = sum(p * w for p, w in zip(over_probs, weights))
        avg_under = sum(p * w for p, w in zip(under_probs, weights))
        
        # 推荐投票
        recommendations = [p.get('recommendation', 'No Edge') for p in preds]
        from collections import Counter
        vote = Counter(recommendations)
        best_rec = vote.most_common(1)[0][0] if vote else 'No Edge'
        
        return {
            'market': 'Over/Under',
            'line': preds[0].get('line', 2.5) if preds else 2.5,
            'lambda': round(avg_lambda, 2),
            'over_prob': round(avg_over, 3),
            'under_prob': round(avg_under, 3),
            'expected_goals': round(avg_lambda, 2),
            'recommendation': best_rec,
            'edge': max(p.get('edge', 0) for p in preds),
            'fusion_method': 'weighted_average + voting'
        }
    
    def _fuse_upset_score(self, preds: List[Dict], weights: List[float]) -> int:
        """融合冷门评分"""
        scores = [p for p in preds if isinstance(p, (int, float))]
        if not scores:
            return 15
        return int(sum(s * w for s, w in zip(scores, weights)))
    
    def calibrate(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """校准所有子模型并调整权重"""
        results = []
        for model in self._models:
            try:
                result = model.calibrate(historical_data)
                results.append(result)
            except Exception as e:
                results.append({'calibration_success': False, 'error': str(e)})
        
        # 根据校准结果调整权重（更好的模型获得更高权重）
        # 简化版：根据准确率调整
        accuracies = []
        for result in results:
            if result.get('calibration_success'):
                accuracies.append(result['metrics'].get('accuracy', 0.5))
            else:
                accuracies.append(0.0)
        
        if sum(accuracies) > 0:
            self._weights = [a / sum(accuracies) for a in accuracies]
        
        return {
            'calibration_success': True,
            'individual_results': results,
            'adjusted_weights': [round(w, 3) for w in self._weights],
            'metrics': {
                'avg_accuracy': sum(accuracies) / len(accuracies) if accuracies else 0
            }
        }
