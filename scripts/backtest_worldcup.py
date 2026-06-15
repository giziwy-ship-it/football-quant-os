#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
World Cup 回测框架 (v0.2)
用于验证当前模型在历史世界杯数据上的表现
使用数据驱动的 calculate_1x2_edge (stage 参数版本)
"""
import json
import sys
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# 导入当前预测逻辑
sys.path.insert(0, str(Path(__file__).parent))
from predict import calculate_1x2_edge, get_historical_upset_rate


def load_historical_data() -> Dict[str, Any]:
    """加载历史世界杯数据"""
    hist_path = Path(__file__).parent.parent / "references" / "worldcup_historical.json"
    if not hist_path.exists():
        raise FileNotFoundError(f"找不到历史数据文件: {hist_path}")
    
    with open(hist_path, "r", encoding="utf-8") as f:
        return json.load(f)


def simulate_prediction(upset_data: Dict[str, Any], stage: str) -> Dict[str, Any]:
    """模拟对一场历史比赛进行预测"""
    odds = upset_data.get("odds_home", 2.5)
    
    # 使用数据驱动的 calculate_1x2_edge
    edge_result = calculate_1x2_edge(odds, 3.2, 3.0, stage)
    
    return edge_result


def run_backtest() -> Dict[str, Any]:
    """执行回测"""
    data = load_historical_data()
    results = {
        "total_matches": 0,
        "group_stage": {"count": 0, "avg_upset_score": 0, "avg_edge_on_upset": 0},
        "knockout_stage": {"count": 0, "avg_upset_score": 0, "avg_edge_on_upset": 0},
        "upsets_detected": 0,
        "details": []
    }
    
    group_upset_scores = []
    knockout_upset_scores = []
    group_edges = []
    knockout_edges = []
    
    for year, tournament in data["tournaments"].items():
        for upset in tournament.get("notable_upsets", []):
            stage = upset.get("stage", "group")
            is_upset = upset.get("is_upset", False)
            
            prediction = simulate_prediction(upset, stage)
            upset_score = prediction["upset_score"]
            
            results["total_matches"] += 1
            results["details"].append({
                "year": year,
                "match": upset["match"],
                "stage": stage,
                "is_upset": is_upset,
                "upset_score": upset_score,
                "edge_home": prediction["edge"]["home"]
            })
            
            if stage == "group":
                group_upset_scores.append(upset_score)
                if is_upset:
                    group_edges.append(prediction["edge"]["home"])
            else:
                knockout_upset_scores.append(upset_score)
                if is_upset:
                    knockout_edges.append(prediction["edge"]["home"])
    
    # 计算统计指标
    if group_upset_scores:
        results["group_stage"]["count"] = len(group_upset_scores)
        results["group_stage"]["avg_upset_score"] = round(sum(group_upset_scores) / len(group_upset_scores), 2)
    if knockout_upset_scores:
        results["knockout_stage"]["count"] = len(knockout_upset_scores)
        results["knockout_stage"]["avg_upset_score"] = round(sum(knockout_upset_scores) / len(knockout_upset_scores), 2)
    
    if group_edges:
        results["group_stage"]["avg_edge_on_upset"] = round(sum(group_edges) / len(group_edges), 4)
    if knockout_edges:
        results["knockout_stage"]["avg_edge_on_upset"] = round(sum(knockout_edges) / len(knockout_edges), 4)
    
    results["upsets_detected"] = sum(1 for d in results["details"] if d["is_upset"])
    
    return results


def print_report(results: Dict[str, Any]):
    """打印回测报告"""
    print("\n" + "="*60)
    print("Football Quant OS - World Cup 回测报告")
    print("="*60)
    print(f"总测试比赛数: {results['total_matches']}")
    print(f"检测到的冷门数: {results['upsets_detected']}")
    
    print("\n【小组赛阶段】")
    gs = results["group_stage"]
    print(f" 比赛数量: {gs['count']}")
    print(f" 平均冷门评分: {gs['avg_upset_score']}")
    print(f" 冷门比赛平均 Edge: {gs.get('avg_edge_on_upset', 0)}")
    
    print("\n【淘汰赛阶段】")
    ko = results["knockout_stage"]
    print(f" 比赛数量: {ko['count']}")
    print(f" 平均冷门评分: {ko['avg_upset_score']}")
    print(f" 冷门比赛平均 Edge: {ko.get('avg_edge_on_upset', 0)}")
    
    print("\n" + "="*60)
    print(f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")


if __name__ == "__main__":
    results = run_backtest()
    print_report(results)
    
    # 保存详细结果
    output_path = Path(__file__).parent / "backtest_result.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"详细结果已保存: {output_path}")
