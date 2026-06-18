#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V4 Full Training - All World Cup Data (1930-2022)
包括小组赛和淘汰赛，修复平局预测

Author: Naga Core Team
Version: 4.1.0
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime

from v4.core.physical_ai import PhysicalAI, TeamState, MarketState


# ============ FIFA 排名数据 ============
FIFA_RANKINGS_2022 = {
    "Brazil": {"rank": 1, "points": 1841},
    "Belgium": {"rank": 2, "points": 1816},
    "Argentina": {"rank": 3, "points": 1773},
    "France": {"rank": 4, "points": 1759},
    "England": {"rank": 5, "points": 1728},
    "Netherlands": {"rank": 8, "points": 1694},
    "Portugal": {"rank": 9, "points": 1676},
    "Spain": {"rank": 7, "points": 1715},
    "United States": {"rank": 16, "points": 1627},
    "Mexico": {"rank": 13, "points": 1649},
    "Germany": {"rank": 11, "points": 1650},
    "Uruguay": {"rank": 14, "points": 1638},
    "Croatia": {"rank": 12, "points": 1645},
    "Denmark": {"rank": 10, "points": 1668},
    "Switzerland": {"rank": 15, "points": 1608},
    "Wales": {"rank": 19, "points": 1569},
    "Poland": {"rank": 26, "points": 1548},
    "Senegal": {"rank": 18, "points": 1584},
    "Serbia": {"rank": 21, "points": 1563},
    "Morocco": {"rank": 22, "points": 1563},
    "Japan": {"rank": 24, "points": 1559},
    "Korea Republic": {"rank": 28, "points": 1530},
    "Tunisia": {"rank": 30, "points": 1507},
    "Costa Rica": {"rank": 31, "points": 1503},
    "Australia": {"rank": 38, "points": 1488},
    "Cameroon": {"rank": 43, "points": 1485},
    "Canada": {"rank": 41, "points": 1475},
    "Ecuador": {"rank": 44, "points": 1463},
    "Qatar": {"rank": 50, "points": 1441},
    "Saudi Arabia": {"rank": 51, "points": 1437},
    "Iran": {"rank": 20, "points": 1564},
    "Ghana": {"rank": 61, "points": 1393},
}

NAME_MAPPING = {
    "Korea Republic": "KOR", "United States": "USA", "IR Iran": "IRN",
    "England": "ENG", "Wales": "WAL", "Argentina": "ARG", "Mexico": "MEX",
    "Poland": "POL", "France": "FRA", "Australia": "AUS", "Denmark": "DEN",
    "Tunisia": "TUN", "Spain": "ESP", "Costa Rica": "CRC", "Germany": "GER",
    "Japan": "JPN", "Belgium": "BEL", "Canada": "CAN", "Morocco": "MAR",
    "Croatia": "CRO", "Brazil": "BRA", "Serbia": "SRB", "Switzerland": "SUI",
    "Cameroon": "CMR", "Portugal": "POR", "Ghana": "GHA", "Uruguay": "URU",
    "Korea": "KOR", "Netherlands": "NED", "Ecuador": "ECU", "Qatar": "QAT",
    "Saudi Arabia": "KSA", "Senegal": "SEN", "Iran": "IRN", "USA": "USA",
    "South Korea": "KOR",
}

# 历史球队映射 (1930-2018)
HISTORICAL_TEAM_MAP = {
    # 常见历史球队名映射到标准名
    "West Germany": "Germany",
    "East Germany": "Germany",
    "Soviet Union": "Russia",
    "Czechoslovakia": "Czech Republic",
    "Yugoslavia": "Serbia",
    "Zaire": "DR Congo",
    "Dutch East Indies": "Indonesia",
}


def get_team_power(team_code: str) -> Dict[str, float]:
    """获取球队实力参数"""
    team_name = None
    for full_name, code in NAME_MAPPING.items():
        if code == team_code or full_name == team_code:
            team_name = full_name
            break
    
    # 检查历史映射
    if not team_name and team_code in HISTORICAL_TEAM_MAP:
        hist_name = HISTORICAL_TEAM_MAP[team_code]
        for full_name, code in NAME_MAPPING.items():
            if full_name == hist_name:
                team_name = full_name
                break
    
    if not team_name or team_name not in FIFA_RANKINGS_2022:
        return {"attack": 0.50, "defense": 0.50, "elo": 1500, "tournament_gene": 0.30}
    
    rank_data = FIFA_RANKINGS_2022[team_name]
    rank = rank_data["rank"]
    points = rank_data["points"]
    
    if rank <= 10:
        attack = 0.90 - (rank - 1) * 0.015
        defense = 0.85 - (rank - 1) * 0.01
    elif rank <= 30:
        attack = 0.75 - (rank - 11) * 0.01
        defense = 0.70 - (rank - 11) * 0.008
    else:
        attack = 0.55 - (rank - 31) * 0.005
        defense = 0.55 - (rank - 31) * 0.004
    
    tournament_gene = 0.95 if rank <= 5 else (0.80 if rank <= 15 else 0.50)
    
    return {
        "attack": max(0.30, min(0.95, attack)),
        "defense": max(0.30, min(0.90, defense)),
        "elo": points,
        "tournament_gene": tournament_gene
    }


def create_team_state(team_code: str, is_home: bool = False) -> TeamState:
    """创建球队状态"""
    power = get_team_power(team_code)
    
    return TeamState(
        attack=power["attack"],
        defense=power["defense"],
        form=0.5,
        fatigue=0.0,
        morale=0.5,
        home_advantage=0.05 if is_home else 0.0,
        elo=power["elo"],
        xg_for=power["attack"] * 2.5,
        xg_against=(1 - power["defense"]) * 2.0,
        coach_factor=0.0,
        tournament_gene=power["tournament_gene"]
    )


# ============ 数据加载 ============

def load_all_worldcup_data() -> List[Dict]:
    """加载所有世界杯数据 (1930-2022)"""
    all_matches = []
    
    # 1. 加载 1930-2018 数据
    csv_path = Path("D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_1930-2018/wcmatches.csv")
    df_old = pd.read_csv(csv_path)
    
    for _, row in df_old.iterrows():
        home_score = row['home_score']
        away_score = row['away_score']
        
        if pd.isna(home_score) or pd.isna(away_score):
            continue
        
        all_matches.append({
            "year": int(row['year']),
            "home": str(row['home_team']).strip(),
            "away": str(row['away_team']).strip(),
            "home_score": int(home_score),
            "away_score": int(away_score),
            "stage": str(row.get('stage', 'Group')).strip(),
            "source": "historical"
        })
    
    # 2. 加载 2022 数据
    with open("D:/openclaw-workspace/football_quant_os/data/worldcup2022_data.json", 'r') as f:
        wc2022 = json.load(f)
    
    # 小组赛
    for m in wc2022.get("group_stage", []):
        all_matches.append({
            "year": 2022,
            "home": m['home'],
            "away": m['away'],
            "home_score": m.get('home_score', 0),
            "away_score": m.get('away_score', 0),
            "stage": "Group",
            "source": "2022"
        })
    
    # 淘汰赛
    knockout = wc2022.get("knockout", {})
    for stage_name, stage_matches in knockout.items():
        if isinstance(stage_matches, list):
            for m in stage_matches:
                # 淘汰赛点球大战算平局
                home_s = m.get('home_score', 0)
                away_s = m.get('away_score', 0)
                all_matches.append({
                    "year": 2022,
                    "home": m['home'],
                    "away": m['away'],
                    "home_score": home_s,
                    "away_score": away_s,
                    "stage": stage_name,
                    "source": "2022"
                })
        elif isinstance(stage_matches, dict):
            m = stage_matches
            home_s = m.get('home_score', 0)
            away_s = m.get('away_score', 0)
            all_matches.append({
                "year": 2022,
                "home": m['home'],
                "away": m['away'],
                "home_score": home_s,
                "away_score": away_s,
                "stage": stage_name,
                "source": "2022"
            })
    
    print(f"Loaded {len(all_matches)} total matches")
    print(f"  1930-2018: {sum(1 for m in all_matches if m['source'] == 'historical')}")
    print(f"  2022: {sum(1 for m in all_matches if m['source'] == '2022')}")
    
    return all_matches


# ============ 训练 ============

def evaluate_weights(matches: List[Dict], weights: Dict[str, float], draw_boost: float = 1.0) -> Dict:
    """评估一组权重"""
    ai = PhysicalAI()
    ai.layer_weights = weights
    ai.draw_boost = draw_boost
    
    correct = 0
    total = 0
    pred_dist = {"home": 0, "draw": 0, "away": 0}
    actual_dist = {"home": 0, "draw": 0, "away": 0}
    brier_scores = []
    
    for m in matches:
        home_code = m['home']
        away_code = m['away']
        h_score = m['home_score']
        a_score = m['away_score']
        
        if h_score > a_score:
            actual = "home"
        elif h_score < a_score:
            actual = "away"
        else:
            actual = "draw"
        
        actual_dist[actual] += 1
        
        try:
            home = create_team_state(home_code, is_home=True)
            away = create_team_state(away_code, is_home=False)
            
            result = ai.predict(home, away)
            probs = result["probabilities"]
            pred = max(probs, key=probs.get)
            
            pred_dist[pred] += 1
            
            if pred == actual:
                correct += 1
            total += 1
            
            # Brier
            actual_vec = {"home": 0, "draw": 0, "away": 0}
            actual_vec[actual] = 1
            brier = sum((probs[k] - actual_vec[k]) ** 2 for k in probs) / 3
            brier_scores.append(brier)
        except Exception as e:
            pass
    
    acc = correct / total if total > 0 else 0
    avg_brier = sum(brier_scores) / len(brier_scores) if brier_scores else 1.0
    
    return {
        "accuracy": acc,
        "brier": avg_brier,
        "total": total,
        "correct": correct,
        "pred_dist": pred_dist,
        "actual_dist": actual_dist
    }


def train():
    """主训练流程"""
    print("=" * 60)
    print("V4 Full Training - All World Cup Data")
    print("=" * 60)
    
    # 加载数据
    all_matches = load_all_worldcup_data()
    
    # 划分训练/验证集
    # 训练: 1930-2014
    # 验证: 2018
    # 测试: 2022
    train_matches = [m for m in all_matches if m['year'] <= 2014]
    val_matches = [m for m in all_matches if m['year'] == 2018]
    test_matches = [m for m in all_matches if m['year'] == 2022]
    
    print(f"\nTrain: {len(train_matches)} matches")
    print(f"Val:   {len(val_matches)} matches")
    print(f"Test:  {len(test_matches)} matches")
    
    # 搜索最优参数
    print("\n=== Grid Search ===")
    
    best_result = None
    best_score = -1
    
    # 参数网格
    param_combos = []
    for mech in [1.0, 1.5, 2.0]:
        for ent in [0.5, 1.0, 1.5, 2.0]:
            for coach in [0.0, 0.5, 1.0]:
                for draw_boost in [0.8, 1.0, 1.2, 1.5, 2.0]:
                    param_combos.append({
                        "mechanics": mech,
                        "field": 0.0,
                        "entropy": ent,
                        "coach": coach,
                        "market": 0.0,
                        "draw_boost": draw_boost
                    })
    
    print(f"Testing {len(param_combos)} combinations...")
    
    # 随机采样 (太多组合)
    import random
    random.seed(42)
    if len(param_combos) > 100:
        param_combos = random.sample(param_combos, 100)
    
    for i, params in enumerate(param_combos):
        weights = {k: v for k, v in params.items() if k != "draw_boost"}
        draw_boost = params["draw_boost"]
        
        # 在训练集上评估
        result = evaluate_weights(train_matches, weights, draw_boost)
        
        # 综合评分: 准确率为主，Brier为辅，平局分布惩罚
        pred_draw_rate = result["pred_dist"]["draw"] / result["total"] if result["total"] > 0 else 0
        actual_draw_rate = result["actual_dist"]["draw"] / result["total"] if result["total"] > 0 else 0
        
        # 平局分布差异惩罚
        draw_penalty = abs(pred_draw_rate - actual_draw_rate) * 0.5
        
        score = result["accuracy"] - result["brier"] * 0.5 - draw_penalty
        
        if score > best_score:
            best_score = score
            best_result = {
                "weights": weights,
                "draw_boost": draw_boost,
                "train_metrics": result
            }
            print(f"  [{i+1}] NEW BEST: Acc={result['accuracy']:.1%}, Brier={result['brier']:.4f}, "
                  f"DrawPred={pred_draw_rate:.1%}, DrawActual={actual_draw_rate:.1%}, "
                  f"Score={score:.3f}")
            print(f"      Weights: {weights}, draw_boost={draw_boost}")
    
    # 在验证集上验证
    print("\n=== Validation (2018) ===")
    val_result = evaluate_weights(val_matches, best_result["weights"], best_result["draw_boost"])
    print(f"Accuracy: {val_result['accuracy']:.1%}")
    print(f"Brier:    {val_result['brier']:.4f}")
    print(f"Pred:     {val_result['pred_dist']}")
    print(f"Actual:   {val_result['actual_dist']}")
    
    # 在测试集上最终验证
    print("\n=== Final Test (2022) ===")
    test_result = evaluate_weights(test_matches, best_result["weights"], best_result["draw_boost"])
    print(f"Accuracy: {test_result['accuracy']:.1%}")
    print(f"Brier:    {test_result['brier']:.4f}")
    print(f"Pred:     {test_result['pred_dist']}")
    print(f"Actual:   {test_result['actual_dist']}")
    
    # 保存结果
    final_result = {
        "weights": best_result["weights"],
        "draw_boost": best_result["draw_boost"],
        "train_metrics": best_result["train_metrics"],
        "val_metrics": val_result,
        "test_metrics": test_result,
        "training_date": datetime.now().isoformat()
    }
    
    output_path = "D:/openclaw-workspace/football_quant_os/v4/data/training_result_v2.json"
    with open(output_path, 'w') as f:
        json.dump(final_result, f, indent=2)
    
    # 保存权重
    weights_path = "D:/openclaw-workspace/football_quant_os/v4/data/trained_weights_v2.json"
    with open(weights_path, 'w') as f:
        json.dump({
            "layer_weights": best_result["weights"],
            "draw_boost": best_result["draw_boost"]
        }, f, indent=2)
    
    print(f"\nSaved to: {output_path}")
    
    return final_result


if __name__ == "__main__":
    result = train()
