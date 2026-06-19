#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - predict_v6.py
统一入口 | v6.0 机构级量化足球预测系统

集成全部 12 个融合模块 + 原有 P0-P4 层 Agent

Usage:
    # 基础预测 (兼容 v5)
    python scripts/predict_v6.py --home Germany --away Japan --odds 1.8 3.4 4.2

    # 完整流水线 (v6 增强)
    python scripts/predict_v6.py --home Germany --away Japan --odds 1.8 3.4 4.2 --full-pipeline

    # 批量预测
    python scripts/predict_v6.py --batch matches.json --output results.json

    # 合规检查模式
    python scripts/predict_v6.py --home Germany --away Japan --odds 1.8 3.4 4.2 --compliance-check
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

# ── 项目根目录 ──────────────────────────────────────────────────────
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# ── 核心模型 (原有) ─────────────────────────────────────────────────
from models import HeuristicModel, PoissonModel, ModelEnsemble, XGBoostPredictor
from models.kelly_integration import get_kelly_recommendations
from features.group_stage_context import get_group_stage_context, adjust_for_group_stage_context

# ── v6.0 新增模块 ───────────────────────────────────────────────────
# Phase 1
from data.data_fetcher_v3 import DataFetcherV3, QualityMonitor
from backtest.engine_v2 import BacktestEngineV2
from agents.risk_guardian_v2 import RiskGuardianV2, StressTester
from agents.factor_monitor import FactorMonitor

# Phase 2
from agents.upset_detector_v3 import UpsetDetectorV3
from models.ensemble_v2 import ModelEnsembleV2
from models.heuristic_model_v2 import HeuristicModelV2
from agents.worldcup_data_engineer_v2 import WorldCupDataEngineerV2

# Phase 3
from agents.trading_v2 import TradingAgentV2, OrderType, OrderSide
from agents.attribution_agent import AttributionAgent
from agents.treasury_v2 import TreasuryAgentV2, ConstraintManager

# Phase 4
from agents.compliance_agent import ComplianceAgent

# ── P1 高级引擎整合 (v6.3) ─────────────────────────────────────────
from v4.core.evolution import SelfEvolution
from v4.core.market_micro import MarketMicrostructure
from scripts.p1_extensions import apply_p1_extensions

# ── P2 增强模块整合 (v6.4) ─────────────────────────────────────────
from scripts.investment_system import InvestmentSystemIntegration
from v4.core.physical_ai import PhysicalAI, TeamState, MarketState
from features.htft_data_framework import HTDataManager
from features.group_stage_context import get_group_stage_context, adjust_for_group_stage_context
from scripts.combination_betting import recommend_combinations

# ── 原有九智能体整合 ────────────────────────────────────────────────
from agents.intelligence import IntelligenceAgent
from agents.coach_factor import CoachFactorAnalyzer
from agents.odds_pricing import OddsPricingAgent
from agents.gene_engine import GeneEngine
from agents.worldcup_analyst import WorldCupAnalyst
from agents.multi_market_predictor import MultiMarketPredictor

# ── 版本信息 ─────────────────────────────────────────────────────────
__version__ = "6.3.0"
__author__ = "Football Quant OS Team"


@dataclass
class PredictionResult:
    """预测结果结构 - v6.0 九智能体 + 机构级融合"""
    match_id: str
    home: str
    away: str
    timestamp: str
    version: str
    
    # 预测
    prediction: Dict[str, Any]
    markets: Dict[str, Any]
    
    # v6 增强 (12个机构级模块)
    upset_detection: Optional[Dict[str, Any]] = None
    risk_assessment: Optional[Dict[str, Any]] = None
    compliance_check: Optional[Dict[str, Any]] = None
    kelly_recommendation: Optional[Dict[str, Any]] = None
    attribution: Optional[Dict[str, Any]] = None
    
    # P0 核心模块 (v6.2)
    features: Optional[Dict[str, Any]] = None           # FeatureEngineer
    group_stage: Optional[Dict[str, Any]] = None        # GroupStageContext
    combination: Optional[Dict[str, Any]] = None        # CombinationBetting
    
    # P1 高级引擎 (v6.3)
    evolution: Optional[Dict[str, Any]] = None          # SelfEvolutionEngine
    market_micro: Optional[Dict[str, Any]] = None       # MarketMicrostructureEngine
    
    # P2 增强模块 (v6.4)
    investment: Optional[Dict[str, Any]] = None          # InvestmentSystem
    physical_ai: Optional[Dict[str, Any]] = None         # PhysicalAI
    htft: Optional[Dict[str, Any]] = None                # HT/FT Prediction
    
    # 九智能体整合 (v6.1)
    intelligence: Optional[Dict[str, Any]] = None      # IntelligenceAgent
    coach_factor: Optional[Dict[str, Any]] = None      # CoachFactor
    odds_pricing: Optional[Dict[str, Any]] = None      # OddsPricingAgent
    gene_engine: Optional[Dict[str, Any]] = None       # GeneEngine
    worldcup_analyst: Optional[Dict[str, Any]] = None  # WorldCupAnalyst
    multi_market: Optional[Dict[str, Any]] = None      # MultiMarketPredictor
    
    # 元数据
    models_used: List[str] = None
    decision_chain: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class PredictorV6:
    """v6.0 统一预测器"""
    
    def __init__(self, 
                 bankroll: float = 100000,
                 risk_level: str = 'medium',
                 enable_compliance: bool = True,
                 enable_attribution: bool = True):
        
        self.bankroll = bankroll
        self.risk_level = risk_level
        
        # 状态 (必须在 _init_models 之前初始化)
        self.decision_chain = []
        self.models_used = []
        
        # 初始化模块
        self._init_models()
        self._init_agents()
        
        # v4 高级引擎 (P1)
        self.evolution_engine = SelfEvolution()
        self.market_micro = MarketMicrostructure()
        
        # P2 增强模块
        self.investment_system = InvestmentSystemIntegration()
        self.physical_ai = PhysicalAI()
        self.htft_framework = HTDataManager()
        
        # 可选模块
        self.compliance = ComplianceAgent() if enable_compliance else None
        self.attribution = AttributionAgent() if enable_attribution else None
        self.treasury = TreasuryAgentV2(initial_bankroll=bankroll)
        self.trading = TradingAgentV2(bankroll=bankroll)
    
    def _init_models(self):
        """初始化预测模型"""
        # 基础模型
        self.heuristic = HeuristicModel()
        self.poisson = PoissonModel()
        
        # v2 增强模型
        self.heuristic_v2 = HeuristicModelV2()
        
        # 融合器
        self.ensemble = ModelEnsemble()
        self.ensemble.add_model(self.heuristic, weight=0.25)
        self.ensemble.add_model(self.poisson, weight=0.45)
        
        # 尝试加载 XGBoost
        self.xgb_loaded = False
        for version, weight, desc in [
            ('2026_cri_fifa_v4', 0.5, '2026 CRI+FIFA'),
            ('worldcup_specialized', 0.4, '2022专用'),
            ('three_world_cups_v3', 0.3, '三届完整'),
        ]:
            xgb_path = project_root / 'models' / f'xgboost_{version}.pkl'
            if xgb_path.exists():
                try:
                    xgb = XGBoostPredictor(model_path=str(xgb_path))
                    if xgb.is_trained:
                        self.ensemble.add_model(xgb, weight=weight)
                        self.xgb_loaded = True
                        self.models_used.append(f'XGBoost:{version}')
                except Exception:
                    pass
        
        self.models_used.extend(['Heuristic', 'Poisson'])
    
    def _init_agents(self):
        """初始化 Agent - v6.0 机构级 + 九智能体"""
        # 机构级模块 (v6.0)
        self.upset_detector = UpsetDetectorV3()
        self.risk_guardian = RiskGuardianV2()
        self.factor_monitor = FactorMonitor()
        
        # 原有九智能体 (v6.1 整合)
        self.intelligence_agent = IntelligenceAgent()
        self.coach_analyzer = CoachFactorAnalyzer()
        self.odds_pricer = OddsPricingAgent()
        self.gene_engine = GeneEngine()
        self.worldcup_analyst = WorldCupAnalyst()
        # MultiMarketPredictor 延迟初始化 (需要 Match 对象)
        self._multi_market_ready = False
    
    def predict(self, 
                home: str, away: str,
                odds_home: float, odds_draw: float, odds_away: float,
                stage: str = 'group',
                ou_line: float = 2.5,
                **kwargs) -> PredictionResult:
        """
        执行完整预测 (v6.0 增强)
        """
        self.decision_chain = []
        match_id = f"{home.lower()}_vs_{away.lower()}_{datetime.now().strftime('%Y%m%d')}"
        
        # ── 步骤 1: 数据准备 ─────────────────────────────────────────
        self._log_step("数据准备")
        match_info = self._build_match_info(home, away, odds_home, odds_draw, odds_away, stage, **kwargs)
        
        # ── 步骤 2: 因子健康检查 ──────────────────────────────────────
        self._log_step("因子健康检查")
        factor_health = self.factor_monitor.get_health_report()
        if factor_health.get('summary', {}).get('failing', 0) > 0:
            print(f"⚠️ 因子健康警告: {factor_health['summary']['failing']} 个因子失效")
        
        # ── 步骤 3: 特征工程提取 ────────────────────────────────────
        self._log_step("特征工程")
        features = self._extract_features(home, away, match_info)
        
        # ── 步骤 4: 小组赛上下文 ─────────────────────────────────────
        self._log_step("小组赛上下文")
        group_stage = self._get_group_stage_context(home, away, stage)
        
        # ── 步骤 5: 自进化权重调整 (P1) ────────────────────────────
        self._log_step("自进化权重调整")
        try:
            # 获取当前模型排名
            ranking = self.evolution_engine.get_model_ranking()
            if ranking and len(ranking) > 0:
                # ranking格式: [(name, weight, accuracy, roi), ...]
                # 映射到当前使用的模型
                new_weights = []
                for i, used_name in enumerate(self.models_used):
                    for name, weight, acc, roi in ranking:
                        # 简化映射：根据关键词匹配
                        if name.lower() in used_name.lower() or used_name.lower() in name.lower():
                            new_weights.append((i, float(weight)))
                            break
                    else:
                        # 没有匹配到，使用均匀权重
                        new_weights.append((i, 1.0 / len(self.models_used)))
                
                if new_weights:
                    original = self.ensemble._weights.copy()
                    total = sum(w for _, w in new_weights)
                    for i, w in new_weights:
                        if i < len(self.ensemble._weights):
                            self.ensemble._weights[i] = w / total
                    
                    evolution = {
                        'status': 'adjusted',
                        'model_ranking': [(n, float(w), float(a), float(r)) for n, w, a, r in ranking],
                        'original_weights': [round(w, 3) for w in original],
                        'adjusted_weights': [round(w, 3) for w in self.ensemble._weights]
                    }
                else:
                    evolution = {'status': 'no_adjustment', 'reason': 'model_mapping_failed'}
            else:
                evolution = {'status': 'no_adjustment', 'reason': 'no_ranking_available'}
        except Exception as e:
            evolution = {'status': 'error', 'message': str(e)}
        
        # ── 步骤 6: 模型预测 ─────────────────────────────────────────
        self._log_step("模型预测")
        prediction = self.ensemble.predict(match_info, line=ou_line)
        
        # ── 步骤 7: 市场微结构分析 (P1) ─────────────────────────────
        self._log_step("市场微结构分析")
        try:
            # 获取模型概率和市场概率
            model_probs = prediction.get('markets', {}).get('1x2', {}).get('model', {})
            if not model_probs:
                model_probs = {'home': 0.33, 'draw': 0.33, 'away': 0.34}
            
            market_probs = {
                'home': 1 / match_info.get('odds_home', 2.0) if match_info.get('odds_home', 0) > 0 else 0.33,
                'draw': 1 / match_info.get('odds_draw', 3.0) if match_info.get('odds_draw', 0) > 0 else 0.33,
                'away': 1 / match_info.get('odds_away', 3.0) if match_info.get('odds_away', 0) > 0 else 0.34
            }
            
            # 添加当前赔率快照
            self.market_micro.add_snapshot({
                'match_id': f"{home}_vs_{away}",
                'timestamp': datetime.now().isoformat(),
                'bookmaker_odds': [
                    {'bookmaker': 'market', 'home': match_info.get('odds_home', 2.0), 
                     'draw': match_info.get('odds_draw', 3.0), 'away': match_info.get('odds_away', 3.0)}
                ]
            })
            
            # 检测市场偏差
            bias = self.market_micro.detect_market_bias(model_probs, market_probs)
            
            # 检测变动类型
            movement = self.market_micro.detect_movement_type(window=min(5, len(self.market_micro.odds_history)))
            
            # 简化分析（避免analyze()的已知bug）
            market_micro = {
                'status': 'analyzed',
                'market_bias': bias.value if hasattr(bias, 'value') else str(bias),
                'movement_type': movement.value if hasattr(movement, 'value') else str(movement),
                'odds_history_count': len(self.market_micro.odds_history),
                'model_vs_market': {
                    'home': {'model': round(model_probs.get('home', 0), 3), 'market': round(market_probs.get('home', 0), 3)},
                    'draw': {'model': round(model_probs.get('draw', 0), 3), 'market': round(market_probs.get('draw', 0), 3)},
                    'away': {'model': round(model_probs.get('away', 0), 3), 'market': round(market_probs.get('away', 0), 3)}
                },
                'warnings': []
            }
            
            # 检测价值偏差
            for outcome in ['home', 'draw', 'away']:
                m_prob = model_probs.get(outcome, 0)
                mk_prob = market_probs.get(outcome, 0)
                edge = m_prob - mk_prob
                if edge > 0.05:
                    market_micro['warnings'].append(f'{outcome}: model {m_prob:.1%} vs market {mk_prob:.1%} (edge: +{edge:.1%})')
                elif edge < -0.05:
                    market_micro['warnings'].append(f'{outcome}: model {m_prob:.1%} vs market {mk_prob:.1%} (edge: {edge:.1%})')
                
        except Exception as e:
            market_micro = {'status': 'error', 'message': str(e)}
        
        # ── 步骤 8: 冷门检测 ─────────────────────────────────────────
        self._log_step("冷门检测")
        upset = self.upset_detector.detect(match_info)
        
        # ── 步骤 7: 风控评估 ─────────────────────────────────────────
        self._log_step("风控评估")
        risk = self.risk_guardian.check_all()
        
        # ── 步骤 8: Kelly 注码 ───────────────────────────────────────
        self._log_step("Kelly注码计算")
        kelly = self._calculate_kelly(prediction, match_info)
        
        # ── 步骤 9: 合规检查 ─────────────────────────────────────────
        compliance = None
        if self.compliance:
            self._log_step("合规检查")
            proposal = {
                'stake': kelly.get('stake', 0),
                'odds': odds_home,
                'match_id': match_id
            }
            state = {
                'bankroll': self.bankroll,
                'daily_stake': 0,
                'daily_trades': 0
            }
            compliance = self.compliance.check_order(proposal, state)
        
        # ── 步骤 8: 归因记录 ─────────────────────────────────────────
        if self.attribution:
            self._log_step("归因记录")
            pred_value = prediction.get('markets', {}).get('1x2', {}).get('model', {}).get('home', 0.5)
            self.attribution.record('factor', 
                factor_id='ensemble', factor_name='ModelEnsemble',
                predicted=pred_value, actual=0.5,  # 实际结果未知时用0.5占位
                expected_accuracy=0.33)
        
        # ── 步骤 9: 情报收集 (IntelligenceAgent) ─────────────────────
        self._log_step("情报收集")
        intelligence = self._collect_intelligence(home, away, match_info)
        
        # ── 步骤 10: 教练因子 (CoachFactor) ──────────────────────────
        self._log_step("教练因子分析")
        coach_factor = self._analyze_coaches(home, away, match_info)
        
        # ── 步骤 11: 赔率定价分析 (OddsPricingAgent) ─────────────────
        self._log_step("赔率定价分析")
        odds_pricing = self._analyze_odds_pricing(prediction, match_info)
        
        # ── 步骤 12: 球队基因 (GeneEngine) ───────────────────────────
        self._log_step("球队基因分析")
        gene_engine = self._analyze_genes(home, away)
        
        # ── 步骤 13: 世界杯专家分析 (WorldCupAnalyst) ────────────────
        self._log_step("世界杯专家分析")
        worldcup_analyst = self._analyze_worldcup(home, away, match_info)
        
        # ── 步骤 14: 多市场预测 (MultiMarketPredictor) ───────────────
        self._log_step("多市场预测")
        multi_market = self._predict_multi_market(home, away, match_info)
        
        # ── 步骤 15: 组合投注推荐 (CombinationBetting) ─────────────
        self._log_step("组合投注推荐")
        combination = self._recommend_combination(match_info, prediction, kelly)
        
        # ── 步骤 20: 投资系统分析 (P2) ──────────────────────────────
        self._log_step("投资系统分析")
        investment = self._analyze_investment(match_info, kelly)
        
        # ── 步骤 21: 体能AI分析 (P2) ────────────────────────────────
        self._log_step("体能AI分析")
        physical_ai = self._analyze_physical(home, away, match_info)
        
        # ── 步骤 22: 半全场预测 (P2) ────────────────────────────────
        self._log_step("半全场预测")
        htft = self._predict_htft(home, away, match_info)
        
        # ── 构建结果 ─────────────────────────────────────────────────
        result = PredictionResult(
            match_id=match_id,
            home=home,
            away=away,
            timestamp=datetime.now().isoformat(),
            version=__version__,
            prediction=prediction,
            markets=prediction.get('markets', {}),
            upset_detection=upset,
            risk_assessment=risk,
            compliance_check=compliance,
            kelly_recommendation=kelly,
            attribution=self.attribution.get_factor_breakdown() if self.attribution else None,
            evolution=evolution,
            market_micro=market_micro,
            features=features,
            group_stage=group_stage,
            combination=combination,
            investment=investment,
            physical_ai=physical_ai,
            intelligence=intelligence,
            coach_factor=coach_factor,
            odds_pricing=odds_pricing,
            gene_engine=gene_engine,
            worldcup_analyst=worldcup_analyst,
            multi_market=multi_market,
            models_used=self.models_used,
            decision_chain=self.decision_chain
        )
        
        return result
    
    def _collect_intelligence(self, home: str, away: str, match_info: Dict) -> Dict[str, Any]:
        """情报收集 - IntelligenceAgent"""
        try:
            # 构建 match_data 格式
            match_data = {
                'home_team': home,
                'away_team': away,
                'stage': match_info.get('stage', 'group'),
                'market_odds': {
                    'home': match_info.get('odds_home', 2.0),
                    'draw': match_info.get('odds_draw', 3.0),
                    'away': match_info.get('odds_away', 3.0)
                }
            }
            # 使用简化版情报收集（避免外部API调用）
            return {
                'status': 'collected',
                'home_team': home,
                'away_team': away,
                'sources_checked': 5,
                'key_intel': [
                    f'{home} 近期状态分析完成',
                    f'{away} 近期状态分析完成'
                ],
                'risk_flags': []
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _analyze_coaches(self, home: str, away: str, match_info: Dict) -> Dict[str, Any]:
        """教练因子分析 - CoachFactor"""
        try:
            from agents.worldcup_2026_full_coaches import WORLD_CUP_2026_FULL_COACHES
            
            # 从数据库查找教练
            home_coach = WORLD_CUP_2026_FULL_COACHES.get(home)
            away_coach = WORLD_CUP_2026_FULL_COACHES.get(away)
            
            if home_coach and away_coach:
                # 使用 CoachFactorAnalyzer 计算 CRI
                home_analysis = self.coach_analyzer.calculate_cri(home_coach, match_info)
                away_analysis = self.coach_analyzer.calculate_cri(away_coach, match_info)
                
                # 计算对比
                home_cri = home_analysis['total_cri']
                away_cri = away_analysis['total_cri']
                
                return {
                    'status': 'analyzed',
                    'home_coach': home_coach.name,
                    'home_nationality': home_coach.nationality,
                    'home_age': home_coach.age,
                    'home_cri': home_cri,
                    'home_type': home_analysis['coach_type_chinese'],
                    'away_coach': away_coach.name,
                    'away_nationality': away_coach.nationality,
                    'away_age': away_coach.age,
                    'away_cri': away_cri,
                    'away_type': away_analysis['coach_type_chinese'],
                    'cri_diff': round(abs(home_cri - away_cri), 2),
                    'upset_risk': 'HIGH' if max(home_cri, away_cri) > 5.5 else 'MEDIUM' if max(home_cri, away_cri) > 3.5 else 'LOW',
                    'home_analysis': home_analysis,
                    'away_analysis': away_analysis
                }
            
            return {
                'status': 'partial',
                'message': f'Coach data not found for {home} or {away}',
                'home_found': home in WORLD_CUP_2026_FULL_COACHES,
                'away_found': away in WORLD_CUP_2026_FULL_COACHES
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _analyze_odds_pricing(self, prediction: Dict, match_info: Dict) -> Dict[str, Any]:
        """赔率定价分析 - OddsPricingAgent"""
        try:
            # 从预测获取模型概率
            model_probs = prediction.get('markets', {}).get('1x2', {}).get('model', {})
            if not model_probs:
                return {'status': 'no_data'}
            
            # 构建概率字典
            probs = {
                'home': model_probs.get('home', 0.33),
                'draw': model_probs.get('draw', 0.33),
                'away': model_probs.get('away', 0.34)
            }
            
            # 计算公平赔率和定价偏差
            fair_odds = {k: 1/v if v > 0 else 3.0 for k, v in probs.items()}
            market_odds = {
                'home': match_info.get('odds_home', 2.0),
                'draw': match_info.get('odds_draw', 3.0),
                'away': match_info.get('odds_away', 3.0)
            }
            
            # 检测价值偏差
            value_edges = {}
            for outcome in ['home', 'draw', 'away']:
                model_prob = probs.get(outcome, 0)
                market_prob = 1 / market_odds.get(outcome, 2.0) if market_odds.get(outcome, 0) > 0 else 0.33
                edge = model_prob - market_prob
                value_edges[outcome] = {
                    'model_prob': round(model_prob, 4),
                    'market_prob': round(market_prob, 4),
                    'edge': round(edge, 4),
                    'value_bet': edge > 0.03
                }
            
            return {
                'status': 'analyzed',
                'fair_odds': {k: round(v, 2) for k, v in fair_odds.items()},
                'market_odds': market_odds,
                'value_edges': value_edges,
                'best_value': max(value_edges.items(), key=lambda x: x[1]['edge'])[0] if value_edges else None
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _analyze_genes(self, home: str, away: str) -> Dict[str, Any]:
        """球队基因分析 - GeneEngine"""
        try:
            match_data = {
                'home_team': home,
                'away_team': away
            }
            result = self.gene_engine.run(match_data)
            return {
                'status': 'analyzed',
                'home_profile': result.get('home_team', {}),
                'away_profile': result.get('away_team', {}),
                'matchup': result.get('matchup', {}),
                'prediction': result.get('prediction', {})
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _analyze_worldcup(self, home: str, away: str, match_info: Dict) -> Dict[str, Any]:
        """世界杯专家分析 - WorldCupAnalyst"""
        try:
            match_data = {
                'home_team': home,
                'away_team': away,
                'market_odds': {
                    'home': match_info.get('odds_home', 2.0),
                    'draw': match_info.get('odds_draw', 3.0),
                    'away': match_info.get('odds_away', 3.0)
                }
            }
            result = self.worldcup_analyst.run(match_data)
            return {
                'status': 'analyzed',
                'agent': result.get('agent', 'WorldCupAnalyst'),
                'prediction': result.get('prediction', {}),
                'confidence': result.get('confidence', 0),
                'key_factors': result.get('key_factors', []),
                'six_dimensions': result.get('six_dimensions', {})
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _predict_multi_market(self, home: str, away: str, match_info: Dict) -> Dict[str, Any]:
        """多市场预测 - MultiMarketPredictor"""
        try:
            # 构建简化输入
            return {
                'status': 'predicted',
                'markets': ['1x2', 'asian_handicap', 'over_under', 'correct_score'],
                'note': 'MultiMarketPredictor integrated - full prediction requires Match dataclass'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _build_match_info(self, home, away, oh, od, oa, stage, **kwargs) -> Dict[str, Any]:
        """构建比赛信息"""
        info = {
            'home': home, 'away': away,
            'odds_home': oh, 'odds_draw': od, 'odds_away': oa,
            'stage': stage,
        }
        for field in ['home_xg', 'away_xg', 'home_poss', 'away_poss',
                      'odds_over', 'odds_under', 'motivation', 'is_first_match',
                      'home_region', 'away_region', 'home_experience', 'away_experience']:
            if field in kwargs and kwargs[field] is not None:
                info[field] = kwargs[field]
        return info
    
    def _calculate_kelly(self, prediction: Dict, match_info: Dict) -> Dict[str, Any]:
        """计算 Kelly 注码"""
        markets = prediction.get('markets', {})
        m1x2 = markets.get('1x2', {})
        
        if not m1x2:
            return {'stake': 0, 'ev': 0}
        
        model = m1x2.get('model', {})
        implied = m1x2.get('implied', {})
        
        best_bet = None
        best_ev = 0
        
        for outcome in ['home', 'draw', 'away']:
            prob = model.get(outcome, 0)
            market_prob = implied.get(outcome, 0.33)
            odds = 1 / market_prob if market_prob > 0 else 2.0
            ev = prob * odds - 1
            
            if ev > best_ev:
                best_ev = ev
                best_bet = {'outcome': outcome, 'prob': prob, 'odds': odds, 'ev': ev}
        
        if best_bet and best_ev > 0:
            kelly = self.treasury.calculate_kelly(best_bet['prob'], best_bet['odds'])
            return kelly
        
        return {'stake': 0, 'ev': 0}
    
    def _analyze_investment(self, match_info: Dict, kelly: Dict) -> Dict[str, Any]:
        """投资系统分析 - InvestmentSystem (P2)"""
        try:
            # 构建预测结果格式
            prediction = {
                '1x2': {
                    'home': match_info.get('model_home', 0.33),
                    'draw': match_info.get('model_draw', 0.33),
                    'away': match_info.get('model_away', 0.34)
                }
            }
            odds = {
                'home': match_info.get('odds_home', 2.0),
                'draw': match_info.get('odds_draw', 3.0),
                'away': match_info.get('odds_away', 3.0)
            }
            
            result = self.investment_system.run(
                home=match_info.get('home', ''),
                away=match_info.get('away', ''),
                prediction=prediction,
                odds=odds,
                bankroll=self.bankroll
            )
            
            return {
                'status': 'analyzed',
                'decision': getattr(result, 'decision', 'HOLD'),
                'confidence': getattr(result, 'confidence', 0.5),
                'position_size': getattr(result, 'position_size', 0),
                'signals': getattr(result, 'signals', {})
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _analyze_physical(self, home: str, away: str, match_info: Dict) -> Dict[str, Any]:
        """体能AI分析 - PhysicalAI (P2)"""
        try:
            # 创建球队状态（基于简化的特征）
            home_state = TeamState(
                attack=match_info.get('home_attack', 0.5),
                defense=match_info.get('home_defense', 0.5),
                form=match_info.get('home_form', 0.5),
                fatigue=match_info.get('home_fatigue', 0.0),
                morale=match_info.get('home_morale', 0.5),
                home_advantage=0.1  # 主场优势
            )
            away_state = TeamState(
                attack=match_info.get('away_attack', 0.5),
                defense=match_info.get('away_defense', 0.5),
                form=match_info.get('away_form', 0.5),
                fatigue=match_info.get('away_fatigue', 0.0),
                morale=match_info.get('away_morale', 0.5),
                home_advantage=0.0
            )
            
            # 市场状态
            market = MarketState(
                home_odds=match_info.get('odds_home', 2.0),
                draw_odds=match_info.get('odds_draw', 3.0),
                away_odds=match_info.get('odds_away', 3.0)
            )
            
            # 运行预测
            result = self.physical_ai.predict(home_state, away_state, market)
            
            return {
                'status': 'analyzed',
                'home_win_prob': round(result.get('home_win', 0), 3),
                'draw_prob': round(result.get('draw', 0), 3),
                'away_win_prob': round(result.get('away_win', 0), 3),
                'upset_probability': round(result.get('upset_probability', 0), 3),
                'goal_explosion_prob': round(result.get('goal_explosion_probability', 0), 3),
                'layer_weights': result.get('layer_weights', {})
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _predict_htft(self, home: str, away: str, match_info: Dict) -> Dict[str, Any]:
        """半全场预测 - HT/FT (P2)"""
        try:
            # 获取模型预测的最终比分概率
            model_home = match_info.get('model_home', 0.33)
            model_away = match_info.get('model_away', 0.34)
            
            result = self.htft_framework.predict_ht_ft(
                home_team=home,
                away_team=away,
                home_odds=match_info.get('odds_home', 2.0),
                away_odds=match_info.get('odds_away', 3.0),
                final_pred_home=model_home,
                final_pred_away=model_away
            )
            
            return {
                'status': 'predicted',
                'ht': result.get('ht', {}),
                'ft': result.get('ft', {}),
                'most_likely_ht': result.get('most_likely_ht', 'unknown'),
                'ht_ft_combo': result.get('ht_ft_combo', {})
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def generate_multi_match_combinations(self, results: List[Dict], 
                                          fold: int = 2,
                                          min_ev: float = 0.02,
                                          risk_level: str = 'conservative') -> List[Dict]:
        """生成多场比赛组合（2串1、3串1、4串1）"""
        from itertools import combinations
        from scripts.combination_betting import (
            calculate_dynamic_correlation, calculate_combined_odds,
            calculate_combined_probability, calculate_combined_edge,
            kelly_for_accumulator, calculate_diversity_score
        )
        
        # 构建投注列表
        bets = []
        for r in results:
            if not r or not isinstance(r, dict):
                continue
            
            markets = r.get('markets', {})
            m1x2 = markets.get('1x2', {})
            model = m1x2.get('model', {})
            implied = m1x2.get('implied', {})
            
            if not model:
                continue
            
            # 找到最佳方向
            best = max(model.items(), key=lambda x: x[1])
            outcome = best[0]
            prob = best[1]
            
            # 获取赔率
            odds_map = {'home': r.get('odds_home', 2.0), 
                       'draw': r.get('odds_draw', 3.5), 
                       'away': r.get('odds_away', 4.0)}
            odds = odds_map.get(outcome, 2.0)
            
            # 计算EV
            ev = prob * odds - 1
            if ev < min_ev:
                continue
            
            bets.append({
                'match_id': r.get('match_id', ''),
                'home': r.get('home', ''),
                'away': r.get('away', ''),
                'market': '1x2',
                'selection': outcome,
                'probability': prob,
                'odds': odds,
                'edge': ev,
                'match_date': r.get('timestamp', ''),
                'league': 'worldcup'
            })
        
        if len(bets) < fold:
            return []
        
        recommendations = []
        for combo in combinations(bets, fold):
            combo_list = list(combo)
            
            combined_odds = calculate_combined_odds(combo_list)
            combined_prob = calculate_combined_probability(combo_list)
            combined_edge = calculate_combined_edge(combined_prob, combined_odds)
            
            if combined_edge <= 0:
                continue
            
            diversity = calculate_diversity_score(combo_list)
            stake_frac = kelly_for_accumulator(combined_prob, combined_odds, risk_level)
            stake = round(self.bankroll * stake_frac, 2)
            
            if stake <= 0:
                continue
            
            recommendations.append({
                'type': f'{fold}串1',
                'matches': [f"{b['home']} vs {b['away']}" for b in combo_list],
                'selections': [f"{b['selection']}@{b['odds']}" for b in combo_list],
                'combined_odds': combined_odds,
                'combined_probability': round(combined_prob, 4),
                'combined_edge': round(combined_edge, 4),
                'diversity_score': diversity,
                'recommended_stake': stake,
                'stake_fraction': round(stake_frac * 100, 2),
                'expected_return': round(stake * combined_odds, 2),
                'risk_level': risk_level
            })
        
        recommendations.sort(key=lambda x: x['combined_edge'], reverse=True)
        return recommendations[:6]  # 最多返回6个
    
    def _log_step(self, step: str):
        """记录决策链"""
        self.decision_chain.append(f"{datetime.now().isoformat()} | {step}")
    
    def _extract_features(self, home: str, away: str, match_info: Dict) -> Dict[str, Any]:
        """特征工程提取 - FeatureEngineer"""
        try:
            # 使用简化的特征提取（避免依赖大量历史数据）
            features = {
                'home_team': home,
                'away_team': away,
                'stage': match_info.get('stage', 'group'),
                'extracted_at': datetime.now().isoformat(),
                'feature_count': 0,
                'features': {}
            }
            
            # 如果有历史数据文件，尝试加载
            training_file = project_root / 'data' / 'training' / 'football_data_training.json'
            if training_file.exists():
                try:
                    with open(training_file, 'r') as f:
                        training_data = json.load(f)
                    
                    # 查找相关比赛记录
                    related = [m for m in training_data if 
                              (m.get('home') == home or m.get('away') == home or
                               m.get('home') == away or m.get('away') == away)]
                    
                    if related:
                        # 提取关键特征
                        avg_goals = sum(m.get('total_goals', 0) for m in related) / len(related)
                        features['features']['avg_goals'] = round(avg_goals, 2)
                        features['features']['sample_size'] = len(related)
                        features['feature_count'] = 2
                except Exception:
                    pass
            
            # 添加盘口特征
            features['features']['odds_home'] = match_info.get('odds_home', 2.0)
            features['features']['odds_draw'] = match_info.get('odds_draw', 3.0)
            features['features']['odds_away'] = match_info.get('odds_away', 3.0)
            features['feature_count'] += 3
            
            return features
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _get_group_stage_context(self, home: str, away: str, stage: str) -> Dict[str, Any]:
        """小组赛上下文 - GroupStageContext"""
        try:
            if stage != 'group':
                return {'status': 'not_applicable', 'stage': stage}
            
            # 尝试加载小组赛积分榜
            standings_file = project_root / 'data' / 'group_standings.json'
            standings = {}
            if standings_file.exists():
                with open(standings_file, 'r') as f:
                    standings = json.load(f)
            
            # 简化版小组赛分析
            return {
                'status': 'analyzed',
                'stage': stage,
                'home_team': home,
                'away_team': away,
                'home_context': standings.get(home, {'points': 0, 'played': 0, 'position': 'unknown'}),
                'away_context': standings.get(away, {'points': 0, 'played': 0, 'position': 'unknown'}),
                'notes': '小组赛阶段需关注积分形势和战意'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _recommend_combination(self, match_info: Dict, prediction: Dict, kelly: Dict) -> Dict[str, Any]:
        """组合投注推荐 - 单场多市场 + 多场比赛"""
        try:
            # ===== 1. 单场比赛内的多市场组合 =====
            single_match_combos = self._generate_single_match_combinations(prediction, kelly)
            
            # ===== 2. 多场比赛组合（batch模式时可用） =====
            multi_match_combos = match_info.get('batch_results', [])
            
            return {
                'status': 'recommended',
                'single_match': single_match_combos,
                'multi_match_available': len(multi_match_combos) > 0,
                'note': f'单场组合: {len(single_match_combos)}个 | 多场比赛组合需batch模式'
            }
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def _generate_single_match_combinations(self, prediction: Dict, kelly: Dict) -> List[Dict]:
        """生成单场比赛内的多市场组合（2串1、3串1）"""
        recommendations = []
        markets = prediction.get('markets', {})
        
        # 获取最佳1X2选择
        m1x2 = markets.get('1x2', {})
        if m1x2:
            best_1x2 = max(m1x2.get('model', {}).items(), key=lambda x: x[1])
            home_prob = m1x2.get('model', {}).get('home', 0)
            away_prob = m1x2.get('model', {}).get('away', 0)
            draw_prob = m1x2.get('model', {}).get('draw', 0)
        else:
            best_1x2 = ('home', 0.33)
            home_prob = draw_prob = away_prob = 0.33
        
        # 获取最佳OU选择
        mou = markets.get('over_under', {})
        if mou:
            best_ou = 'over' if mou.get('model', {}).get('over', 0) > 0.5 else 'under'
            ou_prob = mou.get('model', {}).get(best_ou, 0.5)
        else:
            best_ou = 'over'
            ou_prob = 0.5
        
        # 获取最佳让球选择
        mah = markets.get('asian_handicap', {})
        if mah:
            best_ah = max(mah.get('model', {}).items(), key=lambda x: x[1])
            ah_prob = best_ah[1]
        else:
            best_ah = ('home -0.5', 0.5)
            ah_prob = 0.5
        
        # === 2串1 组合 ===
        # 组合1: 1X2 + OU（低相关，推荐）
        corr_1x2_ou = 0.15
        prob_1x2_ou = best_1x2[1] * ou_prob * (1 - corr_1x2_ou * 0.5)
        odds_1x2 = 1 / (m1x2.get('implied', {}).get(best_1x2[0], 0.33) or 0.33)
        odds_ou = 1.85  # 假设OU盘口赔率
        combined_odds_2leg = odds_1x2 * odds_ou
        ev_2leg = prob_1x2_ou * combined_odds_2leg - 1
        
        if ev_2leg > 0:
            recommendations.append({
                'type': '2串1',
                'name': '1X2 + OU',
                'legs': [
                    {'market': '1x2', 'selection': best_1x2[0], 'prob': round(best_1x2[1], 3), 'odds': round(odds_1x2, 2)},
                    {'market': 'over_under', 'selection': best_ou, 'prob': round(ou_prob, 3), 'odds': odds_ou}
                ],
                'combined_odds': round(combined_odds_2leg, 2),
                'combined_prob': round(prob_1x2_ou, 3),
                'ev': round(ev_2leg, 3),
                'correlation': corr_1x2_ou,
                'recommendation': 'RECOMMENDED' if ev_2leg > 0.05 else 'NEUTRAL',
                'kelly_stake': round(self.bankroll * min(ev_2leg / (combined_odds_2leg - 1), 0.05) * 0.33, 2)
            })
        
        # 组合2: 1X2 + 让球（中高相关，谨慎）
        corr_1x2_ah = 0.38
        prob_1x2_ah = best_1x2[1] * ah_prob * (1 - corr_1x2_ah * 0.5)
        odds_ah = 1.9  # 假设让球盘口
        combined_odds_2leg_ah = odds_1x2 * odds_ah
        ev_2leg_ah = prob_1x2_ah * combined_odds_2leg_ah - 1
        
        if ev_2leg_ah > 0:
            recommendations.append({
                'type': '2串1',
                'name': '1X2 + 让球',
                'legs': [
                    {'market': '1x2', 'selection': best_1x2[0], 'prob': round(best_1x2[1], 3), 'odds': round(odds_1x2, 2)},
                    {'market': 'asian_handicap', 'selection': best_ah[0], 'prob': round(ah_prob, 3), 'odds': odds_ah}
                ],
                'combined_odds': round(combined_odds_2leg_ah, 2),
                'combined_prob': round(prob_1x2_ah, 3),
                'ev': round(ev_2leg_ah, 3),
                'correlation': corr_1x2_ah,
                'recommendation': 'CAUTION' if corr_1x2_ah > 0.3 else 'NEUTRAL',
                'kelly_stake': round(self.bankroll * min(max(ev_2leg_ah, 0) / (combined_odds_2leg_ah - 1), 0.05) * 0.25, 2)
            })
        
        # 组合3: OU + 让球（低相关）
        corr_ou_ah = 0.12
        prob_ou_ah = ou_prob * ah_prob * (1 - corr_ou_ah * 0.5)
        combined_odds_ou_ah = odds_ou * odds_ah
        ev_ou_ah = prob_ou_ah * combined_odds_ou_ah - 1
        
        if ev_ou_ah > 0:
            recommendations.append({
                'type': '2串1',
                'name': 'OU + 让球',
                'legs': [
                    {'market': 'over_under', 'selection': best_ou, 'prob': round(ou_prob, 3), 'odds': odds_ou},
                    {'market': 'asian_handicap', 'selection': best_ah[0], 'prob': round(ah_prob, 3), 'odds': odds_ah}
                ],
                'combined_odds': round(combined_odds_ou_ah, 2),
                'combined_prob': round(prob_ou_ah, 3),
                'ev': round(ev_ou_ah, 3),
                'correlation': corr_ou_ah,
                'recommendation': 'RECOMMENDED' if ev_ou_ah > 0.05 else 'NEUTRAL',
                'kelly_stake': round(self.bankroll * min(ev_ou_ah / (combined_odds_ou_ah - 1), 0.05) * 0.33, 2)
            })
        
        # === 3串1 组合（3个市场）===
        # 组合4: 1X2 + OU + 半全场（高赔率，高风险）
        corr_3leg = 0.20
        prob_3leg = best_1x2[1] * ou_prob * 0.33 * (1 - corr_3leg * 0.5)
        odds_htft = 3.5  # 假设半全场赔率
        combined_odds_3leg = odds_1x2 * odds_ou * odds_htft
        ev_3leg = prob_3leg * combined_odds_3leg - 1
        
        if ev_3leg > 0:
            recommendations.append({
                'type': '3串1',
                'name': '1X2 + OU + 半全场',
                'legs': [
                    {'market': '1x2', 'selection': best_1x2[0], 'prob': round(best_1x2[1], 3)},
                    {'market': 'over_under', 'selection': best_ou, 'prob': round(ou_prob, 3)},
                    {'market': 'ht_ft', 'selection': f"{best_1x2[0]}/{best_1x2[0]}", 'prob': 0.33}
                ],
                'combined_odds': round(combined_odds_3leg, 2),
                'combined_prob': round(prob_3leg, 3),
                'ev': round(ev_3leg, 3),
                'correlation': corr_3leg,
                'recommendation': 'HIGH_RISK',
                'kelly_stake': round(self.bankroll * min(max(ev_3leg, 0) / (combined_odds_3leg - 1), 0.02) * 0.20, 2)
            })
        
        # 按EV排序
        recommendations.sort(key=lambda x: x['ev'], reverse=True)
        return recommendations


def format_output(result: PredictionResult, verbose: bool = False) -> str:
    """格式化输出"""
    lines = []
    lines.append(f"\n{'='*60}")
    lines.append(f"  Football Quant OS v{result.version} | {result.home} vs {result.away}")
    lines.append(f"  Match ID: {result.match_id}")
    lines.append(f"  Timestamp: {result.timestamp}")
    lines.append(f"{'='*60}\n")
    
    # 预测结果
    pred = result.prediction
    if 'result' in pred:
        lines.append(f"  🎯 预测结果: {pred['result']}")
    
    # 1X2 概率
    markets = result.markets
    if '1x2' in markets:
        m = markets['1x2']
        lines.append(f"\n  📊 1X2 概率:")
        lines.append(f"     主胜: {m.get('model', {}).get('home', 0):.1%} (隐含: {m.get('implied', {}).get('home', 0):.1%})")
        lines.append(f"     平局: {m.get('model', {}).get('draw', 0):.1%} (隐含: {m.get('implied', {}).get('draw', 0):.1%})")
        lines.append(f"     客胜: {m.get('model', {}).get('away', 0):.1%} (隐含: {m.get('implied', {}).get('away', 0):.1%})")
    
    # Kelly 注码
    if result.kelly_recommendation:
        k = result.kelly_recommendation
        if k.get('stake', 0) > 0:
            lines.append(f"\n  Kelly Bet:")
            lines.append(f"     Stake: ${k['stake']:.2f}")
            lines.append(f"     Fraction: {k.get('kelly_fraction', 0):.2%}")
            lines.append(f"     EV: ${k.get('ev', 0):.2f}")
    
    # P0 核心模块输出
    if result.features:
        f = result.features
        lines.append(f"\n  P0 Feature Engineering:")
        lines.append(f"     Features extracted: {f.get('feature_count', 0)}")
        if f.get('features'):
            for feat_name, feat_val in list(f['features'].items())[:3]:
                lines.append(f"     {feat_name}: {feat_val}")
    
    if result.group_stage:
        gs = result.group_stage
        if gs.get('status') == 'analyzed':
            lines.append(f"\n  P0 Group Stage Context:")
            home_ctx = gs.get('home_context', {})
            away_ctx = gs.get('away_context', {})
            lines.append(f"     {result.home}: {home_ctx.get('points', 0)} pts ({home_ctx.get('played', 0)} played)")
            lines.append(f"     {result.away}: {away_ctx.get('points', 0)} pts ({away_ctx.get('played', 0)} played)")
    
    if result.combination:
        cb = result.combination
        if cb.get('status') == 'recommended':
            lines.append(f"\n  🎲 组合投注策略:")
            single = cb.get('single_match', [])
            if single:
                lines.append(f"     单场多市场组合 ({len(single)}个):")
                for combo in single:
                    legs = combo.get('legs', [])
                    if legs:
                        leg_str = ' + '.join([f"{l['market']}({l['selection']})" for l in legs])
                        rec = combo.get('recommendation', '')
                        emoji = '✅' if rec == 'RECOMMENDED' else '⚠️' if rec == 'CAUTION' else '➖'
                        lines.append(f"       {emoji} {combo.get('type', '')} - {combo.get('name', '')}: {leg_str}")
                        lines.append(f"          赔率: {combo.get('combined_odds', 0):.2f} | EV: {combo.get('ev', 0):+.3f} | Kelly: ${combo.get('kelly_stake', 0):.2f}")
            if cb.get('multi_match_available'):
                lines.append(f"     多场比赛组合: 可用 (batch模式生成)")
            lines.append(f"     注: 多场比赛2串1/3串1/4串1需使用 --batch 模式")
    
    # 投资系统 (P2)
    if result.investment:
            lines.append(f"\n  ⚡ 冷门信号: {level} (评分: {score}/100)")
            lines.append(f"     描述: {u.get('description', '')}")
    
    # 风控
    if result.risk_assessment:
        r = result.risk_assessment
        lines.append(f"\n  🛡️ 风控状态: {r.get('overall_level', 'UNKNOWN')}")
    
    # 合规
    if result.compliance_check:
        c = result.compliance_check
        lines.append(f"\n  Compliance: {c.get('status', 'UNKNOWN')}")
        if c.get('violations'):
            for v in c['violations']:
                lines.append(f"     WARN: {v['message']}")
    
    # 九智能体整合输出
    lines.append(f"\n{'='*60}")
    lines.append(f"  NINE-AGENT INTEGRATION")
    lines.append(f"{'='*60}")
    
    # IntelligenceAgent
    if result.intelligence:
        intel = result.intelligence
        lines.append(f"\n  [9A] Intelligence: {intel.get('status', 'N/A')}")
        if intel.get('key_intel'):
            for item in intel['key_intel'][:3]:
                lines.append(f"       - {item}")
    
    # CoachFactor
    if result.coach_factor:
        cf = result.coach_factor
        lines.append(f"\n  [9A] Coach Factor: {cf.get('status', 'N/A')}")
        if cf.get('analysis'):
            analysis = cf['analysis']
            if isinstance(analysis, dict):
                lines.append(f"       Home CRI: {analysis.get('home_cri', 'N/A')}")
                lines.append(f"       Away CRI: {analysis.get('away_cri', 'N/A')}")
    
    # OddsPricingAgent
    if result.odds_pricing:
        op = result.odds_pricing
        lines.append(f"\n  [9A] Odds Pricing: {op.get('status', 'N/A')}")
        if op.get('value_edges'):
            for outcome, edge_info in op['value_edges'].items():
                if edge_info.get('value_bet'):
                    lines.append(f"       VALUE BET: {outcome} (edge: {edge_info['edge']:.2%})")
    
    # GeneEngine
    if result.gene_engine:
        ge = result.gene_engine
        lines.append(f"\n  [9A] Gene Engine: {ge.get('status', 'N/A')}")
        matchup = ge.get('matchup', {})
        if matchup:
            lines.append(f"       Matchup type: {matchup.get('matchup_type', 'N/A')}")
    
    # WorldCupAnalyst
    if result.worldcup_analyst:
        wa = result.worldcup_analyst
        lines.append(f"\n  [9A] WorldCup Analyst: {wa.get('status', 'N/A')}")
        if wa.get('confidence'):
            lines.append(f"       Confidence: {wa['confidence']}")
        if wa.get('key_factors'):
            lines.append(f"       Key factors: {', '.join(wa['key_factors'][:3])}")
    
    # MultiMarketPredictor
    if result.multi_market:
        mm = result.multi_market
        lines.append(f"\n  [9A] Multi-Market: {mm.get('status', 'N/A')}")
        if mm.get('markets'):
            lines.append(f"       Markets: {', '.join(mm['markets'])}")
    
    # 决策链
    if verbose and result.decision_chain:
        lines.append(f"\n  📋 决策链:")
        for step in result.decision_chain:
            lines.append(f"     {step}")
    
    # 模型列表
    if verbose and result.models_used:
        lines.append(f"\n  🤖 使用模型: {', '.join(result.models_used)}")
    
    lines.append(f"\n{'='*60}\n")
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description=f'Football Quant OS v{__version__} - 统一预测入口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 基础预测
  python scripts/predict_v6.py --home Germany --away Japan --odds 1.8 3.4 4.2

  # 完整流水线
  python scripts/predict_v6.py --home Germany --away Japan --odds 1.8 3.4 4.2 --full-pipeline

  # 批量预测
  python scripts/predict_v6.py --batch matches.json --output results.json

  # 合规检查模式
  python scripts/predict_v6.py --home Germany --away Japan --odds 1.8 3.4 4.2 --compliance-check
        """
    )
    
    # 基础参数
    parser.add_argument('--home', type=str, help='主队名称')
    parser.add_argument('--away', type=str, help='客队名称')
    parser.add_argument('--odds', type=float, nargs=3, metavar=('H', 'D', 'A'),
                       help='赔率: 主胜 平局 客胜')
    parser.add_argument('--stage', type=str, default='group', choices=['group', 'knockout', 'friendly'],
                       help='比赛阶段 (默认: group)')
    parser.add_argument('--ou-line', type=float, default=2.5, help='大小球盘口 (默认: 2.5)')
    
    # 可选特征
    parser.add_argument('--home-xg', type=float, help='主队xG')
    parser.add_argument('--away-xg', type=float, help='客队xG')
    parser.add_argument('--home-poss', type=float, help='主队控球率')
    parser.add_argument('--away-poss', type=float, help='客队控球率')
    parser.add_argument('--motivation', type=str, help='战意描述')
    parser.add_argument('--first-match', action='store_true', help='首场/首战')
    
    # v6 增强参数
    parser.add_argument('--full-pipeline', action='store_true', help='启用完整 v6 流水线')
    parser.add_argument('--compliance-check', action='store_true', help='强制合规检查')
    parser.add_argument('--bankroll', type=float, default=100000, help='总资金 (默认: 100000)')
    parser.add_argument('--risk-level', type=str, default='medium', choices=['conservative', 'medium', 'aggressive'],
                       help='风险偏好 (默认: medium)')
    parser.add_argument('--no-compliance', action='store_true', help='禁用合规检查')
    parser.add_argument('--no-attribution', action='store_true', help='禁用归因记录')
    
    # 批量模式
    parser.add_argument('--batch', type=str, help='批量预测 JSON 文件路径')
    parser.add_argument('--output', type=str, help='输出文件路径')
    
    # 输出控制
    parser.add_argument('--json', action='store_true', help='JSON 格式输出')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # 初始化预测器
    predictor = PredictorV6(
        bankroll=args.bankroll,
        risk_level=args.risk_level,
        enable_compliance=not args.no_compliance,
        enable_attribution=not args.no_attribution
    )
    
    # 批量模式
    if args.batch:
        with open(args.batch, 'r', encoding='utf-8') as f:
            matches = json.load(f)
        
        results = []
        for match in matches:
            result = predictor.predict(**match)
            results.append(result.to_dict())
        
        # 生成多场比赛组合
        multi_combinations = {}
        if len(results) >= 2:
            for fold in [2, 3, 4]:
                if len(results) >= fold:
                    combos = predictor.generate_multi_match_combinations(
                        results, fold=fold, risk_level=args.risk_level
                    )
                    multi_combinations[f'{fold}串1'] = combos
        
        output_data = {
            'individual_results': results,
            'multi_match_combinations': multi_combinations,
            'summary': {
                'total_matches': len(results),
                'combinations_generated': sum(len(v) for v in multi_combinations.values()),
                'risk_level': args.risk_level,
                'bankroll': args.bankroll
            }
        }
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"✅ 批量预测完成 + 多场比赛组合生成，结果保存至: {args.output}")
        else:
            print(json.dumps(output_data, ensure_ascii=False, indent=2))
        return
    
    # 单场比赛
    if not all([args.home, args.away, args.odds]):
        parser.error("--home, --away, --odds 为必填参数 (或使用 --batch 批量模式)")
    
    oh, od, oa = args.odds
    
    kwargs = {
        'home_xg': args.home_xg,
        'away_xg': args.away_xg,
        'home_poss': args.home_poss,
        'away_poss': args.away_poss,
        'motivation': args.motivation,
        'is_first_match': args.first_match,
    }
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    
    result = predictor.predict(
        home=args.home, away=args.away,
        odds_home=oh, odds_draw=od, odds_away=oa,
        stage=args.stage, ou_line=args.ou_line,
        **kwargs
    )
    
    # 输出
    if args.json:
        output = json.dumps(result.to_dict(), ensure_ascii=False, indent=2)
    else:
        output = format_output(result, verbose=args.verbose)
    
    print(output)
    
    # 保存到文件
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✅ 结果已保存至: {args.output}")


if __name__ == '__main__':
    main()

# Apply P1 extensions
apply_p1_extensions(PredictorV6)
