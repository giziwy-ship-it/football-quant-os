#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
V4 Training v2 - 使用FIFA排名和更精细的球队实力映射
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple

from v4.core.physical_ai import PhysicalAI, TeamState, MarketState


# ============ FIFA 排名数据 (2022年11月) ============
FIFA_RANKINGS_2022 = {
    # 强队 (1-20)
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
    # 中等 (21-40)
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

# 球队名称映射
NAME_MAPPING = {
    "Korea Republic": "KOR",
    "United States": "USA",
    "IR Iran": "IRN",
    "England": "ENG",
    "Wales": "WAL",
    "Argentina": "ARG",
    "Mexico": "MEX",
    "Poland": "POL",
    "France": "FRA",
    "Australia": "AUS",
    "Denmark": "DEN",
    "Tunisia": "TUN",
    "Spain": "ESP",
    "Costa Rica": "CRC",
    "Germany": "GER",
    "Japan": "JPN",
    "Belgium": "BEL",
    "Canada": "CAN",
    "Morocco": "MAR",
    "Croatia": "CRO",
    "Brazil": "BRA",
    "Serbia": "SRB",
    "Switzerland": "SUI",
    "Cameroon": "CMR",
    "Portugal": "POR",
    "Ghana": "GHA",
    "Uruguay": "URU",
    "Korea": "KOR",
    "Netherlands": "NED",
    "Ecuador": "ECU",
    "Qatar": "QAT",
    "Saudi Arabia": "KSA",
    "Senegal": "SEN",
    "Iran": "IRN",
    "USA": "USA",
    "South Korea": "KOR",
}


def get_team_power(team_code: str) -> Dict[str, float]:
    """
    获取球队实力参数
    
    基于FIFA排名和历史表现
    """
    # 查找球队
    team_name = None
    for full_name, code in NAME_MAPPING.items():
        if code == team_code or full_name == team_code:
            team_name = full_name
            break
    
    if not team_name or team_name not in FIFA_RANKINGS_2022:
        # 未知球队 - 中等实力
        return {
            "attack": 0.50,
            "defense": 0.50,
            "elo": 1500,
            "tournament_gene": 0.30
        }
    
    rank_data = FIFA_RANKINGS_2022[team_name]
    rank = rank_data["rank"]
    points = rank_data["points"]
    
    # 基于排名计算实力
    # 排名1-10: attack 0.75-0.90
    # 排名11-30: attack 0.55-0.75
    # 排名31-61: attack 0.40-0.55
    
    if rank <= 10:
        attack = 0.90 - (rank - 1) * 0.015
        defense = 0.85 - (rank - 1) * 0.01
    elif rank <= 30:
        attack = 0.75 - (rank - 11) * 0.01
        defense = 0.70 - (rank - 11) * 0.008
    else:
        attack = 0.55 - (rank - 31) * 0.005
        defense = 0.55 - (rank - 31) * 0.004
    
    #  tournament基因 - 基于历史参赛次数
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
        home_advantage=0.05 if is_home else 0.0,  # 降低主场优势
        elo=power["elo"],
        xg_for=power["attack"] * 2.5,
        xg_against=(1 - power["defense"]) * 2.0,
        coach_factor=0.0,
        tournament_gene=power["tournament_gene"]
    )


# ============ 训练 ============

def train_and_validate():
    """训练并验证"""
    ai = PhysicalAI()
    
    # 加载2022数据
    with open("D:/openclaw-workspace/football_quant_os/data/worldcup2022_data.json", 'r') as f:
        wc2022 = json.load(f)
    
    matches = wc2022.get("group_stage", []) + wc2022.get("knockout_stage", [])
    
    # 简单的权重搜索
    best_weights = None
    best_acc = 0
    
    print("=== V4 Weight Search ===\n")
    
    # 测试不同的权重组合
    for mech in [1.0, 1.5, 2.0]:
        for ent in [0.5, 1.0, 1.5]:
            for coach in [0.0, 0.5, 1.0]:
                weights = {
                    "mechanics": mech,
                    "field": 0.0,  # 无市场情绪数据
                    "entropy": ent,
                    "coach": coach,
                    "market": 0.0
                }
                
                ai.layer_weights = weights
                
                correct = 0
                total = 0
                
                for m in matches:
                    home_code = m['home']
                    away_code = m['away']
                    h_score = m.get('home_score', 0)
                    a_score = m.get('away_score', 0)
                    
                    if h_score > a_score:
                        actual = "home"
                    elif h_score < a_score:
                        actual = "away"
                    else:
                        actual = "draw"
                    
                    home = create_team_state(home_code, is_home=True)
                    away = create_team_state(away_code, is_home=False)
                    
                    result = ai.predict(home, away)
                    pred = max(result["probabilities"], key=result["probabilities"].get)
                    
                    if pred == actual:
                        correct += 1
                    total += 1
                
                acc = correct / total if total > 0 else 0
                
                if acc > best_acc:
                    best_acc = acc
                    best_weights = weights.copy()
                    print(f"NEW BEST: Acc={acc:.1%} | weights={weights}")
    
    print(f"\n=== Best Weights ===")
    print(f"Accuracy: {best_acc:.1%}")
    print(f"Weights: {best_weights}")
    
    # 详细分析
    print(f"\n=== Detailed Analysis ===")
    ai.layer_weights = best_weights
    
    pred_dist = {"home": 0, "draw": 0, "away": 0}
    actual_dist = {"home": 0, "draw": 0, "away": 0}
    
    for m in matches:
        home_code = m['home']
        away_code = m['away']
        h_score = m.get('home_score', 0)
        a_score = m.get('away_score', 0)
        
        if h_score > a_score:
            actual = "home"
        elif h_score < a_score:
            actual = "away"
        else:
            actual = "draw"
        
        actual_dist[actual] += 1
        
        home = create_team_state(home_code, is_home=True)
        away = create_team_state(away_code, is_home=False)
        
        result = ai.predict(home, away)
        probs = result["probabilities"]
        pred = max(probs, key=probs.get)
        
        pred_dist[pred] += 1
        
        marker = "OK" if pred == actual else "XX"
        print(f"{marker} {home_code} {h_score}-{a_score} {away_code} | Pred: {pred} | Probs: H={probs['home']:.2f} D={probs['draw']:.2f} A={probs['away']:.2f}")
    
    print(f"\nPred dist: {pred_dist}")
    print(f"Actual dist: {actual_dist}")
    
    return best_weights, best_acc


if __name__ == "__main__":
    train_and_validate()
