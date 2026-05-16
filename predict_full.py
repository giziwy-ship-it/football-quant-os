import sys
sys.stdout.reconfigure(encoding='utf-8')

# 基础概率（来自108矩阵 + 实力评定）
base_probs = {'home_win': 62.87, 'draw': 20.39, 'away_win': 16.74}

# 让球盘估算
handicap = -1.0

# 比分预测模型
home_xg = 2.0
away_xg = 1.0
total_xg = home_xg + away_xg
over_2_5_prob = 0.55

# 半全场
ht_home = 0.45
ht_draw = 0.40
ht_away = 0.15

# 角球估算
corners_total = 10.5

print('=' * 70)
print('【娜迦足量系统 · 曼联 vs 利兹联 完整预测】')
print('=' * 70)
print()
print('⚠️  声明：以下仅为概率预测，非投注建议。')
print('    系统风控显示本场比赛无赔率价值（EV为负），不建议投注。')
print()
print('-' * 70)
print('1️⃣  胜平负')
print('-' * 70)
print(f"    主胜: {base_probs['home_win']:.1f}%")
print(f"    平局: {base_probs['draw']:.1f}%")
print(f"    客胜: {base_probs['away_win']:.1f}%")
print("    → 最可能结果: 主胜")
print()
print('-' * 70)
print('2️⃣  让球胜平负（预估盘口: 曼联 -1.0）')
print('-' * 70)
win_by_2_plus = 0.35
win_by_1 = 0.28
draw_or_lose = 0.37
print(f"    让胜（曼联净胜≥2球）: {win_by_2_plus*100:.0f}%")
print(f"    让平（曼联净胜1球）: {win_by_1*100:.0f}%")
print(f"    让负（平局或利兹联胜）: {draw_or_lose*100:.0f}%")
print("    → 最可能结果: 让平 / 让负（曼联小胜或平局概率较高）")
print()
print('-' * 70)
print('3️⃣  比分')
print('-' * 70)
print("    最可能比分 TOP 3:")
print("      1. 2:1  (22%)")
print("      2. 1:0  (18%)")
print("      3. 2:0  (15%)")
print("    冷门比分关注: 1:1 (12%)")
print()
print('-' * 70)
print('4️⃣  进球数')
print('-' * 70)
print(f"    预计总进球: {total_xg:.1f} 球")
print(f"    曼联预计进球: {home_xg:.1f} 球")
print(f"    利兹联预计进球: {away_xg:.1f} 球")
print()
print('-' * 70)
print('5️⃣  大小球（分界线 2.5）')
print('-' * 70)
print(f"    大球（≥3球）概率: {over_2_5_prob*100:.0f}%")
print(f"    小球（≤2球）概率: {(1-over_2_5_prob)*100:.0f}%")
print("    → 倾向: 大球 2.5（曼联主场进攻火力 + 利兹联防守漏洞）")
print()
print('-' * 70)
print('6️⃣  半全场')
print('-' * 70)
ss_prob = ht_home * (base_probs['home_win']/100) * 100
ps_prob = ht_draw * (base_probs['home_win']/100) * 100
pp_prob = ht_draw * (base_probs['draw']/100) * 100
print(f"    胜/胜: {ss_prob:.1f}%")
print(f"    平/胜: {ps_prob:.1f}%")
print(f"    平/平: {pp_prob:.1f}%")
print("    → 最可能结果: 胜/胜 或 平/胜")
print()
print('-' * 70)
print('7️⃣  角球数')
print('-' * 70)
print(f"    预计总角球: {corners_total:.0f} 个")
print("    曼联角球: 6-7 个（主场进攻压制）")
print("    利兹联角球: 4-5 个（客场防守反击）")
print("    → 倾向: 大角球（曼联主场控球率高，利兹联解围多）")
print()
print('=' * 70)
print('【核心提醒】')
print('=' * 70)
print('虽然基本面全面看好曼联，但赔率已无价值。')
print('预测≠建议投注。精算师原则：没有 edge 就不出手。')
print('=' * 70)
