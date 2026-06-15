import sys
sys.path.insert(0, 'D:/openclaw-workspace/football_quant_os/scripts')
from predict import calculate_ou_poisson

print("=" * 70)
print("泊松大小球模型 v2.1 - 5因子优化效果对比")
print("=" * 70)

# 基础参数
home, away = '澳大利亚', '土耳其'
stage = 'group'
home_xg, away_xg = 0.74, 0.61
home_odds, away_odds = 5.20, 1.70

# 测试1: 无因子（基准）
print("\n【测试1】基准（无任何因子）")
r1 = calculate_ou_poisson(home, away, stage, home_xg=home_xg, away_xg=away_xg)
print(f"  lambda={r1['lambda']}, Over={r1['over_prob']}, Under={r1['under_prob']}")

# 测试2: 首战因子（强队=土耳其，弱队=澳大利亚）
print("\n【测试2】首战因子")
r2 = calculate_ou_poisson(home, away, stage, home_xg=home_xg, away_xg=away_xg,
                           is_first_match=True, home_odds=home_odds, away_odds=away_odds)
print(f"  强队(土耳其)首战保守0.85，弱队(澳大利亚)首战激进1.20")
print(f"  lambda={r2['lambda']}, Over={r2['over_prob']}, Under={r2['under_prob']}")

# 测试3: 战意因子
print("\n【测试3】战意因子")
r3 = calculate_ou_poisson(home, away, stage, home_xg=home_xg, away_xg=away_xg,
                           motivation='must_win')
print(f"  must_win=1.10")
print(f"  lambda={r3['lambda']}, Over={r3['over_prob']}, Under={r3['under_prob']}")

# 测试4: 区域因子（亚洲vs欧洲）
print("\n【测试4】区域因子（亚洲vs欧洲）")
r4 = calculate_ou_poisson(home, away, stage, home_xg=home_xg, away_xg=away_xg,
                           home_region='asia', away_region='europe')
print(f"  亚洲vs欧洲=1.15")
print(f"  lambda={r4['lambda']}, Over={r4['over_prob']}, Under={r4['under_prob']}")

# 测试5: 新军因子
print("\n【测试5】新军因子")
r5 = calculate_ou_poisson(home, away, stage, home_xg=home_xg, away_xg=away_xg,
                           home_experience='newbie')
print(f"  新军=0.85")
print(f"  lambda={r5['lambda']}, Over={r5['over_prob']}, Under={r5['under_prob']}")

# 测试6: 全部因子叠加
print("\n【测试6】全部5因子叠加")
r6 = calculate_ou_poisson(home, away, stage, home_xg=home_xg, away_xg=away_xg,
                           is_first_match=True, home_odds=home_odds, away_odds=away_odds,
                           motivation='must_win',
                           home_region='asia', away_region='europe',
                           home_experience='newbie')
print(f"  lambda={r6['lambda']}, Over={r6['over_prob']}, Under={r6['under_prob']}")
print(f"  因子详情: {r6['factors_applied']}")

print("\n" + "=" * 70)
print("对比总结")
print("=" * 70)
print(f"基准 lambda:     {r1['lambda']}")
print(f"首战因子:        {r2['lambda']} (变化: {r2['lambda']-r1['lambda']:+.2f})")
print(f"战意因子:        {r3['lambda']} (变化: {r3['lambda']-r1['lambda']:+.2f})")
print(f"区域因子:        {r4['lambda']} (变化: {r4['lambda']-r1['lambda']:+.2f})")
print(f"新军因子:        {r5['lambda']} (变化: {r5['lambda']-r1['lambda']:+.2f})")
print(f"全部叠加:        {r6['lambda']} (变化: {r6['lambda']-r1['lambda']:+.2f})")
