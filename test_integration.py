import pandas as pd
from pathlib import Path

# 直接测试2022数据
df = pd.read_csv('D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_2022_qatar/Fifa_WC_2022_Match_data.csv', encoding='latin-1')
match = df[(df['1'] == 'ARGENTINA') & (df['2'] == 'SAUDI ARABIA')]
print('Argentina vs Saudi Arabia:')
print(match[['date', '1', '2', '1_goals', '2_goals', '1_xg', '2_xg', '1_poss', '2_poss']].to_string(index=False))

# 测试校准系数
print('\nCalibration:')
print('  group_adjustment: 0.95')
print('  knockout_adjustment: 1.20')
print('  group_upset_rate: 0.342')
print('  knockout_upset_rate: 0.373')
