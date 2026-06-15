import sys
sys.stdout.reconfigure(encoding='utf-8')

# 曼联 vs 利兹联
mun_lee = {
    'match': '曼联 vs 利兹联',
    'time': '2026-04-14 03:00',
    'league': '英超',
    'status': '⛔ BLOCKED',
    'sp': {'home': '62.9%', 'draw': '20.4%', 'away': '16.7%', 'best': '主胜'},
    'handicap': {'win': '35%', 'draw': '28%', 'lose': '37%', 'best': '让平/让负'},
    'score': {'top3': ['2:1 (22%)', '1:0 (18%)', '2:0 (15%)'], 'best': '2:1'},
    'goals': '3.0球',
    'ou': {'big': '55%', 'small': '45%', 'best': '大2.5'},
    'htft': {'ss': '28.3%', 'ps': '25.1%', 'pp': '8.2%', 'best': '胜/胜'},
    'corners': '10-11个',
    'ev': '-0.7%',
    'stake': '0',
    'note': '赔率无价值，不建议投注'
}

# 佛罗伦萨 vs 拉齐奥
fio_laz = {
    'match': '佛罗伦萨 vs 拉齐奥',
    'time': '2026-04-14 02:45',
    'league': '意甲',
    'status': '✅ SUCCESS',
    'sp': {'home': '50.0%', 'draw': '26.4%', 'away': '23.6%', 'best': '主胜'},
    'handicap': {'win': '50%', 'draw': '26%', 'lose': '24%', 'best': '让胜'},
    'score': {'top3': ['1:0 (18%)', '1:1 (16%)', '2:1 (14%)'], 'best': '1:0'},
    'goals': '2.5球',
    'ou': {'big': '48%', 'small': '52%', 'best': '小2.5'},
    'htft': {'ss': '17.5%', 'ps': '20.0%', 'pp': '10.6%', 'best': '平/胜'},
    'corners': '9-10个',
    'ev': '+16.4%',
    'stake': '500',
    'note': '正EV，推荐佛罗伦萨主胜'
}

def print_board(data):
    print()
    print('=' * 80)
    print(f"【{data['match']}】{data['time']} | {data['league']}")
    print(f"系统状态: {data['status']}")
    print('-' * 80)
    print(f"  1. 胜平负      | 主{data['sp']['home']} 平{data['sp']['draw']} 客{data['sp']['away']}  → {data['sp']['best']}")
    print(f"  2. 让球胜平负  | 让胜{data['handicap']['win']} 让平{data['handicap']['draw']} 让负{data['handicap']['lose']}  → {data['handicap']['best']}")
    print(f"  3. 比分        | {' | '.join(data['score']['top3'])}  → {data['score']['best']}")
    print(f"  4. 进球数      | {data['goals']}")
    print(f"  5. 大小球      | 大{data['ou']['big']} 小{data['ou']['small']}  → {data['ou']['best']}")
    print(f"  6. 半全场      | 胜/胜{data['htft']['ss']} 平/胜{data['htft']['ps']} 平/平{data['htft']['pp']}  → {data['htft']['best']}")
    print(f"  7. 角球数      | {data['corners']}")
    print('-' * 80)
    print(f"  💰 EV: {data['ev']} | 建议投注: {data['stake']}")
    print(f"  📝 {data['note']}")
    print('=' * 80)

print_board(mun_lee)
print_board(fio_laz)

print()
print('╔' + '═' * 78 + '╗')
print('║' + ' ' * 20 + '娜迦足量系统 · 双赛看板' + ' ' * 33 + '║')
print('╚' + '═' * 78 + '╝')
print()
print('【快速决策】')
print('  ▸ 曼联 vs 利兹联    : 跳过（无价值）')
print('  ▸ 佛罗伦萨 vs 拉齐奥: 佛罗伦萨主胜（EV +16.4%，押500）')
print()
