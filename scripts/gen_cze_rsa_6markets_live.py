#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六盘口完整预测报告 - 捷克 vs 南非 (2026世界杯 A组第二轮)
数据来源: 500.com + oddsportal.com
风格: 彭博为主 + 融合Google/高盛/麦肯锡
"""

import sys
sys.path.insert(0, r'D:\openclaw-workspace\football_quant_os')

from scripts.predict import run_prediction
from reports.gen_pdf import generate_full_report
from features.group_stage_context import get_group_stage_context, format_context_for_display

# ============================================================
# 真实数据 (从500.com抓取)
# ============================================================

# 欧赔 (1X2)
ODDS_1X2 = {'home': 1.85, 'draw': 3.47, 'away': 4.45}

# 让球胜平负 (-1盘口)
ODDS_AH = {'home': 3.36, 'draw': 3.40, 'away': 1.86}  # 让球: 捷克-1

# 大小球 (2/2.5)
ODDS_OU = {'over': 0.97, 'under': 0.87, 'line': 2.25}

# 球队信息
HOME_TEAM = "捷克"
AWAY_TEAM = "南非"
HOME_RANK = 40
AWAY_RANK = 60
HOME_FIFA = 1505
AWAY_FIFA = 1428

# 小组赛积分榜 (第一轮后)
GROUP_STANDINGS = {
    'Mexico': {'points': 3, 'played': 1, 'goal_diff': 2, 'goals_for': 2},
    'Korea Republic': {'points': 3, 'played': 1, 'goal_diff': 1, 'goals_for': 2},
    'Czechia': {'points': 0, 'played': 1, 'goal_diff': -1, 'goals_for': 1},
    'South Africa': {'points': 0, 'played': 1, 'goal_diff': -2, 'goals_for': 0}
}

# 近期战绩
HOME_RECENT = {"wins": 4, "draws": 4, "losses": 2, "gf": 18, "ga": 10}
AWAY_RECENT = {"wins": 3, "draws": 3, "losses": 4, "gf": 12, "ga": 13}

# 历史对战
H2H_RECORD = "暂无历史交战记录"

# ============================================================
# 运行预测
# ============================================================

result = run_prediction(
    home='Czechia', away='South Africa',
    odds_home=ODDS_1X2['home'], odds_draw=ODDS_1X2['draw'], odds_away=ODDS_1X2['away'],
    stage='group', ou_line=2.25,
    odds_over=ODDS_OU['over'], odds_under=ODDS_OU['under'],
    home_xg=1.5, away_xg=1.0,
    home_poss=55, away_poss=45,
    is_first_match=False,
    home_region='europe', away_region='africa',
    home_experience='experienced', away_experience='experienced',
    group_standings=GROUP_STANDINGS,
    bankroll=100000, kelly_fraction=0.25
)

# 提取预测结果
m1x2 = result['markets']['1x2']
ou = result['markets']['over_under']

# 计算让球概率 (基于1X2概率 + 让球调整)
def calc_ah_prob(home_prob, draw_prob, away_prob, handicap=-1):
    """计算让球胜平负概率 ( handicap: 主队让球数 )"""
    # 简化模型: 让1球时，主队需要净胜2球才能让球胜
    # 使用泊松近似
    from math import exp, factorial
    
    # 从1X2概率反推λ
    total_prob = home_prob + draw_prob + away_prob
    home_prob_n = home_prob / total_prob
    draw_prob_n = draw_prob / total_prob
    away_prob_n = away_prob / total_prob
    
    lambda_h = -0.5 * (draw_prob_n + 2 * away_prob_n) / (home_prob_n - away_prob_n)
    lambda_a = -lambda_h
    
    # 让球调整
    lambda_h_adj = lambda_h - handicap * 0.5
    lambda_a_adj = lambda_a + handicap * 0.5
    
    # 计算让球结果概率
    ah_win = 0   # 主队让球胜
    ah_draw = 0  # 让球平
    ah_lose = 0  # 主队让球负
    
    for h_goals in range(6):
        for a_goals in range(6):
            p_h = (exp(-lambda_h_adj) * lambda_h_adj**h_goals) / factorial(max(1, h_goals))
            p_a = (exp(-lambda_a_adj) * lambda_a_adj**a_goals) / factorial(max(1, a_goals))
            p = p_h * p_a
            
            margin = h_goals - a_goals - handicap
            if margin > 0:
                ah_win += p
            elif margin == 0:
                ah_draw += p
            else:
                ah_lose += p
    
    total = ah_win + ah_draw + ah_lose
    return {
        'home': ah_win / total,
        'draw': ah_draw / total,
        'away': ah_lose / total
    }

ah_probs = calc_ah_prob(
    m1x2['model']['home'], m1x2['model']['draw'], m1x2['model']['away'],
    handicap=-1
)

# 计算半全场概率
def calc_htft_prob(home_prob, draw_prob, away_prob):
    """计算半全场概率 (基于半场模型: λ_half = λ_full * 0.45)"""
    from math import exp, factorial
    
    # 反推全场λ
    total = home_prob + draw_prob + away_prob
    hp = home_prob / total
    dp = draw_prob / total
    ap = away_prob / total
    
    lambda_h = -0.5 * (dp + 2 * ap) / (hp - ap) if hp != ap else 1.0
    lambda_a = -lambda_h
    
    # 半场λ
    lambda_h_h = lambda_h * 0.45
    lambda_a_h = lambda_a * 0.45
    
    # 全场λ (下半场)
    lambda_h_2 = lambda_h * 0.55
    lambda_a_2 = lambda_a * 0.55
    
    htft = {}
    for ht in ['H', 'D', 'A']:
        for ft in ['H', 'D', 'A']:
            prob = 0
            for h1 in range(4):
                for a1 in range(4):
                    p1_h = (exp(-lambda_h_h) * lambda_h_h**h1) / factorial(max(1, h1))
                    p1_a = (exp(-lambda_a_h) * lambda_a_h**a1) / factorial(max(1, a1))
                    
                    # 半场结果
                    if h1 > a1 and ht != 'H': continue
                    if h1 == a1 and ht != 'D': continue
                    if h1 < a1 and ht != 'A': continue
                    
                    for h2 in range(4):
                        for a2 in range(4):
                            p2_h = (exp(-lambda_h_2) * lambda_h_2**h2) / factorial(max(1, h2))
                            p2_a = (exp(-lambda_a_2) * lambda_a_2**a2) / factorial(max(1, a2))
                            
                            h_total = h1 + h2
                            a_total = a1 + a2
                            
                            if h_total > a_total and ft != 'H': continue
                            if h_total == a_total and ft != 'D': continue
                            if h_total < a_total and ft != 'A': continue
                            
                            prob += p1_h * p1_a * p2_h * p2_a
            
            htft[f"{ht}/{ft}"] = prob
    
    total = sum(htft.values())
    for k in htft:
        htft[k] /= total
    
    return htft

htft_probs = calc_htft_prob(
    m1x2['model']['home'], m1x2['model']['draw'], m1x2['model']['away']
)

# 计算比分概率
def calc_cs_prob(home_prob, draw_prob, away_prob):
    """计算正确比分概率"""
    from math import exp, factorial
    
    total = home_prob + draw_prob + away_prob
    hp = home_prob / total
    dp = draw_prob / total
    ap = away_prob / total
    
    lambda_h = -0.5 * (dp + 2 * ap) / (hp - ap) if hp != ap else 1.0
    lambda_a = -lambda_h
    
    cs = {}
    for h in range(5):
        for a in range(5):
            p_h = (exp(-lambda_h) * lambda_h**h) / factorial(max(1, h))
            p_a = (exp(-lambda_a) * lambda_a**a) / factorial(max(1, a))
            cs[f"{h}:{a}"] = p_h * p_a
    
    total = sum(cs.values())
    for k in cs:
        cs[k] /= total
    
    return dict(sorted(cs.items(), key=lambda x: -x[1])[:18])

cs_probs = calc_cs_prob(
    m1x2['model']['home'], m1x2['model']['draw'], m1x2['model']['away']
)

# 计算进球数概率
def calc_tg_prob(lambda_val):
    """计算总进球数概率"""
    from math import exp, factorial
    
    tg = {}
    for g in range(7):
        tg[str(g)] = (exp(-lambda_val) * lambda_val**g) / factorial(max(1, g))
    
    tg['7+'] = 1 - sum(tg.values())
    
    total = sum(tg.values())
    for k in tg:
        tg[k] /= total
    
    return tg

tg_probs = calc_tg_prob(ou['lambda'])

# ============================================================
# 生成报告数据
# ============================================================

report_data = {
    'match': {
        'home': HOME_TEAM,
        'away': AWAY_TEAM,
        'home_en': 'Czechia',
        'away_en': 'South Africa',
        'date': '2026-06-19',
        'time': '00:00',
        'stage': 'A组第二轮',
        'venue': '墨西哥城',
        'tournament': '2026美加墨世界杯'
    },
    'teams': {
        'home': {
            'rank': HOME_RANK,
            'fifa_points': HOME_FIFA,
            'recent': HOME_RECENT,
            'form': '4胜4平2负'
        },
        'away': {
            'rank': AWAY_RANK,
            'fifa_points': AWAY_FIFA,
            'recent': AWAY_RECENT,
            'form': '3胜3平4负'
        }
    },
    'standings': {
        'group': 'A组',
        'table': [
            {'team': '墨西哥', 'played': 1, 'w': 1, 'd': 0, 'l': 0, 'gf': 2, 'ga': 0, 'gd': 2, 'pts': 3},
            {'team': '韩国', 'played': 1, 'w': 1, 'd': 0, 'l': 0, 'gf': 2, 'ga': 1, 'gd': 1, 'pts': 3},
            {'team': '捷克', 'played': 1, 'w': 0, 'd': 0, 'l': 1, 'gf': 1, 'ga': 2, 'gd': -1, 'pts': 0},
            {'team': '南非', 'played': 1, 'w': 0, 'd': 0, 'l': 1, 'gf': 0, 'ga': 2, 'gd': -2, 'pts': 0}
        ]
    },
    'markets': {
        '1x2': {
            'odds': ODDS_1X2,
            'model_prob': m1x2['model'],
            'implied': m1x2['implied'],
            'edge': m1x2['edge'],
            'recommendation': m1x2.get('recommendations', ['N/A'])[0] if m1x2.get('recommendations') else 'N/A',
            'context_adjusted': m1x2.get('model', {}).get('context_adjusted', False)
        },
        'ah': {
            'handicap': -1,
            'odds': ODDS_AH,
            'model_prob': ah_probs,
            'recommendation': '让球客胜' if ah_probs['away'] > max(ah_probs['home'], ah_probs['draw']) else '让球主胜'
        },
        'ou': {
            'line': 2.25,
            'odds': ODDS_OU,
            'lambda': ou['lambda'],
            'model_prob': {
                'over': sum(tg_probs.get(str(g), 0) for g in range(3, 8)) + tg_probs.get('7+', 0),
                'under': sum(tg_probs.get(str(g), 0) for g in range(0, 3))
            },
            'recommendation': ou.get('recommendation', 'N/A')
        },
        'htft': {
            'probabilities': dict(sorted(htft_probs.items(), key=lambda x: -x[1])[:9]),
            'top_recommendation': max(htft_probs, key=htft_probs.get)
        },
        'cs': {
            'probabilities': cs_probs,
            'top_recommendation': max(cs_probs, key=cs_probs.get)
        },
        'tg': {
            'probabilities': tg_probs,
            'top_recommendation': max(tg_probs, key=tg_probs.get)
        }
    },
    'group_context': result.get('group_context', {}),
    'group_context_display': result.get('group_context_display', ''),
    'upset_score': result.get('upset_score', 0),
    'kelly': result.get('kelly', {}),
    'h2h': H2H_RECORD,
    'data_sources': [
        '500.com 欧赔/让球/大小球/数据分析',
        'oddsportal.com H2H历史对战',
        'FIFA官方排名 (2026年6月)'
    ]
}

# ============================================================
# 生成PDF
# ============================================================

from pathlib import Path
from datetime import datetime

output_path = Path(r"C:\Users\Administrator\Desktop") / f"预测报告_捷克vs南非_六盘口_{datetime.now().strftime('%Y%m%d')}.pdf"

try:
    from reports.gen_pdf import generate_full_report
    generate_full_report(report_data, str(output_path))
    print(f"✅ PDF报告已生成: {output_path}")
    print(f"   大小: {output_path.stat().st_size:,} bytes")
except Exception as e:
    print(f"❌ PDF生成失败: {e}")
    import json
    json_path = Path(r"C:\Users\Administrator\Desktop") / f"report_data_捷克vs南非_{datetime.now().strftime('%Y%m%d')}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print(f"📄 报告数据已保存: {json_path}")
