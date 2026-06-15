#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 组合投注推荐集成器
Version: 5.1.0
自动从预测结果中提取有价值的投注，生成组合推荐
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from combination_betting import recommend_combinations, format_recommendations
from typing import List, Dict, Any


def extract_value_bets_from_predictions(predictions: List[Dict]) -> List[Dict]:
    """
    从多场比赛预测结果中提取有价值的投注
    
    Args:
        predictions: 多场比赛的预测结果列表
        
    Returns:
        有价值的投注列表
    """
    value_bets = []
    
    for pred in predictions:
        home = pred.get('home', 'Home')
        away = pred.get('away', 'Away')
        match_date = pred.get('match_date', '2026-06-15')
        league = pred.get('league', '世界杯')
        
        # 1X2 市场
        if '1x2' in pred:
            for outcome in ['home', 'draw', 'away']:
                edge = pred['1x2'].get(f'{outcome}_edge', 0)
                if edge > 0.03:
                    odds = pred['1x2'].get(f'{outcome}_odds', 2.0)
                    prob = pred['1x2'].get(f'{outcome}_prob', 0.33)
                    selection_map = {'home': f'{home}胜', 'draw': '平局', 'away': f'{away}胜'}
                    value_bets.append({
                        'home': home, 'away': away,
                        'market': '1x2',
                        'selection': selection_map.get(outcome, outcome),
                        'odds': odds, 'probability': prob, 'edge': edge,
                        'match_date': match_date, 'league': league
                    })
        
        # 让球市场
        if 'asian_handicap' in pred:
            ah = pred['asian_handicap']
            edge = ah.get('edge', 0)
            if edge > 0.03:
                selection = ah.get('recommendation', '让球推荐')
                odds = ah.get('odds', 1.90)
                prob = ah.get('probability', 0.50)
                value_bets.append({
                    'home': home, 'away': away,
                    'market': 'asian_handicap',
                    'selection': selection,
                    'odds': odds, 'probability': prob, 'edge': edge,
                    'match_date': match_date, 'league': league
                })
        
        # 大小球市场
        if 'over_under' in pred:
            ou = pred['over_under']
            edge = ou.get('edge', 0)
            if edge > 0.02:
                selection = ou.get('recommendation', '大小球推荐')
                odds = ou.get('odds', 1.90)
                prob = ou.get('probability', 0.50)
                value_bets.append({
                    'home': home, 'away': away,
                    'market': 'over_under',
                    'selection': selection,
                    'odds': odds, 'probability': prob, 'edge': edge,
                    'match_date': match_date, 'league': league
                })
    
    return value_bets


def generate_combination_report(predictions: List[Dict], 
                                 bankroll: float = 10000,
                                 risk_level: str = "conservative") -> Dict[str, Any]:
    """
    生成完整的组合投注报告
    
    Args:
        predictions: 多场比赛预测结果
        bankroll: 资金池
        risk_level: 风险等级
        
    Returns:
        包含组合推荐和报告的字典
    """
    # 提取有价值的投注
    value_bets = extract_value_bets_from_predictions(predictions)
    
    if not value_bets:
        return {
            'status': 'no_value_bets',
            'message': '没有找到有价值的投注，无法生成组合推荐',
            'recommendations': {}
        }
    
    # 生成组合推荐
    recommendations = recommend_combinations(value_bets, bankroll=bankroll, risk_level=risk_level)
    
    # 格式化输出
    report = format_recommendations(recommendations)
    
    return {
        'status': 'success',
        'value_bets_count': len(value_bets),
        'recommendations': recommendations,
        'report': report,
        'bankroll': bankroll,
        'risk_level': risk_level
    }


# ====================== 示例用法 ======================
if __name__ == "__main__":
    # 模拟多场比赛预测结果
    sample_predictions = [
        {
            'home': '瑞典', 'away': '突尼斯',
            'match_date': '2026-06-15', 'league': '世界杯',
            '1x2': {
                'home_odds': 1.72, 'draw_odds': 3.45, 'away_odds': 4.47,
                'home_prob': 0.316, 'draw_prob': 0.407, 'away_prob': 0.277,
                'home_edge': -0.265, 'draw_edge': 0.188, 'away_edge': 0.053
            },
            'asian_handicap': {
                'recommendation': '突尼斯+0.75',
                'odds': 1.93, 'probability': 0.65, 'edge': 0.08
            },
            'over_under': {
                'recommendation': '小球2/2.5',
                'odds': 0.88, 'probability': 0.61, 'edge': 0.08
            }
        },
        {
            'home': '科特迪瓦', 'away': '厄瓜多尔',
            'match_date': '2026-06-15', 'league': '世界杯',
            '1x2': {
                'home_odds': 2.53, 'draw_odds': 3.05, 'away_odds': 2.93,
                'home_prob': 0.242, 'draw_prob': 0.443, 'away_prob': 0.315,
                'home_edge': -0.153, 'draw_edge': 0.172, 'away_edge': 0.033
            },
            'asian_handicap': {
                'recommendation': '厄瓜多尔+0.25',
                'odds': 1.85, 'probability': 0.65, 'edge': 0.11
            }
        },
        {
            'home': '荷兰', 'away': '日本',
            'match_date': '2026-06-15', 'league': '世界杯',
            '1x2': {
                'home_odds': 1.92, 'draw_odds': 3.55, 'away_odds': 3.73,
                'home_prob': 0.45, 'draw_prob': 0.30, 'away_prob': 0.25,
                'home_edge': -0.03, 'draw_edge': 0.05, 'away_edge': 0.02
            }
        }
    ]
    
    # 生成组合推荐
    result = generate_combination_report(sample_predictions, bankroll=10000)
    
    print("=" * 60)
    print("组合投注推荐报告")
    print("=" * 60)
    print(f"\n有价值的投注数量: {result['value_bets_count']}")
    print(f"资金池: {result['bankroll']}")
    print(f"风险等级: {result['risk_level']}")
    
    if result['status'] == 'success':
        print("\n" + result['report'])
    else:
        print(f"\n{result['message']}")
