#!/usr/bin/env python3
"""
Football Quant OS - OddsPortal Data Parser

Parse OddsPortal H2H data into structured features for training
"""

import json
import re
from typing import Dict, List, Any
from pathlib import Path


def parse_oddsportal_data(raw_data: Dict) -> Dict[str, Any]:
    """
    Parse OddsPortal raw data into structured features
    
    Returns:
        {
            'h2h': {...},
            'recent_form': {...},
            'odds': {...},
            'trends': {...}
        }
    """
    text = raw_data.get('raw_text', '')
    result = {
        'h2h': {'matches': [], 'home_wins': 0, 'away_wins': 0, 'draws': 0},
        'recent_form': {'home': [], 'away': []},
        'odds': {'1x2': {}, 'over_under': {}, 'ah': {}},
        'trends': {'btts': {}, 'over_25': {}, 'form': {}}
    }
    
    # Parse H2H Results section
    h2h_section = extract_section(text, 'H2H Results', 'Show more|Bayern Munich vs PSG')
    if h2h_section:
        h2h_matches = parse_h2h_matches(h2h_section)
        result['h2h']['matches'] = h2h_matches
        result['h2h']['total'] = len(h2h_matches)
    
    # Parse Previous Matches - Home
    home_section = extract_section(text, 'Previous Matches: Bayern Munich', 'Previous Matches: PSG')
    if home_section:
        result['recent_form']['home'] = parse_recent_matches(home_section)
    
    # Parse Previous Matches - Away
    away_section = extract_section(text, 'Previous Matches: PSG', 'H2H Results')
    if away_section:
        result['recent_form']['away'] = parse_recent_matches(away_section)
    
    # Parse Match Facts / Trends
    trends_section = extract_section(text, 'Match Facts', 'Previous Matches:')
    if trends_section:
        result['trends'] = parse_trends(trends_section)
    
    # Parse Odds
    odds_section = extract_section(text, '1X2', 'Match Facts')
    if odds_section:
        result['odds'] = parse_odds(odds_section)
    
    return result


def extract_section(text: str, start_marker: str, end_marker: str) -> str:
    """Extract section between markers"""
    start = text.find(start_marker)
    if start == -1:
        return None
    
    end = text.find(end_marker, start + len(start_marker))
    if end == -1:
        end = len(text)
    
    return text[start:end]


def parse_h2h_matches(text: str) -> List[Dict]:
    """Parse H2H match records"""
    matches = []
    
    # Pattern: Date\nTeam1\nScore1\n–\nScore2\nTeam2
    lines = text.split('\n')
    i = 0
    while i < len(lines) - 5:
        if re.match(r'\d{2}/\w+', lines[i]):  # Date pattern
            if lines[i+2].isdigit() and lines[i+4].isdigit():
                match = {
                    'date': lines[i],
                    'home': lines[i+1],
                    'home_score': int(lines[i+2]),
                    'away_score': int(lines[i+4]),
                    'away': lines[i+5],
                    'competition': lines[i-1] if i > 0 else 'Unknown'
                }
                matches.append(match)
                i += 6
                continue
        i += 1
    
    return matches


def parse_recent_matches(text: str) -> List[Dict]:
    """Parse recent match form"""
    matches = []
    
    # Similar pattern to H2H but for single team
    lines = text.split('\n')
    i = 0
    while i < len(lines) - 5:
        if re.match(r'\d{2}/\w+', lines[i]):
            if i+3 < len(lines) and lines[i+2].isdigit():
                match = {
                    'date': lines[i],
                    'opponent': lines[i+3] if i+3 < len(lines) else 'Unknown',
                    'home_score': int(lines[i+1]) if lines[i+1].isdigit() else 0,
                    'away_score': int(lines[i+2]) if lines[i+2].isdigit() else 0,
                    'result': 'W' if int(lines[i+1]) > int(lines[i+2]) else 'L' if int(lines[i+1]) < int(lines[i+2]) else 'D'
                }
                matches.append(match)
                i += 4
                continue
        i += 1
    
    return matches


def parse_trends(text: str) -> Dict:
    """Parse match trends/facts"""
    trends = {
        'home_over_25': False,
        'away_over_25': False,
        'home_btts': False,
        'away_btts': False,
        'home_form': [],
        'away_form': []
    }
    
    # Extract Over 2.5 trends
    if 'Over 2.5 Goals' in text:
        trends['home_over_25'] = '5/5' in text or '4/5' in text
        trends['away_over_25'] = '3/5' in text or '4/5' in text
    
    # Extract BTTS trends
    if 'Both Teams To Score' in text:
        trends['home_btts'] = '5/5' in text or '4/5' in text
        trends['away_btts'] = '2/5' in text or '3/5' in text
    
    return trends


def parse_odds(text: str) -> Dict:
    """Parse odds from text"""
    odds = {'1x2': {}, 'over_under': {}, 'ah': {}}
    
    # Extract 1X2 odds (decimal format)
    decimal_pattern = r'[+-]?\d+\n([+-]?\d+)\n([+-]?\d+)\n([+-]?\d+)'
    matches = re.findall(decimal_pattern, text)
    
    if matches:
        # Try to find home, draw, away odds
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if line in ['1', 'X', '2']:
                if i+1 < len(lines) and re.match(r'[+-]?\d+', lines[i+1]):
                    odds['1x2'][line] = lines[i+1]
    
    return odds


def extract_features_from_oddsportal(oddsportal_data: Dict) -> Dict[str, Any]:
    """
    Extract training features from OddsPortal data
    
    Returns features compatible with FeatureEngineer
    """
    parsed = parse_oddsportal_data(oddsportal_data)
    
    features = {
        'source': 'oddsportal',
        'h2h': parsed['h2h'],
        'recent_form': parsed['recent_form'],
        'trends': parsed['trends'],
        'odds': parsed['odds']
    }
    
    # Calculate derived features
    home_form = parsed['recent_form']['home']
    away_form = parsed['recent_form']['away']
    
    if home_form:
        home_wins = sum(1 for m in home_form if m['result'] == 'W')
        home_goals = sum(m['home_score'] for m in home_form)
        features['home_recent_wins'] = home_wins / len(home_form)
        features['home_recent_goals'] = home_goals / len(home_form)
    
    if away_form:
        away_wins = sum(1 for m in away_form if m['result'] == 'W')
        away_goals = sum(m['away_score'] for m in away_form)
        features['away_recent_wins'] = away_wins / len(away_form)
        features['away_recent_goals'] = away_goals / len(away_form)
    
    # H2H features
    h2h = parsed['h2h']
    if h2h['matches']:
        total = len(h2h['matches'])
        home_wins = sum(1 for m in h2h['matches'] if m['home_score'] > m['away_score'])
        draws = sum(1 for m in h2h['matches'] if m['home_score'] == m['away_score'])
        features['h2h_home_win_rate'] = home_wins / total
        features['h2h_draw_rate'] = draws / total
    
    return features


def main():
    """Test parsing"""
    import os
    
    data_file = 'D:/openclaw-workspace/football_quant_os/data/oddsportal_bayern_psg.json'
    
    if not os.path.exists(data_file):
        print("No OddsPortal data found")
        return
    
    with open(data_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    print("Parsing OddsPortal data...")
    parsed = parse_oddsportal_data(raw_data)
    
    print(f"\nH2H matches: {len(parsed['h2h']['matches'])}")
    print(f"Home recent form: {len(parsed['recent_form']['home'])} matches")
    print(f"Away recent form: {len(parsed['recent_form']['away'])} matches")
    
    # Extract features
    features = extract_features_from_oddsportal(raw_data)
    
    print(f"\nExtracted features:")
    for key, value in features.items():
        if not isinstance(value, list):
            print(f"  {key}: {value}")
    
    return features


if __name__ == '__main__':
    main()
