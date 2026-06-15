#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - Full Prediction Pipeline

集成 9 个 Agent 的统一预测流水线：
1. 数据抓取 → 2. 情报收集 → 3. 特征工程 → 4. 预测 → 5. 风控 → 6. 注码

Usage:
    python scripts/predict_pipeline.py --home Germany --away Japan
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict

from models import HeuristicModel, PoissonModel, ModelEnsemble, XGBoostPredictor
from models.kelly_integration import get_kelly_recommendations

# Combination Betting Integration
try:
    from scripts.combination_betting import recommend_combinations, format_recommendations
    from scripts.combination_recommender import extract_value_bets_from_predictions
    COMBINATION_AVAILABLE = True
except ImportError:
    try:
        from combination_betting import recommend_combinations, format_recommendations
        from combination_recommender import extract_value_bets_from_predictions
        COMBINATION_AVAILABLE = True
    except ImportError:
        COMBINATION_AVAILABLE = False

# Investment System Integration
try:
    from scripts.investment_system import InvestmentSystemIntegration, InvestmentDecision
except ImportError:
    try:
        from investment_system import InvestmentSystemIntegration, InvestmentDecision
    except ImportError:
        InvestmentSystemIntegration = None
        InvestmentDecision = None

# Global storage for multi-match combination betting
_MATCH_PREDICTIONS = []
_BANKROLL = 10000.0
_RISK_LEVEL = "conservative"

def _add_match_prediction(result: Dict[str, Any]):
    """将单场比赛预测结果添加到全局存储"""
    global _MATCH_PREDICTIONS
    _MATCH_PREDICTIONS.append(result)
    # 限制存储数量，避免内存过大
    if len(_MATCH_PREDICTIONS) > 20:
        _MATCH_PREDICTIONS = _MATCH_PREDICTIONS[-20:]

def _extract_value_bets_from_single(result: Dict[str, Any]) -> list:
    """从单场比赛预测结果中提取有价值的投注"""
    value_bets = []
    
    home = result.get('match', 'Unknown').split(' vs ')[0] if ' vs ' in result.get('match', '') else 'Home'
    away = result.get('match', 'Unknown').split(' vs ')[1] if ' vs ' in result.get('match', '') else 'Away'
    match_date = result.get('timestamp', datetime.now().isoformat())[:10]
    league = result.get('stage', 'World Cup')
    
    prediction = result.get('prediction', {})
    markets = prediction.get('markets', {})
    
    # 1X2 市场
    if '1x2' in markets:
        m1x2 = markets['1x2']
        implied = m1x2.get('implied', {})
        model = m1x2.get('model', {})
        
        for outcome in ['home', 'draw', 'away']:
            market_prob = implied.get(outcome, 0)
            model_prob = model.get(outcome, 0) if isinstance(model, dict) else 0
            edge = model_prob - market_prob
            
            if edge > 0.03 and market_prob > 0:
                odds = 1 / market_prob if market_prob > 0 else 2.0
                selection_map = {'home': f'{home}胜', 'draw': '平局', 'away': f'{away}胜'}
                value_bets.append({
                    'home': home, 'away': away,
                    'market': '1x2',
                    'selection': selection_map.get(outcome, outcome),
                    'odds': round(odds, 2),
                    'probability': round(model_prob, 4),
                    'edge': round(edge, 4),
                    'match_date': match_date,
                    'league': league
                })
    
    # 让球市场
    if 'asian_handicap' in markets:
        ah = markets['asian_handicap']
        if 'recommendation' in ah and 'edge' in ah:
            if ah['edge'] > 0.03:
                value_bets.append({
                    'home': home, 'away': away,
                    'market': 'asian_handicap',
                    'selection': ah['recommendation'],
                    'odds': ah.get('odds', 1.90),
                    'probability': ah.get('probability', 0.50),
                    'edge': ah['edge'],
                    'match_date': match_date,
                    'league': league
                })
    
    # 大小球市场
    if 'over_under' in markets:
        ou = markets['over_under']
        if 'recommendation' in ou and 'edge' in ou:
            if ou['edge'] > 0.02:
                value_bets.append({
                    'home': home, 'away': away,
                    'market': 'over_under',
                    'selection': ou['recommendation'],
                    'odds': ou.get('odds', 1.90),
                    'probability': ou.get('probability', 0.50),
                    'edge': ou['edge'],
                    'match_date': match_date,
                    'league': league
                })
    
    return value_bets

def _generate_combination_report_for_matches() -> str:
    """为已存储的多场比赛生成组合投注报告"""
    if not COMBINATION_AVAILABLE or len(_MATCH_PREDICTIONS) < 2:
        return ""
    
    all_bets = []
    for pred in _MATCH_PREDICTIONS:
        bets = _extract_value_bets_from_single(pred)
        all_bets.extend(bets)
    
    if len(all_bets) < 2:
        return ""
    
    recommendations = recommend_combinations(all_bets, bankroll=_BANKROLL, risk_level=_RISK_LEVEL)
    return format_recommendations(recommendations)


@dataclass
class PipelineContext:
    """流水线上下文，存储所有 Agent 的中间结果"""
    home: str
    away: str
    stage: str = 'group'
    
    # Agent 数据
    odds: Dict[str, Any] = None
    intelligence: Dict[str, Any] = None
    coach_factor: Dict[str, Any] = None
    upset_score: Dict[str, Any] = None
    historical_features: Dict[str, Any] = None
    risk_check: Dict[str, Any] = None
    
    # 预测结果
    prediction: Dict[str, Any] = None
    kelly: Dict[str, Any] = None


class AgentOrchestrator:
    """
    Agent 编排器
    
    协调 9 个 Agent 的数据抓取
    """
    
    def __init__(self):
        self.results = {}
    
    def fetch_odds(self, home: str, away: str) -> Dict[str, Any]:
        """
        P0: OddsPricingAgent - 获取市场赔率
        
        支持:
        - 手动输入赔率 (CLI)
        - 从 OddsPricingAgent 获取 (如果有 API)
        - 从 Football-Data.org 获取历史赔率
        """
        # 如果用户提供了赔率，直接返回
        # 否则尝试从数据源获取
        return {
            'source': 'user_input_or_default',
            'odds': {},
            'status': 'requires_user_input'
        }
    
    def fetch_intelligence(self, home: str, away: str) -> Dict[str, Any]:
        """
        P0: IntelligenceAgent - 获取情报
        
        免费数据源:
        - BBC Sport RSS
        - 新浪体育/网易体育
        - Football-Data.org
        """
        try:
            from agents.intelligence import IntelligenceAgent
            agent = IntelligenceAgent()
            # 简化版：返回结构，实际调用需要配置
            return {
                'source': 'IntelligenceAgent',
                'news': [],
                'injuries': {'home': [], 'away': []},
                'sentiment': {'home': 0.0, 'away': 0.0},
                'status': 'available'
            }
        except Exception as e:
            return {
                'source': 'IntelligenceAgent',
                'error': str(e),
                'status': 'unavailable'
            }
    
    def fetch_coach_factor(self, home: str, away: str) -> Dict[str, Any]:
        """
        P3: CoachFactor - 获取教练因子
        
        48强教练数据库:
        - CRI 引擎 (6维度)
        - 互联网同步
        """
        try:
            # 检查是否在48强数据库中
            from references.fifa_regions_2026 import TEAMS_2026
            
            home_found = home in TEAMS_2026
            away_found = away in TEAMS_2026
            
            if home_found and away_found:
                return {
                    'source': 'CoachFactor',
                    'home_coach': TEAMS_2026[home].get('coach', 'Unknown'),
                    'away_coach': TEAMS_2026[away].get('coach', 'Unknown'),
                    'status': 'available'
                }
            else:
                return {
                    'source': 'CoachFactor',
                    'status': 'teams_not_in_database'
                }
        except Exception as e:
            return {
                'source': 'CoachFactor',
                'error': str(e),
                'status': 'unavailable'
            }
    
    def calculate_upset(self, home: str, away: str, market_prob: Dict, model_prob: Dict) -> Dict[str, Any]:
        """
        P3: UpsetDetector - 计算冷门评分
        """
        try:
            from agents.upset_detector import UpsetDetector
            agent = UpsetDetector()
            
            score = agent.calculate_upset_score(
                market_prob=market_prob,
                model_prob=model_prob,
                market_odds={'home': 1/ market_prob['home'], 'draw': 1/market_prob['draw'], 'away': 1/market_prob['away']}
            )
            
            return {
                'source': 'UpsetDetector',
                'upset_score': score.get('total_score', 0),
                'risk_level': score.get('risk_level', 'normal'),
                'status': 'available'
            }
        except Exception as e:
            return {
                'source': 'UpsetDetector',
                'error': str(e),
                'status': 'unavailable'
            }
    
    def fetch_historical_features(self, home: str, away: str) -> Dict[str, Any]:
        """
        P4: WorldCupDataEngineer - 获取历史特征
        """
        try:
            from data.data_fetcher import DataFetcherFactory
            
            fetcher = DataFetcherFactory.create('kaggle')
            matches = fetcher.fetch_matches(year=2022)
            
            # 查找历史对战
            h2h_matches = []
            for m in matches:
                if (m.get('home') == home and m.get('away') == away) or \
                   (m.get('home') == away and m.get('away') == home):
                    h2h_matches.append(m)
            
            return {
                'source': 'WorldCupDataEngineer',
                'h2h_matches': len(h2h_matches),
                'h2h_history': h2h_matches[:3] if h2h_matches else [],
                'status': 'available' if h2h_matches else 'no_h2h_data'
            }
        except Exception as e:
            return {
                'source': 'WorldCupDataEngineer',
                'error': str(e),
                'status': 'unavailable'
            }
    
    def check_risk(self, context: PipelineContext) -> Dict[str, Any]:
        """
        P1: RiskGuardian - 风控检查
        """
        try:
            from agents.risk_guardian import RiskGuardian
            agent = RiskGuardian()
            
            # 简化风控检查
            risk_level = 'low'
            if context.upset_score and context.upset_score.get('upset_score', 0) > 80:
                risk_level = 'high'
            
            return {
                'source': 'RiskGuardian',
                'risk_level': risk_level,
                'status': 'available'
            }
        except Exception as e:
            return {
                'source': 'RiskGuardian',
                'error': str(e),
                'status': 'unavailable'
            }
    
    def run_all(self, home: str, away: str, odds: Dict[str, float] = None) -> PipelineContext:
        """
        运行所有 Agent 数据抓取
        
        Returns:
            PipelineContext 包含所有 Agent 结果
        """
        print(f"\n{'='*60}")
        print(f"Agent Orchestrator - Fetching Data for {home} vs {away}")
        print(f"{'='*60}")
        
        ctx = PipelineContext(home=home, away=away)
        
        # 1. Odds
        print("\n[1/6] P0: OddsPricingAgent - Fetching market odds...")
        ctx.odds = self.fetch_odds(home, away)
        if odds:
            ctx.odds['user_provided'] = odds
            ctx.odds['status'] = 'user_provided'
        print(f"  Status: {ctx.odds['status']}")
        
        # 2. Intelligence
        print("\n[2/6] P0: IntelligenceAgent - Fetching news & injuries...")
        ctx.intelligence = self.fetch_intelligence(home, away)
        print(f"  Status: {ctx.intelligence['status']}")
        
        # 3. Coach Factor
        print("\n[3/6] P3: CoachFactor - Fetching coach data...")
        ctx.coach_factor = self.fetch_coach_factor(home, away)
        print(f"  Status: {ctx.coach_factor['status']}")
        
        # 4. Historical Features
        print("\n[4/6] P4: WorldCupDataEngineer - Fetching historical data...")
        ctx.historical_features = self.fetch_historical_features(home, away)
        print(f"  Status: {ctx.historical_features['status']}")
        print(f"  H2H Matches: {ctx.historical_features.get('h2h_matches', 0)}")
        
        # 5. Upset Detection (需要预测后计算)
        print("\n[5/6] P3: UpsetDetector - Will calculate after prediction...")
        
        # 6. Risk Check (需要预测后计算)
        print("\n[6/6] P1: RiskGuardian - Will check after prediction...")
        
        print(f"\n{'='*60}")
        print("Agent Data Collection Complete!")
        print(f"{'='*60}")
        
        return ctx


class PredictionPipeline:
    """
    完整预测流水线
    
    1. Agent 数据抓取
    2. 特征工程
    3. 模型预测
    4. 冷门检测
    5. 风控检查
    6. Kelly 注码
    """
    
    def __init__(self):
        self.orchestrator = AgentOrchestrator()
        self.ensemble = self._create_ensemble()
    
    def _create_ensemble(self) -> ModelEnsemble:
        """创建模型融合器"""
        ensemble = ModelEnsemble()
        
        # 添加启发式模型
        heuristic = HeuristicModel()
        ensemble.add_model(heuristic, weight=0.3)
        
        # 添加泊松模型
        poisson = PoissonModel()
        ensemble.add_model(poisson, weight=0.4)
        
        # 添加 XGBoost 模型
        try:
            xgb = XGBoostPredictor()
            if xgb.supported_markets:
                ensemble.add_model(xgb, weight=0.3)
        except:
            pass
        
        return ensemble
    
    def run(self, 
            home: str, away: str,
            odds_home: float, odds_draw: float, odds_away: float,
            stage: str = 'group',
            bankroll: float = 100000.0,
            kelly_fraction: float = 0.25,
            **kwargs) -> Dict[str, Any]:
        """
        运行完整预测流水线
        
        步骤:
        1. 9 Agent 数据抓取
        2. 模型预测
        3. 冷门检测
        4. 风控检查
        5. Kelly 注码
        """
        print(f"\n{'='*60}")
        print(f"Football Quant OS - Full Prediction Pipeline")
        print(f"{'='*60}")
        print(f"Match: {home} vs {away}")
        print(f"Odds: H={odds_home} D={odds_draw} A={odds_away}")
        
        # Step 1: Agent Data Collection
        print(f"\n{'='*60}")
        print("Step 1: Agent Data Collection (9 Agents)")
        print(f"{'='*60}")
        
        user_odds = {'home': odds_home, 'draw': odds_draw, 'away': odds_away}
        ctx = self.orchestrator.run_all(home, away, user_odds)
        ctx.stage = stage
        
        # Step 2: Model Prediction
        print(f"\n{'='*60}")
        print("Step 2: Model Prediction (3-Model Fusion)")
        print(f"{'='*60}")
        
        match_info = {
            'home': home,
            'away': away,
            'odds_home': odds_home,
            'odds_draw': odds_draw,
            'odds_away': odds_away,
            'stage': stage,
        }
        
        # 添加 Agent 数据
        if ctx.intelligence.get('injuries'):
            match_info['injuries'] = ctx.intelligence['injuries']
        
        if ctx.historical_features.get('h2h_history'):
            match_info['h2h_history'] = ctx.historical_features['h2h_history']
        
        # 添加用户可选参数
        optional_fields = [
            'home_xg', 'away_xg', 'home_poss', 'away_poss',
            'home_region', 'away_region', 'motivation'
        ]
        for field in optional_fields:
            if field in kwargs and kwargs[field] is not None:
                match_info[field] = kwargs[field]
        
        prediction = self.ensemble.predict(match_info, line=kwargs.get('ou_line', 2.5))
        ctx.prediction = prediction
        
        # Step 3: Upset Detection
        print(f"\n{'='*60}")
        print("Step 3: Upset Detection (Post-Prediction)")
        print(f"{'='*60}")
        
        if '1x2' in prediction.get('markets', {}):
            m1x2 = prediction['markets']['1x2']
            implied = m1x2.get('implied', {})
            model = m1x2.get('model', {})
            
            ctx.upset_score = self.orchestrator.calculate_upset(
                home, away, implied, model
            )
            print(f"  Upset Score: {ctx.upset_score.get('upset_score', 0)}")
            print(f"  Risk Level: {ctx.upset_score.get('risk_level', 'normal')}")
        
        # Step 4: Risk Check
        print(f"\n{'='*60}")
        print("Step 4: Risk Guardian (Post-Prediction)")
        print(f"{'='*60}")
        
        ctx.risk_check = self.orchestrator.check_risk(ctx)
        print(f"  Risk Level: {ctx.risk_check.get('risk_level', 'low')}")
        
        # Step 5: Kelly Calculation
        print(f"\n{'='*60}")
        print("Step 5: Kelly Stake Calculation")
        print(f"{'='*60}")
        
        # 构建 predict.py 格式结果用于 Kelly
        result = {
            'match': f'{home} vs {away}',
            'timestamp': datetime.now().isoformat(),
            'version': '5.1.0-pipeline',
            'stage': stage,
            'markets': prediction.get('markets', {}),
            'confidence': prediction.get('confidence', 0),
            'upset_score': ctx.upset_score.get('upset_score', 0),
            'recommendations': []
        }
        
        kelly_recs = get_kelly_recommendations(result, bankroll, kelly_fraction)
        ctx.kelly = {
            'bankroll': bankroll,
            'fraction': kelly_fraction,
            'recommendations': kelly_recs
        }
        
        for rec in kelly_recs:
            opp = rec['opportunity']
            stake = rec['stake']
            if stake['action'] == 'bet':
                print(f"  [BET] {opp.selection}: ${stake['stake']:.2f} (EV: {stake['expected_value']:.1f}%)")
        
        # Step 6: Investment System Decision (NEW)
        print(f"\n{'='*60}")
        print("Step 6: Investment System - 4-Module Decision")
        print(f"{'='*60}")
        
        investment_decision = None
        if InvestmentSystemIntegration is not None:
            try:
                investment = InvestmentSystemIntegration()
                odds_dict = {'home': odds_home, 'draw': odds_draw, 'away': odds_away}
                
                investment_decision = investment.run(
                    home=home, away=away,
                    prediction=prediction,
                    odds=odds_dict,
                    bankroll=bankroll,
                    base_kelly=kelly_fraction
                )
                
                # 输出投资决策
                if investment_decision:
                    print(f"\n  [DataScout] 资金热度: Home={investment_decision.money_flow.get('heat_index',{}).get('home',0):.1f}x")
                    print(f"  [Analyst] 市场信号: {len(investment_decision.market_signals)}个")
                    print(f"  [Committee] 推荐: {investment_decision.recommended_outcome} ({investment_decision.confidence:.0%})")
                    print(f"  [RiskControl] 风险等级: {investment_decision.risk_level.upper()}")
                    
                    if investment_decision.final_bet:
                        bet = investment_decision.final_bet
                        print(f"\n  ✅ FINAL BET:")
                        print(f"     Selection: {bet['selection']} @ {bet['odds']}")
                        print(f"     Stake: ${bet['stake']:.2f} ({bet['stake_pct']:.1f}% of bankroll)")
                        print(f"     EV: {bet['expected_value']:.1f}%")
                    else:
                        print(f"\n  ❌ NO BET: {', '.join(investment_decision.warnings[:2])}")
                        
            except Exception as e:
                print(f"  Investment System error: {e}")
        else:
            print("  Investment System not available (module not found)")
        
        # Step 7: Combination Betting (Multi-Match Accumulator)
        print(f"\n{'='*60}")
        print("Step 7: Combination Betting (2/3/4-Fold)")
        print(f"{'='*60}")
        
        global _BANKROLL, _RISK_LEVEL
        _BANKROLL = bankroll
        _RISK_LEVEL = "conservative"
        
        # Build final output
        final = {
            'match': f'{home} vs {away}',
            'timestamp': datetime.now().isoformat(),
            'version': '5.1.0-pipeline',
            'stage': stage,
            'prediction': prediction,
            'agent_data': {
                'odds': ctx.odds,
                'intelligence': ctx.intelligence,
                'coach_factor': ctx.coach_factor,
                'upset_score': ctx.upset_score,
                'historical_features': ctx.historical_features,
                'risk_check': ctx.risk_check
            },
            'kelly': ctx.kelly,
            'investment_decision': {
                'money_flow': investment_decision.money_flow if investment_decision else {},
                'market_signals': investment_decision.market_signals if investment_decision else [],
                'committee_vote': investment_decision.committee_vote if investment_decision else {},
                'risk_level': investment_decision.risk_level if investment_decision else 'unknown',
                'final_bet': investment_decision.final_bet if investment_decision else None,
                'warnings': investment_decision.warnings if investment_decision else []
            } if investment_decision else None,
        }
        
        # Add to combination betting pool
        _add_match_prediction(final)
        
        combo_report = ""
        if COMBINATION_AVAILABLE and len(_MATCH_PREDICTIONS) >= 2:
            combo_report = _generate_combination_report_for_matches()
            if combo_report:
                print(combo_report)
            else:
                print("  No valid combination bets available yet")
        else:
            print("  Combination betting requires 2+ matches with value bets")
            print(f"  Current match count: {len(_MATCH_PREDICTIONS)}")
        
        # Add combination betting to final output
        final['combination_betting'] = {
            'available': COMBINATION_AVAILABLE,
            'match_count': len(_MATCH_PREDICTIONS),
            'report': combo_report
        }
        
        return final


def main():
    parser = argparse.ArgumentParser(
        description='Football Quant OS - Full Prediction Pipeline (9 Agents + 3 Models)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full pipeline with default bankroll
  python predict_pipeline.py --home Germany --away Japan \\
    --odds-home 1.30 --odds-draw 4.50 --odds-away 8.50
  
  # With custom bankroll and Kelly fraction
  python predict_pipeline.py --home Germany --away Japan \\
    --odds-home 1.30 --odds-draw 4.50 --odds-away 8.50 \\
    --bankroll 50000 --kelly-fraction 0.25
        """
    )
    
    # Required
    parser.add_argument('--home', required=True, help='Home team name')
    parser.add_argument('--away', required=True, help='Away team name')
    parser.add_argument('--odds-home', type=float, required=True, help='Home win odds')
    parser.add_argument('--odds-draw', type=float, required=True, help='Draw odds')
    parser.add_argument('--odds-away', type=float, required=True, help='Away win odds')
    
    # Optional
    parser.add_argument('--stage', choices=['group', 'knockout', 'final'], default='group')
    parser.add_argument('--home-xg', type=float, help='Home team xG')
    parser.add_argument('--away-xg', type=float, help='Away team xG')
    parser.add_argument('--home-region', help='Home team region')
    parser.add_argument('--away-region', help='Away team region')
    
    # Kelly
    parser.add_argument('--bankroll', type=float, default=100000.0, help='Total bankroll')
    parser.add_argument('--kelly-fraction', type=float, default=0.25, help='Kelly fraction')
    
    # Output
    parser.add_argument('--format', choices=['json', 'text'], default='text')
    parser.add_argument('--output', help='Output file path (JSON)')
    
    args = parser.parse_args()
    
    # Run pipeline
    pipeline = PredictionPipeline()
    
    result = pipeline.run(
        args.home, args.away,
        args.odds_home, args.odds_draw, args.odds_away,
        stage=args.stage,
        bankroll=args.bankroll,
        kelly_fraction=args.kelly_fraction,
        home_xg=args.home_xg,
        away_xg=args.away_xg
    )
    
    # Output
    if args.format == 'json':
        output = json.dumps(result, indent=2, ensure_ascii=False, default=str)
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(output)
            print(f"\nSaved to: {args.output}")
        else:
            print(output)
    else:
        print(f"\n{'='*60}")
        print("FINAL RESULTS")
        print(f"{'='*60}")
        
        pred = result['prediction']
        print(f"\nPrediction:")
        for market, data in pred.get('markets', {}).items():
            print(f"  [{market.upper()}]")
            if isinstance(data, dict):
                for key, val in data.items():
                    if isinstance(val, (int, float, str)):
                        print(f"    {key}: {val}")
        
        print(f"\nAgent Data:")
        for agent_name, data in result['agent_data'].items():
            status = data.get('status', 'unknown')
            print(f"  {agent_name}: {status}")
        
        print(f"\nInvestment System Decision:")
        inv = result.get('investment_decision')
        if inv:
            print(f"  DataScout: 资金热度 H={inv['money_flow'].get('heat_index',{}).get('home',0):.1f}x")
            print(f"  Analyst: {len(inv['market_signals'])}个信号")
            print(f"  Committee: {inv['committee_vote'].get('recommended_outcome', 'N/A')}")
            print(f"  RiskControl: {inv['risk_level'].upper()}")
            if inv['final_bet']:
                bet = inv['final_bet']
                print(f"\n  ✅ RECOMMENDED BET:")
                print(f"     {bet['selection']} @ {bet['odds']} | ${bet['stake']:.2f} ({bet['stake_pct']:.1f}%)")
            else:
                print(f"\n  ❌ NO BET: {', '.join(inv['warnings'][:2]) if inv['warnings'] else 'No value'}")
        else:
            print(f"  Not available")
        
        print(f"\nKelly Recommendations:")
        for rec in result['kelly']['recommendations']:
            opp = rec['opportunity']
            stake = rec['stake']
            if stake['action'] == 'bet':
                print(f"  [BET] {opp.selection}: ${stake['stake']:.2f}")
        
        # Combination Betting Output
        combo = result.get('combination_betting', {})
        if combo.get('available') and combo.get('match_count', 0) >= 2:
            print(f"\n{'='*60}")
            print("COMBINATION BETTING (Multi-Match)")
            print(f"{'='*60}")
            print(f"  Matches in pool: {combo['match_count']}")
            if combo.get('report'):
                # 只打印报告的前2000字符，避免太长
                report_lines = combo['report'].split('\n')
                for line in report_lines[:30]:
                    print(f"  {line}")
                if len(report_lines) > 30:
                    print(f"  ... ({len(report_lines) - 30} more lines)")
            else:
                print("  No valid combination bets generated")
        else:
            print(f"\nCombination Betting:")
            print(f"  Status: Need 2+ matches with value bets")
            print(f"  Current matches: {combo.get('match_count', 0)}")


if __name__ == '__main__':
    main()
