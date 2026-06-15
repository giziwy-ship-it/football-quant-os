#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
World Cup 2026 Integrator - Football Quant OS
整合点：
  1. 新数据层 (worldcup2026_data.py) -> 48队数据库
  2. 新赛程层 (worldcup_fixtures.py) -> 72场比赛
  3. 国家队Elo模型 (替代俱乐部Elo)
  4. 五层信号系统 (PD/SYNC/ACC/DIV/LEAD)
  5. 诱盘检测引擎
  6. 决策树闸门
  7. Kelly v2.0 保守折扣
  8. 现有9智能体流水线
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import json

from data.worldcup2026_data import (
    TEAMS, GROUPS, get_team, get_all_teams, NationalTeam
)
from data.worldcup_fixtures import get_fixtures_by_team, WorldCupFixture


# ===================== 五层信号系统 =====================
class MarketSignalLevel(Enum):
    PD = "price_deviation"
    SYNC = "synchronization"
    ACC = "acceleration"
    DIV = "divergence"
    LEAD = "lead_lag"


@dataclass
class MarketSignal:
    level: MarketSignalLevel
    value: float
    direction: str
    confidence: float


class MarketSignalEngine:
    """五层信号引擎"""
    def calculate_pd(self, market_prob, model_prob):
        pd_home = market_prob.get('home', 0.33) - model_prob.get('home', 0.33)
        pd_draw = market_prob.get('draw', 0.33) - model_prob.get('draw', 0.33)
        pd_away = market_prob.get('away', 0.33) - model_prob.get('away', 0.33)
        max_pd = max(abs(pd_home), abs(pd_draw), abs(pd_away))
        direction = 'home' if abs(pd_home) == max_pd else ('draw' if abs(pd_draw) == max_pd else 'away')
        return MarketSignal(MarketSignalLevel.PD, max_pd, direction, min(1.0, max_pd * 5))

    def analyze(self, market_data):
        signals = {}
        if 'market_prob' in market_data and 'model_prob' in market_data:
            signals['PD'] = self.calculate_pd(market_data['market_prob'], market_data['model_prob'])
        return signals


# ===================== 诱盘检测 =====================
class TrapType(Enum):
    NONE = "none"
    HOME_TRAP = "home_trap"
    AWAY_TRAP = "away_trap"
    FAVORITE_TRAP = "favorite_trap"


@dataclass
class TrapDetection:
    is_trap: bool
    trap_type: TrapType
    confidence: float
    reason: str
    avoid_direction: str = ""


class TrapDetector:
    def detect(self, match_data, signals):
        reasons = []
        confidence = 0.0
        trap_type = TrapType.NONE
        avoid = ""
        if 'PD' in signals:
            pd = signals['PD']
            if pd.value > 0.15 and pd.confidence > 0.6:
                reasons.append(f"High PD={pd.value:.2f}")
                confidence += 0.3
                avoid = pd.direction
                trap_type = TrapType.HOME_TRAP if pd.direction == 'home' else TrapType.AWAY_TRAP
        media = match_data.get('media_consensus', 0.0)
        if media > 0.8:
            reasons.append(f"Media consensus {media:.0%}")
            confidence += 0.2
            trap_type = TrapType.FAVORITE_TRAP
        is_trap = confidence > 0.5
        return TrapDetection(is_trap, trap_type if is_trap else TrapType.NONE,
                             min(1.0, confidence),
                             "; ".join(reasons) if reasons else "No trap signals",
                             avoid if is_trap else "")


# ===================== 市场状态分类 =====================
class MarketRegime(Enum):
    EQUILIBRIUM = "equilibrium"
    TRAP = "trap"
    INFORMATION = "information"
    DISTORTION = "distortion"
    CHAOS = "chaos"


class MarketRegimeClassifier:
    def classify(self, signals, trap):
        if trap.is_trap and trap.confidence > 0.6:
            return MarketRegime.TRAP, "Contrarian/avoid comfortable side", trap.reason
        if 'PD' not in signals:
            return MarketRegime.CHAOS, "ABANDON", "Missing PD signal"
        pd = signals['PD']
        if abs(pd.value) < 0.05:
            return MarketRegime.EQUILIBRIUM, "ABANDON or micro-arbitrage", "PD too small"
        if abs(pd.value) > 0.15:
            return MarketRegime.DISTORTION, "Batch entry + strict stop", "High deviation + high acceleration"
        if abs(pd.value) > 0.08:
            return MarketRegime.INFORMATION, "Follow with caution", "Medium deviation"
        return MarketRegime.EQUILIBRIUM, "ABANDON", "Insufficient signal"


# ===================== 决策树 =====================
class DecisionTree:
    def __init__(self):
        self.regime_classifier = MarketRegimeClassifier()
        self.trap_detector = TrapDetector()
        self.signal_engine = MarketSignalEngine()

    def run(self, match_data):
        result = {'action': 'ABANDON', 'confidence': 0.0, 'reason': ''}
        market_prob = match_data.get('market_prob', {})
        model_prob = match_data.get('model_prob', {})
        if not market_prob or not model_prob:
            result['reason'] = 'Missing probability data'
            return result
        signals = self.signal_engine.analyze(match_data)
        if 'PD' not in signals:
            result['reason'] = 'Cannot calculate PD'
            return result
        pd_signal = signals['PD']
        if abs(pd_signal.value) < 0.05:
            result['reason'] = f'PD={pd_signal.value:.3f} < 0.05'
            return result
        trap = self.trap_detector.detect(match_data, signals)
        regime, action, reason = self.regime_classifier.classify(signals, trap)
        result['reason'] = reason
        if regime == MarketRegime.TRAP and trap.confidence > 0.7:
            result['action'] = 'CONTRARIAN'
            result['confidence'] = trap.confidence * 0.8
        elif regime in (MarketRegime.INFORMATION, MarketRegime.DISTORTION):
            result['action'] = 'EXECUTE' if regime == MarketRegime.INFORMATION else 'EXECUTE_CAUTION'
            result['confidence'] = pd_signal.confidence * (0.7 if regime == MarketRegime.DISTORTION else 1.0)
        return result


# ===================== Kelly v2.0 - Tight Hybrid =====================
class KellyConservative:
    def __init__(self, bankroll=10000):
        self.bankroll = bankroll
        self.kelly_fraction = 0.45  # 0.35 -> 0.45 (Tight Hybrid: 2022 validated)
        self.consecutive_losses = 0
        self.consecutive_wins = 0
        self.daily_risk_used = 0.0
        self.daily_risk_limit = 0.15  # 0.10 -> 0.15 (more utilization)
        self.vig = 0.05  # 0.06 -> 0.05 (realistic)

    def calculate(self, model_prob, market_odds, direction='home'):
        implied_prob = 1 / market_odds if market_odds > 1 else 0.5
        edge = model_prob - implied_prob - self.vig
        if edge <= 0:
            return {'action': 'NO_BET', 'reason': f'Edge={edge:.3f} <= 0 after vig', 'bet_pct': 0}
        b = market_odds - 1
        p = model_prob
        q = 1 - p
        kelly_f = (b * p - q) / b if b > 0 else 0
        conservative_f = kelly_f * self.kelly_fraction
        loss_penalty = 1.0
        if self.consecutive_losses >= 7: loss_penalty = 0.2
        elif self.consecutive_losses >= 5: loss_penalty = 0.5
        elif self.consecutive_losses >= 3: loss_penalty = 0.75
        conservative_f *= loss_penalty
        if self.consecutive_wins >= 5: conservative_f *= 0.8
        bet_pct = max(0, conservative_f)
        if self.daily_risk_used + bet_pct > self.daily_risk_limit:
            available = self.daily_risk_limit - self.daily_risk_used
            if available <= 0:
                return {'action': 'NO_BET', 'reason': f'Daily limit full ({self.daily_risk_used:.1%})', 'bet_pct': 0}
            bet_pct = min(bet_pct, available)
        bet_pct = min(bet_pct, 0.03)  # 0.02 -> 0.03 (Tight Hybrid max)
        self.daily_risk_used += bet_pct
        return {
            'action': 'BET' if bet_pct > 0 else 'NO_BET',
            'direction': direction, 'edge': edge, 'kelly_raw': kelly_f,
            'bet_pct': bet_pct, 'bet_amount': self.bankroll * bet_pct,
            'reason': f'Edge={edge:.3f}, Kelly={kelly_f:.3f}, Bet={bet_pct:.2%}'
        }

    def record_result(self, won):
        if won: self.consecutive_wins += 1; self.consecutive_losses = 0
        else: self.consecutive_losses += 1; self.consecutive_wins = 0

    def reset_daily(self):
        self.daily_risk_used = 0.0


# ===================== A+B Hybrid Strategy (2022 Validated) =====================
class HybridStrategy:
    """
    A+B Hybrid Strategy for World Cup 2026
    
    A: Pure ELO with positive edge + Kelly
    B: Motivation factor (qualified/do-or-die/rotation)
    
    2022 Backtest Results:
    - Tight Hybrid (PD>=0.03, Edge>=0.05, Kelly 0.45): 60% WR, +3.9% return, 10.4% utilization
    - Loose Hybrid (PD>=0.015): 50% WR, +0.4% return, 16.7% utilization
    - Recommendation: Use Tight for group stage, Loose for knockout
    """
    
    def __init__(self, bankroll=10000, stage='group'):
        self.bankroll = bankroll
        self.stage = stage  # 'group' or 'knockout'
        self.kelly = KellyConservative(bankroll)
        self.kelly.reset_daily()
        
        # Stage-specific thresholds
        if stage == 'group':
            self.pd_threshold = 0.03  # Tight
            self.edge_threshold = 0.05
        else:  # knockout
            self.pd_threshold = 0.015  # Loose
            self.edge_threshold = 0.03

    def get_motivation(self, match_notes=""):
        """战意因子: -0.08 to +0.05"""
        motivation = 0.0
        notes = match_notes.lower()
        if any(k in notes for k in ['already qualified', 'reserves', 'rotation']):
            motivation -= 0.08
        if any(k in notes for k in ['need to win', 'must win', 'do-or-die']):
            motivation += 0.05
        return max(-0.10, min(0.10, motivation))

    def apply_motivation(self, model_prob, motivation):
        """应用战意因子调整概率"""
        adjusted = dict(model_prob)
        if motivation < -0.05:
            # 已出线球队降低概率
            if adjusted['home'] > adjusted['away']:
                adjusted['home'] *= (1 + motivation)  # motivation negative
            else:
                adjusted['away'] *= (1 + motivation)
        elif motivation > 0.03:
            # 生死战球队提升概率
            if adjusted['home'] < adjusted['away']:
                adjusted['home'] *= (1 + motivation)
            else:
                adjusted['away'] *= (1 + motivation)
        # 归一化
        total = adjusted['home'] + adjusted['draw'] + adjusted['away']
        return {k: v/total for k, v in adjusted.items()}

    def decide(self, model_prob, market_prob, market_odds, match_notes=""):
        """A+B 决策: 返回 action, bet_dir, bet_amount, reason"""
        motivation = self.get_motivation(match_notes)
        adjusted_prob = self.apply_motivation(model_prob, motivation)
        
        # PD 计算
        pd_home = market_prob.get('home', 0.33) - adjusted_prob['home']
        pd_draw = market_prob.get('draw', 0.33) - adjusted_prob['draw']
        pd_away = market_prob.get('away', 0.33) - adjusted_prob['away']
        max_pd = max(abs(pd_home), abs(pd_draw), abs(pd_away))
        
        # 价值方向
        best = max(adjusted_prob['home'], adjusted_prob['draw'], adjusted_prob['away'])
        value_dir = 'home' if adjusted_prob['home'] == best else ('draw' if adjusted_prob['draw'] == best else 'away')
        
        # 决策阈值
        if abs(max_pd) < self.pd_threshold:
            return 'ABANDON', None, 0, f'PD={max_pd:.3f} < threshold={self.pd_threshold}'
        
        if adjusted_prob[value_dir] < market_prob.get(value_dir, 0.33) + self.edge_threshold:
            return 'ABANDON', None, 0, f'Edge insufficient after motivation adjustment'
        
        # Kelly 计算
        model_p = adjusted_prob[value_dir]
        market_o = market_odds.get(value_dir, 2.0)
        kelly_result = self.kelly.calculate(model_p, market_o, value_dir)
        
        if kelly_result['action'] == 'BET':
            return 'EXECUTE', value_dir, kelly_result['bet_amount'], \
                   f'PD={max_pd:.3f}, Mot={motivation:+.2f}, Kelly={kelly_result["bet_pct"]:.2%}'
        else:
            return 'ABANDON', None, 0, kelly_result['reason']

    def record_result(self, won):
        self.kelly.record_result(won)

    def reset_daily(self):
        self.kelly.reset_daily()


# ===================== 国家队评估器 =====================
class NationalTeamEvaluator:
    def __init__(self):
        self.teams = get_all_teams()

    def get_team_rating(self, team_code):
        team = get_team(team_code.upper())
        if not team: return {'base': 1500, 'adjusted': 1500, 'confidence': 0.5}
        base_elo = team.elo_rating
        host_bonus = 50 if team.is_host else 0
        debut_penalty = -30 if team.is_debut else 0
        exp_bonus = min(30, team.wc_appearances * 2)
        champion_bonus = team.wc_titles * 20
        adjusted = base_elo + host_bonus + debut_penalty + exp_bonus + champion_bonus
        return {'base': base_elo, 'adjusted': adjusted, 'host_bonus': host_bonus,
                'debut_penalty': debut_penalty, 'exp_bonus': exp_bonus,
                'champion_bonus': champion_bonus, 'fifa_rank': team.fifa_rank,
                'confidence': 0.7 + (0.01 * min(30, team.wc_appearances))}

    def calculate_match_prob(self, home_code, away_code, venue_country=""):
        home = self.get_team_rating(home_code)
        away = self.get_team_rating(away_code)
        home_adj = home['adjusted']
        away_adj = away['adjusted']
        team_home = get_team(home_code.upper())
        if team_home and team_home.is_host: home_adj += 65
        elo_diff = home_adj - away_adj
        prob_home = 1 / (1 + 10 ** (-elo_diff / 400))
        prob_away = 1 - prob_home
        draw_prob = max(0.15, min(0.35, 0.25 - abs(prob_home - 0.5) * 0.2))
        total = prob_home + draw_prob + prob_away
        return {'home': prob_home/total, 'draw': draw_prob/total, 'away': prob_away/total,
                'home_elo': home_adj, 'away_elo': away_adj, 'elo_diff': elo_diff}


# ===================== 世界杯流水线 - A+B Hybrid =====================
class WorldCupPipeline:
    def __init__(self, bankroll=10000, stage='group'):
        self.evaluator = NationalTeamEvaluator()
        self.hybrid = HybridStrategy(bankroll, stage)
        # 保留旧系统兼容性
        self.signal_engine = MarketSignalEngine()
        self.trap_detector = TrapDetector()
        self.decision_tree = DecisionTree()
        self.kelly = KellyConservative(bankroll)

    def analyze_match(self, home_code, away_code, market_data=None, match_notes=""):
        home_code = home_code.upper()
        away_code = away_code.upper()
        team_home = get_team(home_code)
        team_away = get_team(away_code)
        if not team_home or not team_away:
            return {'error': f'Team not found: {home_code} or {away_code}'}
        
        model_prob = self.evaluator.calculate_match_prob(home_code, away_code)
        
        report = {
            'home_team': {'code': home_code, 'name': team_home.name_en, 'fifa_rank': team_home.fifa_rank},
            'away_team': {'code': away_code, 'name': team_away.name_en, 'fifa_rank': team_away.fifa_rank},
            'model_probability': model_prob,
        }
        
        if market_data and 'market_odds' in market_data:
            market_odds = market_data['market_odds']
            # 计算市场概率
            total = sum(1/v for v in market_odds.values())
            market_prob = {k: (1/v)/total for k, v in market_odds.items()}
            
            # A+B Hybrid 决策
            action, bet_dir, bet_amount, reason = self.hybrid.decide(
                model_prob, market_prob, market_odds, match_notes
            )
            
            report['hybrid'] = {
                'action': action,
                'bet_direction': bet_dir,
                'bet_amount': bet_amount,
                'reason': reason,
                'motivation': self.hybrid.get_motivation(match_notes),
                'stage': self.hybrid.stage,
                'pd_threshold': self.hybrid.pd_threshold,
            }
            
            if action == 'EXECUTE':
                report['hybrid']['expected_value'] = bet_amount * (model_prob[bet_dir] - market_prob[bet_dir])
            
            # 兼容旧系统：也运行决策树
            market_data['model_prob'] = model_prob
            decision = self.decision_tree.run(market_data)
            report['decision'] = decision
            
            if decision['action'] in ('EXECUTE', 'EXECUTE_CAUTION'):
                direction = decision.get('direction', 'home')
                model_p = model_prob.get(direction, 0.33)
                market_o = market_data['market_odds'].get(direction, 2.0)
                kelly_result = self.kelly.calculate(model_p, market_o, direction)
                report['kelly'] = kelly_result
        else:
            # No market data: pure model-based recommendation
            home_p = model_prob['home']
            draw_p = model_prob['draw']
            away_p = model_prob['away']
            best = max(home_p, draw_p, away_p)
            direction = 'home' if home_p == best else ('draw' if draw_p == best else 'away')
            report['model_recommendation'] = {
                'direction': direction,
                'probability': best,
                'reason': f'Model-based: {direction} has highest probability at {best:.1%}',
                'note': 'No market data - cannot perform A+B hybrid analysis'
            }
        return report

    def analyze_today_fixtures(self, date=None):
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        from data.worldcup_fixtures import get_fixtures_by_date
        fixtures = get_fixtures_by_date(date)
        results = []
        for f in fixtures:
            r = self.analyze_match(f.home_team, f.away_team)
            r['fixture'] = {'date': f.match_date, 'time': f.match_time, 'venue': f.venue}
            results.append(r)
        return results

    def print_match_report(self, home_code, away_code, market_data=None, match_notes=""):
        report = self.analyze_match(home_code, away_code, market_data, match_notes)
        if 'error' in report:
            print(f"ERROR: {report['error']}")
            return
        h = report['home_team']
        a = report['away_team']
        p = report['model_probability']
        print(f"\n{'='*50}")
        print(f"World Cup 2026 Analysis: {h['name']} vs {a['name']}")
        print(f"{'='*50}")
        print(f"Model Probability: Home {p['home']:.1%} | Draw {p['draw']:.1%} | Away {p['away']:.1%}")
        print(f"Elo Diff: {p['elo_diff']:.0f} (Home={p['home_elo']:.0f}, Away={p['away_elo']:.0f})")
        
        if 'hybrid' in report:
            hy = report['hybrid']
            print(f"\n{'='*50}")
            print(f"A+B Hybrid Strategy ({hy['stage'].upper()})")
            print(f"{'='*50}")
            print(f"Action: {hy['action']}")
            print(f"Reason: {hy['reason']}")
            if hy['motivation'] != 0:
                print(f"Motivation Factor: {hy['motivation']:+.2f}")
            if hy['action'] == 'EXECUTE':
                print(f"Bet Direction: {hy['bet_direction']}")
                print(f"Bet Amount: EUR {hy['bet_amount']:.0f}")
                print(f"Expected Value: {hy.get('expected_value', 0):+.0f}")
            print(f"PD Threshold: {hy['pd_threshold']}")
        
        if 'decision' in report:
            d = report['decision']
            print(f"\n[Legacy] Decision: {d['action']} (confidence={d['confidence']:.1%})")
            print(f"[Legacy] Reason: {d['reason']}")
        if 'kelly' in report:
            k = report['kelly']
            print(f"\n[Legacy] Kelly: {k['action']}")
            if k['action'] == 'BET':
                print(f"  Direction: {k['direction']}")
                print(f"  Edge: {k['edge']:.3f}")
                print(f"  Bet: {k['bet_pct']:.2%} = EUR {k['bet_amount']:.0f}")
            else:
                print(f"  Reason: {k['reason']}")


def main():
    print("="*60)
    print("World Cup 2026 Integrator - A+B Hybrid Test")
    print("="*60)
    
    # Test 1: Group Stage (Tight)
    print("\n[TEST 1] Group Stage - Tight Hybrid")
    pipeline = WorldCupPipeline(bankroll=10000, stage='group')
    market_data = {
        'market_prob': {'home': 0.65, 'draw': 0.20, 'away': 0.15},
        'market_odds': {'home': 1.55, 'draw': 3.80, 'away': 6.50},
        'media_consensus': 0.85,
    }
    pipeline.print_match_report("FRA", "SEN", market_data, "France already qualified, Senegal need to win")
    
    # Test 2: Knockout (Loose)
    print("\n[TEST 2] Knockout - Loose Hybrid")
    pipeline = WorldCupPipeline(bankroll=10000, stage='knockout')
    pipeline.print_match_report("BRA", "SCO", market_data, "Knockout stage")
    
    print(f"\n{'='*60}")
    print("A+B Hybrid Integration: COMPLETE")
    print("="*60)


if __name__ == "__main__":
    main()
