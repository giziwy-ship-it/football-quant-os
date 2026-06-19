#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
高盛风格足球量化策略架构师 (Strategist Goldman)
Football Quant OS —— 机构级策略顶层设计
================================================================================

角色定位：
    你是高盛算法交易台的执行董事，负责设计系统化足球投注策略。
    你不是在做"预测比赛结果"，你是在构建一个可重复、可验证、
    可迭代的量化投资系统。

核心职责：
    1. 策略论题设计 —— 这个策略在赚什么钱？alpha 来源是什么？
    2. 信号体系架构 —— 从原始数据到交易信号的完整链路
    3. 进出场规则 —— 什么时候开仓？什么时候平仓？什么时候放弃？
    4. 头寸规模模型 —— 凯利、风险平价、martingale 的取舍
    5. 回测验证框架 —— 怎么证明这个策略不是过拟合？
    6. 边际衰减监控 —— 策略什么时候失效？怎么检测？

输出格式：
    机构级策略备忘录 (Goldman Quant Strategy Memo)
    含：策略论题、数学公式、伪代码逻辑、风险参数表、执行检查清单
================================================================================
"""

import sys
sys.stdout.reconfigure(encoding='utf-8')

import math
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════════
# 数据结构定义
# ═══════════════════════════════════════════════════════════════════════════════

class StrategyTheme(Enum):
    """策略论题类型 —— 你到底在赚什么钱？"""
    ODDS_MISPRICING = "赔率错估"          # 市场赔率 vs 真实概率的偏差
    MONEY_FLOW_CONTRARIAN = "资金流向逆向" # 大众资金流向的反向操作
    MARKET_EFFICIENCY_GAP = "市场效率缺口" # 特定市场/时段的信息不对称
    FACTOR_PREMIUM = "因子溢价"           # 球队因子/教练因子的风险溢价
    ARBITRAGE = "跨市场套利"              # 不同平台间的赔率差异
    MOMENTUM = "动量延续"                # 趋势跟踪
    MEAN_REVERSION = "均值回归"           # 赔率/水位的均值回归
    EVENT_DRIVEN = "事件驱动"             # 伤病、红黄牌、换人等突发事件


class MarketRegime(Enum):
    """市场状态分类 —— 当前市场处于什么阶段？"""
    INFORMATIONAL = "信息透明"    # 强队在正常赔率下，市场效率高
    EFFICIENT = "有效市场"       # 赔率充分反映所有信息
    DISTORTED = "市场扭曲"       # 大众情绪/大额投注导致赔率偏离
    BALANCED = "均衡市场"        # 双方实力接近，难以判断
    NO_TRADE = "不交易"          # 信息不足或赔率无价值


@dataclass
class SignalArchitecture:
    """信号体系架构 —— 从数据到信号的完整链路"""
    raw_data_sources: List[str] = field(default_factory=list)
    feature_engineering: List[str] = field(default_factory=list)
    signal_generators: List[str] = field(default_factory=list)
    signal_combination: str = "equal_weight"
    decay_monitoring: bool = True
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EntryRule:
    """进场规则"""
    name: str
    condition: str           # 文字描述
    threshold: float         # 触发阈值
    required_signals: List[str] = field(default_factory=list)
    forbidden_signals: List[str] = field(default_factory=list)
    max_odds: float = 10.0   # 最高可接受赔率
    min_edge: float = 0.05   # 最低期望优势
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExitRule:
    """出场规则"""
    name: str
    condition: str
    threshold: float
    action: str              # "close", "partial", "hedge"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PositionSizing:
    """头寸规模模型"""
    model: str               # "kelly", "fixed_fraction", "risk_parity", "martingale"
    base_fraction: float = 0.02    # 基础仓位比例
    kelly_fraction: float = 0.25   # 凯利分数（保守折扣）
    max_single_bet: float = 0.10   # 单场最大仓位
    max_daily_exposure: float = 0.30  # 日最大敞口
    drawdown_reduction: bool = True   # 回撤时降仓
    
    def calculate_kelly(self, edge: float, odds: float) -> float:
        """计算凯利比例"""
        if edge <= 0:
            return 0.0
        p = edge  # 简化为胜率估计
        b = odds - 1  # 净赔率
        kelly = (p * b - (1 - p)) / b
        return max(0.0, min(kelly * self.kelly_fraction, self.max_single_bet))
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class RiskParameters:
    """风险参数表"""
    max_drawdown: float = 0.20        # 最大可接受回撤
    daily_loss_limit: float = 0.05    # 日亏损限额
    consecutive_loss_limit: int = 5   # 连续亏损次数上限
    correlation_threshold: float = 0.7  # 相关性阈值（避免集中）
    var_confidence: float = 0.95      # VaR 置信度
    stress_scenarios: List[str] = field(default_factory=lambda: [
        "世界杯小组赛爆冷",
        "决赛圈球队战意变化",
        "重大伤病临场公布",
        "裁判争议/VAR改判",
        "平台赔率延迟更新"
    ])
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class BacktestProtocol:
    """回测验证协议 —— 文艺复兴式严格标准"""
    walk_forward: bool = True         # 必须使用walk-forward
    out_of_sample_pct: float = 0.30   # 样本外比例
    min_trades: int = 100             # 最小交易次数
    significance_level: float = 0.05  # 统计显著性
    monte_carlo_runs: int = 1000      # 蒙特卡洛模拟次数
    transaction_cost: float = 0.02    # 交易成本（抽水）
    survivor_bias_check: bool = True  # 幸存者偏差检查
    lookahead_bias_check: bool = True # 前向偏差检查
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class DecayMonitor:
    """边际衰减监控 —— 策略什么时候失效？"""
    metrics: List[str] = field(default_factory=lambda: [
        "sharpe_ratio_30d",
        "win_rate_50trade",
        "avg_edge_per_trade",
        "max_consecutive_losses"
    ])
    alert_threshold: float = 0.5      # 衰减预警阈值（vs 历史均值）
    review_frequency: str = "weekly"  # review 频率
    retirement_criteria: str = "连续30天Sharpe < 0.5 且累计回撤 > 15%"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class StrategyMemo:
    """完整策略备忘录"""
    # 元信息
    memo_id: str = ""
    created_at: str = ""
    version: str = "1.0"
    strategist: str = "Goldman_Football_Quant"
    
    # 核心策略
    theme: StrategyTheme = field(default=StrategyTheme.ODDS_MISPRICING)
    regime_filter: List[MarketRegime] = field(default_factory=list)
    thesis: str = ""
    alpha_source: str = ""
    
    # 系统组件
    signal_architecture: SignalArchitecture = field(default_factory=SignalArchitecture)
    entry_rules: List[EntryRule] = field(default_factory=list)
    exit_rules: List[ExitRule] = field(default_factory=list)
    position_sizing: PositionSizing = field(default_factory=lambda: PositionSizing(model="kelly"))
    risk_params: RiskParameters = field(default_factory=RiskParameters)
    
    # 验证
    backtest_protocol: BacktestProtocol = field(default_factory=BacktestProtocol)
    decay_monitor: DecayMonitor = field(default_factory=DecayMonitor)
    
    # 执行检查清单
    pre_trade_checklist: List[str] = field(default_factory=list)
    post_trade_checklist: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """序列化为字典"""
        return {
            "memo_id": self.memo_id,
            "created_at": self.created_at,
            "version": self.version,
            "strategist": self.strategist,
            "theme": self.theme.value,
            "regime_filter": [r.value for r in self.regime_filter],
            "thesis": self.thesis,
            "alpha_source": self.alpha_source,
            "signal_architecture": self.signal_architecture.to_dict(),
            "entry_rules": [r.to_dict() for r in self.entry_rules],
            "exit_rules": [r.to_dict() for r in self.exit_rules],
            "position_sizing": self.position_sizing.to_dict(),
            "risk_params": self.risk_params.to_dict(),
            "backtest_protocol": self.backtest_protocol.to_dict(),
            "decay_monitor": self.decay_monitor.to_dict(),
            "pre_trade_checklist": self.pre_trade_checklist,
            "post_trade_checklist": self.post_trade_checklist
        }
    
    def to_json(self, indent: int = 2) -> str:
        """序列化为 JSON"""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)
    
    def validate(self) -> Tuple[bool, List[str]]:
        """验证策略完整性"""
        errors = []
        
        if not self.thesis:
            errors.append("策略论题不能为空")
        if not self.alpha_source:
            errors.append("Alpha来源必须明确")
        if not self.entry_rules:
            errors.append("至少需要一条进场规则")
        if self.position_sizing.max_single_bet > 0.20:
            errors.append("单场仓位超过20%，风险过高")
        if not self.backtest_protocol.walk_forward:
            errors.append("必须使用walk-forward回测")
        
        return len(errors) == 0, errors


# ═══════════════════════════════════════════════════════════════════════════════
# 策略架构师 Agent
# ═══════════════════════════════════════════════════════════════════════════════

class StrategistGoldman:
    """
    高盛风格足球量化策略架构师
    
    核心方法：
        1. design_strategy() —— 从零设计完整策略
        2. adapt_to_regime() —— 根据市场状态调整策略
        3. generate_memo() —— 输出机构级策略备忘录
        4. validate_pipeline() —— 验证下游Agent是否满足策略要求
    """
    
    name = "Strategist_Goldman"
    version = "1.0"
    
    def __init__(self, capital: float = 100000.0, risk_tolerance: str = "medium"):
        self.capital = capital
        self.risk_tolerance = risk_tolerance
        self.memo: Optional[StrategyMemo] = None
        
        # 根据风险偏好调整参数
        self._risk_profile = self._load_risk_profile(risk_tolerance)
    
    def _load_risk_profile(self, risk_tolerance: str) -> Dict[str, float]:
        """加载风险偏好配置"""
        profiles = {
            "conservative": {
                "kelly_fraction": 0.15,
                "max_single_bet": 0.03,
                "max_daily_exposure": 0.10,
                "min_edge": 0.08,
                "max_drawdown": 0.10
            },
            "medium": {
                "kelly_fraction": 0.25,
                "max_single_bet": 0.05,
                "max_daily_exposure": 0.20,
                "min_edge": 0.05,
                "max_drawdown": 0.20
            },
            "aggressive": {
                "kelly_fraction": 0.50,
                "max_single_bet": 0.10,
                "max_daily_exposure": 0.40,
                "min_edge": 0.03,
                "max_drawdown": 0.35
            }
        }
        return profiles.get(risk_tolerance, profiles["medium"])
    
    def design_strategy(
        self,
        theme: StrategyTheme,
        thesis: str,
        alpha_source: str,
        target_leagues: List[str],
        data_sources: List[str],
        regime_preference: Optional[List[MarketRegime]] = None
    ) -> StrategyMemo:
        """
        从零设计完整策略
        
        Args:
            theme: 策略论题类型
            thesis: 一句话策略论题
            alpha_source: alpha 来源说明
            target_leagues: 目标联赛
            data_sources: 数据源列表
            regime_preference: 偏好的市场状态（默认排除 NO_TRADE）
        
        Returns:
            StrategyMemo: 完整策略备忘录
        """
        
        # 1. 市场状态过滤器 —— 默认在大多数状态下交易，排除 NO_TRADE
        if regime_preference is None:
            regime_preference = [
                MarketRegime.INFORMATIONAL,
                MarketRegime.DISTORTED,
                MarketRegime.BALANCED
            ]
        
        # 2. 信号体系架构 —— 根据策略论题选择信号
        signal_arch = self._design_signal_architecture(theme, data_sources)
        
        # 3. 进出场规则 —— 核心交易逻辑
        entry_rules = self._design_entry_rules(theme)
        exit_rules = self._design_exit_rules(theme)
        
        # 4. 头寸规模 —— 根据风险偏好
        position_sizing = PositionSizing(
            model="kelly",
            base_fraction=0.02,
            kelly_fraction=self._risk_profile["kelly_fraction"],
            max_single_bet=self._risk_profile["max_single_bet"],
            max_daily_exposure=self._risk_profile["max_daily_exposure"],
            drawdown_reduction=True
        )
        
        # 5. 风险参数
        risk_params = RiskParameters(
            max_drawdown=self._risk_profile["max_drawdown"],
            daily_loss_limit=self._risk_profile["max_single_bet"] * 2,
            consecutive_loss_limit=5,
            correlation_threshold=0.7,
            var_confidence=0.95
        )
        
        # 6. 回测协议 —— 文艺复兴标准
        backtest = BacktestProtocol(
            walk_forward=True,
            out_of_sample_pct=0.30,
            min_trades=100,
            significance_level=0.05,
            monte_carlo_runs=1000,
            transaction_cost=0.02,
            survivor_bias_check=True,
            lookahead_bias_check=True
        )
        
        # 7. 衰减监控
        decay = DecayMonitor(
            alert_threshold=0.5,
            review_frequency="weekly",
            retirement_criteria="连续30天Sharpe < 0.5 且累计回撤 > 15%"
        )
        
        # 8. 检查清单
        pre_trade = [
            "□ 市场状态是否匹配策略regime_filter？",
            "□ 信号强度是否达到阈值？",
            "□ 赔率是否提供足够edge（>={min_edge}）？",
            "□ 当日累计仓位是否超过日限额？",
            "□ 是否有重大伤病/停赛等未定价信息？",
            "□ 上一场同策略交易结果（避免连黑情绪化）"
        ]
        
        post_trade = [
            "□ 记录实际赔率、水位、投注额",
            "□ 标注策略信号类型和置信度",
            "□ 更新当日累计盈亏",
            "□ 检查是否触发风控阈值",
            "□ 写入交易日志（供回测使用）"
        ]
        
        # 组装备忘录
        memo = StrategyMemo(
            memo_id=f"GFS-{datetime.now().strftime('%Y%m%d')}-{theme.value[:3].upper()}",
            created_at=datetime.now().isoformat(),
            theme=theme,
            regime_filter=regime_preference,
            thesis=thesis,
            alpha_source=alpha_source,
            signal_architecture=signal_arch,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            position_sizing=position_sizing,
            risk_params=risk_params,
            backtest_protocol=backtest,
            decay_monitor=decay,
            pre_trade_checklist=pre_trade,
            post_trade_checklist=post_trade
        )
        
        self.memo = memo
        return memo
    
    def _design_signal_architecture(
        self,
        theme: StrategyTheme,
        data_sources: List[str]
    ) -> SignalArchitecture:
        """根据策略论题设计信号体系"""
        
        # 基础特征工程（所有策略通用）
        base_features = [
            "历史交锋胜率",
            "近期状态（近5场积分）",
            "攻防效率（xG/xGA）",
            "主客场优势因子",
            "伤病/停赛影响指数"
        ]
        
        # 根据策略类型选择特定信号
        if theme == StrategyTheme.ODDS_MISPRICING:
            specific_features = [
                "赔率隐含概率 vs 模型概率偏差",
                "亚欧赔率转换差异",
                "百家欧赔离散度",
                "凯利指数计算"
            ]
            generators = [
                "odds_deviation_signal",
                "market_efficiency_signal",
                "value_bet_detector"
            ]
            
        elif theme == StrategyTheme.MONEY_FLOW_CONTRARIAN:
            specific_features = [
                "必发交易资金流向",
                "庄家盈亏指数",
                "冷热指数（大众倾向）",
                "大额投注异动检测"
            ]
            generators = [
                "contrarian_flow_signal",
                "smart_money_tracker",
                "public_sentiment_reversal"
            ]
            
        elif theme == StrategyTheme.FACTOR_PREMIUM:
            specific_features = [
                "教练因子（战术风格/大赛经验）",
                "球队阵容深度指数",
                "赛制形势因子（出线压力/战意）",
                "杯赛特异性因子"
            ]
            generators = [
                "coach_factor_signal",
                "squad_depth_signal",
                "tournament_context_signal"
            ]
            
        elif theme == StrategyTheme.ARBITRAGE:
            specific_features = [
                "多平台赔率对比",
                "汇率调整后的真实赔率",
                "平台延迟检测",
                "套利窗口持续时间估计"
            ]
            generators = [
                "cross_platform_arb_signal",
                "odds_divergence_tracker"
            ]
            
        else:
            specific_features = ["综合多因子评分"]
            generators = ["ensemble_signal"]
        
        return SignalArchitecture(
            raw_data_sources=data_sources,
            feature_engineering=base_features + specific_features,
            signal_generators=generators,
            signal_combination="weighted_average",
            decay_monitoring=True
        )
    
    def _design_entry_rules(self, theme: StrategyTheme) -> List[EntryRule]:
        """设计进场规则"""
        
        rules = []
        
        # 通用规则：必须有正期望
        rules.append(EntryRule(
            name="正期望过滤",
            condition="模型概率 × 赔率 > 1.0 + 抽水成本",
            threshold=self._risk_profile["min_edge"],
            required_signals=["positive_expectation"]
        ))
        
        # 策略特定规则
        if theme == StrategyTheme.ODDS_MISPRICING:
            rules.append(EntryRule(
                name="赔率错估确认",
                condition="市场赔率隐含概率与模型概率偏差 > threshold",
                threshold=0.05,
                required_signals=["odds_deviation"],
                min_edge=0.05
            ))
            
        elif theme == StrategyTheme.MONEY_FLOW_CONTRARIAN:
            rules.append(EntryRule(
                name="资金流向逆向确认",
                condition="大众资金流向与模型方向相反，且资金流向极端（>70%）",
                threshold=0.70,
                required_signals=["contrarian_flow"],
                forbidden_signals=["trap_signal"]  # 避免被诱盘
            ))
            
        elif theme == StrategyTheme.FACTOR_PREMIUM:
            rules.append(EntryRule(
                name="因子溢价确认",
                condition="目标因子暴露显著且历史回测验证有效",
                threshold=1.5,  # 因子z-score
                required_signals=["factor_exposure"]
            ))
        
        # 通用规则：赔率范围
        rules.append(EntryRule(
            name="赔率范围过滤",
            condition="赔率必须在可接受范围内（避免极低概率事件）",
            threshold=10.0,
            max_odds=10.0,
            min_edge=0.03
        ))
        
        return rules
    
    def _design_exit_rules(self, theme: StrategyTheme) -> List[ExitRule]:
        """设计出场规则"""
        
        rules = []
        
        # 通用止损
        rules.append(ExitRule(
            name="日亏损止损",
            condition="当日累计亏损达到日限额",
            threshold=self._risk_profile["max_single_bet"] * 2,
            action="close"
        ))
        
        # 连续亏损降仓
        rules.append(ExitRule(
            name="连黑降仓",
            condition="连续亏损次数达到阈值",
            threshold=5,
            action="partial"
        ))
        
        # 回撤控制
        rules.append(ExitRule(
            name="最大回撤控制",
            condition="累计回撤达到max_drawdown",
            threshold=self._risk_profile["max_drawdown"],
            action="close"
        ))
        
        # 特定策略出场
        if theme == StrategyTheme.ODDS_MISPRICING:
            rules.append(ExitRule(
                name="赔率回归出场",
                condition="赔率向模型概率方向回归，edge缩小到阈值以下",
                threshold=0.02,
                action="close"
            ))
        
        return rules
    
    def adapt_to_regime(self, current_regime: MarketRegime) -> Dict[str, Any]:
        """
        根据当前市场状态调整策略参数
        
        Returns:
            调整后的策略参数
        """
        if self.memo is None:
            raise ValueError("必须先调用 design_strategy() 生成策略备忘录")
        
        adjustments = {}
        
        if current_regime == MarketRegime.NO_TRADE:
            adjustments["action"] = "HALT"
            adjustments["reason"] = "市场状态为 NO_TRADE，停止交易"
            adjustments["position_multiplier"] = 0.0
            
        elif current_regime == MarketRegime.EFFICIENT:
            adjustments["action"] = "REDUCE"
            adjustments["reason"] = "市场有效，edge减小，降低仓位"
            adjustments["position_multiplier"] = 0.5
            adjustments["min_edge_adjustment"] = 1.5  # 提高edge要求
            
        elif current_regime == MarketRegime.DISTORTED:
            adjustments["action"] = "AGGRESSIVE"
            adjustments["reason"] = "市场扭曲，可能存在超额机会"
            adjustments["position_multiplier"] = 1.2
            
        elif current_regime == MarketRegime.INFORMATIONAL:
            adjustments["action"] = "NORMAL"
            adjustments["reason"] = "信息透明，正常执行"
            adjustments["position_multiplier"] = 1.0
            
        else:
            adjustments["action"] = "CAUTION"
            adjustments["reason"] = "均衡市场，谨慎交易"
            adjustments["position_multiplier"] = 0.8
        
        return adjustments
    
    def validate_pipeline(
        self,
        downstream_agents: List[str],
        required_capabilities: List[str]
    ) -> Tuple[bool, List[str]]:
        """
        验证下游Agent是否满足策略要求
        
        Args:
            downstream_agents: 下游Agent列表
            required_capabilities: 策略要求的Agent能力
        
        Returns:
            (是否通过, 缺失的能力列表)
        """
        agent_capability_map = {
            "DataScout": ["odds_fetching", "data_cleaning", "schedule_api"],
            "Analyst": ["probability_model", "signal_detection", "factor_analysis"],
            "Committee": ["weighted_decision", "confidence_scoring"],
            "RiskControl": ["kelly_calculation", "drawdown_control", "position_limit"],
            "Arbitrage": ["cross_platform_comparison", "arb_detection"],
            "CoachFactor": ["coach_evaluation", "tactical_analysis"],
            "GeneEngine": ["evolution", "optimization"]
        }
        
        available = set()
        for agent in downstream_agents:
            caps = agent_capability_map.get(agent, [])
            available.update(caps)
        
        missing = [cap for cap in required_capabilities if cap not in available]
        
        return len(missing) == 0, missing
    
    def generate_execution_summary(self) -> str:
        """生成可读的执行摘要"""
        if self.memo is None:
            return "错误：尚未生成策略备忘录"
        
        m = self.memo
        lines = []
        lines.append("=" * 70)
        lines.append(f"  高盛足球量化策略备忘录  #{m.memo_id}")
        lines.append("=" * 70)
        lines.append("")
        lines.append(f"  策略论题: {m.thesis}")
        lines.append(f"  Alpha来源: {m.alpha_source}")
        lines.append(f"  适用市场: {[r.value for r in m.regime_filter]}")
        lines.append("")
        lines.append("  信号体系:")
        for sig in m.signal_architecture.signal_generators:
            lines.append(f"    - {sig}")
        lines.append("")
        lines.append("  进场规则:")
        for rule in m.entry_rules:
            lines.append(f"    [{rule.name}] {rule.condition} (阈值: {rule.threshold})")
        lines.append("")
        lines.append("  风控参数:")
        lines.append(f"    - 最大回撤: {m.risk_params.max_drawdown:.0%}")
        lines.append(f"    - 单场最大: {m.position_sizing.max_single_bet:.0%}")
        lines.append(f"    - 凯利分数: {m.position_sizing.kelly_fraction:.0%}")
        lines.append(f"    - 日亏损限额: {m.risk_params.daily_loss_limit:.0%}")
        lines.append("")
        lines.append("  回测标准:")
        lines.append(f"    - Walk-forward: {'[OK]' if m.backtest_protocol.walk_forward else '[NO]'})")
        lines.append(f"    - Monte Carlo: {m.backtest_protocol.monte_carlo_runs}runs")
        lines.append(f"    - Out-of-sample: {m.backtest_protocol.out_of_sample_pct:.0%}")
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# 快捷入口
# ═══════════════════════════════════════════════════════════════════════════════

def create_default_strategy(
    capital: float = 100000.0,
    risk_tolerance: str = "medium"
) -> StrategyMemo:
    """
    创建默认策略 —— 赔率错估 + 资金流向逆向的混合策略
    """
    strategist = StrategistGoldman(capital=capital, risk_tolerance=risk_tolerance)
    
    memo = strategist.design_strategy(
        theme=StrategyTheme.ODDS_MISPRICING,
        thesis="通过量化模型识别市场赔率错估，结合资金流向逆向信号，在信息不对称的比赛中获取正期望收益",
        alpha_source="1. 赔率隐含概率与基本面模型概率的系统性偏差；2. 大众资金流向的过度反应导致的赔率扭曲",
        target_leagues=["英超", "西甲", "意甲", "德甲", "法甲", "欧冠", "世界杯"],
        data_sources=["500网赔率", "OddsPortal", "Football-Data.co.uk", "ESPN赛程", "FIFA阵容"]
    )
    
    return memo


# ═══════════════════════════════════════════════════════════════════════════════
# 测试入口
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # 示例：创建默认策略
    memo = create_default_strategy(capital=100000.0, risk_tolerance="medium")
    
    # 验证
    valid, errors = memo.validate()
    print(f"策略验证: {'通过' if valid else '失败'}")
    if errors:
        for e in errors:
            print(f"  - {e}")
    
    # 输出摘要
    strategist = StrategistGoldman()
    strategist.memo = memo
    print("\n" + strategist.generate_execution_summary())
    
    # 输出完整JSON
    print("\n" + "=" * 70)
    print("完整策略备忘录 (JSON):")
    print("=" * 70)
    print(memo.to_json())
