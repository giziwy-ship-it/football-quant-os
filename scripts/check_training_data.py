import json

with open('D:/openclaw-workspace/football_quant_os/data/training/football_data_training.json', 'r') as f:
    data = json.load(f)

print('First sample:')
print(json.dumps(data[0], indent=2)[:1000])

print('\n')

# Check if scores exist
has_scores = sum(1 for d in data if 'home_score' in d and 'away_score' in d)
print(f'Samples with scores: {has_scores}/{len(data)}')

if has_scores > 0:
    for i in range(5):
        d = data[i]
        if 'home_score' in d:
            home_team = d['home']['team']
            away_team = d['away']['team']
            print(f'  {home_team} vs {away_team}: {d["home_score"]}:{d["away_score"]}')

# Check 1x2 labels
home_wins = sum(1 for d in data if d.get('home_score', 0) > d.get('away_score', 0))
draws = sum(1 for d in data if d.get('home_score', 0) == d.get('away_score', 0))
away_wins = sum(1 for d in data if d.get('home_score', 0) < d.get('away_score', 0))

print(f'\n1X2 distribution:')
print(f'  Home wins: {home_wins} ({100*home_wins/len(data):.1f}%)')
print(f'  Draws: {draws} ({100*draws/len(data):.1f}%)')
print(f'  Away wins: {away_wins} ({100*away_wins/len(data):.1f}%)')
