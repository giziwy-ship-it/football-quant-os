import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.tasks import run_match_task

# 从500彩票网和OddsPortal抓取的真实数据
match = {
    'home_team': '曼联',
    'away_team': '利兹联',
    'league': 'EPL',
    'home_team_rank': 3,
    'away_team_rank': 15,
    'home_recent_5': ['D', 'W', 'L', 'W', 'W'],  # 伯恩茅斯平、维拉胜、纽卡负、水晶宫胜、埃弗顿胜
    'away_recent_5': ['D', 'D', 'D', 'L', 'L'],  # 西汉姆平、布伦特福德平、水晶宫平、桑德兰负、曼城负
    'home_team_genes': {
        '逆转基因': 0.45,    # 阿森纳客场逆转等
        '追平基因': 0.50,    # 伯恩茅斯2:2追平
        '守住基因': 0.65,    # 主场10胜3平2负，胜率67%
        '痛失好局基因': 0.20,
        '被追平基因': 0.30,  # 伯恩茅斯被追平
        '平局大师基因': 0.15
    },
    'away_team_genes': {
        '逆转基因': 0.20,    # 客场战绩极差
        '追平基因': 0.60,    # 大量平局（6场平）
        '守住基因': 0.25,    # 客场1胜7平7负
        '痛失好局基因': 0.40, # 客场输球多
        '被追平基因': 0.55,  # 平局大师
        '平局大师基因': 0.45  # 10场6平
    },
    # OddsPortal 平均赔率
    'market_odds': {'home_win': 1.58, 'draw': 4.31, 'away_win': 5.73},
    'bankroll': 10000
}

async def main():
    result = await run_match_task(match)
    print()
    print('='*70)
    print('【娜迦足量系统 · 真实数据分析结果】')
    print('='*70)
    
    if result['status'] == 'blocked':
        print(f"比赛: {match['home_team']} vs {match['away_team']}")
        print(f"状态: ⛔ BLOCKED（被风控拦截）")
        print(f"风险等级: {result.get('risk_level', 'HIGH')}")
        print()
        print('⚠️ 拦截原因:')
        for w in result.get('warnings', []):
            print(f'  - {w}')
    else:
        print(f"比赛: {result['match']['home_team']} vs {result['match']['away_team']}")
        print(f"联赛: {result['match']['league']} | 时间: 2026-04-14 03:00")
        print(f"状态: {result['status']}")
        print()
        print('【实力评定】')
        ts = result['team_strengths']
        print(f"  曼联: {ts['home_team']['adjusted_level']} (评分{ts['home_team']['strength_score']}, 排名{ts['home_team']['league_rank']})")
        print(f"  利兹联: {ts['away_team']['adjusted_level']} (评分{ts['away_team']['strength_score']}, 排名{ts['away_team']['league_rank']})")
        print(f"  实力差距: {ts['matchup_type']} (分差{ts['adjusted_diff']})")
        print()
        print('【108矩阵】')
        probs = result['matrix_108']['probabilities']
        print(f"  主胜{probs['home_win']}% | 平局{probs['draw']}% | 客胜{probs['away_win']}%")
        print()
        print('【基因洞察】')
        print(f"  {result['gene_analysis'].get('insight', 'N/A')}")
        print()
        print('【Agent决策】')
        dec = result['decision']
        print(f"  推荐: {dec.get('recommended_outcome', 'N/A')}")
        print(f"  信心度: {dec.get('confidence', 0)*100:.0f}%")
        print(f"  预测概率: 主胜{dec['prediction']['home_win']}% | 平局{dec['prediction']['draw']}% | 客胜{dec['prediction']['away_win']}%")
        print()
        print('【资金建议】')
        stake = result['stake']
        print(f"  凯利比例: {stake['safe_fraction']*100:.2f}%")
        print(f"  建议投注: {stake['stake']:.0f}")
        print(f"  风险等级: {stake['risk_level']}")
        print(f"  期望收益: {stake['expected_value']:+.1f}%")
        print()
        if result.get('risk_control', {}).get('warnings'):
            print('⚠️ 风险警告:')
            for w in result['risk_control']['warnings']:
                print(f'  - {w}')
    
    print('='*70)
    print()
    print('【数据摘要 - 来源: 500彩票网 + OddsPortal】')
    print('  曼联近10场: 7胜2平1负，进20失11')
    print('  利兹联近10场: 2胜6平2负，进12失9')
    print('  曼联主场: 10胜3平2负，胜率67%')
    print('  利兹联客场: 1胜7平7负，胜率7%')
    print('  历史交锋: 曼联3胜3平0负（近6次）')
    print('  赔率: 主胜1.58 | 平局4.31 | 客胜5.73（平均）')
    print('='*70)

asyncio.run(main())
