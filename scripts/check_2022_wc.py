import pandas as pd
df = pd.read_csv('D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_2022/international_matches.csv')
# 筛选2022世界杯数据
wc_2022 = df[df['tournament'] == 'FIFA World Cup']
print('2022 World Cup matches:', len(wc_2022))
print('Date range:', wc_2022['date'].min(), 'to', wc_2022['date'].max())
print(wc_2022[['date', 'home_team', 'away_team', 'home_team_score', 'away_team_score', 'home_team_fifa_rank', 'away_team_fifa_rank']].head(10).to_json(force_ascii=False, orient='records'))
