"""
Football Quant OS - XGBoost Prediction Model

基于梯度提升树的大小球/1X2预测模型。
训练数据来自 feature_engineer.py 提取的历史特征。
"""

from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import json
import pickle
import numpy as np
from collections import Counter

from .base_model import BaseModel

# Try to import XGBoost
try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    xgb = None


class XGBoostPredictor(BaseModel):
    """
    XGBoost 预测模型

    支持:
    - Over/Under 2.5 分类
    - 1X2 分类 (home/draw/away)

    特征维度: ~22个 (主队8 + 客队8 + 交互5 + 历史对战1)
    """

    # 特征名列表 (必须与 flatten_features 输出顺序一致)
    FEATURE_NAMES = [
        # 主队特征
        'home_avg_goals_scored', 'home_avg_goals_conceded', 'home_avg_xg',
        'home_recent_form', 'home_attack_efficiency', 'home_defense_efficiency',
        'home_advantage', 'home_consistency',
        # 客队特征
        'away_avg_goals_scored', 'away_avg_goals_conceded', 'away_avg_xg',
        'away_recent_form', 'away_attack_efficiency', 'away_defense_efficiency',
        'away_disadvantage', 'away_consistency',
        # 交互特征
        'home_xg_diff', 'away_xg_diff', 'total_xg',
        'home_attack_vs_away_defense', 'away_attack_vs_home_defense',
        # 历史对战
        'h2h_avg_total_goals',
    ]

    def __init__(
        self,
        model_path: Optional[str] = None,
        ou_model_params: Optional[Dict] = None,
        _1x2_model_params: Optional[Dict] = None
    ):
        self._ou_model = None
        self._1x2_model = None
        self._is_trained = False
        self._ou_accuracy = 0.0
        self._1x2_accuracy = 0.0
        self._worldcup_engineer = None  # Cache for World Cup historical data

        # 默认超参数
        self._ou_params = ou_model_params or {
            'n_estimators': 200,
            'max_depth': 5,
            'learning_rate': 0.1,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'binary:logistic',
            'eval_metric': 'logloss',
            'random_state': 42,
            'n_jobs': -1,
        }
        self._1x2_params = _1x2_model_params or {
            'n_estimators': 200,
            'max_depth': 6,
            'learning_rate': 0.08,
            'subsample': 0.8,
            'colsample_bytree': 0.8,
            'objective': 'multi:softprob',
            'num_class': 3,
            'eval_metric': 'mlogloss',
            'random_state': 42,
            'n_jobs': -1,
        }

        # 如果提供了模型路径，尝试加载
        if model_path and Path(model_path).exists():
            self.load(model_path)

    @property
    def name(self) -> str:
        return "XGBoostPredictor"

    @property
    def version(self) -> str:
        return "1.0"

    @property
    def supported_markets(self) -> List[str]:
        return ['1x2', 'over_under']

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    # ------------------------------------------------------------------
    # 特征工程: 嵌套JSON -> 1D numpy
    # ------------------------------------------------------------------
    @classmethod
    def flatten_features(cls, sample: Dict[str, Any]) -> np.ndarray:
        """
        将 feature_engineer.py 生成的嵌套特征展平为 1D 向量

        Args:
            sample: build_training_data() 输出的单条记录

        Returns:
            np.ndarray: 形状 (n_features,)
        """
        home = sample.get('home', {})
        away = sample.get('away', {})
        interaction = sample.get('interaction', {})
        h2h = sample.get('head_to_head', {})

        vec = [
            # 主队
            home.get('avg_goals_scored', 1.0),
            home.get('avg_goals_conceded', 1.0),
            home.get('avg_xg', 1.0),
            home.get('recent_form', 1.5),
            home.get('attack_efficiency', 1.0),
            home.get('defense_efficiency', 1.0),
            home.get('home_advantage', 1.0),
            home.get('consistency', 0.5),
            # 客队
            away.get('avg_goals_scored', 1.0),
            away.get('avg_goals_conceded', 1.0),
            away.get('avg_xg', 1.0),
            away.get('recent_form', 1.5),
            away.get('attack_efficiency', 1.0),
            away.get('defense_efficiency', 1.0),
            away.get('away_disadvantage', 1.0),
            away.get('consistency', 0.5),
            # 交互
            interaction.get('home_xg_diff', 0.0),
            interaction.get('away_xg_diff', 0.0),
            interaction.get('total_xg', 2.0),
            interaction.get('home_attack_vs_away_defense', 1.0),
            interaction.get('away_attack_vs_home_defense', 1.0),
            # 历史对战
            h2h.get('avg_total_goals', 2.0),
        ]
        return np.array(vec, dtype=np.float32)

    @classmethod
    def build_feature_matrix(cls, samples: List[Dict[str, Any]]) -> np.ndarray:
        """批量展平特征"""
        return np.stack([cls.flatten_features(s) for s in samples])

    @classmethod
    def extract_labels(cls, samples: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """
        提取标签

        Returns:
            (ou_labels, _1x2_labels)
            ou_labels: (N,)  binary 0/1  for Over 2.5
            _1x2_labels: (N,)  int 0/1/2  for home/draw/away
        """
        ou = np.array([s['label']['over_2_5'] for s in samples], dtype=np.int32)

        _1x2 = []
        for s in samples:
            hs = s.get('home_score', s['label'].get('home_score', 0))
            aws = s.get('away_score', s['label'].get('away_score', 0))
            if hs > aws:
                _1x2.append(0)
            elif hs == aws:
                _1x2.append(1)
            else:
                _1x2.append(2)
        _1x2 = np.array(_1x2, dtype=np.int32)

        return ou, _1x2

    # ------------------------------------------------------------------
    # 训练
    # ------------------------------------------------------------------
    def train(
        self,
        training_samples: List[Dict[str, Any]],
        test_size: float = 0.2,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        训练 XGBoost 模型

        Args:
            training_samples: feature_engineer.build_training_data() 输出
            test_size: 测试集比例
            verbose: 是否打印进度

        Returns:
            训练结果报告
        """
        if not XGBOOST_AVAILABLE:
            raise ImportError("XGBoost is not installed. Run: pip install xgboost")

        if len(training_samples) < 50:
            raise ValueError(f"Need at least 50 samples, got {len(training_samples)}")

        # 特征矩阵
        X = self.build_feature_matrix(training_samples)
        y_ou, y_1x2 = self.extract_labels(training_samples)

        # 分层划分训练/测试
        from sklearn.model_selection import train_test_split
        X_train, X_test, y_ou_train, y_ou_test, y_1x2_train, y_1x2_test = \
            train_test_split(X, y_ou, y_1x2, test_size=test_size, random_state=42, stratify=y_ou)

        # ---- Over/Under 模型 ----
        if verbose:
            print(f"[XGBoost] Training Over/Under model on {len(X_train)} samples...")

        self._ou_model = xgb.XGBClassifier(**self._ou_params)
        self._ou_model.fit(
            X_train, y_ou_train,
            eval_set=[(X_test, y_ou_test)],
            verbose=False
        )
        ou_pred = self._ou_model.predict(X_test)
        self._ou_accuracy = float(np.mean(ou_pred == y_ou_test))

        if verbose:
            print(f"  OU Test Accuracy: {self._ou_accuracy:.1%}")
            print(f"  OU Class balance: {np.mean(y_ou_test):.1%} Over")

        # ---- 1X2 模型 ----
        if verbose:
            print(f"[XGBoost] Training 1X2 model on {len(X_train)} samples...")

        self._1x2_model = xgb.XGBClassifier(**self._1x2_params)
        self._1x2_model.fit(
            X_train, y_1x2_train,
            eval_set=[(X_test, y_1x2_test)],
            verbose=False
        )
        _1x2_pred = self._1x2_model.predict(X_test)
        self._1x2_accuracy = float(np.mean(_1x2_pred == y_1x2_test))

        if verbose:
            print(f"  1X2 Test Accuracy: {self._1x2_accuracy:.1%}")
            print(f"  1X2 Class distribution: {dict(Counter(y_1x2_test))}")

        self._is_trained = True

        return {
            'trained': True,
            'samples': len(training_samples),
            'train_size': len(X_train),
            'test_size': len(X_test),
            'ou_accuracy': self._ou_accuracy,
            '_1x2_accuracy': self._1x2_accuracy,
            'feature_importance_ou': self.get_feature_importance('over_under'),
            'feature_importance_1x2': self.get_feature_importance('1x2'),
        }

    # ------------------------------------------------------------------
    # 预测 (BaseModel 接口)
    # ------------------------------------------------------------------
    def predict(self, match_info: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        执行预测

        Args:
            match_info: 支持两种格式
                A) 特征格式 (来自 feature_engineer): {'home': {...}, 'away': {...}, 'interaction': {...}}
                B) 简单格式 (来自 predict.py): {'home': 'Germany', 'away': 'Japan', 'odds_home': 2.5}
                  当加载了世界杯专用模型且有历史数据时，自动提取特征

        Returns:
            兼容 ModelEnsemble 融合逻辑的预测结果
        """
        if not self._is_trained:
            return {'error': 'Model not trained. Call .train() first.'}

        # 检查输入格式: 简单格式 (home 是 str) — 尝试自动提取特征
        if isinstance(match_info.get('home'), str):
            if self._worldcup_engineer is not None:
                try:
                    home = match_info['home']
                    away = match_info['away']
                    features = self._worldcup_engineer.extract_match_features(home, away)
                    # 合并 odds
                    for key in ['odds_home', 'odds_draw', 'odds_away', 'odds_over_2_5']:
                        if key in match_info:
                            features[key] = match_info[key]
                    match_info = features
                except Exception as e:
                    return {'error': f'Feature extraction failed: {e}'}
            else:
                return {'error': 'XGBoost requires feature-engineered input (use feature_engineer.extract_match_features)'}

        # 展平特征
        try:
            X = self.flatten_features(match_info).reshape(1, -1)
        except Exception as e:
            return {'error': f'Feature flattening failed: {e}'}

        markets = {}

        # ---- Over/Under ----
        if self._ou_model is not None:
            ou_prob = self._ou_model.predict_proba(X)[0]
            over_2_5 = float(ou_prob[1])
            under_2_5 = float(ou_prob[0])

            # Edge 计算 (vs 隐含概率)
            odds_over = match_info.get('odds_over_2_5', 1.9)
            implied_over = 1.0 / odds_over if odds_over > 1 else 0.5
            edge = over_2_5 - implied_over

            if edge > 0.03:
                rec = "Over 2.5"
            elif edge < -0.03:
                rec = "Under 2.5"
            else:
                rec = "No Edge"

            markets['over_under'] = {
                'market': 'Over/Under',
                'line': 2.5,
                'over_2_5': round(over_2_5, 3),
                'under_2_5': round(under_2_5, 3),
                'expected_goals': round(over_2_5 * 3.0 + under_2_5 * 1.5, 2),  # 简化
                'recommendation': rec,
                'edge': round(edge, 3),
            }

        # ---- 1X2 ----
        if self._1x2_model is not None:
            probs = self._1x2_model.predict_proba(X)[0]
            home = float(probs[0])
            draw = float(probs[1])
            away = float(probs[2])

            odds_home = match_info.get('odds_home', 3.0)
            odds_draw = match_info.get('odds_draw', 3.2)
            odds_away = match_info.get('odds_away', 3.0)

            implied = {
                'home': round(1.0 / odds_home, 3) if odds_home > 1 else 0.33,
                'draw': round(1.0 / odds_draw, 3) if odds_draw > 1 else 0.33,
                'away': round(1.0 / odds_away, 3) if odds_away > 1 else 0.33,
            }

            edge_h = home - implied['home']
            edge_d = draw - implied['draw']
            edge_a = away - implied['away']

            recommendations = []
            if edge_h > 0.02:
                recommendations.append(f"主胜 ({edge_h:+.1%})")
            if edge_d > 0.02:
                recommendations.append(f"平局 ({edge_d:+.1%})")
            if edge_a > 0.02:
                recommendations.append(f"客胜 ({edge_a:+.1%})")

            markets['1x2'] = {
                'market': '1X2',
                'implied': implied,
                'home': round(home, 3),
                'draw': round(draw, 3),
                'away': round(away, 3),
                'edge': {
                    'home': round(edge_h, 3),
                    'draw': round(edge_d, 3),
                    'away': round(edge_a, 3),
                },
                'recommendations': recommendations,
            }

        return {
            'model_name': self.name,
            'version': self.version,
            'markets': markets,
            'confidence': round(max(
                markets.get('over_under', {}).get('edge', 0),
                max(abs(e) for e in markets.get('1x2', {}).get('edge', {}).values())
            ), 3),
            'metadata': {
                'model_type': 'xgboost',
                'features_used': len(self.FEATURE_NAMES),
                'ou_accuracy': self._ou_accuracy,
                '_1x2_accuracy': self._1x2_accuracy,
            }
        }

    # ------------------------------------------------------------------
    # 校准 (BaseModel 接口)
    # ------------------------------------------------------------------
    def calibrate(self, historical_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """用历史数据重新训练"""
        result = self.train(historical_data, verbose=False)
        return {
            'calibration_success': result['trained'],
            'metrics': {
                'accuracy': (result['ou_accuracy'] + result['_1x2_accuracy']) / 2,
                'ou_accuracy': result['ou_accuracy'],
                '_1x2_accuracy': result['_1x2_accuracy'],
            },
            'parameters': {
                'ou_params': self._ou_params,
                '_1x2_params': self._1x2_params,
            }
        }

    # ------------------------------------------------------------------
    # 特征重要性
    # ------------------------------------------------------------------
    def get_feature_importance(self, market: str = 'over_under') -> Dict[str, float]:
        """获取 XGBoost 特征重要性 (gain)"""
        model = self._ou_model if market == 'over_under' else self._1x2_model
        if model is None:
            return {}

        importance = model.feature_importances_
        total = sum(importance)
        if total > 0:
            importance = importance / total

        return {name: round(float(imp), 4) for name, imp in zip(self.FEATURE_NAMES, importance)}

    # ------------------------------------------------------------------
    # 保存/加载
    # ------------------------------------------------------------------
    def save(self, path: str):
        """保存模型到文件"""
        data = {
            'ou_model': self._ou_model,
            '_1x2_model': self._1x2_model,
            'ou_accuracy': self._ou_accuracy,
            '_1x2_accuracy': self._1x2_accuracy,
            'ou_params': self._ou_params,
            '_1x2_params': self._1x2_params,
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        print(f"[XGBoost] Model saved to {path}")

    def load(self, path: str):
        """从文件加载模型 — 支持原生格式、世界杯专用格式、v4 CRI格式"""
        with open(path, 'rb') as f:
            data = pickle.load(f)

        # 检测格式：v4 CRI 格式有 'cri_2026' 键
        if 'cri_2026' in data:
            # v4 CRI + FIFA + Position 格式
            self._ou_model = data['ou_model']
            self._1x2_model = data['_1x2_model']
            self._ou_accuracy = data.get('ou_2022_loocv', 0.0)
            self._1x2_accuracy = data.get('_1x2_2022_loocv', 0.0)
            self._is_trained = True
            self._load_worldcup_engineer()
            print(f"[XGBoost] 2026 CRI model loaded (OU:{self._ou_accuracy:.1%}, 1X2:{self._1x2_accuracy:.1%})")
        elif 'ou_2022_loocv' in data or 'ou_loocv_accuracy' in data:
            # 世界杯专用/三届格式 (v3/v4前身)
            self._ou_model = data['ou_model']
            self._1x2_model = data['_1x2_model']
            self._ou_accuracy = data.get('ou_2022_loocv', data.get('ou_loocv_accuracy', 0.0))
            self._1x2_accuracy = data.get('_1x2_2022_loocv', data.get('_1x2_loocv_accuracy', 0.0))
            self._is_trained = True
            self._load_worldcup_engineer()
            print(f"[XGBoost] World Cup specialized model loaded (OU:{self._ou_accuracy:.1%}, 1X2:{self._1x2_accuracy:.1%})")
        elif 'ou_mean_accuracy' in data or 'ou_cv_scores' in data:
            # 全历史格式 (v2)
            self._ou_model = data['ou_model']
            self._1x2_model = data['_1x2_model']
            self._ou_accuracy = data.get('ou_mean_accuracy', 0.0)
            self._1x2_accuracy = data.get('_1x2_mean_accuracy', 0.0)
            self._is_trained = True
            self._load_worldcup_engineer()
            print(f"[XGBoost] Full history model loaded (OU:{self._ou_accuracy:.1%}, 1X2:{self._1x2_accuracy:.1%})")
        else:
            # 原生 XGBoostPredictor 格式 (v1/v2)
            self._ou_model = data['ou_model']
            self._1x2_model = data['_1x2_model']
            # v2_optimized has 'ou_cv_accuracy' key
            self._ou_accuracy = data.get('ou_cv_accuracy', data.get('ou_accuracy', 0.0))
            self._1x2_accuracy = data.get('_1x2_cv_accuracy', data.get('_1x2_accuracy', 0.0))
            self._ou_params = data.get('ou_params', self._ou_params)
            self._1x2_params = data.get('_1x2_params', self._1x2_params)
            self._is_trained = True
            print(f"[XGBoost] Standard model loaded (OU:{self._ou_accuracy:.1%}, 1X2:{self._1x2_accuracy:.1%})")

    def _load_worldcup_engineer(self):
        """预加载世界杯历史数据用于自动特征提取"""
        try:
            import pandas as pd
            from features.feature_engineer import FeatureEngineer

            # 加载 1930-2018 历史数据
            df_hist = pd.read_csv(
                r'D:\openclaw-workspace\football_quant_os\data\kaggle\worldcup_1930-2018\wcmatches.csv',
                encoding='latin-1'
            )
            hist_matches = []
            for _, row in df_hist.iterrows():
                hist_matches.append({
                    'home': row['home_team'], 'away': row['away_team'],
                    'home_score': int(row['home_score']), 'away_score': int(row['away_score']),
                    'home_xg': 0, 'away_xg': 0,
                })

            # 加载 2022 数据
            df_2022 = pd.read_csv(
                r'D:\openclaw-workspace\football_quant_os\data\kaggle\worldcup_2022_qatar\Fifa_WC_2022_Match_data.csv',
                encoding='latin-1'
            )
            for _, row in df_2022.iterrows():
                hist_matches.append({
                    'home': str(row['1']), 'away': str(row['2']),
                    'home_score': int(row['1_goals']), 'away_score': int(row['2_goals']),
                    'home_xg': float(row['1_xg']) if pd.notna(row['1_xg']) else 0,
                    'away_xg': float(row['2_xg']) if pd.notna(row['2_xg']) else 0,
                })

            self._worldcup_engineer = FeatureEngineer(hist_matches)
            print(f"[XGBoost] World Cup historical data loaded: {len(hist_matches)} matches")
        except Exception as e:
            print(f"[XGBoost] Warning: Could not load World Cup historical data: {e}")
            self._worldcup_engineer = None

    # ------------------------------------------------------------------
    # 便捷: 从原始比赛数据预测
    # ------------------------------------------------------------------
    def predict_from_match(
        self,
        home: str, away: str,
        engineer,  # FeatureEngineer instance
        odds_home: float = 3.0,
        odds_draw: float = 3.2,
        odds_away: float = 3.0,
        odds_over_2_5: float = 1.9
    ) -> Dict[str, Any]:
        """从 FeatureEngineer 提取特征后预测"""
        features = engineer.extract_match_features(home, away)
        features['odds_home'] = odds_home
        features['odds_draw'] = odds_draw
        features['odds_away'] = odds_away
        features['odds_over_2_5'] = odds_over_2_5
        return self.predict(features)
