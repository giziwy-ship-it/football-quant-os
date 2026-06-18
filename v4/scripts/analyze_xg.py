#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze 2022 World Cup xG Data"""
import pandas as pd
import json

df = pd.read_csv('D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_2022_qatar/Fifa_WC_2022_Match_data.csv', encoding='latin1')

team_stats = {}

for _, row in df.iterrows():
    t1 = str(row['1']).strip()
    t2 = str(row['2']).strip()
    
    for team, prefix in [(t1, '1'), (t2, '2')]:
        if team not in team_stats:
            team_stats[team] = {
                'matches': 0, 'xg': 0, 'xga': 0, 'poss': 0, 'attempts': 0, 'ontarget': 0,
                'goals': 0, 'goals_against': 0, 'passes': 0, 'passes_comp': 0, 'corners': 0,
                'yellow': 0, 'def_pressure': 0
            }
        
        opp_prefix = '2' if prefix == '1' else '1'
        team_stats[team]['matches'] += 1
        team_stats[team]['xg'] += row[f'{prefix}_xg']
        team_stats[team]['xga'] += row[f'{opp_prefix}_xg']
        team_stats[team]['poss'] += row[f'{prefix}_poss']
        team_stats[team]['attempts'] += row[f'{prefix}_attempts']
        team_stats[team]['ontarget'] += row[f'{prefix}_ontarget']
        team_stats[team]['goals'] += row[f'{prefix}_goals']
        team_stats[team]['goals_against'] += row[f'{opp_prefix}_goals']
        team_stats[team]['passes'] += row[f'{prefix}_passes']
        team_stats[team]['passes_comp'] += row[f'{prefix}_passes_compeletd']
        team_stats[team]['corners'] += row[f'{prefix}_corners']
        team_stats[team]['yellow'] += row[f'{prefix}_yellow_cards']
        team_stats[team]['def_pressure'] += row[f'{prefix}_defensive_pressure_applied']

for team, stats in team_stats.items():
    m = stats['matches']
    for k in stats:
        if k != 'matches':
            stats[k] = round(stats[k] / m, 2)
    # 计算净xG
    stats['xg_diff'] = round(stats['xg'] - stats['xga'], 2)

sorted_teams = sorted(team_stats.items(), key=lambda x: x[1]['xg_diff'], reverse=True)

print("2022 World Cup xG Ranking (by xG Difference):")
print(f"{'Team':20s} {'xG':>5s} {'xGA':>5s} {'Diff':>5s} {'Goals':>5s} {'GA':>5s} {'Poss':>5s} {'Shots':>5s}")
for team, s in sorted_teams:
    print(f"{team:20s} {s['xg']:>5.2f} {s['xga']:>5.2f} {s['xg_diff']:>5.2f} {s['goals']:>5.2f} {s['goals_against']:>5.2f} {s['poss']:>5.0f} {s['attempts']:>5.1f}")

# Save
with open('D:/openclaw-workspace/football_quant_os/v4/data/wc2022_xg_stats.json', 'w') as f:
    json.dump(team_stats, f, indent=2)

print("\nSaved to wc2022_xg_stats.json")
