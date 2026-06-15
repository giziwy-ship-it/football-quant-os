#!/usr/bin/env python3
"""
Football Quant OS - Training Data Generator

Generate training data for Over/Under prediction models
Combines historical data + features + labels
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from typing import List, Dict, Any
from features.feature_engineer import FeatureEngineer
from data.data_fetcher import DataFetcherFactory, get_multi_source_fetcher


def generate_training_dataset(
    sources: List[str] = None,
    tournament: str = 'worldcup',
    years: List[int] = None,
    output_file: str = None
) -> List[Dict[str, Any]]:
    """
    Generate training dataset from multiple sources
    
    Args:
        sources: List of data sources ['kaggle', 'football_data', 'api_football']
        tournament: Tournament name
        years: List of years to include
        output_file: Path to save JSON output
    
    Returns:
        List[Dict]: Training samples with features and labels
    """
    if sources is None:
        sources = ['kaggle']
    if years is None:
        years = [2022]
    
    print("=" * 60)
    print("Training Data Generator")
    print("=" * 60)
    
    all_matches = []
    
    # Collect data from all sources
    for source in sources:
        try:
            print(f"\nFetching from {source}...")
            fetcher = DataFetcherFactory.create(source)
            
            for year in years:
                matches = fetcher.fetch_matches(tournament=tournament, year=year)
                if matches and 'error' not in matches[0]:
                    all_matches.extend(matches)
                    print(f"  {year}: {len(matches)} matches")
                else:
                    print(f"  {year}: No data or error")
        except Exception as e:
            print(f"  Error: {e}")
    
    if not all_matches:
        print("\nNo historical data available. Using mock data.")
        all_matches = [
            {'home': 'Germany', 'away': 'Japan', 'home_score': 1, 'away_score': 2, 'home_xg': 2.3, 'away_xg': 0.8},
            {'home': 'Spain', 'away': 'Costa Rica', 'home_score': 7, 'away_score': 0, 'home_xg': 4.5, 'away_xg': 0.3},
            {'home': 'Brazil', 'away': 'Serbia', 'home_score': 2, 'away_score': 0, 'home_xg': 2.8, 'away_xg': 0.5},
            {'home': 'Germany', 'away': 'Spain', 'home_score': 1, 'away_score': 1, 'home_xg': 1.2, 'away_xg': 1.8},
            {'home': 'Japan', 'away': 'Spain', 'home_score': 2, 'away_score': 1, 'home_xg': 1.5, 'away_xg': 2.0},
        ] * 10  # Repeat to have enough data
    
    print(f"\nTotal matches: {len(all_matches)}")
    
    # Build features
    print("\nBuilding feature engineering...")
    engineer = FeatureEngineer(all_matches)
    
    print("Generating training samples...")
    training_data = engineer.build_training_data(lookback=5)
    
    print(f"Generated {len(training_data)} training samples")
    
    # Feature statistics
    if training_data:
        overs_25 = sum(1 for s in training_data if s['label']['over_2_5'] == 1)
        overs_15 = sum(1 for s in training_data if s['label']['over_1_5'] == 1)
        
        print(f"\nLabel distribution:")
        print(f"  Over 2.5: {overs_25}/{len(training_data)} ({100*overs_25/len(training_data):.1f}%)")
        print(f"  Over 1.5: {overs_15}/{len(training_data)} ({100*overs_15/len(training_data):.1f}%)")
        
        avg_goals = sum(s['label']['total_goals'] for s in training_data) / len(training_data)
        print(f"  Avg total goals: {avg_goals:.2f}")
    
    # Save to file
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(training_data, f, indent=2, ensure_ascii=False)
        
        print(f"\nSaved to: {output_path}")
    
    print("\n" + "=" * 60)
    print("Training data generation complete!")
    print("=" * 60)
    
    return training_data


if __name__ == '__main__':
    # Generate with Kaggle data (if available)
    data = generate_training_dataset(
        sources=['kaggle'],
        years=[2022],
        output_file='D:/openclaw-workspace/football_quant_os/data/training/ou_training_data.json'
    )
