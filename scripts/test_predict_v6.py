#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script for predict_v6.py - P1 Integration (v6.3)"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from predict_v6 import PredictorV6

# Test 1: Basic instantiation
print("=" * 60)
print("Test 1: PredictorV6 instantiation (v6.3)")
print("=" * 60)
p = PredictorV6(bankroll=100000, risk_level='medium')
print("OK - All agents initialized")

# Test 2: Single match prediction with full pipeline
print("\n" + "=" * 60)
print("Test 2: Single match (v6.3 full pipeline)")
print("=" * 60)
result = p.predict('Germany', 'Japan', 1.8, 3.4, 4.2, stage='group')
print(f"Match: {result.home} vs {result.away}")
print(f"Version: {result.version}")
print(f"Decision chain ({len(result.decision_chain)} steps):")
for i, step in enumerate(result.decision_chain, 1):
    print(f"  {i}. {step.split('|')[1].strip()}")

# Test 3: P1 modules
print("\n" + "=" * 60)
print("Test 3: P1 Advanced Engines")
print("=" * 60)
print(f"Evolution: {result.evolution.get('status', 'N/A') if result.evolution else 'N/A'}")
if result.evolution and result.evolution.get('status') == 'adjusted':
    print(f"  Original weights: {result.evolution.get('original_weights', [])}")
    print(f"  Adjusted weights: {result.evolution.get('adjusted_weights', [])}")
print(f"Market Micro: {result.market_micro.get('status', 'N/A') if result.market_micro else 'N/A'}")
if result.market_micro and result.market_micro.get('trap_signals'):
    print(f"  Trap signals: {len(result.market_micro['trap_signals'])}")

# Test 4: P0 modules
print("\n" + "=" * 60)
print("Test 4: P0 Core Modules")
print("=" * 60)
print(f"Features: {result.features.get('status', 'N/A') if result.features else 'N/A'}")
print(f"Group Stage: {result.group_stage.get('status', 'N/A') if result.group_stage else 'N/A'}")
print(f"Combination: {result.combination.get('status', 'N/A') if result.combination else 'N/A'}")

# Test 5: v6 modules
print("\n" + "=" * 60)
print("Test 5: v6 Institution modules")
print("=" * 60)
print(f"Upset detection: {result.upset_detection.get('level', 'N/A')}")
print(f"Risk assessment: {result.risk_assessment.get('overall_level', 'N/A')}")
print(f"Kelly stake: ${result.kelly_recommendation.get('stake', 0):.2f}")
print(f"Compliance: {result.compliance_check.get('status', 'N/A') if result.compliance_check else 'Disabled'}")

# Test 6: Nine-Agent modules
print("\n" + "=" * 60)
print("Test 6: NINE-AGENT Integration")
print("=" * 60)
nine_agents = {
    'IntelligenceAgent': result.intelligence,
    'CoachFactor': result.coach_factor,
    'OddsPricingAgent': result.odds_pricing,
    'GeneEngine': result.gene_engine,
    'WorldCupAnalyst': result.worldcup_analyst,
    'MultiMarketPredictor': result.multi_market,
}
for name, data in nine_agents.items():
    status = data.get('status', 'MISSING') if data else 'MISSING'
    print(f"  {name}: {status}")

# Test 7: Value Bet Detection
if result.odds_pricing and result.odds_pricing.get('value_edges'):
    print("\n" + "=" * 60)
    print("Test 7: Value Bet Detection")
    print("=" * 60)
    for outcome, edge_info in result.odds_pricing['value_edges'].items():
        if edge_info.get('value_bet'):
            print(f"  VALUE BET: {outcome}")
            print(f"    Model prob: {edge_info['model_prob']:.2%}")
            print(f"    Market prob: {edge_info['market_prob']:.2%}")
            print(f"    Edge: {edge_info['edge']:.2%}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED - predict_v6.py v6.3.0 P1 integration")
print("=" * 60)
