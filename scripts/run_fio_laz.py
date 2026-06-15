import asyncio
import sys
sys.stdout.reconfigure(encoding='utf-8')

from app.tasks import run_match_task

# 从500彩票网和OddsPortal抓取的真实数据
match = {
    'home_team': '佛罗伦萨',
    'away_team': '拉齐奥',
    'league': 'Serie A',
    'home_team_rank': 16,
    'away_team_rank': 9,
    'home_recent_5': ['L', 'W', 'D', 'W', 'D'],  # 水晶宫负、维罗纳胜、国米平、克雷莫纳胜、帕尔马平
    'away_recent_5': ['D', 'W', 'W', 'W', 'L'],  # 帕尔马平、博洛尼亚胜、米兰胜、萨索洛胜、都灵负
    'home_team_genes': {
        '逆转基因': 0.35,    # 主场战绩差，逆转能力一般
        '追平基因': 0.55,    # 主场6平，追平能力强
        '守住基因': 0.30,    # 主场胜率仅20%
        '痛失好局基因': 0.45, # 主场6负
        '被追平基因': 0.50,  # 主场多次被追平
        '平局大师基因': 0.40  # 主场平局多
    },
    'away_team_genes': {
        '逆转基因': 0.40,
        '追平基因': 0.45,    # 客场6平
        '守住基因': 0.50,    # 客场相对稳定
        '痛失好局基因': 0.30,
        '被追平基因': 0.40,
        '平局大师基因': 0.35
    },
    # OddsPortal 平均赔率
    'market_odds': {'home_win': 2.33, 'draw': 3.15, 'away_win': 3.35},
    'bankroll': 10000
}

async def main():
    result = await run_match_task(match)
    print()
    print('='*70)
    print('【娜迦足量系统 · 佛罗伦萨 vs 拉齐奥 真实数据分析】')
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
        print(f"联赛: {result['match']['league']} | 时间: 2026-04-14 02:45")
        print(f"状态: {result['status']}")
        print()
        print('【实力评定】')
        ts = result['team_strengths']
        print(f"  佛罗伦萨: {ts['home_team']['adjusted_level']} (评分{ts['home_team']['strength_score']}, 排名{ts['home_team']['league_rank']})")
        print(f"  拉齐奥: {ts['away_team']['adjusted_level']} (评分{ts['away_team']['strength_score']}, 排名{ts['away_team']['league_rank']})")
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
    print('  佛罗伦萨近10场: 5胜2平3负，进11失13')
    print('  拉齐奥近10场: 3胜5平2负，进11失11')
    print('  佛罗伦萨主场: 3胜6平6负，胜率20%')
    print('  拉齐奥客场: 4胜6平5负，胜率27%')
    print('  历史交锋: 佛罗伦萨3胜2平1负（近6次）')
    print('  赔率: 主胜2.33 | 平局3.15 | 客胜3.35（平均）')
    print('='*70)

asyncio.run(main())
