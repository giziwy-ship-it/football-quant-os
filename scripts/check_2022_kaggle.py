import pandas as pd
df = pd.read_csv('D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_2022/international_matches.csv')
print('Rows:', len(df))
print('Columns:', list(df.columns))
print(df.head(3).to_json(force_ascii=False, orient='records'))
