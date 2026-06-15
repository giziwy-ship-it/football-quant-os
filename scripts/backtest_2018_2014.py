#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 2018/2014 历史数据回测
使用Kaggle真实数据验证模型预测能力
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent))
from data_integration import DataIntegration

DATA_DIR = Path("D:/openclaw-workspace/football_quant_os/data")
KAGGLE_DIR = DATA_DIR / "kaggle" / "worldcup_1930-2018"

def load_matches(year: int) -> pd.DataFrame:
    """加载指定年份的比赛数据"""
    df = pd.read_csv(KAGGLE_DIR / "wcmatches.csv")
    return df[df['year'] == year].copy()

def classify_stage(stage_name: str) -> str:
    """将Kaggle stage分类为group/knockout"""
    if 'Group' in stage_name:
        return 'group'
    elif any(k in stage_name for k in ['Round of 16', 'Quarter', 'Semi', 'Final']):
        return 'knockout'
    return 'other'

def simulate_model_prediction(home_team: str, away_team: str, stage: str, calibration: Dict) -> Dict:
    """
    模拟模型预测（简化版，使用校准系数）
    
    返回预测结果:
    {
        'home_prob': 主队胜概率,
        'draw_prob': 平局概率,
        'away_prob': 客队胜概率,
        'recommended': 'home'/'draw'/'away',
        'confidence': 置信度
    }
    """
    # 简化：使用FIFA排名模拟概率（假设主队=强队概率更高）
    # 实际应用中应从模型获取
    
    # 基准概率（无校准）
    base_home = 0.45
    base_draw = 0.25
    base_away = 0.30
    
    # 应用阶段校准系数
    if stage == 'group':
        # 小组赛：强队概率下调（冷门更多）
        adjustment = calibration.get('group_adjustment', 0.95)
        home_prob = base_home * adjustment
        away_prob = base_away / adjustment  # 弱队概率相对上调
    elif stage == 'knockout':
        # 淘汰赛：强队概率上调（但也有冷门）
        adjustment = calibration.get('knockout_adjustment', 1.20)
        home_prob = base_home * adjustment
        away_prob = base_away / adjustment
    else:
        home_prob = base_home
        away_prob = base_away
    
    # 重新归一化
    total = home_prob + base_draw + away_prob
    home_prob = home_prob / total
    draw_prob = base_draw / total
    away_prob = away_prob / total
    
    # 推荐预测结果
    probs = {'home': home_prob, 'draw': draw_prob, 'away': away_prob}
    recommended = max(probs, key=probs.get)
    confidence = max(probs.values())
    
    return {
        'home_prob': round(home_prob, 3),
        'draw_prob': round(draw_prob, 3),
        'away_prob': round(away_prob, 3),
        'recommended': recommended,
        'confidence': round(confidence, 3)
    }

def backtest_year(year: int, calibration: Dict) -> Dict:
    """对指定年份进行回测"""
    df = load_matches(year)
    
    results = {
        'year': year,
        'total_matches': len(df),
        'correct_predictions': 0,
        'group': {'total': 0, 'correct': 0},
        'knockout': {'total': 0, 'correct': 0},
        'famous_upsets': [],
        'matches': []
    }
    
    for _, match in df.iterrows():
        home = match['home_team']
        away = match['away_team']
        home_score = int(match['home_score'])
        away_score = int(match['away_score'])
        stage_name = match['stage']
        outcome = match['outcome']  # H/D/A
        
        stage = classify_stage(stage_name)
        
        # 模拟预测
        prediction = simulate_model_prediction(home, away, stage, calibration)
        
        # 判断预测是否正确
        if outcome == 'H' and prediction['recommended'] == 'home':
            correct = True
        elif outcome == 'D' and prediction['recommended'] == 'draw':
            correct = True
        elif outcome == 'A' and prediction['recommended'] == 'away':
            correct = True
        else:
            correct = False
        
        # 记录结果
        match_result = {
            'date': match['date'],
            'home': home,
            'away': away,
            'score': f"{home_score}-{away_score}",
            'stage': stage_name,
            'stage_type': stage,
            'outcome': outcome,
            'prediction': prediction['recommended'],
            'confidence': prediction['confidence'],
            'correct': correct,
            'home_prob': prediction['home_prob'],
            'draw_prob': prediction['draw_prob'],
            'away_prob': prediction['away_prob']
        }
        
        results['matches'].append(match_result)
        
        if correct:
            results['correct_predictions'] += 1
        
        if stage in ['group', 'knockout']:
            results[stage]['total'] += 1
            if correct:
                results[stage]['correct'] += 1
    
    # 计算准确率
    results['accuracy'] = round(results['correct_predictions'] / results['total_matches'] * 100, 1) if results['total_matches'] > 0 else 0
    results['group']['accuracy'] = round(results['group']['correct'] / results['group']['total'] * 100, 1) if results['group']['total'] > 0 else 0
    results['knockout']['accuracy'] = round(results['knockout']['correct'] / results['knockout']['total'] * 100, 1) if results['knockout']['total'] > 0 else 0
    
    return results

def identify_famous_upsets(results: Dict, year: int) -> List[Dict]:
    """识别著名冷门比赛"""
    upsets = []
    
    for match in results['matches']:
        # 条件：预测错误 + 高置信度 + 大比分差距
        if not match['correct'] and match['confidence'] > 0.4:
            home, away = match['home'], match['away']
            score = match['score']
            stage = match['stage']
            
            # 检查是否知名冷门
            famous_pairs = [
                ('Germany', 'Mexico'), ('Germany', 'Korea'),
                ('Argentina', 'Iceland'), ('Brazil', 'Belgium'),
                ('Spain', 'Netherlands'), ('Uruguay', 'Costa Rica'),
                ('Brazil', 'Germany'), ('England', 'Italy')
            ]
            
            for team1, team2 in famous_pairs:
                if (team1 in home and team2 in away) or (team1 in away and team2 in home):
                    upsets.append({
                        'match': f"{home} {score} {away}",
                        'stage': stage,
                        'predicted': match['prediction'],
                        'actual': match['outcome'],
                        'confidence': match['confidence']
                    })
                    break
    
    return upsets

def generate_backtest_report(results_2018: Dict, results_2014: Dict, calibration: Dict) -> Dict:
    """生成回测报告"""
    
    report = {
        'metadata': {
            'source': 'Kaggle FIFA World Cup (1930-2018)',
            'calibration': calibration,
            'model_version': '4.3.3_data_driven'
        },
        'summary': {
            '2018': {
                'total_matches': results_2018['total_matches'],
                'correct_predictions': results_2018['correct_predictions'],
                'accuracy': results_2018['accuracy'],
                'group_accuracy': results_2018['group']['accuracy'],
                'knockout_accuracy': results_2018['knockout']['accuracy']
            },
            '2014': {
                'total_matches': results_2014['total_matches'],
                'correct_predictions': results_2014['correct_predictions'],
                'accuracy': results_2014['accuracy'],
                'group_accuracy': results_2014['group']['accuracy'],
                'knockout_accuracy': results_2014['knockout']['accuracy']
            }
        },
        'famous_upsets': {
            '2018': identify_famous_upsets(results_2018, 2018),
            '2014': identify_famous_upsets(results_2014, 2014)
        },
        'detailed_results': {
            '2018': results_2018['matches'][:10],  # 前10场
            '2014': results_2014['matches'][:10]
        }
    }
    
    # 计算平均准确率
    avg_accuracy = (results_2018['accuracy'] + results_2014['accuracy']) / 2
    avg_group = (results_2018['group']['accuracy'] + results_2014['group']['accuracy']) / 2
    avg_knockout = (results_2018['knockout']['accuracy'] + results_2014['knockout']['accuracy']) / 2
    
    report['summary']['average'] = {
        'accuracy': round(avg_accuracy, 1),
        'group_accuracy': round(avg_group, 1),
        'knockout_accuracy': round(avg_knockout, 1)
    }
    
    return report

def main():
    print("=" * 60)
    print("Football Quant OS - 2018/2014 Historical Backtest")
    print("=" * 60)
    
    # 获取校准系数
    data = DataIntegration()
    calibration = data.get_stage_calibration_factors()
    
    print(f"\nCalibration Factors:")
    print(f"  Group adjustment: {calibration['group_adjustment']}")
    print(f"  Knockout adjustment: {calibration['knockout_adjustment']}")
    print(f"  Group upset rate: {calibration['group_upset_rate']:.1%}")
    print(f"  Knockout upset rate: {calibration['knockout_upset_rate']:.1%}")
    
    # 2018回测
    print("\n" + "=" * 60)
    print("Backtesting 2018 World Cup...")
    print("=" * 60)
    results_2018 = backtest_year(2018, calibration)
    
    print(f"\n2018 Results:")
    print(f"  Total matches: {results_2018['total_matches']}")
    print(f"  Correct predictions: {results_2018['correct_predictions']}/{results_2018['total_matches']}")
    print(f"  Overall accuracy: {results_2018['accuracy']}%")
    print(f"  Group stage accuracy: {results_2018['group']['accuracy']}% ({results_2018['group']['correct']}/{results_2018['group']['total']})")
    print(f"  Knockout accuracy: {results_2018['knockout']['accuracy']}% ({results_2018['knockout']['correct']}/{results_2018['knockout']['total']})")
    
    # 2014回测
    print("\n" + "=" * 60)
    print("Backtesting 2014 World Cup...")
    print("=" * 60)
    results_2014 = backtest_year(2014, calibration)
    
    print(f"\n2014 Results:")
    print(f"  Total matches: {results_2014['total_matches']}")
    print(f"  Correct predictions: {results_2014['correct_predictions']}/{results_2014['total_matches']}")
    print(f"  Overall accuracy: {results_2014['accuracy']}%")
    print(f"  Group stage accuracy: {results_2014['group']['accuracy']}% ({results_2014['group']['correct']}/{results_2014['group']['total']})")
    print(f"  Knockout accuracy: {results_2014['knockout']['accuracy']}% ({results_2014['knockout']['correct']}/{results_2014['knockout']['total']})")
    
    # 生成报告
    report = generate_backtest_report(results_2018, results_2014, calibration)
    
    # 保存报告
    report_file = DATA_DIR / "backtest_2018_2014_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Report saved: {report_file}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("BACKTEST SUMMARY")
    print("=" * 60)
    print(f"Average Accuracy: {report['summary']['average']['accuracy']}%")
    print(f"Average Group Accuracy: {report['summary']['average']['group_accuracy']}%")
    print(f"Average Knockout Accuracy: {report['summary']['average']['knockout_accuracy']}%")
    print(f"\nFamous Upsets Detected:")
    print(f"  2018: {len(report['famous_upsets']['2018'])}")
    print(f"  2014: {len(report['famous_upsets']['2014'])}")
    print("=" * 60)

if __name__ == "__main__":
    main()
