import pandas as pd
df = pd.read_csv('D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_2022_qatar/Fifa_WC_2022_Match_data.csv', encoding='latin-1')

print('=== 2022 World Cup Famous Upsets ===')
matches = [
    ('ARGENTINA', 'SAUDI ARABIA'),
    ('GERMANY', 'JAPAN'),
    ('MOROCCO', 'SPAIN'),
    ('BRAZIL', 'CROATIA')
]

for t1, t2 in matches:
    m = df[(df['1']==t1) & (df['2']==t2)]
    if len(m) == 0:
        # 可能主客场反过来
        m = df[(df['1']==t2) & (df['2']==t1)]
    print(f'{t1} vs {t2}: {len(m)} matches')
    if len(m) > 0:
        print(m[['date','1','2','1_goals','2_goals','score','1_xg','2_xg','1_poss','2_poss']].to_string(index=False))
        print()

# 查看所有比赛列表
print('\n=== All 2022 Matches ===')
print(df[['match_no','date','1','2','score']].to_string())
