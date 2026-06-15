#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""中国 vs 捷克 完整预测 - 基于实际抓取数据"""

import sys
import os

sys.path.insert(0, r'D:\openclaw-workspace\football_quant_os')

from core.worldcup_integrator import WorldCupPipeline

print("=" * 80)
print("           娜迦足球量化决策系统 v5.0 - 完整预测报告")
print("              中国 vs 捷克 | 2026世界杯")
print("=" * 80)
print()

# 市场赔率数据（从500.com抓取）
market_odds = {
    'home': 2.60,  # 主胜（中国）
    'draw': 3.05,  # 平局
    'away': 2.94   # 客胜（捷克）
}

market_data = {
    'market_odds': market_odds,
    'market_prob': {k: 1/v for k, v in market_odds.items()},
    'media_consensus': 0.75,
}

# 运行分析
pipeline = WorldCupPipeline(bankroll=10000, stage='group')
pipeline.print_match_report('CHN', 'CZE', market_data, "世界杯小组赛")
