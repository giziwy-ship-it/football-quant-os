import sys
sys.path.insert(0, 'D:/openclaw-workspace/football_quant_os/scripts')
from predict import run_prediction, calculate_ou_poisson

# 测试1: 基础大小球
result = calculate_ou_poisson('澳大利亚', '土耳其', 'group', line=2.5)
print('Test 1 (Basic OU):')
print(f"  lambda={result['lambda']}, Over={result['over_prob']}, Under={result['under_prob']}")
print(f"  Recommendation: {result['recommendation']}")

# 测试2: 带xG
result2 = calculate_ou_poisson('澳大利亚', '土耳其', 'group', home_xg=0.74, away_xg=0.61, line=2.5)
print('\nTest 2 (With xG):')
print(f"  lambda={result2['lambda']}, Over={result2['over_prob']}, Under={result2['under_prob']}")
print(f"  Recommendation: {result2['recommendation']}")

# 测试3: 完整预测
result3 = run_prediction('澳大利亚', '土耳其', 5.20, 3.67, 1.70, 'group', home_xg=0.74, away_xg=0.61)
print('\nTest 3 (Full Prediction):')
print(f"  Match: {result3['match']}")
print(f"  Upset Score: {result3['upset_score']}")
print(f"  1X2: {result3['markets'].get('1x2', {}).get('recommendations', [])}")
print(f"  OU: λ={result3['markets']['over_under']['lambda']}, "
      f"Over={result3['markets']['over_under']['over_prob']}, "
      f"Rec={result3['markets']['over_under']['recommendation']}")
print(f"  All Recommendations: {result3['recommendations']}")
