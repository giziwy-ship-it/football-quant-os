import pandas as pd
from pathlib import Path

file = Path(r'D:\openclaw-workspace\football_quant_os\data\football_data_uk\worldcup2022.csv')
if file.exists():
    df = pd.read_csv(file)
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)[:20]}")
    print(f"First match: {df.iloc[0]['HomeTeam']} vs {df.iloc[0]['AwayTeam']}")
    print(f"Result: {df.iloc[0]['FTHG']}-{df.iloc[0]['FTAG']} ({df.iloc[0]['FTR']})")
else:
    print("File not found")
