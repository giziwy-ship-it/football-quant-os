import json
import sys
sys.path.insert(0, '.')

# 加载数据
with open('data/bayern_psg_raw.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 计算概率
def american_to_prob(odds_str):
    odd = int(odds_str)
    if odd > 0:
        return 100 / (odd + 100)
    else:
        return abs(odd) / (abs(odd) + 100)

# 取 Fanduel 赔率（最高赔付）
home_odd = data['odds_1x2']['sources']['fanduel']['home']
draw_odd = data['odds_1x2']['sources']['fanduel']['draw']
away_odd = data['odds_1x2']['sources']['fanduel']['away']

home_prob = american_to_prob(home_odd)
draw_prob = american_to_prob(draw_odd)
away_prob = american_to_prob(away_odd)

# 归一化
total = home_prob + draw_prob + away_prob
home_prob_norm = home_prob / total
draw_prob_norm = draw_prob / total
away_prob_norm = away_prob / total

print('='*70)
print(' 拜仁慕尼黑 vs 巴黎圣日耳曼 - 初始预测')
print('='*70)
print('\n[比赛信息]')
print(f'  时间: {data["match"]["datetime"]}')
print(f'  赛事: {data["match"]["competition"]}')
print(f'  首回合: {data["match"]["first_leg"]}')

print('\n[市场赔率 (Fanduel - 最高赔付率)]')
print(f'  主胜 (拜仁): {home_odd} -> {home_prob_norm*100:.2f}%')
print(f'  平局:        {draw_odd} -> {draw_prob_norm*100:.2f}%')
print(f'  客胜 (PSG):  {away_odd} -> {away_prob_norm*100:.2f}%')

print('\n[用户预测 (OddsPortal 社区)]')
up = data['user_predictions']
print(f'  主胜: {up["home_win"]} | 平局: {up["draw"]} | 客胜: {up["away_win"]}')

print('\n[近期战绩]')
print('  拜仁 (最近5场):')
for m in data['form_home_last5']:
    comp_short = m['competition'][:10]
    print(f'    {m["date"]} {comp_short:10} {m["venue"]} vs {m["opponent"]:20} {m["score"]:7} -> {m["result"]}')
print('  PSG (最近5场):')
for m in data['form_away_last5']:
    comp_short = m['competition'][:10]
    print(f'    {m["date"]} {comp_short:10} {m["venue"]} vs {m["opponent"]:20} {m["score"]:7} -> {m["result"]}')

print('\n[H2H 历史 (最近5次)]')
for m in data['h2h_last5']:
    print(f'  {m["date"]:20} {m["home"]:15} {m["score"]:7} {m["away"]:15} -> 胜方: {m["winner"]}')

print('\n[Match Facts]')
mf = data['match_facts']
print(f'  拜仁近5场胜率: {mf["bayern_last5"]}')
print(f'  PSG近5场胜率:  {mf["psg_last5"]}')
print(f'  拜仁近5场大2.5: {mf["over_2_5"]["bayern"]}')
print(f'  PSG近5场大2.5:  {mf["over_2_5"]["psg"]}')
print(f'  拜仁近5场BTTS:  {mf["btts_yes"]["bayern"]}')
print(f'  PSG近5场BTTS:   {mf["btts_yes"]["psg"]}')

print('\n[初始概率推断]')
print(f'  市场隐含: 主胜 {home_prob_norm*100:.1f}% | 平 {draw_prob_norm*100:.1f}% | 客胜 {away_prob_norm*100:.1f}%')
print(f'  用户预测: 主胜 80% | 平 8% | 客胜 12%')
print(f'  综合倾向: 拜仁主场优势明显，但首回合1-5惨败给PSG，PSG状态火热(5连胜)')
print(f'           市场给拜仁主场让球(-167)，但用户极度看好拜仁(80%)')
print(f'           分歧点: 市场更谨慎，用户更乐观')

print('\n' + '='*70)
print(' 数据已保存至 data/bayern_psg_raw.json')
print(' 建议下一步: 调用 Football Quant OS 深度分析 Pipeline')
print('='*70)
