#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
football-data.co.uk 数据批量下载脚本
下载 2022/2018/2014 世界杯数据
"""
import pandas as pd
import requests
from pathlib import Path
from typing import Optional


class FootballDataUKDownloader:
    """football-data.co.uk 批量下载器"""
    
    BASE_URL = "https://www.football-data.co.uk"
    
    # 世界杯数据映射
    WORLD_CUPS = {
        "2022": "worldcup2022.csv",
        "2018": "worldcup2018.csv",
        "2014": "worldcup2014.csv",
        "2010": "worldcup2010.csv",
        "2006": "worldcup2006.csv",
    }
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            # 使用绝对路径
            self.cache_dir = Path(__file__).parent.parent / "data" / "football_data_uk"
        else:
            self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        print(f"[Info] Cache directory: {self.cache_dir}")
    
    def download_file(self, filename: str) -> Optional[Path]:
        """下载单个文件"""
        url = f"{self.BASE_URL}/{filename}"
        cache_file = self.cache_dir / filename
        
        if cache_file.exists():
            print(f"[Cache] Using local file: {cache_file}")
            return cache_file
        
        try:
            print(f"[Download] {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            with open(cache_file, "w", encoding="utf-8") as f:
                f.write(response.text)
            
            print(f"[Success] Downloaded {len(response.text)} bytes")
            print(f"[Info] Saved to: {cache_file}")
            return cache_file
            
        except Exception as e:
            print(f"[Failed] {e}")
            return None
    
    def download_worldcup(self, year: str) -> Optional[pd.DataFrame]:
        """Download World Cup data for specified year"""
        filename = self.WORLD_CUPS.get(year)
        if not filename:
            print(f"[Error] Unknown year: {year}")
            return None
        
        cache_file = self.download_file(filename)
        if not cache_file:
            return None
        
        try:
            df = pd.read_csv(cache_file)
            print(f"[Data] {year} World Cup: {len(df)} matches")
            return df
        except Exception as e:
            print(f"[Error] Failed to parse CSV: {e}")
            return None
    
    def download_all_worldcups(self):
        """Download all World Cup data (with fallback for older years)"""
        results = {}
        
        # 2022 - 确定可用
        for year in ["2022", "2018", "2014"]:
            df = self.download_worldcup(year)
            if df is not None:
                results[year] = {
                    "matches": len(df),
                    "file": str(self.cache_dir / self.WORLD_CUPS[year])
                }
        
        return results


def main():
    """Download 2022/2018/2014 World Cup data"""
    downloader = FootballDataUKDownloader()
    
    print("=" * 60)
    print("Football Quant OS - World Cup Data Download")
    print("Source: football-data.co.uk")
    print("=" * 60)
    
    # Download all
    results = downloader.download_all_worldcups()
    
    print("\n" + "=" * 60)
    print("Download Summary:")
    for year, info in results.items():
        print(f"  [OK] {year}: {info['matches']} matches")
    
    if "2018" not in results or "2014" not in results:
        print("\n  [Note] 2018/2014 not available on football-data.co.uk")
        print("  [Alternative] Use Kaggle dataset:")
        print("    kaggle datasets download -d datasets/fifa-world-cup-2018")
        print("  [Alternative] Use OpenFootball:")
        print("    git clone https://github.com/openfootball/worldcup.git")
    
    print(f"\nData directory: {downloader.cache_dir}")
    print("=" * 60)


if __name__ == "__main__":
    main()
