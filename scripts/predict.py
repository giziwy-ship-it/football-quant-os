#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 主预测脚本 (v5.0.0)
支持: 1X2 + 泊松大小球 + 多模型融合 + 阶段校准
架构: Orchestration Layer (模型逻辑已迁移至 models/)
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到路径 (models/ 在根目录)
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import HeuristicModel, PoissonModel, ModelEnsemble, XGBoostPredictor
from models.kelly_integration import get_kelly_recommendations
from features.group_stage_context import get_group_stage_context, adjust_for_group_stage_context, format_context_for_display


def create_ensemble() -> ModelEnsemble:
    """创建默认模型融合器"""
    ensemble = ModelEnsemble()

    # 添加启发式模型 (权重0.3)
    heuristic = HeuristicModel()
    ensemble.add_model(heuristic, weight=0.3)

    # 添加泊松模型 (权重0.5)
    poisson = PoissonModel()
    ensemble.add_model(poisson, weight=0.5)

    # 添加 XGBoost 模型 — 优先级：2026 CRI完整版 > 2022专用 > 三届完整 > 全历史 > 优化版 > v1
    xgb_loaded = False
    for version, weight, desc in [
        ('2026_cri_fifa_v4', 0.5, '2026 CRI+FIFA+位置 (34特征, 70.3% OU)'),   # 最完整
        ('worldcup_specialized', 0.4, '2022专用 (xG-rich, 71.9% OU)'),         # 有xG时最强
        ('three_world_cups_v3', 0.3, '三届完整 (FIFA+位置, 65.6% OU)'),         # 次选
        ('full_history_v2', 0.3, '全历史 (保守 backup)'),                       # 后备
        ('v2_optimized', 0.3, '俱乐部优化版'),
        ('v1', 0.2, '基础版'),
    ]:
        xgb_path = Path(__file__).parent.parent / 'models' / f'xgboost_{version}.pkl'
        if xgb_path.exists():
            try:
                xgb = XGBoostPredictor(model_path=str(xgb_path))
                if xgb.is_trained:
                    ensemble.add_model(xgb, weight=weight)
                    print(f"[Ensemble] XGBoost {version} ({desc}) loaded: OU={xgb._ou_accuracy:.1%}, 1X2={xgb._1x2_accuracy:.1%}")
                    xgb_loaded = True
            except Exception as e:
                print(f"[Ensemble] XGBoost {version} load failed: {e}")

    if not xgb_loaded:
        print(f"[Ensemble] XGBoost model not found")

    return ensemble


def run_prediction(home: str, away: str, odds_home: float, odds_draw: float, odds_away: float,
                   stage: str = 'group', **kwargs) -> Dict[str, Any]:
    """
    执行完整预测 (Orchestration Layer)

    1. 准备比赛信息
    2. 调用模型融合器预测
    3. 整合结果并返回
    """
    # 构建比赛信息
    match_info = {
        'home': home,
        'away': away,
        'odds_home': odds_home,
        'odds_draw': odds_draw,
        'odds_away': odds_away,
        'stage': stage,
    }

    # 添加可选参数
    optional_fields = [
        'home_xg', 'away_xg', 'home_poss', 'away_poss',
        'odds_over', 'odds_under', 'motivation', 'is_first_match',
        'home_region', 'away_region', 'home_experience', 'away_experience',
        'xg_bias'
    ]
    for field in optional_fields:
        if field in kwargs and kwargs[field] is not None:
            match_info[field] = kwargs[field]

    # 创建模型融合器
    ensemble = create_ensemble()

    # 执行预测
    prediction = ensemble.predict(match_info, line=kwargs.get('ou_line', 2.5))

    if 'error' in prediction:
        return {
            'match': f'{home} vs {away}',
            'timestamp': datetime.now().isoformat(),
            'version': '5.0.0',
            'stage': stage,
            'error': prediction['error']
        }

    # 整合结果
    result = {
        'match': f'{home} vs {away}',
        'timestamp': datetime.now().isoformat(),
        'version': '5.1.0',
        'stage': stage,
        'models': prediction['metadata']['models_used'],
        'weights': prediction['metadata']['weights'],
        'confidence': prediction['confidence'],
        'markets': prediction['markets']
    }
    
    # 小组赛上下文调整 (v5.1新增)
    group_standings = kwargs.get('group_standings', None)
    if group_standings and stage == 'group':
        try:
            context = get_group_stage_context(home, away, group_standings)
            if '1x2' in prediction['markets']:
                m1x2 = prediction['markets']['1x2']
                base_probs = {
                    'home': m1x2['model']['home'],
                    'draw': m1x2['model']['draw'],
                    'away': m1x2['model']['away']
                }
                adjusted = adjust_for_group_stage_context(base_probs, context)
                prediction['markets']['1x2']['model'] = adjusted
                prediction['markets']['1x2']['model']['context_adjusted'] = True
                prediction['markets']['1x2']['group_context'] = context
                
                # 重新计算Edge
                imp = m1x2['implied']
                prediction['markets']['1x2']['edge'] = {
                    'home': round(adjusted['home'] - imp['home'], 3),
                    'draw': round(adjusted['draw'] - imp['draw'], 3),
                    'away': round(adjusted['away'] - imp['away'], 3)
                }
                
                # 重新生成推荐
                new_recs = []
                edge = prediction['markets']['1x2']['edge']
                if edge['home'] > 0.02:
                    new_recs.append(f"主胜 ({edge['home']:+.1%})")
                if edge['draw'] > 0.02:
                    new_recs.append(f"平局 ({edge['draw']:+.1%})")
                if edge['away'] > 0.02:
                    new_recs.append(f"客胜 ({edge['away']:+.1%})")
                prediction['markets']['1x2']['recommendations'] = new_recs
                
                result['group_context'] = context
                result['group_context_display'] = format_context_for_display(context)
        except Exception as e:
            result['group_context_error'] = str(e)

    # 提取推荐
    recommendations = []
    if '1x2' in prediction['markets']:
        m1x2 = prediction['markets']['1x2']
        if 'recommendations' in m1x2:
            recommendations.extend(m1x2['recommendations'])
        elif 'prediction' in m1x2:
            recommendations.append(f"1X2: {m1x2['prediction']} (conf: {m1x2.get('confidence', 0):.1%})")

    if 'over_under' in prediction['markets']:
        ou = prediction['markets']['over_under']
        if 'recommendation' in ou and ou['recommendation'] != 'No Edge':
            recommendations.append(f"大小球{ou.get('line', 2.5)}: {ou['recommendation']}")
        elif 'prediction' in ou:
            recommendations.append(f"大小球{ou.get('line', 2.5)}: {ou['prediction']}")

    result['recommendations'] = recommendations

    # 冷门评分
    upset_score = 0
    if 'upset_score' in prediction['markets']:
        upset_score = prediction['markets']['upset_score']
    elif '1x2' in prediction['markets']:
        # 从1X2计算
        m1x2 = prediction['markets']['1x2']
        if 'implied' in m1x2 and 'model' in m1x2 and 'edge' in m1x2:
            mkt_home = m1x2['implied']['home']
            mod_home = m1x2['model']['home']
            upset_score = int((1 - mod_home) * 30 + abs(m1x2['edge']['away']) * 50)
            upset_score = min(upset_score, 65)
        elif 'confidence' in m1x2:
            upset_score = int((1 - m1x2.get('home', 0.33)) * 30 + m1x2.get('confidence', 0) * 20)
            upset_score = min(upset_score, 65)

    result['upset_score'] = upset_score

    # 计算Kelly注码 (v5.0 Kelly集成)
    bankroll = kwargs.get('bankroll', 100000.0)
    kelly_fraction = kwargs.get('kelly_fraction', 0.25)

    kelly_recs = get_kelly_recommendations(result, bankroll, kelly_fraction)
    result['kelly'] = {
        'bankroll': bankroll,
        'fraction': kelly_fraction,
        'recommendations': kelly_recs
    }

    return result


def main():
    parser = argparse.ArgumentParser(description='Football Quant OS - Prediction Engine v5.0.0')
    parser.add_argument('--home', required=True, help='主队名称')
    parser.add_argument('--away', required=True, help='客队名称')
    parser.add_argument('--odds-home', type=float, required=True, help='主胜赔率')
    parser.add_argument('--odds-draw', type=float, required=True, help='平局赔率')
    parser.add_argument('--odds-away', type=float, required=True, help='客胜赔率')
    parser.add_argument('--stage', choices=['group', 'knockout', 'final'], default='group', help='比赛阶段')

    # 泊松大小球参数
    parser.add_argument('--ou-line', type=float, default=2.5, help='大小球盘口线')
    parser.add_argument('--home-xg', type=float, help='主队xG')
    parser.add_argument('--away-xg', type=float, help='客队xG')
    parser.add_argument('--home-poss', type=float, help='主队控球率(%%%)')
    parser.add_argument('--away-poss', type=float, help='客队控球率(%%%)')
    parser.add_argument('--odds-over', type=float, help='大球赔率')
    parser.add_argument('--odds-under', type=float, help='小球赔率')

    # 5因子参数
    parser.add_argument('--motivation', choices=['must_win', 'can_draw', 'qualified', 'neutral'],
                        default='neutral', help='战意因子')
    parser.add_argument('--first-match', action='store_true', help='是否首战')
    parser.add_argument('--home-region',
                        choices=['asia', 'europe', 'south_america', 'africa', 'north_america', 'oceania', 'neutral'],
                        default='neutral', help='主队区域 (FIFA 6大洲际联合会)')
    parser.add_argument('--away-region',
                        choices=['asia', 'europe', 'south_america', 'africa', 'north_america', 'oceania', 'neutral'],
                        default='neutral', help='客队区域 (FIFA 6大洲际联合会)')
    parser.add_argument('--home-exp', choices=['newbie', 'experienced', 'neutral'],
                        default='experienced', help='主队经验')
    parser.add_argument('--away-exp', choices=['newbie', 'experienced', 'neutral'],
                        default='experienced', help='客队经验')
    parser.add_argument('--xg-bias', type=float, default=0.0, help='xG偏差修正(-0.2~+0.2)')
    
    # Kelly 注码参数
    parser.add_argument('--bankroll', type=float, default=100000.0, help='总资金(默认100k)')
    parser.add_argument('--kelly-fraction', type=float, default=0.25, 
                        help='Kelly分数: 保守0.25/标准0.5/激进1.0')
    
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='输出格式')
    args = parser.parse_args()

    result = run_prediction(
        args.home, args.away, args.odds_home, args.odds_draw, args.odds_away, stage=args.stage,
        ou_line=args.ou_line, home_xg=args.home_xg, away_xg=args.away_xg,
        home_poss=args.home_poss, away_poss=args.away_poss,
        odds_over=args.odds_over, odds_under=args.odds_under,
        motivation=args.motivation, is_first_match=args.first_match,
        home_region=args.home_region, away_region=args.away_region,
        home_experience=args.home_exp, away_experience=args.away_exp,
        xg_bias=args.xg_bias,
        bankroll=args.bankroll, kelly_fraction=args.kelly_fraction
    )

    if args.format == 'json':
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"\n=== {result['match']} | Stage: {result['stage']} ===")
        print(f"Models: {', '.join(result['models'])} (weights: {result['weights']})")
        print(f"Confidence: {result['confidence']}")
        print(f"Upset Score: {result['upset_score']}")

        for market, data in result['markets'].items():
            print(f"\n[{market.upper()}]")
            if market == '1x2':
                if 'implied' in data and 'model' in data:
                    print(f"  Implied: {data['implied']}")
                    print(f"  Model: {data['model']}")
                    print(f"  Edge: {data['edge']}")
                    print(f"  Recommendations: {data.get('recommendations', [])}")
                else:
                    print(f"  Probabilities: {data}")
            elif market == 'over_under':
                if 'lambda' in data:
                    print(f"  lambda={data.get('lambda')}, Line={data.get('line')}")
                print(f"  Over: {data['over_prob']} | Under: {data['under_prob']}")
                print(f"  Recommendation: {data['recommendation']} (Edge: {data.get('edge', 0)})")

        print(f"\nAll Recommendations:")
        for rec in result.get('recommendations', []):
            print(f"  - {rec}")
        
        # Kelly 注码推荐 (v5.0)
        kelly = result.get('kelly', {})
        if kelly and kelly.get('recommendations'):
            print(f"\n[Kelly注码 | Bankroll: ${kelly['bankroll']:.0f} | Fraction: {kelly['fraction']}]")
            for rec in kelly['recommendations']:
                opp = rec['opportunity']
                stake = rec['stake']
                if stake['action'] == 'bet':
                    print(f"  [BET] {opp.selection}: ${stake['stake']:.2f} (Kelly: {stake['kelly_pct']}%, EV: {stake['expected_value']:.1f}%)")
                else:
                    print(f"  [SKIP] {opp.selection}: {stake.get('reason', 'skipped')} (Kelly: {stake.get('kelly_pct', 'N/A')})")


if __name__ == '__main__':
    main()
