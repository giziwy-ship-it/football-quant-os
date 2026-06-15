#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
football-data.co.uk 数据集成脚本
P0 优先级：历史赔率 + 结果数据
"""
import pandas as pd
import requests
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class FootballDataUK:
    """football-data.co.uk 数据接口"""
    
    BASE_URL = "https://www.football-data.co.uk"
    
    # 联赛代码映射
    LEAGUES = {
        "E0": "英超",
        "E1": "英冠",
        "SP1": "西甲",
        "D1": "德甲",
        "I1": "意甲",
        "F1": "法甲",
        "WC": "世界杯",
        "EC": "欧洲杯"
    }
    
    def __init__(self, cache_dir: str = "data/football_data_uk"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def download_season(self, league: str, season: str) -> Optional[pd.DataFrame]:
        """
        下载指定联赛赛季数据
        
        Args:
            league: 联赛代码 (E0, SP1, D1, WC, etc.)
            season: 赛季年份 (2022, 2023, 2024)
        """
        # 构建URL
        if league == "WC":  # 世界杯
            url = f"{self.BASE_URL}/worldcup{season}.csv"
        elif league == "EC":  # 欧洲杯
            url = f"{self.BASE_URL}/euro{season}.csv"
        else:
            # 联赛格式: mmms/season.csv (mmm = 联赛代码, s = 赛季缩写)
            season_short = str(season)[-2:]  # 2022 -> 22
            url = f"{self.BASE_URL}/{league}{season_short}/{season}.csv"
        
        # 检查缓存
        cache_file = self.cache_dir / f"{league}_{season}.csv"
        if cache_file.exists():
            print(f"[缓存] 使用本地文件: {cache_file}")
            return pd.read_csv(cache_file)
        
        # 下载
        try:
            print(f"[下载] {url}")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 保存缓存
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            # 读取
            df = pd.read_csv(cache_file)
            print(f"[成功] 下载 {len(df)} 场比赛")
            return df
            
        except Exception as e:
            print(f"[失败] {e}")
            return None
    
    def calculate_implied_probs(self, df: pd.DataFrame, bookmaker: str = "B365") -> pd.DataFrame:
        """
        计算隐含概率（去除margin）
        
        Args:
            df: 原始数据
            bookmaker: 博彩商代码 (B365, BW, IW, PS, WH, VC)
        """
        # 检查列是否存在
        h_col = f"{bookmaker}H"
        d_col = f"{bookmaker}D"
        a_col = f"{bookmaker}A"
        
        if not all(col in df.columns for col in [h_col, d_col, a_col]):
            available = [c for c in df.columns if c.endswith(("H", "D", "A"))]
            print(f"[警告] 找不到 {bookmaker} 赔率，可用: {available[:5]}")
            return df
        
        # 计算隐含概率
        df["mkt_home"] = 1 / df[h_col]
        df["mkt_draw"] = 1 / df[d_col]
        df["mkt_away"] = 1 / df[a_col]
        
        # 去除margin
        margin = df["mkt_home"] + df["mkt_draw"] + df["mkt_away"]
        df["imp_home"] = df["mkt_home"] / margin
        df["imp_draw"] = df["mkt_draw"] / margin
        df["imp_away"] = df["mkt_away"] / margin
        
        return df
    
    def calculate_edge(self, df: pd.DataFrame, model_probs: Dict[str, List[float]]) -> pd.DataFrame:
        """
        计算模型 Edge
        
        Args:
            df: 包含隐含概率的数据
            model_probs: {"home": [0.65, 0.42, ...], "draw": [...], "away": [...]}
        """
        df["edge_home"] = model_probs["home"] - df["imp_home"]
        df["edge_draw"] = model_probs["draw"] - df["imp_draw"]
        df["edge_away"] = model_probs["away"] - df["imp_away"]
        
        return df
    
    def get_upcoming_fixtures(self, league: str = "WC") -> pd.DataFrame:
        """获取即将进行的比赛（从最新数据中提取）"""
        # football-data.co.uk 不提供实时赛程，需要手动维护或使用其他API
        print("[提示] football-data.co.uk 不提供实时赛程，请使用 API-Football 获取")
        return pd.DataFrame()


def main():
    """示例：下载2022世界杯数据并分析"""
    fd = FootballDataUK()
    
    # 下载2022世界杯数据
    df = fd.download_season("WC", "2022")
    if df is None:
        print("下载失败")
        return
    
    print(f"\n数据预览:")
    print(df.head())
    print(f"\n列名: {df.columns.tolist()}")
    
    # 计算隐含概率
    df = fd.calculate_implied_probs(df, "B365")
    
    # 查看结果分布
    print(f"\n结果分布:")
    print(df["FTR"].value_counts())
    
    # 计算平均赔率
    print(f"\n平均赔率:")
    print(f"  主胜: {df['B365H'].mean():.2f}")
    print(f"  平局: {df['B365D'].mean():.2f}")
    print(f"  客胜: {df['B365A'].mean():.2f}")
    
    # 保存处理后的数据
    output_path = fd.cache_dir / "processed_wc2022.csv"
    df.to_csv(output_path, index=False)
    print(f"\n处理后的数据已保存: {output_path}")


if __name__ == "__main__":
    main()
