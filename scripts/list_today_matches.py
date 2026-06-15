import json, urllib.request, sys
sys.stdout.reconfigure(encoding='utf-8')

# 获取今天和明天的赛程
for date in ['2026-05-30', '2026-05-31', '2026-06-01']:
    url = f'http://localhost:8000/api/v1/fixtures/date/{date}'
    req = urllib.request.Request(url, headers={'Content-Type': 'application/json'})
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read().decode())
        
        print(f"\n=== {date} ({data['total']} 场) ===")
        
        # 筛选重要比赛
        important_leagues = ['UEFA Champions League', 'Premier League', 'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'Europa League', 'Conference League']
        
        for f in data['fixtures']:
            league_en = f.get('league_en', '')
            league = f.get('league', '')
            
            # 检查是否是重要联赛或包含知名球队
            is_important = any(l.lower() in league_en.lower() or l.lower() in league.lower() 
                              for l in important_leagues)
            
            known_teams = ['real madrid', 'barcelona', 'atletico', 'manchester', 'liverpool', 'arsenal', 'chelsea', 'tottenham', 'bayern', 'dortmund', 'juventus', 'inter', 'milan', 'napoli', 'psg', 'lyon', 'ajax', 'porto', 'benfica', 'sporting', 'celtic', 'rangers', 'feyenoord', 'monaco', 'marseille', 'roma', 'lazio', 'atalanta', 'fiorentina', 'betis', 'sevilla', 'villarreal', 'real sociedad', 'athletic', 'valencia', 'newcastle', 'brighton', 'aston villa', 'west ham', 'leicester', 'everton', 'wolves', 'nottingham', 'brentford', 'fulham', 'crystal palace', 'bournemouth', 'southampton', 'burnley', 'luton', 'sheffield', 'leeds', 'ipswich', 'derby', 'watford', 'millwall', 'stoke', 'blackburn', 'middlesbrough', 'sunderland', 'west brom', 'preston', 'coventry', 'norwich', 'hull', 'bristol', 'birmingham', 'swansea', 'cardiff', 'reading', 'qpr', 'plymouth', 'portsmouth', 'oxford', 'rotherham', 'wigan', 'wycombe', 'bristol', 'peterborough', 'bolton', 'shrewsbury', 'lincoln', 'barnsley', 'fleetwood', 'walsall', 'blackpool', 'exeter', 'stevenage', 'burton', 'crawley', 'salford', 'colchester', 'grimsby', 'crewe', 'gillingham', 'doncaster', 'accrington', 'swindon', 'tranmere', 'morecambe', 'newport', 'harrogate', 'milton keynes', 'forest green', 'wrexham', 'mansfield', 'notts', 'bradford', 'doncaster', 'grimsby', 'stockport', 'sutton', 'aldershot', 'altrincham', 'boreham', 'chesterfield', 'dorking', 'eastleigh', 'ebbsfleet', 'fylde', 'halifax', 'maidenhead', 'oldham', 'rochdale', 'solihull', 'wealdstone', 'woking', 'yeovil', 'york', 'bromley', 'dundee', 'hibernian', 'hearts', 'kilmarnock', 'motherwell', 'st johnstone', 'st mirren', 'ross county', 'livingston', 'hamilton', 'inverness', 'partick', 'raith', 'dundee united', 'falkirk', 'hamilton', 'greenock', 'ayr', 'morton', 'queens', 'dunfermline', 'alloa', 'cowdenbeath', 'edinburgh', 'kelty', 'stenhousemuir', 'stranraer', 'clyde', 'annan', 'albion', 'elgin', 'forfar', 'montrose', 'stirling', 'east fife', 'peterhead', 'clyde', 'cowdenbeath', 'berwick', 'brechin', 'edinburgh city', 'fort william']
            
            has_known_team = any(t in f['home_team_en'].lower() or t in f['away_team_en'].lower() 
                                  for t in known_teams)
            
            if is_important or has_known_team:
                print(f"  [{f['match_time']}] {f['home_team_en']} vs {f['away_team_en']} ({league})")
    except Exception as e:
        print(f"{date}: {e}")

print("\nDone.")
