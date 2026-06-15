#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""切尔西 vs 曼联 比赛分析 - 基于OddsPortal数据 (H2H赔率回溯增强版)"""

import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

sys.stdout.reconfigure(encoding='utf-8')

# 基于OddsPortal抓取的数据 - 包含历史交锋赔率
MATCH_DATA = {
    "home_team": "切尔西",
    "away_team": "曼联",
    "league": "英超",
    "match_date": "2026-04-19",
    "kickoff": "03:00",

    "chelsea_recent": {
        "last_5": ["L", "W", "L", "L", "L"],
        "recent_results": [
            {"date": "12/Apr", "opponent": "曼城", "result": "0-3", "venue": "H"},
            {"date": "05/Apr", "opponent": "维尔港", "result": "7-0", "venue": "H"},
            {"date": "22/Mar", "opponent": "埃弗顿", "result": "0-3", "venue": "A"},
            {"date": "18/Mar", "opponent": "巴黎", "result": "0-3", "venue": "H"},
            {"date": "15/Mar", "opponent": "纽卡斯尔", "result": "0-1", "venue": "H"},
        ],
        "form_score": 1.2,
        "goals_scored": 7,
        "goals_conceded": 10,
    },

    "manutd_recent": {
        "last_5": ["L", "D", "W", "L", "W"],
        "recent_results": [
            {"date": "14/Apr", "opponent": "利兹联", "result": "1-2", "venue": "H"},
            {"date": "21/Mar", "opponent": "伯恩茅斯", "result": "2-2", "venue": "A"},
            {"date": "15/Mar", "opponent": "维拉", "result": "3-1", "venue": "H"},
            {"date": "05/Mar", "opponent": "纽卡斯尔", "result": "1-2", "venue": "A"},
            {"date": "01/Mar", "opponent": "水晶宫", "result": "2-1", "venue": "H"},
        ],
        "form_score": 1.4,
        "goals_scored": 9,
        "goals_conceded": 8,
    },

    "h2h": [
        {
            "date": "21/Sep 2025", "venue": "A", "result": "1-2", "winner": "曼联",
            "odds": {"home": 2.65, "draw": 3.75, "away": 2.50},
            "implied_prob": {"home": 35.8, "draw": 25.3, "away": 38.0},
            "actual_return": {"home": -1, "draw": -1, "away": +1.50}
        },
        {
            "date": "17/May 2025", "venue": "H", "result": "1-0", "winner": "切尔西",
            "odds": {"home": 1.57, "draw": 4.50, "away": 5.25},
            "implied_prob": {"home": 60.5, "draw": 21.1, "away": 18.1},
            "actual_return": {"home": +0.57, "draw": -1, "away": -1}
        },
        {
            "date": "04/Nov 2024", "venue": "A", "result": "1-1", "winner": "平局",
            "odds": {"home": 2.62, "draw": 3.50, "away": 2.60},
            "implied_prob": {"home": 36.2, "draw": 27.1, "away": 36.5},
            "actual_return": {"home": -1, "draw": +2.50, "away": -1}
        },
        {
            "date": "05/Apr 2024", "venue": "H", "result": "4-3", "winner": "切尔西",
            "odds": {"home": 1.80, "draw": 4.20, "away": 4.00},
            "implied_prob": {"home": 52.9, "draw": 22.7, "away": 23.8},
            "actual_return": {"home": +0.80, "draw": -1, "away": -1}
        },
        {
            "date": "07/Dec 2023", "venue": "A", "result": "2-1", "winner": "曼联",
            "odds": {"home": 2.75, "draw": 3.50, "away": 2.45},
            "implied_prob": {"home": 34.5, "draw": 27.1, "away": 38.7},
            "actual_return": {"home": -1, "draw": -1, "away": +1.45}
        },
    ],

    "market_odds": {
        "home_win": 2.19,
        "draw": 3.40,
        "away_win": 3.20,
        "under_2_5": 2.50,
        "btts_no": 2.73,
    },

    "standings": {
        "chelsea_rank": 6,
        "manutd_rank": 12,
    }
}


def calculate_h2h_odds_analysis(h2h_data, current_odds):
    """H2H赔率回溯分析"""
    try:
        chelsea_home_matches = [m for m in h2h_data if m["venue"] == "H"]
        chelsea_home_actual_wins = len([m for m in chelsea_home_matches if m["winner"] == "切尔西"])
        chelsea_home_expected = sum([m["implied_prob"]["home"] for m in chelsea_home_matches]) / 100

        total_return = 0
        for match in h2h_data:
            if match["venue"] == "H":
                total_return += match["actual_return"]["home"]
            else:
                total_return += match["actual_return"]["away"]

        avg_return = total_return / len(h2h_data) if h2h_data else 0

        avg_home_odds_historical = sum([m["odds"]["home"] for m in chelsea_home_matches]) / len(chelsea_home_matches)
        odds_trend = current_odds["home_win"] - avg_home_odds_historical

        market_efficiency = {
            "correct_predictions": len([m for m in h2h_data if
                (m["implied_prob"]["home"] > 50 and m["winner"] == "切尔西") or
                (m["implied_prob"]["away"] > 50 and m["winner"] == "曼联") or
                (max(m["implied_prob"].values()) < 40 and m["winner"] == "平局")]),
            "total_matches": len(h2h_data)
        }
        market_efficiency["accuracy"] = market_efficiency["correct_predictions"] / market_efficiency["total_matches"]

        return {
            "chelsea_home_actual_wins": chelsea_home_actual_wins,
            "chelsea_home_expected_wins": chelsea_home_expected,
            "home_matches_count": len(chelsea_home_matches),
            "avg_historical_return": avg_return,
            "avg_home_odds_historical": avg_home_odds_historical,
            "current_home_odds": current_odds["home_win"],
            "odds_trend": odds_trend,
            "market_efficiency": market_efficiency,
            "value_indicator": "undervalued" if odds_trend > 0.2 else "overvalued" if odds_trend < -0.2 else "fair"
        }
    except Exception as e:
        logger.error(f"H2H odds analysis failed: {e}", exc_info=True)
        return {
            "chelsea_home_actual_wins": 0,
            "chelsea_home_expected_wins": 0.0,
            "home_matches_count": 0,
            "avg_historical_return": 0.0,
            "avg_home_odds_historical": 0.0,
            "current_home_odds": current_odds.get("home_win", 0),
            "odds_trend": 0.0,
            "market_efficiency": {"correct_predictions": 0, "total_matches": 0, "accuracy": 0},
            "value_indicator": "unknown"
        }


def calculate_naga_metrics_v2(data):
    """娜迦足量系统指标 v2.0"""
    try:
        rank_diff = data["standings"]["manutd_rank"] - data["standings"]["chelsea_rank"]
        h2h_analysis = calculate_h2h_odds_analysis(data["h2h"], data["market_odds"])

        odds = data["market_odds"]
        margin = 1/odds["home_win"] + 1/odds["draw"] + 1/odds["away_win"]

        prob_home = (1/odds["home_win"]) / margin * 100
        prob_draw = (1/odds["draw"]) / margin * 100
        prob_away = (1/odds["away_win"]) / margin * 100

        h2h_adjustment = h2h_analysis["avg_historical_return"] * 5
        adjusted_prob_home = min(95, max(5, prob_home + h2h_adjustment))

        ev_home = (adjusted_prob_home/100 * odds["home_win"]) - 1

        if rank_diff > 5 and h2h_analysis["value_indicator"] == "undervalued":
            strength_rating = "strong_home_value"
        elif rank_diff > 5:
            strength_rating = "strong_home"
        elif rank_diff > 0:
            strength_rating = "slight_home"
        else:
            strength_rating = "balanced"

        return {
            "strength_rating": strength_rating,
            "rank_diff": rank_diff,
            "base_probabilities": {
                "home_win": round(prob_home, 1),
                "draw": round(prob_draw, 1),
                "away_win": round(prob_away, 1)
            },
            "adjusted_probabilities": {
                "home_win": round(adjusted_prob_home, 1),
                "draw": round(prob_draw - h2h_adjustment/2, 1),
                "away_win": round(prob_away - h2h_adjustment/2, 1)
            },
            "expected_value": {
                "home": round(ev_home * 100, 2),
            },
            "margin": round(margin, 3),
            "h2h_analysis": h2h_analysis
        }
    except Exception as e:
        logger.error(f"Naga metrics calculation failed: {e}", exc_info=True)
        return {
            "strength_rating": "unknown",
            "rank_diff": 0,
            "base_probabilities": {"home_win": 0.0, "draw": 0.0, "away_win": 0.0},
            "adjusted_probabilities": {"home_win": 0.0, "draw": 0.0, "away_win": 0.0},
            "expected_value": {"home": 0.0},
            "margin": 0.0,
            "h2h_analysis": calculate_h2h_odds_analysis(data.get("h2h", []), data.get("market_odds", {}))
        }


def print_analysis(metrics, match_data):
    """打印分析报告"""
    try:
        print("=" * 70)
        print("    娜迦足球量化决策系统 v4.2 - H2H赔率回溯增强版")
        print("=" * 70)
        print()
        print("[比赛信息]")
        print(f"  对阵: {match_data['home_team']} vs {match_data['away_team']}")
        print(f"  联赛: {match_data['league']} (Premier League)")
        print(f"  日期: {match_data['match_date']} {match_data['kickoff']}")
        print(f"  场地: 斯坦福桥 ({match_data['home_team']}主场)")
        print()

        print("[基础实力评估]")
        print(f"  排名差距: 切尔西第{match_data['standings']['chelsea_rank']} vs 曼联第{match_data['standings']['manutd_rank']}")
        print(f"  近期状态: 切尔西 {match_data['chelsea_recent']['form_score']:.1f} vs 曼联 {match_data['manutd_recent']['form_score']:.1f}")
        print(f"  实力评级: {metrics['strength_rating']}")
        print()

        print("[历史交锋赔率回溯分析 - 核心升级]")
        print("-" * 70)
        h2h = metrics["h2h_analysis"]

        print(f"  切尔西主场交锋: {h2h['home_matches_count']}场")
        print(f"  实际获胜: {h2h['chelsea_home_actual_wins']}场")
        print(f"  赔率预期获胜: {h2h['chelsea_home_expected_wins']:.1f}场")
        print()

        print(f"  历史平均主场赔率: {h2h['avg_home_odds_historical']:.2f}")
        print(f"  当前主场赔率: {h2h['current_home_odds']:.2f}")
        print(f"  赔率变化: {h2h['odds_trend']:+.2f} ({h2h['value_indicator']})")
        print()

        print(f"  历史交锋平均回报: {h2h['avg_historical_return']:+.2f}%")
        me = h2h['market_efficiency']
        print(f"  市场定价准确率: {me['accuracy']*100:.0f}%")
        print(f"  ({me['correct_predictions']}/{me['total_matches']}场预测正确)")
        print()

        print("[概率模型对比]")
        print("-" * 70)
        print("                基础概率    调整后概率(H2H加权)")
        print(f"  主胜(切尔西):  {metrics['base_probabilities']['home_win']:>6}%    {metrics['adjusted_probabilities']['home_win']:>6}%")
        print(f"  平局:          {metrics['base_probabilities']['draw']:>6}%    {metrics['adjusted_probabilities']['draw']:>6}%")
        print(f"  客胜(曼联):    {metrics['base_probabilities']['away_win']:>6}%    {metrics['adjusted_probabilities']['away_win']:>6}%")
        print()

        print("[期望值分析 v2.0]")
        ev = metrics['expected_value']['home']
        print(f"  切尔西胜期望值: {ev:+.2f}% (基于调整后概率)")
        if ev > 0.05:
            print("  -> 正期望值，考虑投注")
        elif ev > -0.02:
            print("  -> 接近盈亏平衡")
        else:
            print("  -> 负期望值，不建议投注")
        print()

        print("[历史交锋详情 - 含赔率回溯]")
        print("-" * 70)
        for match in match_data['h2h']:
            venue = "主" if match['venue'] == "H" else "客"
            odds_str = f"[{match['odds']['home']}/{match['odds']['draw']}/{match['odds']['away']}]"
            return_str = f"回报:{match['actual_return']['home']:+.2f}" if match['venue'] == "H" else f"回报:{match['actual_return']['away']:+.2f}"
            print(f"  {match['date']} ({venue}): {match['result']} -> {match['winner']:6} {odds_str} {return_str}")
        print()

        print("[娜迦足量系统建议 v2.0]")
        print("=" * 70)

        h2h = metrics["h2h_analysis"]
        if ev < -0.02 and h2h['value_indicator'] != "undervalued":
            print("⚠️  风控拦截: 综合期望值不足")
            print(f"    原因: 调整后期望值{ev:+.2f}%，且赔率未明显低估")
            print(f"    历史交锋回报: {h2h['avg_historical_return']:+.2f}%")
            print("    建议: 观望")
        elif h2h['value_indicator'] == "undervalued" and ev > -0.05:
            bankroll = 10000
            kelly_fraction = 0.05

            p = metrics['adjusted_probabilities']['home_win'] / 100
            q = 1 - p
            b = match_data['market_odds']['home_win'] - 1

            kelly = (p * b - q) / b if b > 0 else 0
            kelly_compressed = max(0, kelly * kelly_fraction)
            stake = bankroll * kelly_compressed

            print("💡 投资建议 [H2H赔率价值发现]:")
            print(f"    方向: 切尔西胜")
            print(f"    理由: 赔率较历史平均高{h2h['odds_trend']:+.2f}，存在价值")
            print(f"    凯利比例: {kelly*100:.2f}%")
            print(f"    压缩后(5%): {kelly_compressed*100:.2f}%")
            print(f"    建议仓位: ¥{stake:.0f}")
            print(f"    信心指数: ★★★★☆ (中高)")
        else:
            print("⚠️  风控提示: 条件不满足")
            print(f"    赔率趋势: {h2h['value_indicator']}")
            print(f"    调整后期望值: {ev:+.2f}%")
            print("    建议: 观望")

        print()
        print("=" * 70)
        print("  系统: 娜迦足量 v4.2 | 风控: 精算师凯利≤5% | 功能: H2H赔率回溯")
        print("=" * 70)
    except Exception as e:
        logger.error(f"Print analysis failed: {e}", exc_info=True)
        print(f"\n[ERROR] 报告生成中断: {e}")


def main():
    try:
        metrics = calculate_naga_metrics_v2(MATCH_DATA)
        print_analysis(metrics, MATCH_DATA)
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        print(f"\n[ERROR] 系统异常，已优雅降级: {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
