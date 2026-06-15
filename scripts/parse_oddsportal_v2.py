#!/usr/bin/env python3
"""
Football Quant OS - OddsPortal Data Parser v2

Parse OddsPortal data into structured features for model training
Based on actual raw text structure from scrape_oddsportal.py
"""

import json
import re
from typing import Dict, List, Any
from pathlib import Path


def parse_oddsportal_v2(raw_text: str) -> Dict[str, Any]:
    """
    Parse OddsPortal raw text into structured features
    
    Args:
        raw_text: Raw text from OddsPortal scrape
    
    Returns:
        Structured features including recent form, trends, and odds
    """
    result = {
        'match': None,
        'recent_form': {'home': {}, 'away': {}},
        'trends': {'over_25': {}, 'btts': {}, 'form': {}},
        'odds': {'1x2': {}, 'over_under': {}},
        'h2h': []
    }
    
    lines = raw_text.split('\n')
    
    # Extract match name
    for i, line in enumerate(lines):
        if line and ' - ' in line and not line.startswith('http'):
            # Check if it's a match title (e.g., "Bayern Munich - PSG")
            if not any(x in line for x in ['Home', 'Football', 'Europe', 'Champions League']):
                result['match'] = line.strip()
                break
    
    # Extract recent form trends
    for i, line in enumerate(lines):
        if 'Last Matches' in line:
            # Pattern: "Team won - X/5 Last Matches" or "Team won - X/5 Last Matches"
            match = re.search(r'([\w\s]+) won\s*-\s*(\d)/(\d)\s*Last Matches', line)
            if match:
                team = match.group(1).strip()
                wins = int(match.group(2))
                total = int(match.group(3))
                
                if 'home' not in result['recent_form'] or not result['recent_form']['home']:
                    result['recent_form']['home'] = {'team': team, 'wins': wins, 'total': total}
                else:
                    result['recent_form']['away'] = {'team': team, 'wins': wins, 'total': total}
    
    # Extract Over 2.5 trends
    for i, line in enumerate(lines):
        if 'Over 2.5 Goals' in line:
            match = re.search(r'([\w\s]+):\s*Over 2\.5 Goals\s*-\s*(\d)/(\d)\s*Last Matches', line)
            if match:
                team = match.group(1).strip()
                over_count = int(match.group(2))
                total = int(match.group(3))
                
                if 'home' not in result['trends']['over_25'] or not result['trends']['over_25']['home']:
                    result['trends']['over_25']['home'] = {'team': team, 'over_count': over_count, 'total': total}
                else:
                    result['trends']['over_25']['away'] = {'team': team, 'over_count': over_count, 'total': total}
    
    # Extract Both Teams to Score trends
    for i, line in enumerate(lines):
        if 'Both Teams to Score' in line:
            match = re.search(r'([\w\s]+):\s*Both Teams to Score\s*-\s*(\d)/(\d)\s*Last Matches', line)
            if match:
                team = match.group(1).strip()
                btts_count = int(match.group(2))
                total = int(match.group(3))
                
                if 'home' not in result['trends']['btts'] or not result['trends']['btts']['home']:
                    result['trends']['btts']['home'] = {'team': team, 'btts_count': btts_count, 'total': total}
                else:
                    result['trends']['btts']['away'] = {'team': team, 'btts_count': btts_count, 'total': total}
    
    # Extract 1X2 odds (decimal format from bookmakers)
    odds_section = False
    bookmaker_odds = []
    for i, line in enumerate(lines):
        if 'Bookmakers' in line:
            odds_section = True
        if odds_section and line in ['1', 'X', '2']:
            if i+1 < len(lines) and re.match(r'[+-]?\d+', lines[i+1]):
                odds_val = lines[i+1]
                bookmaker_odds.append({
                    'type': line,
                    'odds': odds_val
                })
    
    if bookmaker_odds:
        result['odds']['1x2'] = bookmaker_odds
    
    # Extract 1X2 predictions from user/community
    for i, line in enumerate(lines):
        if 'User Predictions' in line:
            if i+3 < len(lines):
                try:
                    home_pct = int(lines[i+1].replace('%', ''))
                    draw_pct = int(lines[i+2].replace('%', ''))
                    away_pct = int(lines[i+3].replace('%', ''))
                    result['trends']['form']['user_predictions'] = {
                        'home': home_pct,
                        'draw': draw_pct,
                        'away': away_pct
                    }
                except:
                    pass
    
    return result


def extract_training_features(parsed_data: Dict) -> Dict[str, float]:
    """
    Extract numerical features from parsed OddsPortal data for model training
    
    Returns features compatible with XGBoost training pipeline
    """
    features = {}
    
    # Recent form features
    home_form = parsed_data['recent_form'].get('home', {})
    if home_form and home_form.get('total', 0) > 0:
        features['home_recent_win_rate'] = home_form.get('wins', 0) / home_form['total']
    else:
        features['home_recent_win_rate'] = 0.5
    
    away_form = parsed_data['recent_form'].get('away', {})
    if away_form and away_form.get('total', 0) > 0:
        features['away_recent_win_rate'] = away_form.get('wins', 0) / away_form['total']
    else:
        features['away_recent_win_rate'] = 0.5
    
    # Over 2.5 trends
    home_over = parsed_data['trends'].get('over_25', {}).get('home', {})
    if home_over and home_over.get('total', 0) > 0:
        features['home_over_25_rate'] = home_over.get('over_count', 0) / home_over['total']
    else:
        features['home_over_25_rate'] = 0.5
    
    away_over = parsed_data['trends'].get('over_25', {}).get('away', {})
    if away_over and away_over.get('total', 0) > 0:
        features['away_over_25_rate'] = away_over.get('over_count', 0) / away_over['total']
    else:
        features['away_over_25_rate'] = 0.5
    
    # BTTS trends
    home_btts = parsed_data['trends'].get('btts', {}).get('home', {})
    if home_btts and home_btts.get('total', 0) > 0:
        features['home_btts_rate'] = home_btts.get('btts_count', 0) / home_btts['total']
    else:
        features['home_btts_rate'] = 0.5
    
    away_btts = parsed_data['trends'].get('btts', {}).get('away', {})
    if away_btts and away_btts.get('total', 0) > 0:
        features['away_btts_rate'] = away_btts.get('btts_count', 0) / away_btts['total']
    else:
        features['away_btts_rate'] = 0.5
    
    # User predictions (crowd wisdom)
    user_pred = parsed_data['trends'].get('form', {}).get('user_predictions', {})
    if user_pred:
        features['crowd_home_prob'] = user_pred.get('home', 33) / 100.0
        features['crowd_draw_prob'] = user_pred.get('draw', 33) / 100.0
        features['crowd_away_prob'] = user_pred.get('away', 33) / 100.0
    else:
        features['crowd_home_prob'] = 0.33
        features['crowd_draw_prob'] = 0.33
        features['crowd_away_prob'] = 0.34
    
    # Odds implied probabilities (if available)
    odds_1x2 = parsed_data.get('odds', {}).get('1x2', [])
    if odds_1x2:
        # Try to get average odds
        home_odds = [float(o['odds']) for o in odds_1x2 if o['type'] == '1' and re.match(r'\d+\.?\d*', o['odds'])]
        if home_odds:
            features['avg_home_odds'] = sum(home_odds) / len(home_odds)
    
    return features


def parse_oddsportal_file(file_path: str) -> Dict:
    """Parse OddsPortal JSON file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    raw_text = data.get('raw_text', '')
    parsed = parse_oddsportal_v2(raw_text)
    features = extract_training_features(parsed)
    
    return {
        'parsed': parsed,
        'features': features,
        'match': data.get('match', 'Unknown')
    }


def main():
    """Test parsing"""
    import os
    
    data_file = 'D:/openclaw-workspace/football_quant_os/data/oddsportal_bayern_psg.json'
    
    if not os.path.exists(data_file):
        print("No OddsPortal data found")
        return
    
    result = parse_oddsportal_file(data_file)
    
    print("=" * 60)
    print("OddsPortal Data Parser v2")
    print("=" * 60)
    
    print(f"\nMatch: {result['match']}")
    print(f"Parsed: {result['parsed']}")
    
    print(f"\nTraining Features:")
    for key, value in result['features'].items():
        print(f"  {key}: {value:.3f}")
    
    return result


if __name__ == '__main__':
    main()
