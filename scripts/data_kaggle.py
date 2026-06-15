#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kaggle 数据集集成脚本
P1 优先级：历史世界杯数据集
需要：Kaggle CLI (pip install kaggle)
"""
import pandas as pd
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import json


class KaggleData:
    """Kaggle 数据集接口"""
    
    # 推荐数据集
    DATASETS = {
        "worldcup_2022": {
            "owner": "datasets",
            "name": "fifa-world-cup-2022",
            "files": ["worldcup_2022.csv"],
            "description": "2022世界杯完整数据"
        },
        "worldcup_historical": {
            "owner": "datasets",
            "name": "world-cup-historical-data",
            "files": ["world_cup_matches.csv", "world_cup_players.csv"],
            "description": "1930-2018 世界杯历史数据"
        },
        "international_results": {
            "owner": "datasets",
            "name": "international-football-results",
            "files": ["results.csv"],
            "description": "所有国家队比赛结果"
        }
    }
    
    def __init__(self, cache_dir: str = "data/kaggle"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def download_dataset(self, dataset_key: str) -> Optional[Path]:
        """
        下载 Kaggle 数据集
        
        Args:
            dataset_key: 数据集名称 (worldcup_2022, worldcup_historical, etc.)
        """
        if dataset_key not in self.DATASETS:
            print(f"[错误] 未知数据集: {dataset_key}")
            print(f"[可用] {list(self.DATASETS.keys())}")
            return None
        
        dataset = self.DATASETS[dataset_key]
        dataset_path = f"{dataset['owner']}/{dataset['name']}"
        
        # 检查是否已下载
        target_dir = self.cache_dir / dataset_key
        if target_dir.exists() and any(target_dir.iterdir()):
            print(f"[缓存] 数据集已存在: {target_dir}")
            return target_dir
        
        # 下载
        try:
            print(f"[下载] {dataset_path} ({dataset['description']})")
            target_dir.mkdir(parents=True, exist_ok=True)
            
            subprocess.run([
                "kaggle", "datasets", "download",
                "-d", dataset_path,
                "-p", str(target_dir),
                "--unzip"
            ], check=True, capture_output=True)
            
            print(f"[成功] 下载到: {target_dir}")
            return target_dir
            
        except subprocess.CalledProcessError as e:
            print(f"[失败] Kaggle CLI 错误: {e}")
            print("[提示] 请确保已安装 kaggle: pip install kaggle")
            print("[提示] 配置 Kaggle API Key: ~/.kaggle/kaggle.json")
            return None
        except FileNotFoundError:
            print("[失败] 找不到 kaggle 命令，请安装: pip install kaggle")
            return None
    
    def load_worldcup_2022(self) -> Optional[pd.DataFrame]:
        """加载2022世界杯数据"""
        target_dir = self.download_dataset("worldcup_2022")
        if not target_dir:
            return None
        
        # 查找CSV文件
        csv_files = list(target_dir.glob("*.csv"))
        if not csv_files:
            print("[错误] 找不到CSV文件")
            return None
        
        return pd.read_csv(csv_files[0])
    
    def load_historical_matches(self) -> Optional[pd.DataFrame]:
        """加载历史世界杯比赛数据 (1930-2018)"""
        target_dir = self.download_dataset("worldcup_historical")
        if not target_dir:
            return None
        
        csv_files = list(target_dir.glob("*matches*.csv"))
        if not csv_files:
            csv_files = list(target_dir.glob("*.csv"))
        
        if not csv_files:
            return None
        
        return pd.read_csv(csv_files[0])
    
    def get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """获取可用的特征列"""
        # 常用特征列
        feature_cols = [
            'home_team', 'away_team', 'home_score', 'away_score',
            'home_xg', 'away_xg', 'home_possession', 'away_possession',
            'home_shots', 'away_shots', 'home_shots_on_target', 'away_shots_on_target',
            'home_corners', 'away_corners', 'home_fouls', 'away_fouls',
            'home_yellow_cards', 'away_yellow_cards', 'home_red_cards', 'away_red_cards'
        ]
        
        available = [col for col in feature_cols if col in df.columns]
        return available


def main():
    """示例：下载并查看2022世界杯数据"""
    kg = KaggleData()
    
    # 下载2022世界杯数据
    df = kg.load_worldcup_2022()
    if df is not None:
        print(f"\n数据预览:")
        print(df.head())
        print(f"\n形状: {df.shape}")
        print(f"\n列名: {df.columns.tolist()}")
        
        # 查看可用特征
        features = kg.get_feature_columns(df)
        print(f"\n可用特征: {features}")
    else:
        print("\n[提示] 需要 Kaggle API Key 才能下载数据")
        print("1. 访问 https://www.kaggle.com/account")
        print("2. 创建 API Token (kaggle.json)")
        print("3. 保存到 ~/.kaggle/kaggle.json")
        print("4. 安装: pip install kaggle")


if __name__ == "__main__":
    main()
