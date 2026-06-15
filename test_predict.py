import sys
sys.path.insert(0, 'D:/openclaw-workspace/football_quant_os/scripts')
from predict import estimate_true_probability

print('Group 0.7:', estimate_true_probability(0.7, 'group'))
print('Knockout 0.7:', estimate_true_probability(0.7, 'knockout'))
print('Group 0.3:', estimate_true_probability(0.3, 'group'))
print('Knockout 0.3:', estimate_true_probability(0.3, 'knockout'))
