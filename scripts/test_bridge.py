import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')
from agents.coach_factor_bridge import CoachFactorDataBridge

print('=== CoachFactor Data Bridge Test ===')
bridge = CoachFactorDataBridge()

result = bridge.refresh_coach('Argentina')
print('Team:', result['team'])
print('Status:', result['status'])
print('Changes:', len(result['changes']))
print('Warnings:', len(result['warnings']))
print()
print('Bridge initialized successfully.')
