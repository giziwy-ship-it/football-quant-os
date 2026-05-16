import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.tasks import run_match_task

match = {
    'home_team': '曼联',
    'away_team': '利兹联',
    'league': 'EPL',
    'home_team_rank': 6,
    'away_team_rank': 15,
    'home_recent_5': ['W', 'D', 'W', 'L', 'W'],
    'away_recent_5': ['L', 'L', 'D', 'L', 'L'],
    'home_team_genes': {
        '逆转基因': 0.45,
        '追平基因': 0.50,
        '守住基因': 0.55,
        '痛失好局基因': 0.30,
        '被追平基因': 0.35,
        '平局大师基因': 0.20
    },
    'away_team_genes': {
        '逆转基因': 0.25,
        '追平基因': 0.40,
        '守住基因': 0.30,
        '痛失好局基因': 0.50,
        '被追平基因': 0.45,
        '平局大师基因': 0.35
    },
    'market_odds': {'home_win': 1.65, 'draw': 3.80, 'away_win': 5.20},
    'bankroll': 10000
}

async def main():
    result = await run_match_task(match)
    print()
    print('='*60)
    print('【娜迦足量系统 · 分析结果】')
    print('='*60)
    
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
        print(f"状态: {result['status']}")
        print(f"决策: {result['decision'].get('recommended_outcome', 'N/A')}")
        print(f"信心度: {result['decision'].get('confidence', 0)*100:.0f}%")
        print(f"实力差距: {result['team_strengths'].get('matchup_type', 'N/A')}")
        probs = result['matrix_108']['probabilities']
        print(f"108矩阵: 主胜{probs['home_win']}% | 平局{probs['draw']}% | 客胜{probs['away_win']}%")
        print(f"基因洞察: {result['gene_analysis'].get('insight', 'N/A')}")
        print(f"凯利比例: {result['stake']['safe_fraction']*100:.2f}%")
        print(f"建议投注: {result['stake']['stake']:.0f}")
        print(f"风险等级: {result['stake']['risk_level']}")
        print(f"期望收益: {result['stake']['expected_value']:+.1f}%")
        if result.get('risk_control', {}).get('warnings'):
            print()
            print('⚠️ 风险警告:')
            for w in result['risk_control']['warnings']:
                print(f'  - {w}')
    print('='*60)

asyncio.run(main())
