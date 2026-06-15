#!/usr/bin/env python3
"""
Football Quant OS - Training Data Collection from Football-Data.org
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.data_fetcher import DataFetcherFactory
from features.feature_engineer import FeatureEngineer
import json

def collect_training_data():
    """Collect training data from Football-Data.org"""
    print("=" * 60)
    print("Football Quant OS - Training Data Collection")
    print("=" * 60)
    
    # Create fetcher
    fetcher = DataFetcherFactory.create('football_data_org')
    print(f"\nFetcher: {fetcher.name}")
    print(f"Supports live: {fetcher.supports_live}")
    print(f"Supports historical: {fetcher.supports_historical}")
    
    # Get available competitions
    print("\n" + "-" * 40)
    print("Available Competitions:")
    print("-" * 40)
    
    comps = fetcher.get_competitions()
    if comps and 'error' not in comps[0]:
        for c in comps:
            code = c.get('code', 'N/A')
            name = c.get('name', 'Unknown')
            print(f"  {code}: {name}")
    else:
        print("  Could not fetch competitions")
        return
    
    # Try to fetch matches from different competitions
    competitions_to_try = ['PL', 'CL', 'EC', 'ELC', 'BSA']
    all_matches = []
    
    print("\n" + "-" * 40)
    print("Fetching Matches:")
    print("-" * 40)
    
    for comp in competitions_to_try:
        try:
            matches = fetcher.fetch_matches(tournament=comp, year=2023)
            if matches and 'error' not in matches[0]:
                all_matches.extend(matches)
                print(f"  {comp}: {len(matches)} matches")
            else:
                print(f"  {comp}: No data available")
        except Exception as e:
            print(f"  {comp}: Error - {e}")
    
    print(f"\nTotal matches collected: {len(all_matches)}")
    
    if len(all_matches) < 10:
        print("\nNot enough data from API. Using local Kaggle data...")
        kaggle_fetcher = DataFetcherFactory.create('kaggle')
        kaggle_matches = kaggle_fetcher.fetch_matches(year=2022)
        if kaggle_matches and 'error' not in kaggle_matches[0]:
            all_matches = kaggle_matches
            print(f"Using {len(all_matches)} matches from Kaggle 2022")
    
    # Build features
    if all_matches:
        print("\n" + "-" * 40)
        print("Feature Engineering:")
        print("-" * 40)
        
        engineer = FeatureEngineer(all_matches)
        
        # Show team features for top teams
        teams = ['Germany', 'Japan', 'Spain', 'Brazil', 'France']
        for team in teams[:3]:
            try:
                features = engineer.extract_team_features(team)
                print(f"\n  {team}:")
                print(f"    Avg goals: {features.avg_goals_scored}")
                print(f"    Avg xG: {features.avg_xg}")
                print(f"    Attack eff: {features.attack_efficiency}")
            except:
                pass
        
        # Build training data
        print("\n" + "-" * 40)
        print("Training Data:")
        print("-" * 40)
        
        training_data = engineer.build_training_data(lookback=5)
        print(f"Generated {len(training_data)} training samples")
        
        if training_data:
            # Statistics
            overs_25 = sum(1 for s in training_data if s['label']['over_2_5'] == 1)
            overs_15 = sum(1 for s in training_data if s['label']['over_1_5'] == 1)
            avg_goals = sum(s['label']['total_goals'] for s in training_data) / len(training_data)
            
            print(f"\nLabel distribution:")
            print(f"  Over 2.5: {overs_25}/{len(training_data)} ({100*overs_25/len(training_data):.1f}%)")
            print(f"  Over 1.5: {overs_15}/{len(training_data)} ({100*overs_15/len(training_data):.1f}%)")
            print(f"  Avg goals: {avg_goals:.2f}")
            
            # Save to file
            output_file = 'D:/openclaw-workspace/football_quant_os/data/training/football_data_training.json'
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(training_data, f, indent=2, ensure_ascii=False)
            
            print(f"\nSaved to: {output_file}")
        
        return training_data
    else:
        print("\nNo data available for training")
        return []
    
    print("\n" + "=" * 60)
    print("Training data collection complete!")
    print("=" * 60)

if __name__ == '__main__':
    collect_training_data()
