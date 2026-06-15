#!/usr/bin/env python3
"""IntelligenceAgent Demo - English Output"""
import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from agents.intelligence import IntelligenceAgent, IntelCategory

agent = IntelligenceAgent()
match_id = 'USA_PAR_20260613'

# Add 6 intelligence items
agent.add_intelligence(match_id, 'club_website', 
    'Captain Christian Pulisic is fit and ready. Confirmed in starting XI.', 
    IntelCategory.INJURY, related_players=['Pulisic'])

agent.add_intelligence(match_id, 'espn', 
    'USA team showing excellent form. High motivation for home opener.', 
    IntelCategory.FORM)

agent.add_intelligence(match_id, 'twitter', 
    'Rumor: Multiple players have locker room conflict after friendly loss.', 
    IntelCategory.LOCKER_ROOM)

agent.add_intelligence(match_id, 'opta', 
    'USA xG last 5 matches: 1.8, 2.1, 1.5, 2.3, 1.9. Average: 1.92', 
    IntelCategory.FORM)

agent.add_intelligence(match_id, 'transfermarkt', 
    'Paraguay key defender suspended for yellow cards.', 
    IntelCategory.SUSPENSION)

agent.add_intelligence(match_id, 'weibo', 
    'Heavy rain expected in LA. 80% precipitation.', 
    IntelCategory.WEATHER)

intel = agent.get_match_intelligence(match_id)

print("=" * 60)
print("     IntelligenceAgent - Pre-Match Briefing")
print("     Match: USA vs Paraguay | 2026 World Cup Group A")
print("=" * 60)
print()
print("[INTELLIGENCE SUMMARY]")
print(f"  Total Items: {intel['total_intelligence']}")
print(f"  Avg Confidence: {intel['avg_confidence']*100:.0f}%")
print(f"  Data Freshness: {intel['data_freshness_hours']:.1f} hours ago")
print()
print("[IMPACT ASSESSMENT]")
print(f"  Net Impact: {intel['net_impact']:+.1%} ({intel['impact_description']})")
print(f"  Risk Level: {intel['risk_level'].upper()}")
print()
print("[RISK EVENTS]")
if intel['risk_events']:
    for risk in intel['risk_events']:
        print(f"  !! {risk['trigger']} [{risk['severity'].upper()}]")
        print(f"     Action: {risk['recommended_action']}")
else:
    print("  No risk events detected")
print()
print("[CATEGORY BREAKDOWN]")
for cat, count in intel['by_category'].items():
    print(f"  {cat}: {count} items")
print()
print(f"[RECOMMENDATION]")
print(f"  {intel['recommendation']}")
print()
print("[TOP 5 INTELLIGENCE ITEMS]")
for i, item in enumerate(intel['top_intelligence'], 1):
    print(f"  {i}. [{item['tier']}] {item['source']}")
    print(f"     Content: {item['content']}")
    print(f"     Impact: {item['impact']:+.1%} | Confidence: {item['confidence']*100:.0f}% | Weighted: {item['weighted_score']}")
    print()
print("=" * 60)

print("\n[WEIGHTED SCORE EXPLANATION]")
print("  Formula: Tier Weight x Reliability x Confidence x Time Decay")
print("  Example - Club Website (Tier 1):")
print("    1.0 (Tier 1) x 0.9 (Reliability) x 1.0 (Confidence) x 1.0 (Fresh) = 0.9")
print("  Example - Twitter/X (Tier 4):")
print("    0.4 (Tier 4) x 0.4 (Reliability) x 0.4 (Confidence) x 1.0 (Fresh) = 0.064")
print()
print("[RISK TRIGGER LOGIC]")
print("  key_player_injured  -> Confidence > 70% + key words -> HIGH")
print("  multiple_injuries   -> Confidence > 60% + count words -> CRITICAL")
print("  coach_sacked        -> Confidence > 80% + sack words -> CRITICAL")
print("  locker_room_crisis  -> Confidence > 60% + conflict words -> HIGH")
print("  betting_anomaly     -> Confidence > 50% + surge words -> MEDIUM")
print("  lineup_leak         -> Confidence > 70% + leak words -> MEDIUM")
print("  weather_extreme     -> Confidence > 60% + storm words -> MEDIUM")
