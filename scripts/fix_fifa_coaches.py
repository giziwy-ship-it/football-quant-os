import sys, re

with open('agents/worldcup_2026_full_coaches.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix Iraq coach
content = content.replace(
    "    'Iraq': CoachProfile(\n        name='Jesus Casas', nationality='Spain', age=48,",
    "    'Iraq': CoachProfile(\n        name='Graham Arnold', nationality='Australia', age=61,"
)

# Fix Morocco coach
content = content.replace(
    "    'Morocco': CoachProfile(\n        name='Walid Regragui', nationality='Morocco', age=49,",
    "    'Morocco': CoachProfile(\n        name='Mohamed Ouahbi', nationality='Morocco', age=49,"
)

# Fix Saudi Arabia coach
content = content.replace(
    "    'Saudi_Arabia': CoachProfile(\n        name='Herve Renard', nationality='France', age=56,",
    "    'Saudi_Arabia': CoachProfile(\n        name='Georgios Donis', nationality='Greece', age=55,"
)

# Fix Uzbekistan coach
content = content.replace(
    "    'Uzbekistan': CoachProfile(\n        name='Srecko Katanec', nationality='Slovenia', age=61,",
    "    'Uzbekistan': CoachProfile(\n        name='Fabio Cannavaro', nationality='Italy', age=52,"
)

with open('agents/worldcup_2026_full_coaches.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('Fixed 4 coaches to match FIFA official data')
