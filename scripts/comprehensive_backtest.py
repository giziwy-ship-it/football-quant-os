#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 综合回测框架 v1.0
整合2018/2014/2022数据，验证模型，提取xG特征
"""

import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import sys

sys.path.insert(0, str(Path(__file__).parent))
from data_integration import DataIntegration

DATA_DIR = Path("D:/openclaw-workspace/football_quant_os/data")
KAGGLE_DIR = DATA_DIR / "kaggle"

def load_2022_data() -> pd.DataFrame:
    """加载2022卡塔尔世界杯数据"""
    df = pd.read_csv(
        KAGGLE_DIR / "worldcup_2022_qatar" / "Fifa_WC_2022_Match_data.csv",
        encoding='latin-1'
    )
    return df

def load_2018_2014_data() -> pd.DataFrame:
    """加载2018/2014数据"""
    df = pd.read_csv(KAGGLE_DIR / "worldcup_1930-2018" / "wcmatches.csv")
    return df

def classify_stage_2022(group: str) -> str:
    """分类2022比赛阶段"""
    if 'Group' in str(group):
        return 'group'
    elif any(k in str(group) for k in ['Round of 16', 'Quarter', 'Semi', 'Final', '3rd']):
        return 'knockout'
    return 'other'

def classify_stage_2018_2014(stage: str) -> str:
    """分类2018/2014比赛阶段"""
    if 'Group' in str(stage):
        return 'group'
    elif any(k in str(stage) for k in ['Round of 16', 'Quarter', 'Semi', 'Final', '3rd']):
        return 'knockout'
    return 'other'

def simulate_model_with_xg(home_xg: float, away_xg: float, home_poss: float, away_poss: float,
                           stage: str, calibration: Dict) -> Dict:
    """
    基于xG的模型预测（简化版）
    
    返回预测结果:
    {
        'home_prob': 主队胜概率,
        'draw_prob': 平局概率,
        'away_prob': 客队胜概率,
        'recommended': 'home'/'draw'/'away',
        'confidence': 置信度
    }
    """
    # 基于xG计算基础概率
    total_xg = home_xg + away_xg
    if total_xg == 0:
        base_home = 0.33
        base_away = 0.33
        base_draw = 0.34
    else:
        base_home = home_xg / total_xg * 0.8  # xG不是直接概率，需要缩放
        base_away = away_xg / total_xg * 0.8
        base_draw = 0.2  # 平局基准概率
    
    # 控球率调整（控球率高的队伍略占优）
    poss_diff = (home_poss - away_poss) / 100
    base_home += poss_diff * 0.05
    base_away -= poss_diff * 0.05
    
    # 应用阶段校准系数
    if stage == 'group':
        adjustment = calibration.get('group_adjustment', 0.95)
        # 小组赛：根据xG优势，强队概率下调
        if base_home > base_away:
            base_home *= adjustment
            base_away = base_away / adjustment if base_away > 0 else base_away
        else:
            base_away *= adjustment
            base_home = base_home / adjustment if base_home > 0 else base_home
    elif stage == 'knockout':
        adjustment = calibration.get('knockout_adjustment', 1.20)
        # 淘汰赛：强队概率上调
        if base_home > base_away:
            base_home *= adjustment
            base_away = base_away / adjustment if base_away > 0 else base_away
        else:
            base_away *= adjustment
            base_home = base_home / adjustment if base_home > 0 else base_home
    
    # 重新归一化
    total = base_home + base_draw + base_away
    home_prob = base_home / total
    draw_prob = base_draw / total
    away_prob = base_away / total
    
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

def backtest_2022(df: pd.DataFrame, calibration: Dict) -> Dict:
    """对2022进行回测"""
    results = {
        'year': 2022,
        'total_matches': len(df),
        'correct_predictions': 0,
        'group': {'total': 0, 'correct': 0},
        'knockout': {'total': 0, 'correct': 0},
        'famous_upsets': [],
        'matches': []
    }
    
    for _, match in df.iterrows():
        home = match['1']
        away = match['2']
        home_goals = int(match['1_goals'])
        away_goals = int(match['2_goals'])
        home_xg = float(match['1_xg'])
        away_xg = float(match['2_xg'])
        home_poss = float(match['1_poss'])
        away_poss = float(match['2_poss'])
        group = match['group']
        
        stage = classify_stage_2022(group)
        
        # 判断实际结果
        if home_goals > away_goals:
            actual = 'home'
        elif home_goals < away_goals:
            actual = 'away'
        else:
            actual = 'draw'
        
        # 模拟预测
        prediction = simulate_model_with_xg(home_xg, away_xg, home_poss, away_poss, stage, calibration)
        
        # 判断预测是否正确
        correct = prediction['recommended'] == actual
        
        match_result = {
            'date': match['date'],
            'home': home,
            'away': away,
            'score': f"{home_goals}-{away_goals}",
            'stage': group,
            'stage_type': stage,
            'actual': actual,
            'prediction': prediction['recommended'],
            'confidence': prediction['confidence'],
            'correct': correct,
            'home_xg': home_xg,
            'away_xg': away_xg,
            'home_poss': home_poss,
            'away_poss': away_poss
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

def backtest_2018_2014(df: pd.DataFrame, year: int, calibration: Dict) -> Dict:
    """对2018/2014进行回测（简化版，无xG）"""
    year_df = df[df['year'] == year].copy()
    
    results = {
        'year': year,
        'total_matches': len(year_df),
        'correct_predictions': 0,
        'group': {'total': 0, 'correct': 0},
        'knockout': {'total': 0, 'correct': 0},
        'matches': []
    }
    
    for _, match in year_df.iterrows():
        home = match['home_team']
        away = match['away_team']
        home_goals = int(match['home_score'])
        away_goals = int(match['away_score'])
        stage = match['stage']
        outcome = match['outcome']  # H/D/A
        
        stage_type = classify_stage_2018_2014(stage)
        
        # 无xG的简化预测（使用基准概率）
        base_home = 0.45
        base_draw = 0.25
        base_away = 0.30
        
        # 应用阶段校准
        if stage_type == 'group':
            adjustment = calibration.get('group_adjustment', 0.95)
            base_home *= adjustment
            base_away = base_away / adjustment
        elif stage_type == 'knockout':
            adjustment = calibration.get('knockout_adjustment', 1.20)
            base_home *= adjustment
            base_away = base_away / adjustment
        
        total = base_home + base_draw + base_away
        home_prob = base_home / total
        draw_prob = base_draw / total
        away_prob = base_away / total
        
        probs = {'home': home_prob, 'draw': draw_prob, 'away': away_prob}
        recommended = max(probs, key=probs.get)
        
        # 判断预测是否正确
        if outcome == 'H' and recommended == 'home':
            correct = True
        elif outcome == 'D' and recommended == 'draw':
            correct = True
        elif outcome == 'A' and recommended == 'away':
            correct = True
        else:
            correct = False
        
        match_result = {
            'date': match['date'],
            'home': home,
            'away': away,
            'score': f"{home_goals}-{away_goals}",
            'stage': stage,
            'stage_type': stage_type,
            'outcome': outcome,
            'prediction': recommended,
            'correct': correct
        }
        
        results['matches'].append(match_result)
        
        if correct:
            results['correct_predictions'] += 1
        
        if stage_type in ['group', 'knockout']:
            results[stage_type]['total'] += 1
            if correct:
                results[stage_type]['correct'] += 1
    
    results['accuracy'] = round(results['correct_predictions'] / results['total_matches'] * 100, 1) if results['total_matches'] > 0 else 0
    results['group']['accuracy'] = round(results['group']['correct'] / results['group']['total'] * 100, 1) if results['group']['total'] > 0 else 0
    results['knockout']['accuracy'] = round(results['knockout']['correct'] / results['knockout']['total'] * 100, 1) if results['knockout']['total'] > 0 else 0
    
    return results

def identify_famous_upsets_2022(results: Dict) -> List[Dict]:
    """识别2022著名冷门"""
    upsets = []
    famous_pairs = [
        ('ARGENTINA', 'SAUDI ARABIA'),
        ('GERMANY', 'JAPAN'),
        ('MOROCCO', 'SPAIN'),
        ('CROATIA', 'BRAZIL')
    ]
    
    for match in results['matches']:
        home, away = match['home'], match['away']
        for t1, t2 in famous_pairs:
            if (t1 in home and t2 in away) or (t1 in away and t2 in home):
                if not match['correct']:
                    upsets.append({
                        'match': f"{home} {match['score']} {away}",
                        'stage': match['stage'],
                        'predicted': match['prediction'],
                        'actual': match['actual'],
                        'confidence': match['confidence'],
                        'home_xg': match['home_xg'],
                        'away_xg': match['away_xg']
                    })
                break
    
    return upsets

def generate_comprehensive_report(results_2022: Dict, results_2018: Dict, results_2014: Dict, 
                                   calibration: Dict) -> Dict:
    """生成综合回测报告"""
    
    report = {
        'metadata': {
            'source': 'Kaggle + Football Quant OS',
            'calibration': calibration,
            'model_version': '4.3.4_xg_enhanced',
            'data_sources': {
                '2022': 'shrikrishnaparab/fifa-world-cup-2022-qatar-match-data',
                '2018': 'evangower/fifa-world-cup',
                '2014': 'evangower/fifa-world-cup'
            }
        },
        'summary': {
            '2022': {
                'total': results_2022['total_matches'],
                'correct': results_2022['correct_predictions'],
                'accuracy': results_2022['accuracy'],
                'group_accuracy': results_2022['group']['accuracy'],
                'knockout_accuracy': results_2022['knockout']['accuracy'],
                'features': ['xG', 'possession', 'stage_calibration']
            },
            '2018': {
                'total': results_2018['total_matches'],
                'correct': results_2018['correct_predictions'],
                'accuracy': results_2018['accuracy'],
                'group_accuracy': results_2018['group']['accuracy'],
                'knockout_accuracy': results_2018['knockout']['accuracy'],
                'features': ['stage_calibration']
            },
            '2014': {
                'total': results_2014['total_matches'],
                'correct': results_2014['correct_predictions'],
                'accuracy': results_2014['accuracy'],
                'group_accuracy': results_2014['group']['accuracy'],
                'knockout_accuracy': results_2014['knockout']['accuracy'],
                'features': ['stage_calibration']
            }
        },
        'famous_upsets': {
            '2022': identify_famous_upsets_2022(results_2022),
            '2018': [],
            '2014': []
        },
        'xG_analysis': {
            '2022_matches_with_xg': len([m for m in results_2022['matches'] if m.get('home_xg') is not None]),
            'avg_home_xg': round(sum(m['home_xg'] for m in results_2022['matches']) / len(results_2022['matches']), 2),
            'avg_away_xg': round(sum(m['away_xg'] for m in results_2022['matches']) / len(results_2022['matches']), 2)
        }
    }
    
    # 计算平均准确率
    avg_accuracy = (results_2022['accuracy'] + results_2018['accuracy'] + results_2014['accuracy']) / 3
    avg_group = (results_2022['group']['accuracy'] + results_2018['group']['accuracy'] + results_2014['group']['accuracy']) / 3
    avg_knockout = (results_2022['knockout']['accuracy'] + results_2018['knockout']['accuracy'] + results_2014['knockout']['accuracy']) / 3
    
    report['summary']['average'] = {
        'accuracy': round(avg_accuracy, 1),
        'group_accuracy': round(avg_group, 1),
        'knockout_accuracy': round(avg_knockout, 1)
    }
    
    # 校准建议
    report['recommendations'] = [
        f"2022 xG增强模型准确率: {results_2022['accuracy']}%",
        f"2018基准模型准确率: {results_2018['accuracy']}%",
        f"2014基准模型准确率: {results_2014['accuracy']}%",
        f"三届平均准确率: {avg_accuracy:.1f}%",
        "建议：xG特征显著提升2022预测准确率" if results_2022['accuracy'] > max(results_2018['accuracy'], results_2014['accuracy']) else "建议：xG特征未显著提升，需优化模型",
        f"小组赛平均准确率: {avg_group:.1f}%",
        f"淘汰赛平均准确率: {avg_knockout:.1f}%"
    ]
    
    return report

def main():
    print("=" * 60)
    print("Football Quant OS - Comprehensive Backtest v1.0")
    print("Features: xG + Possession + Stage Calibration")
    print("=" * 60)
    
    # 获取校准系数
    data = DataIntegration()
    calibration = data.get_stage_calibration_factors()
    
    print(f"\nCalibration Factors:")
    print(f"  Group adjustment: {calibration['group_adjustment']}")
    print(f"  Knockout adjustment: {calibration['knockout_adjustment']}")
    
    # 加载数据
    print("\n[Loading] 2022 Qatar data...")
    df_2022 = load_2022_data()
    print(f"  Loaded: {len(df_2022)} matches")
    
    print("[Loading] 2018/2014 data...")
    df_2018_2014 = load_2018_2014_data()
    print(f"  Loaded: {len(df_2018_2014)} matches (1930-2018)")
    
    # 2022回测（xG增强）
    print("\n" + "=" * 60)
    print("Backtesting 2022 World Cup (xG Enhanced)...")
    print("=" * 60)
    results_2022 = backtest_2022(df_2022, calibration)
    
    print(f"\n2022 Results:")
    print(f"  Total: {results_2022['total_matches']} matches")
    print(f"  Correct: {results_2022['correct_predictions']}/{results_2022['total_matches']}")
    print(f"  Accuracy: {results_2022['accuracy']}%")
    print(f"  Group: {results_2022['group']['accuracy']}% ({results_2022['group']['correct']}/{results_2022['group']['total']})")
    print(f"  Knockout: {results_2022['knockout']['accuracy']}% ({results_2022['knockout']['correct']}/{results_2022['knockout']['total']})")
    
    # 2018回测
    print("\n" + "=" * 60)
    print("Backtesting 2018 World Cup...")
    print("=" * 60)
    results_2018 = backtest_2018_2014(df_2018_2014, 2018, calibration)
    
    print(f"\n2018 Results:")
    print(f"  Total: {results_2018['total_matches']} matches")
    print(f"  Correct: {results_2018['correct_predictions']}/{results_2018['total_matches']}")
    print(f"  Accuracy: {results_2018['accuracy']}%")
    print(f"  Group: {results_2018['group']['accuracy']}%")
    print(f"  Knockout: {results_2018['knockout']['accuracy']}%")
    
    # 2014回测
    print("\n" + "=" * 60)
    print("Backtesting 2014 World Cup...")
    print("=" * 60)
    results_2014 = backtest_2018_2014(df_2018_2014, 2014, calibration)
    
    print(f"\n2014 Results:")
    print(f"  Total: {results_2014['total_matches']} matches")
    print(f"  Correct: {results_2014['correct_predictions']}/{results_2014['total_matches']}")
    print(f"  Accuracy: {results_2014['accuracy']}%")
    print(f"  Group: {results_2014['group']['accuracy']}%")
    print(f"  Knockout: {results_2014['knockout']['accuracy']}%")
    
    # 生成综合报告
    report = generate_comprehensive_report(results_2022, results_2018, results_2014, calibration)
    
    # 保存报告
    report_file = DATA_DIR / "comprehensive_backtest_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n[OK] Report saved: {report_file}")
    
    # 打印摘要
    print("\n" + "=" * 60)
    print("COMPREHENSIVE BACKTEST SUMMARY")
    print("=" * 60)
    print(f"2022 (xG Enhanced): {results_2022['accuracy']}%")
    print(f"2018 (Baseline): {results_2018['accuracy']}%")
    print(f"2014 (Baseline): {results_2014['accuracy']}%")
    print(f"Average Accuracy: {report['summary']['average']['accuracy']}%")
    print(f"\nGroup Stage Average: {report['summary']['average']['group_accuracy']}%")
    print(f"Knockout Stage Average: {report['summary']['average']['knockout_accuracy']}%")
    print(f"\n2022 Famous Upsets Detected: {len(report['famous_upsets']['2022'])}")
    print(f"2022 Avg Home xG: {report['xG_analysis']['avg_home_xg']}")
    print(f"2022 Avg Away xG: {report['xG_analysis']['avg_away_xg']}")
    print("=" * 60)
    
    for rec in report['recommendations']:
        print(f"  {rec}")
    print("=" * 60)

if __name__ == "__main__":
    main()
