#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kaggle 数据集直接下载器
使用 Python requests + API Token 下载数据
"""

import requests
import os
from pathlib import Path

# Kaggle API Token
ACCESS_TOKEN = "KGAT_1a0bf30093466db53f638e21ec89b6a3"
USERNAME = "weiweigui"

# 下载目录
DATA_DIR = Path("D:/openclaw-workspace/football_quant_os/data/kaggle")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# 数据集列表
DATASETS = {
    "2022-qatar": "shrikrishnaparab/fifa-world-cup-2022-qatar-match-data",
    "1930-2018": "evangower/fifa-world-cup",
}

HEADERS = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "User-Agent": "Kaggle-CLI/2.2.1",
}

def download_dataset(dataset_slug, year):
    """下载Kaggle数据集"""
    url = f"https://www.kaggle.com/api/v1/datasets/download/{dataset_slug}"
    
    print(f"[Downloading] {year} World Cup data...")
    print(f"  URL: {url}")
    
    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=120)
        
        if response.status_code == 200:
            # 保存为zip文件
            zip_file = DATA_DIR / f"worldcup_{year}.zip"
            total_size = int(response.headers.get('content-length', 0))
            
            with open(zip_file, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            print(f"\r  Progress: {progress:.1f}%", end='')
            
            print(f"\n  [OK] Downloaded: {zip_file}")
            print(f"  Size: {zip_file.stat().st_size / 1024:.1f} KB")
            return True
            
        elif response.status_code == 401:
            print(f"  [ERROR] 401 Unauthorized - Token invalid or expired")
            return False
        elif response.status_code == 404:
            print(f"  [ERROR] 404 Dataset not found: {dataset_slug}")
            return False
        else:
            print(f"  [ERROR] HTTP {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"  [ERROR] {e}")
        return False
def main():
    print("=" * 60)
    print("Kaggle World Cup Data Download")
    print("=" * 60)
    
    results = {}
    for year, slug in DATASETS.items():
        success = download_dataset(slug, year)
        results[year] = success
        print()
    
    print("=" * 60)
    print("Download Summary:")
    for year, success in results.items():
        status = "OK" if success else "FAILED"
        print(f"  {year}: {status}")
    print(f"\nData directory: {DATA_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    main()
