import pandas as pd
df = pd.read_csv('D:/openclaw-workspace/football_quant_os/data/football_data_uk/worldcup2022.csv')
# 保存到JSON，避免编码问题
df.to_json('D:/openclaw-workspace/football_quant_os/data/football_data_uk/worldcup2022_preview.json', orient='records', force_ascii=False, indent=2)
print('OK')
