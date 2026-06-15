#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - Investment System Integration Layer
将 4 个核心投资模块集成到预测流水线

模块:
1. DataScout v3 - 资金流向追踪 (欧赔/交易所/盈亏指数)
2. Analyst v2 - 市场信号分析 (偏离度/异常)
3. Committee v2 - 委员会加权决策 (多信号投票)
4. RiskControl v2 - 动态Kelly调整 + 风险熔断

集成流程:
predict → DataScout(资金信号) → Analyst(市场分析) → Committee(委员会投票) → RiskControl(风控调整) → 最终决策
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json


@dataclass
class InvestmentDecision:
    """投资决策结果"""
    match: str
    timestamp: str
    
    # 预测层
    prediction: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    
    # 资金信号层
    money_flow: Dict[str, Any] = field(default_factory=dict)
    fund_signals: List[Dict] = field(default_factory=list)
    
    # 市场分析层
    market_signals: List[Dict] = field(default_factory=list)
    odds_deviation: Dict[str, Any] = field(default_factory=dict)
    
    # 委员会决策层
    committee_vote: Dict[str, Any] = field(default_factory=dict)
    recommended_outcome: str = ""
    
    # 风控层
    risk_level: str = "low"
    kelly_adjustment: Dict[str, Any] = field(default_factory=dict)
    adjusted_stake: float = 0.0
    max_bet_pct: float = 0.0
    
    # 执行层
    final_bet: Optional[Dict] = None
    warnings: List[str] = field(default_factory=list)


class InvestmentSystemIntegration:
    """
    投资系统集成层
    
    将4个核心模块集成到统一决策流程
    """
    
    def __init__(self):
        self.datascout = None
        self.analyst = None
        self.committee = None
        self.risk_control = None
        self._init_modules()
    
    def _init_modules(self):
        """初始化4个核心模块"""
        # 1. DataScout - 资金流向
        try:
            from agents.datascout_v2 import DataScout, MoneyFlowData
            self.datascout = DataScout()
            print("[InvestmentSystem] DataScout v3 初始化成功")
        except Exception as e:
            print(f"[InvestmentSystem] DataScout v3 初始化失败: {e}")
            self.datascout = None
        
        # 2. Analyst - 市场信号
        try:
            from agents.analyst_v2 import Analyst, MarketSignal
            self.analyst = Analyst()
            print("[InvestmentSystem] Analyst v2 初始化成功")
        except Exception as e:
            print(f"[InvestmentSystem] Analyst v2 初始化失败: {e}")
            self.analyst = None
        
        # 3. Committee - 委员会决策
        try:
            from agents.committee_v2 import Committee, FundSignal
            self.committee = Committee()
            print("[InvestmentSystem] Committee v2 初始化成功")
        except Exception as e:
            print(f"[InvestmentSystem] Committee v2 初始化失败: {e}")
            self.committee = None
        
        # 4. RiskControl - 风控调整
        try:
            from agents.risk_control_v2 import RiskControl, KellyAdjustment, MoneyRiskLevel
            self.risk_control = RiskControl()
            print("[InvestmentSystem] RiskControl v2 初始化成功")
        except Exception as e:
            print(f"[InvestmentSystem] RiskControl v2 初始化失败: {e}")
            self.risk_control = None
    
    def run(self, 
            home: str, away: str,
            prediction: Dict[str, Any],
            odds: Dict[str, float],
            bankroll: float = 100000.0,
            base_kelly: float = 0.25,
            **kwargs) -> InvestmentDecision:
        """
        运行完整投资系统决策流程
        
        Args:
            home, away: 球队
            prediction: predict.py 的预测结果
            odds: 市场赔率 {home, draw, away}
            bankroll: 资金池
            base_kelly: 基础Kelly比例
            
        Returns:
            InvestmentDecision 完整决策
        """
        print(f"\n{'='*60}")
        print("Investment System - Full Decision Pipeline")
        print(f"{'='*60}")
        
        decision = InvestmentDecision(
            match=f"{home} vs {away}",
            timestamp=datetime.now().isoformat(),
            prediction=prediction
        )
        
        # Step 1: DataScout - 资金流向追踪
        print(f"\n[Step 1/4] DataScout - Money Flow Analysis")
        print(f"{'='*60}")
        
        money_flow = self._run_datascout(home, away, odds)
        decision.money_flow = money_flow
        
        # Step 2: Analyst - 市场信号分析
        print(f"\n[Step 2/4] Analyst - Market Signal Analysis")
        print(f"{'='*60}")
        
        market_analysis = self._run_analyst(home, away, prediction, odds, money_flow)
        decision.market_signals = market_analysis.get('signals', [])
        decision.odds_deviation = market_analysis.get('odds_analysis', {})
        
        # Step 3: Committee - 委员会投票
        print(f"\n[Step 3/4] Committee - Weighted Decision")
        print(f"{'='*60}")
        
        committee_result = self._run_committee(
            prediction, market_analysis, money_flow, odds
        )
        decision.committee_vote = committee_result
        decision.recommended_outcome = committee_result.get('recommended_outcome', '')
        decision.confidence = committee_result.get('confidence', 0)
        
        # Step 4: RiskControl - 风控调整
        print(f"\n[Step 4/4] RiskControl - Kelly Adjustment & Risk Fusing")
        print(f"{'='*60}")
        
        risk_result = self._run_riskcontrol(
            committee_result, money_flow, bankroll, base_kelly
        )
        decision.risk_level = risk_result.get('risk_level', 'low')
        decision.kelly_adjustment = risk_result.get('kelly_adjustment', {})
        decision.adjusted_stake = risk_result.get('adjusted_stake', 0)
        decision.max_bet_pct = risk_result.get('max_bet_pct', 0.1)
        decision.warnings = risk_result.get('warnings', [])
        
        # 构建最终投注决策
        decision.final_bet = self._build_final_bet(decision, bankroll)
        
        return decision
    
    def _run_datascout(self, home: str, away: str, odds: Dict[str, float]) -> Dict[str, Any]:
        """
        运行 DataScout - 资金流向分析
        
        即使没有真实数据源，也能基于赔率计算模拟信号
        """
        if self.datascout is None:
            # 模拟资金信号基于赔率
            return self._simulate_money_flow(home, away, odds)
        
        try:
            # 尝试获取真实资金数据
            match_data = {
                'home_team': home,
                'away_team': away,
                'odds_home': odds.get('home', 0),
                'odds_draw': odds.get('draw', 0),
                'odds_away': odds.get('away', 0)
            }
            
            # DataScout 需要异步运行，简化处理
            result = self._simulate_money_flow(home, away, odds)
            result['source'] = 'DataScout_v3_simulated'
            return result
            
        except Exception as e:
            print(f"  DataScout error: {e}")
            return self._simulate_money_flow(home, away, odds)
    
    def _simulate_money_flow(self, home: str, away: str, odds: Dict[str, float]) -> Dict[str, Any]:
        """
        基于赔率模拟资金流向
        
        逻辑: 赔率越低 = 投注越多 = 资金越热
        """
        home_odds = odds.get('home', 2.0)
        draw_odds = odds.get('draw', 3.5)
        away_odds = odds.get('away', 4.0)
        
        # 计算隐含概率
        home_prob = 1 / home_odds if home_odds > 0 else 0
        draw_prob = 1 / draw_odds if draw_odds > 0 else 0
        away_prob = 1 / away_odds if away_odds > 0 else 0
        total = home_prob + draw_prob + away_prob
        
        if total > 0:
            home_prob /= total
            draw_prob /= total
            away_prob /= total
        
        # 模拟资金分布 (热门方获得更多资金)
        total_volume = 1000000  # 假设总交易量100万
        home_volume = int(total_volume * home_prob * 1.2)  # 热门方多20%
        draw_volume = int(total_volume * draw_prob * 0.9)
        away_volume = int(total_volume * away_prob * 0.9)
        
        # 盈亏指数 (庄家视角)
        home_pnl = int(home_volume * (home_odds - 1) * 0.05)  # 5% margin
        draw_pnl = int(draw_volume * (draw_odds - 1) * 0.05)
        away_pnl = int(away_volume * (away_odds - 1) * 0.05)
        
        # 资金热度信号
        home_heat = home_volume / (total_volume / 3)
        draw_heat = draw_volume / (total_volume / 3)
        away_heat = away_volume / (total_volume / 3)
        
        # 识别陷阱信号 (赔率与资金背离)
        trap_signals = []
        if home_heat > 1.3 and home_odds > 2.0:
            trap_signals.append(f"{home}: 高资金但高赔率，可能陷阱")
        if away_heat > 1.3 and away_odds > 3.0:
            trap_signals.append(f"{away}: 高资金但高赔率，可能陷阱")
        
        return {
            'source': 'simulated_from_odds',
            'home_team': home,
            'away_team': away,
            'odds': {'home': home_odds, 'draw': draw_odds, 'away': away_odds},
            'implied_prob': {'home': round(home_prob, 3), 'draw': round(draw_prob, 3), 'away': round(away_prob, 3)},
            'volume': {
                'home': home_volume,
                'draw': draw_volume,
                'away': away_volume,
                'total': home_volume + draw_volume + away_volume
            },
            'heat_index': {
                'home': round(home_heat, 2),
                'draw': round(draw_heat, 2),
                'away': round(away_heat, 2)
            },
            'profit_index': {
                'home': home_pnl,
                'draw': draw_pnl,
                'away': away_pnl
            },
            'trap_signals': trap_signals,
            'timestamp': datetime.now().isoformat()
        }
    
    def _run_analyst(self, home: str, away: str, 
                     prediction: Dict[str, Any], 
                     odds: Dict[str, float],
                     money_flow: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行 Analyst - 市场信号分析
        
        分析: 赔率偏离度、市场共识、资金异常
        """
        if self.analyst is None:
            return self._simulate_analyst(home, away, prediction, odds, money_flow)
        
        try:
            # 构建 Analyst 输入
            match_data = {
                'home_win': prediction.get('markets', {}).get('1x2', {}).get('model', {}).get('home', 33),
                'draw': prediction.get('markets', {}).get('1x2', {}).get('model', {}).get('draw', 33),
                'away_win': prediction.get('markets', {}).get('1x2', {}).get('model', {}).get('away', 33),
                'market_odds': {
                    'home_win': odds.get('home', 2.0),
                    'draw': odds.get('draw', 3.5),
                    'away_win': odds.get('away', 4.0)
                },
                'money_flow': money_flow,
                'expected_goals': prediction.get('markets', {}).get('over_under', {}).get('lambda', 2.5)
            }
            
            result = self.analyst.run(match_data)
            result['source'] = 'Analyst_v2'
            return result
            
        except Exception as e:
            print(f"  Analyst error: {e}")
            return self._simulate_analyst(home, away, prediction, odds, money_flow)
    
    def _simulate_analyst(self, home: str, away: str,
                          prediction: Dict, odds: Dict, money_flow: Dict) -> Dict:
        """模拟 Analyst 信号分析"""
        signals = []
        odds_analysis = {}
        
        # 1. 赔率偏离度分析
        model_prob = prediction.get('markets', {}).get('1x2', {}).get('model', {})
        if model_prob:
            home_model = model_prob.get('home', 33) / 100
            draw_model = model_prob.get('draw', 33) / 100
            away_model = model_prob.get('away', 33) / 100
            
            home_odds = odds.get('home', 2.0)
            draw_odds = odds.get('draw', 3.5)
            away_odds = odds.get('away', 4.0)
            
            home_implied = 1 / home_odds if home_odds > 0 else 0
            draw_implied = 1 / draw_odds if draw_odds > 0 else 0
            away_implied = 1 / away_odds if away_odds > 0 else 0
            total = home_implied + draw_implied + away_implied
            
            if total > 0:
                home_implied /= total
                draw_implied /= total
                away_implied /= total
            
            # 偏离度 = 模型概率 - 市场隐含概率
            home_dev = home_model - home_implied
            draw_dev = draw_model - draw_implied
            away_dev = away_model - away_implied
            
            odds_analysis = {
                'home_deviation': round(home_dev, 3),
                'draw_deviation': round(draw_dev, 3),
                'away_deviation': round(away_dev, 3),
                'market_efficiency': 'inefficient' if max(abs(home_dev), abs(draw_dev), abs(away_dev)) > 0.1 else 'efficient'
            }
            
            # 生成信号
            if home_dev > 0.1:
                signals.append({
                    'type': 'value_home',
                    'confidence': min(home_dev * 5, 1.0),
                    'description': f'{home} 模型概率高于市场 {home_dev:.1%}',
                    'source': 'odds_deviation'
                })
            if away_dev > 0.1:
                signals.append({
                    'type': 'value_away',
                    'confidence': min(away_dev * 5, 1.0),
                    'description': f'{away} 模型概率高于市场 {away_dev:.1%}',
                    'source': 'odds_deviation'
                })
        
        # 2. 资金异常信号
        trap_signals = money_flow.get('trap_signals', [])
        for trap in trap_signals:
            signals.append({
                'type': 'trap_warning',
                'confidence': 0.7,
                'description': trap,
                'source': 'money_flow'
            })
        
        # 3. 市场共识信号
        heat = money_flow.get('heat_index', {})
        if heat.get('home', 0) > 1.5:
            signals.append({
                'type': 'crowded_home',
                'confidence': 0.8,
                'description': f'{home} 资金过热 ({heat["home"]:.1f}x)',
                'source': 'money_flow'
            })
        
        return {
            'source': 'Analyst_v2_simulated',
            'signals': signals,
            'odds_analysis': odds_analysis,
            'signal_count': len(signals)
        }
    
    def _run_committee(self, prediction: Dict, 
                       market_analysis: Dict,
                       money_flow: Dict,
                       odds: Dict[str, float]) -> Dict[str, Any]:
        """
        运行 Committee - 委员会加权决策
        
        融合: 模型预测 + 市场信号 + 资金信号
        """
        if self.committee is None:
            return self._simulate_committee(prediction, market_analysis, money_flow, odds)
        
        try:
            # 构建 Agent 观点
            opinions = []
            
            # 1. 预测模型观点
            model_pred = prediction.get('markets', {}).get('1x2', {}).get('model', {})
            if model_pred:
                opinions.append({
                    'agent': 'PredictionModel',
                    'prediction': {
                        'home_win': model_pred.get('home', 33),
                        'draw': model_pred.get('draw', 33),
                        'away_win': model_pred.get('away', 33)
                    },
                    'confidence': prediction.get('confidence', 0.7),
                    'weight': 1.0
                })
            
            # 2. 市场分析观点
            signals = market_analysis.get('signals', [])
            for signal in signals:
                if signal.get('type') in ['value_home', 'value_away']:
                    direction = 'home_win' if 'home' in signal['type'] else 'away_win'
                    opinions.append({
                        'agent': f"Analyst_{signal['source']}",
                        'prediction': {
                            'home_win': 60 if direction == 'home_win' else 20,
                            'draw': 20,
                            'away_win': 60 if direction == 'away_win' else 20
                        },
                        'confidence': signal.get('confidence', 0.5),
                        'weight': 0.8
                    })
            
            # 资金信号 - 使用 FundSignal 对象
            fund_signals = []
            heat = money_flow.get('heat_index', {})
            if heat.get('home', 0) > 1.2:
                from agents.committee_v2 import FundSignal, FundSignalType
                try:
                    fs = FundSignal(
                        signal_type=FundSignalType.STRONG_HOME,
                        confidence=min(heat['home'] / 2, 1.0),
                        direction='home',
                        strength='strong' if heat['home'] > 1.5 else 'moderate',
                        source='money_flow',
                        weight=0.6
                    )
                    fund_signals = [fs]
                except Exception:
                    fund_signals = [{
                        'signal_type': FundSignalType.STRONG_HOME,
                        'confidence': min(heat['home'] / 2, 1.0),
                        'direction': 'home',
                        'strength': 'strong' if heat['home'] > 1.5 else 'moderate',
                        'source': 'money_flow',
                        'weight': 0.6
                    }]
            
            # 运行委员会
            self.committee.receive_other_opinions(opinions)
            self.committee.receive_fund_signals(fund_signals)
            
            result = self.committee.make_final_decision({
                'market_odds': {
                    'home_win': odds.get('home', 2.0),
                    'draw': odds.get('draw', 3.5),
                    'away_win': odds.get('away', 4.0)
                }
            })
            
            result['source'] = 'Committee_v2'
            return result
            
        except Exception as e:
            print(f"  Committee error: {e}")
            return self._simulate_committee(prediction, market_analysis, money_flow, odds)
    
    def _simulate_committee(self, prediction, market_analysis, money_flow, odds) -> Dict:
        """模拟委员会决策"""
        # 获取模型预测
        model_pred = prediction.get('markets', {}).get('1x2', {}).get('model', {})
        home_p = model_pred.get('home', 33)
        draw_p = model_pred.get('draw', 33)
        away_p = model_pred.get('away', 33)
        
        # 获取市场信号调整
        signals = market_analysis.get('signals', [])
        signal_adjustment = {'home': 0, 'draw': 0, 'away': 0}
        
        for signal in signals:
            if isinstance(signal, dict):
                conf = signal.get('confidence', 0)
                stype = signal.get('type', '')
                if stype == 'value_home':
                    signal_adjustment['home'] += conf * 10
                elif stype == 'value_away':
                    signal_adjustment['away'] += conf * 10
                elif stype == 'trap_warning':
                    desc = signal.get('description', '')
                    home_team = money_flow.get('home_team', '')
                    away_team = money_flow.get('away_team', '')
                    if home_team in desc:
                        signal_adjustment['home'] -= conf * 15
                    if away_team in desc:
                        signal_adjustment['away'] -= conf * 15
        
        # 资金热度调整
        heat = money_flow.get('heat_index', {})
        if heat.get('home', 0) > 1.5:
            # 资金过热 - 可能陷阱
            signal_adjustment['home'] -= 5
        
        # 综合调整
        final_home = max(5, min(95, home_p + signal_adjustment['home']))
        final_draw = max(5, min(95, draw_p + signal_adjustment['draw']))
        final_away = max(5, min(95, away_p + signal_adjustment['away']))
        
        # 归一化
        total = final_home + final_draw + final_away
        final_home = final_home / total * 100
        final_draw = final_draw / total * 100
        final_away = final_away / total * 100
        
        # 推荐结果
        best = max([('home_win', final_home), ('draw', final_draw), ('away_win', final_away)], 
                   key=lambda x: x[1])
        
        return {
            'source': 'Committee_v2_simulated',
            'prediction': {
                'home_win': round(final_home, 2),
                'draw': round(final_draw, 2),
                'away_win': round(final_away, 2)
            },
            'confidence': round(best[1] / 100, 2),
            'recommended_outcome': best[0],
            'key_factors': [f'模型预测 + {len(signals)}个市场信号调整'],
            'fund_signal_applied': len(signals) > 0,
            'market_odds_used': True
        }
    
    def _run_riskcontrol(self, committee_result: Dict,
                         money_flow: Dict,
                         bankroll: float,
                         base_kelly: float) -> Dict[str, Any]:
        """
        运行 RiskControl - 风控调整
        
        动态 Kelly 调整 + 风险熔断
        """
        if self.risk_control is None:
            return self._simulate_riskcontrol(committee_result, money_flow, bankroll, base_kelly)
        
        try:
            # 构建 RiskControl 输入
            match_data = {
                'base_kelly': base_kelly,
                'money_flow_analysis': {
                    'heat_index': money_flow.get('heat_index', {}),
                    'trap_signals': money_flow.get('trap_signals', [])
                },
                'committee_confidence': committee_result.get('confidence', 0.5)
            }
            
            result = self.risk_control.run(match_data)
            
            # 提取 Kelly 调整
            kelly_adj = result.get('kelly_adjustment', {})
            adjusted_kelly = kelly_adj.get('adjusted_kelly', base_kelly)
            max_pct = kelly_adj.get('max_bet_pct', 0.1)
            
            # 计算调整后的注码
            recommended = committee_result.get('recommended_outcome', '')
            recommended_prob = committee_result.get('prediction', {}).get(recommended, 33) / 100
            
            # 简化的 Kelly 计算
            if recommended and 'win' in recommended:
                odds_key = 'home' if 'home' in recommended else 'away' if 'away' in recommended else 'draw'
                odds_val = money_flow.get('odds', {}).get(odds_key, 2.0)
                
                b = odds_val - 1  # 净赔率
                p = recommended_prob  # 获胜概率
                q = 1 - p
                
                if b > 0 and p > 0 and q > 0:
                    kelly_pct = (b * p - q) / b
                    kelly_pct = max(0, kelly_pct)
                    
                    # 应用调整后的 Kelly fraction
                    adjusted_stake = bankroll * kelly_pct * adjusted_kelly
                    max_stake = bankroll * max_pct
                    final_stake = min(adjusted_stake, max_stake)
                else:
                    final_stake = 0
            else:
                final_stake = 0
            
            return {
                'source': 'RiskControl_v2',
                'risk_level': result.get('risk_level', 'low'),
                'kelly_adjustment': kelly_adj,
                'adjusted_stake': round(final_stake, 2),
                'max_bet_pct': max_pct,
                'warnings': result.get('warnings', [])
            }
            
        except Exception as e:
            print(f"  RiskControl error: {e}")
            return self._simulate_riskcontrol(committee_result, money_flow, bankroll, base_kelly)
    
    def _simulate_riskcontrol(self, committee_result, money_flow, bankroll, base_kelly) -> Dict:
        """模拟 RiskControl"""
        warnings = []
        
        # 检查陷阱信号
        trap_signals = money_flow.get('trap_signals', [])
        if trap_signals:
            warnings.append(f"⚠️ 陷阱信号: {len(trap_signals)}个")
        
        # 检查资金过热
        heat = money_flow.get('heat_index', {})
        if heat.get('home', 0) > 1.5:
            warnings.append(f"⚠️ {money_flow.get('home_team')} 资金过热 ({heat['home']:.1f}x)")
        
        # 风险等级
        risk_level = 'low'
        kelly_mult = 1.0
        max_pct = 0.1
        
        if len(trap_signals) >= 2:
            risk_level = 'danger'
            kelly_mult = 0.3
            max_pct = 0.03
            warnings.append("🚫 高风险：多个陷阱信号，建议观望")
        elif len(trap_signals) == 1:
            risk_level = 'warning'
            kelly_mult = 0.6
            max_pct = 0.06
            warnings.append("⚠️ 中风险：存在陷阱信号，降低注码")
        elif heat.get('home', 0) > 1.5 or heat.get('away', 0) > 1.5:
            risk_level = 'caution'
            kelly_mult = 0.8
            max_pct = 0.08
            warnings.append("⚠️ 谨慎：资金过热，降低注码")
        
        # 计算调整后的 Kelly
        adjusted_kelly = base_kelly * kelly_mult
        
        # 计算注码
        recommended = committee_result.get('recommended_outcome', '')
        recommended_prob = committee_result.get('prediction', {}).get(recommended, 33) / 100
        
        odds_key = 'home' if 'home' in recommended else 'away' if 'away' in recommended else 'draw'
        odds_val = money_flow.get('odds', {}).get(odds_key, 2.0)
        
        b = odds_val - 1
        p = recommended_prob
        q = 1 - p
        
        if b > 0 and p > 0 and q > 0:
            kelly_pct = (b * p - q) / b
            kelly_pct = max(0, kelly_pct)
            adjusted_stake = bankroll * kelly_pct * adjusted_kelly
            max_stake = bankroll * max_pct
            final_stake = min(adjusted_stake, max_stake)
        else:
            final_stake = 0
        
        return {
            'source': 'RiskControl_v2_simulated',
            'risk_level': risk_level,
            'kelly_adjustment': {
                'base_kelly': base_kelly,
                'adjusted_kelly': adjusted_kelly,
                'max_bet_pct': max_pct,
                'adjustment_reason': f'风险等级: {risk_level}'
            },
            'adjusted_stake': round(final_stake, 2),
            'max_bet_pct': max_pct,
            'warnings': warnings
        }
    
    def _build_final_bet(self, decision: InvestmentDecision, bankroll: float) -> Optional[Dict]:
        """构建最终投注决策"""
        if decision.adjusted_stake <= 0:
            return None
        
        recommended = decision.recommended_outcome
        if not recommended:
            return None
        
        # 映射到赔率key
        odds_map = {'home_win': 'home', 'draw': 'draw', 'away_win': 'away'}
        odds_key = odds_map.get(recommended, 'home')
        
        # 从 money_flow 获取赔率
        odds = decision.money_flow.get('odds', {}).get(odds_key, 2.0)
        
        # 计算期望价值
        prob = decision.committee_vote.get('prediction', {}).get(recommended, 33) / 100
        ev = (odds * prob - 1) * 100
        
        return {
            'selection': recommended,
            'team': decision.money_flow.get('home_team' if 'home' in recommended else 'away_team', ''),
            'odds': odds,
            'probability': round(prob, 3),
            'expected_value': round(ev, 1),
            'stake': decision.adjusted_stake,
            'stake_pct': round(decision.adjusted_stake / bankroll * 100, 2),
            'risk_level': decision.risk_level,
            'confidence': decision.confidence,
            'warnings': decision.warnings
        }


if __name__ == '__main__':
    # 测试
    integration = InvestmentSystemIntegration()
    
    test_prediction = {
        'markets': {
            '1x2': {
                'model': {'home': 69, 'draw': 19, 'away': 12}
            },
            'over_under': {'lambda': 2.5}
        },
        'confidence': 0.69
    }
    
    test_odds = {'home': 1.30, 'draw': 4.50, 'away': 8.50}
    
    decision = integration.run(
        home='Germany', away='Japan',
        prediction=test_prediction,
        odds=test_odds,
        bankroll=50000,
        base_kelly=0.25
    )
    
    print(f"\n{'='*60}")
    print("FINAL INVESTMENT DECISION")
    print(f"{'='*60}")
    print(json.dumps(decision.__dict__, indent=2, ensure_ascii=False, default=str))
