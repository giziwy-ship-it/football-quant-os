from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple

class BaseModel(ABC):
    """
    Football Quant OS - 预测模型抽象基类
    
    所有预测模型必须实现此接口。
    支持：1X2、大小球、让球、冷门评分等多种市场预测。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """模型名称"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """模型版本号"""
        pass
    
    @property
    def supported_markets(self) -> List[str]:
        """
        支持的市场类型
        返回: ['1x2', 'over_under', 'asian_handicap', 'upset_score'] 的子集
        """
        return ['1x2', 'over_under']
    
    @abstractmethod
    def predict(self, match_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        执行预测
        
        Args:
            match_info: 比赛信息字典
                - home: 主队名
                - away: 客队名
                - odds_home: 主胜赔率
                - odds_draw: 平局赔率
                - odds_away: 客胜赔率
                - stage: group/knockout/final
                - home_xg: 主队xG (可选)
                - away_xg: 客队xG (可选)
                - ... 其他可选参数
            **kwargs: 模型特定参数
        
        Returns:
            {
                'model_name': str,
                'version': str,
                'markets': {
                    '1x2': { ... },
                    'over_under': { ... }
                },
                'confidence': float,  # 0-1
                'metadata': dict  # 模型特定元数据
            }
        """
        pass
    
    @abstractmethod
    def calibrate(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        使用历史数据校准模型
        
        Args:
            historical_data: 历史比赛结果列表
        
        Returns:
            {
                'calibration_success': bool,
                'metrics': {
                    'accuracy': float,
                    'mae': float,
                    'roi': float
                },
                'parameters': dict  # 校准后的参数
            }
        """
        pass
    
    def validate_inputs(self, match_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        输入校验
        
        Returns:
            (是否通过, 错误信息)
        """
        required_fields = ['home', 'away', 'odds_home', 'odds_draw', 'odds_away']
        
        for field in required_fields:
            if field not in match_info:
                return False, f"Missing required field: {field}"
        
        # 赔率校验
        for odds_field in ['odds_home', 'odds_draw', 'odds_away']:
            odds = match_info.get(odds_field)
            if odds is not None and (odds <= 1.0 or odds > 100):
                return False, f"Invalid odds in {odds_field}: {odds}"
        
        return True, ""
    
    def calculate_edge(self, model_prob: float, market_prob: float) -> float:
        """
        计算 Edge (模型概率 vs 市场概率的差值)
        """
        return model_prob - market_prob
    
    def get_historical_upset_rate(self, stage: str = "group") -> float:
        """
        获取历史爆冷率 (可被子类覆盖)
        """
        if stage == "knockout":
            return 0.373
        elif stage == "final":
            return 0.35
        return 0.342
