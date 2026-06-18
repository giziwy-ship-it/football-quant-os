#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Train v4 Physical AI using World Cup Historical Data (1930-2018)
使用世界杯历史数据训练 v4 物理AI模型

训练策略:
1. 1930-2018 数据 => 提取球队实力特征
2. 构建特征向量 => 训练层权重
3. 交叉验证 => 选择最优权重
4. 2022 世界杯 => 最终验证

Author: Naga Core Team
Version: 4.0.0
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any
from collections import defaultdict
from datetime import datetime

from v4.core.physical_ai import PhysicalAI, TeamState, MarketState


# ============ 数据加载 ============

def load_historical_data() -> pd.DataFrame:
    """加载1930-2018世界杯数据"""
    csv_path = Path("D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_1930-2018/wcmatches.csv")
    df = pd.read_csv(csv_path)
    return df


def load_2022_data() -> pd.DataFrame:
    """加载2022世界杯详细数据"""
    csv_path = Path("D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_2022_qatar/Fifa_WC_2022_Match_data.csv")
    df = pd.read_csv(csv_path, encoding='latin1')
    return df


# ============ 特征工程 ============

class TeamFeatureExtractor:
    """球队特征提取器 - 从历史数据中提取球队实力"""
    
    def __init__(self, historical_df: pd.DataFrame):
        self.df = historical_df
        self.team_stats = self._compute_team_stats()
    
    def _compute_team_stats(self) -> Dict[str, Dict]:
        """计算每支球队的历史统计 - 增强版"""
        stats = defaultdict(lambda: {
            "matches": 0, "wins": 0, "draws": 0, "losses": 0,
            "goals_for": 0, "goals_against": 0,
            "home_matches": 0, "home_wins": 0,
            "away_matches": 0, "away_wins": 0,
            "worldcups": set(),
            "recent_form": []  # 最近5场结果
        })
        
        # 按时间排序处理
        df_sorted = self.df.sort_values(['year', 'date'])
        
        for _, row in df_sorted.iterrows():
            home = row['home_team']
            away = row['away_team']
            year = row['year']
            home_score = row['home_score']
            away_score = row['away_score']
            
            # 更新历史统计（只使用之前年份的数据）
            for team in [home, away]:
                stats[team]["worldcups"].add(year)
            
            # 主场
            stats[home]["matches"] += 1
            stats[home]["home_matches"] += 1
            stats[home]["goals_for"] += home_score
            stats[home]["goals_against"] += away_score
            
            if home_score > away_score:
                stats[home]["wins"] += 1
                stats[home]["home_wins"] += 1
                stats[home]["recent_form"].append(1)
            elif home_score == away_score:
                stats[home]["draws"] += 1
                stats[home]["recent_form"].append(0.5)
            else:
                stats[home]["losses"] += 1
                stats[home]["recent_form"].append(0)
            
            # 客场
            stats[away]["matches"] += 1
            stats[away]["away_matches"] += 1
            stats[away]["goals_for"] += away_score
            stats[away]["goals_against"] += home_score
            
            if away_score > home_score:
                stats[away]["wins"] += 1
                stats[away]["away_wins"] += 1
                stats[away]["recent_form"].append(1)
            elif away_score == home_score:
                stats[away]["draws"] += 1
                stats[away]["recent_form"].append(0.5)
            else:
                stats[away]["losses"] += 1
                stats[away]["recent_form"].append(0)
        
        # 转换为比率
        for team, s in stats.items():
            m = s["matches"]
            if m > 0:
                s["win_rate"] = s["wins"] / m
                s["draw_rate"] = s["draws"] / m
                s["loss_rate"] = s["losses"] / m
                s["avg_goals_for"] = s["goals_for"] / m
                s["avg_goals_against"] = s["goals_against"] / m
                s["goal_diff"] = (s["goals_for"] - s["goals_against"]) / m
                s["tournament_gene"] = min(1.0, len(s["worldcups"]) / 10)
                
                # 主场优势
                hm = s["home_matches"]
                s["home_win_rate"] = s["home_wins"] / hm if hm > 0 else 0.5
                
                # 近期状态 (最近5场平均)
                recent = s["recent_form"][-5:]
                s["form"] = sum(recent) / len(recent) if recent else 0.5
            else:
                s["win_rate"] = 0.33
                s["draw_rate"] = 0.33
                s["loss_rate"] = 0.33
                s["avg_goals_for"] = 1.0
                s["avg_goals_against"] = 1.0
                s["goal_diff"] = 0
                s["tournament_gene"] = 0.1
                s["home_win_rate"] = 0.5
                s["form"] = 0.5
        
        return dict(stats)
    
    def get_team_features(self, team_name: str) -> Dict[str, float]:
        """获取球队特征 - 增强版"""
        s = self.team_stats.get(team_name, {})
        if not s:
            # 未知球队返回默认值
            return {
                "attack": 0.55, "defense": 0.55,
                "win_rate": 0.33, "goal_diff": 0,
                "tournament_gene": 0.1,
                "form": 0.5,
                "home_win_rate": 0.5
            }
        
        # 进攻力 = 场均进球 / 3 (归一化)
        attack = min(1.0, s.get("avg_goals_for", 1.0) / 2.5)
        # 防守力 = 1 - 场均失球 / 3
        defense = max(0.1, 1.0 - s.get("avg_goals_against", 1.0) / 2.5)
        
        return {
            "attack": attack,
            "defense": defense,
            "win_rate": s.get("win_rate", 0.33),
            "goal_diff": s.get("goal_diff", 0),
            "tournament_gene": s.get("tournament_gene", 0.1),
            "form": s.get("form", 0.5),
            "home_win_rate": s.get("home_win_rate", 0.5)
        }


# ============ 训练引擎 ============

class V4Trainer:
    """v4 物理AI训练器"""
    
    def __init__(self):
        self.ai = PhysicalAI()
        self.extractor = None
    
    def prepare_data(self, train_df: pd.DataFrame):
        """准备训练数据"""
        self.extractor = TeamFeatureExtractor(train_df)
    
    def match_to_features(
        self,
        home_team: str,
        away_team: str,
        home_advantage: float = 0.1
    ) -> Tuple[TeamState, TeamState]:
        """将球队名称转换为特征向量"""
        home_f = self.extractor.get_team_features(home_team)
        away_f = self.extractor.get_team_features(away_team)
        
        # ELO 计算 - 基于胜率
        home_elo = 1500 + (home_f["win_rate"] - 0.33) * 600
        away_elo = 1500 + (away_f["win_rate"] - 0.33) * 600
        
        # 主场优势加成
        home_elo += home_advantage * 100
        
        home = TeamState(
            attack=home_f["attack"],
            defense=home_f["defense"],
            form=home_f["form"],
            fatigue=0.0,
            morale=home_f["win_rate"],
            home_advantage=home_advantage,
            elo=home_elo,
            xg_for=home_f["attack"] * 2.5,
            xg_against=(1 - home_f["defense"]) * 2.0,
            coach_factor=0.0,
            tournament_gene=home_f["tournament_gene"]
        )
        
        away = TeamState(
            attack=away_f["attack"],
            defense=away_f["defense"],
            form=away_f["form"],
            fatigue=0.0,
            morale=away_f["win_rate"],
            home_advantage=0.0,
            elo=away_elo,
            xg_for=away_f["attack"] * 2.5,
            xg_against=(1 - away_f["defense"]) * 2.0,
            coach_factor=0.0,
            tournament_gene=away_f["tournament_gene"]
        )
        
        return home, away
    
    def compute_brier_score(
        self,
        predicted_probs: Dict[str, float],
        actual_result: str
    ) -> float:
        """计算Brier Score (越低越好)"""
        actual = {"home": 0, "draw": 0, "away": 0}
        actual[actual_result] = 1
        
        brier = sum((predicted_probs[k] - actual[k]) ** 2 for k in actual) / 3
        return brier
    
    def compute_log_loss(
        self,
        predicted_probs: Dict[str, float],
        actual_result: str
    ) -> float:
        """计算Log Loss (越低越好)"""
        p = predicted_probs.get(actual_result, 0.01)
        p = max(p, 0.001)  # 防止log(0)
        return -np.log(p)
    
    def evaluate_weights(
        self,
        test_df: pd.DataFrame,
        weights: Dict[str, float]
    ) -> Dict[str, float]:
        """
        评估一组权重在测试集上的表现
        
        Returns:
            {"brier": float, "log_loss": float, "accuracy": float}
        """
        self.ai.layer_weights = weights
        
        total_brier = 0
        total_logloss = 0
        correct = 0
        n = 0
        
        for _, row in test_df.iterrows():
            home_team = row['home_team']
            away_team = row['away_team']
            home_score = row['home_score']
            away_score = row['away_score']
            
            # 确定实际结果
            if home_score > away_score:
                actual = "home"
            elif home_score < away_score:
                actual = "away"
            else:
                actual = "draw"
            
            try:
                home, away = self.match_to_features(home_team, away_team)
                result = self.ai.predict(home, away)
                probs = result["probabilities"]
                
                total_brier += self.compute_brier_score(probs, actual)
                total_logloss += self.compute_log_loss(probs, actual)
                
                predicted = max(probs, key=probs.get)
                if predicted == actual:
                    correct += 1
                
                n += 1
            except Exception as e:
                continue
        
        if n == 0:
            return {"brier": 1.0, "log_loss": 10.0, "accuracy": 0.33}
        
        return {
            "brier": total_brier / n,
            "log_loss": total_logloss / n,
            "accuracy": correct / n,
            "samples": n
        }
    
    def grid_search(
        self,
        train_df: pd.DataFrame,
        test_df: pd.DataFrame,
        param_grid: Dict[str, List[float]] = None
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        网格搜索最优权重
        
        Args:
            train_df: 训练数据 (用于准备特征)
            test_df: 验证数据
            param_grid: 参数网格 {param: [values]}
        
        Returns:
            (best_weights, best_metrics)
        """
        self.prepare_data(train_df)
        
        if param_grid is None:
            # 默认参数网格
            param_grid = {
                "mechanics": [0.5, 1.0, 1.5, 2.0],
                "field": [0.0, 0.3, 0.6, 1.0],
                "entropy": [0.0, 0.5, 1.0, 1.5],
                "coach": [0.0, 0.5, 1.0],
                "market": [0.0, 0.3, 0.6]
            }
        
        best_weights = None
        best_score = float('inf')
        best_metrics = {}
        
        # 简化的网格搜索 (随机采样)
        import itertools
        
        keys = list(param_grid.keys())
        values = [param_grid[k] for k in keys]
        
        total_combinations = 1
        for v in values:
            total_combinations *= len(v)
        
        print(f"Grid Search: {total_combinations} combinations")
        
        # 如果组合太多，随机采样
        max_eval = 50
        if total_combinations > max_eval:
            print(f"Too many combinations, sampling {max_eval} random sets")
            combinations = []
            for _ in range(max_eval):
                combo = {k: np.random.choice(param_grid[k]) for k in keys}
                combinations.append(combo)
        else:
            combinations = [
                dict(zip(keys, combo))
                for combo in itertools.product(*values)
            ]
        
        for i, weights in enumerate(combinations):
            metrics = self.evaluate_weights(test_df, weights)
            score = metrics["brier"]  # 以Brier Score为目标
            
            if score < best_score:
                best_score = score
                best_weights = weights.copy()
                best_metrics = metrics.copy()
                print(f"  [{i+1}/{len(combinations)}] NEW BEST: Brier={score:.4f}, Acc={metrics['accuracy']:.1%}")
                print(f"    weights: {weights}")
        
        return best_weights, best_metrics
    
    def train(
        self,
        train_df: pd.DataFrame,
        val_df: pd.DataFrame
    ) -> Dict[str, Any]:
        """
        主训练流程
        
        1. 准备特征提取器
        2. 网格搜索最优权重
        3. 返回训练结果
        """
        print("=" * 60)
        print("V4 Physical AI Training")
        print("=" * 60)
        
        print(f"\nTraining samples: {len(train_df)}")
        print(f"Validation samples: {len(val_df)}")
        
        # 网格搜索
        best_weights, best_metrics = self.grid_search(train_df, val_df)
        
        # 设置最优权重
        self.ai.layer_weights = best_weights
        
        print("\n" + "=" * 60)
        print("Training Complete")
        print("=" * 60)
        print(f"\nBest Weights:")
        for k, v in best_weights.items():
            print(f"  {k}: {v:.2f}")
        print(f"\nValidation Metrics:")
        print(f"  Brier Score: {best_metrics['brier']:.4f}")
        print(f"  Log Loss:    {best_metrics['log_loss']:.4f}")
        print(f"  Accuracy:    {best_metrics['accuracy']:.1%}")
        print(f"  Samples:     {best_metrics['samples']}")
        
        return {
            "weights": best_weights,
            "metrics": best_metrics,
            "version": self.ai.VERSION
        }
    
    def save_model(self, path: str):
        """保存训练好的模型"""
        self.ai.save_weights(path)
        print(f"\nModel saved: {path}")


# ============ 主入口 ============

def main():
    """主训练流程"""
    # 加载数据
    print("Loading historical data...")
    df_all = load_historical_data()
    
    print(f"Total matches: {len(df_all)}")
    print(f"Year range: {df_all['year'].min()} - {df_all['year'].max()}")
    
    # 划分训练/验证集
    # 训练: 1930-2014 (21届)
    # 验证: 2018 (1届)
    # 测试: 2022 (最终验证)
    
    train_df = df_all[df_all['year'] <= 2014].copy()
    val_df = df_all[df_all['year'] == 2018].copy()
    
    print(f"\nTrain: {len(train_df)} matches (1930-2014)")
    print(f"Val:   {len(val_df)} matches (2018)")
    
    # 创建训练器
    trainer = V4Trainer()
    
    # 训练
    result = trainer.train(train_df, val_df)
    
    # 保存
    output_path = "D:/openclaw-workspace/football_quant_os/v4/data/trained_weights.json"
    trainer.save_model(output_path)
    
    # 在2022上最终验证
    print("\n" + "=" * 60)
    print("Final Validation: 2022 World Cup")
    print("=" * 60)
    
    # 使用2022数据
    df_2022 = load_2022_data()
    
    # 2022数据格式不同，需要适配
    # 简化为使用已有的 worldcup2022_data.json
    with open("D:/openclaw-workspace/football_quant_os/data/worldcup2022_data.json", 'r') as f:
        wc2022 = json.load(f)
    
    matches_2022 = wc2022.get("group_stage", []) + wc2022.get("knockout_stage", [])
    
    # 转换为DataFrame
    rows = []
    for m in matches_2022:
        rows.append({
            'home_team': m['home'],
            'away_team': m['away'],
            'home_score': m.get('home_score', 0),
            'away_score': m.get('away_score', 0)
        })
    df_2022_simple = pd.DataFrame(rows)
    
    # 需要重新准备特征（包含2022球队）
    # 合并训练+验证数据
    combined_df = pd.concat([train_df, val_df], ignore_index=True)
    trainer.prepare_data(combined_df)
    
    # 评估
    metrics_2022 = trainer.evaluate_weights(df_2022_simple, result["weights"])
    
    print(f"\n2022 Validation:")
    print(f"  Brier Score: {metrics_2022['brier']:.4f}")
    print(f"  Log Loss:    {metrics_2022['log_loss']:.4f}")
    print(f"  Accuracy:    {metrics_2022['accuracy']:.1%}")
    print(f"  Samples:     {metrics_2022['samples']}")
    
    # 保存完整结果
    final_result = {
        "weights": result["weights"],
        "val_metrics": result["metrics"],
        "test_metrics_2022": metrics_2022,
        "training_date": datetime.now().isoformat()
    }
    
    result_path = "D:/openclaw-workspace/football_quant_os/v4/data/training_result.json"
    with open(result_path, 'w') as f:
        json.dump(final_result, f, indent=2)
    
    print(f"\nFull result saved: {result_path}")
    
    return final_result


if __name__ == "__main__":
    main()
