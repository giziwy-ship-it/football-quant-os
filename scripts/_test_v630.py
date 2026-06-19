import sys
sys.path.insert(0, 'scripts')
from predict_v6 import PredictorV6

p = PredictorV6()
result = p.predict('Germany', 'Japan', odds_home=1.8, odds_draw=3.4, odds_away=4.2)

checks = {
    'evolution': result.evolution,
    'market_micro': result.market_micro,
    'investment': result.investment,
    'physical_ai': result.physical_ai,
    'coach_factor': result.coach_factor,
    'compliance': result.compliance_check,
    'kelly': result.kelly_recommendation,
}

print('=== v6.3.0 模块检查 ===')
for name, val in checks.items():
    if val:
        status = val.get('status', 'ok') if isinstance(val, dict) else 'ok'
        print(f'{name}: {status}')
    else:
        print(f'{name}: None')

print()
print('决策链步数:', len(result.decision_chain))
for i, step in enumerate(result.decision_chain, 1):
    name = step.split('|')[-1].strip()
    print(f'{i:2d}. {name}')
