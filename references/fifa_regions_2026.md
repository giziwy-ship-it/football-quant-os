# FIFA 2026 World Cup - 48强官方名单 & 区域归属参考
# 来源: Yahoo Sports 2026-04-01 官方确认
# 使用说明: 在 predict.py 中通过 --home-region / --away-region 参数指定

FIFA_CONFEDERATIONS_2026 = {
    'AFC': {
        'name': '亚洲足球联合会',
        'code': 'asia',
        'slots': 8,
        'teams': [
            'AUSTRALIA', 'IR IRAN', 'JAPAN', 'JORDAN',
            'KOREA REPUBLIC', 'QATAR', 'SAUDI ARABIA', 'UZBEKISTAN', 'IRAQ'
        ]
    },
    'CAF': {
        'name': '非洲足球联合会',
        'code': 'africa',
        'slots': 9,
        'teams': [
            'ALGERIA', 'CAPE VERDE', 'DR CONGO', "COTE D'IVOIRE",
            'EGYPT', 'GHANA', 'MOROCCO', 'SENEGAL', 'SOUTH AFRICA', 'TUNISIA'
        ]
    },
    'CONCACAF': {
        'name': '北美/中美洲/加勒比足球联合会',
        'code': 'north_america',
        'slots': 6,
        'teams': [
            'CANADA', 'MEXICO', 'USA',  # 东道主
            'CURACAO', 'HAITI', 'PANAMA'
        ]
    },
    'CONMEBOL': {
        'name': '南美洲足球联合会',
        'code': 'south_america',
        'slots': 6,
        'teams': [
            'ARGENTINA', 'BRAZIL', 'COLOMBIA', 'ECUADOR', 'PARAGUAY', 'URUGUAY'
        ]
    },
    'OFC': {
        'name': '大洋洲足球联合会',
        'code': 'oceania',
        'slots': 1,
        'teams': ['NEW ZEALAND']
    },
    'UEFA': {
        'name': '欧洲足球联合会',
        'code': 'europe',
        'slots': 16,
        'teams': [
            'AUSTRIA', 'BELGIUM', 'BOSNIA AND HERZEGOVINA', 'CROATIA', 'CZECHIA',
            'ENGLAND', 'FRANCE', 'GERMANY', 'NETHERLANDS', 'NORWAY',
            'PORTUGAL', 'SCOTLAND', 'SPAIN', 'SWEDEN', 'SWITZERLAND', 'TURKIYE'
        ]
    }
}

# 区域代码映射表 (用于 predict.py 参数)
REGION_CODE_MAP_2026 = {
    # AFC (Asia)
    'AUSTRALIA': 'asia', 'IR IRAN': 'asia', 'JAPAN': 'asia', 'JORDAN': 'asia',
    'KOREA REPUBLIC': 'asia', 'QATAR': 'asia', 'SAUDI ARABIA': 'asia', 'UZBEKISTAN': 'asia',
    'IRAQ': 'asia',
    
    # CAF (Africa)
    'ALGERIA': 'africa', 'CAPE VERDE': 'africa', 'DR CONGO': 'africa',
    "COTE D'IVOIRE": 'africa', 'EGYPT': 'africa', 'GHANA': 'africa',
    'MOROCCO': 'africa', 'SENEGAL': 'africa', 'SOUTH AFRICA': 'africa', 'TUNISIA': 'africa',
    
    # CONCACAF (North America)
    'CANADA': 'north_america', 'MEXICO': 'north_america', 'USA': 'north_america',
    'CURACAO': 'north_america', 'HAITI': 'north_america', 'PANAMA': 'north_america',
    
    # CONMEBOL (South America)
    'ARGENTINA': 'south_america', 'BRAZIL': 'south_america', 'COLOMBIA': 'south_america',
    'ECUADOR': 'south_america', 'PARAGUAY': 'south_america', 'URUGUAY': 'south_america',
    
    # OFC (Oceania)
    'NEW ZEALAND': 'oceania',
    
    # UEFA (Europe)
    'AUSTRIA': 'europe', 'BELGIUM': 'europe', 'BOSNIA AND HERZEGOVINA': 'europe',
    'CROATIA': 'europe', 'CZECHIA': 'europe', 'ENGLAND': 'europe', 'FRANCE': 'europe',
    'GERMANY': 'europe', 'NETHERLANDS': 'europe', 'NORWAY': 'europe', 'PORTUGAL': 'europe',
    'SCOTLAND': 'europe', 'SPAIN': 'europe', 'SWEDEN': 'europe', 'SWITZERLAND': 'europe',
    'TURKIYE': 'europe'
}

# ============================================================
# 区域因子矩阵 (FIFA 6大洲际联合会完整覆盖)
# ============================================================

REGIONAL_FACTOR = {
    # 亚洲 (AFC) 对阵
    'asia_vs_europe': 1.15,
    'asia_vs_africa': 1.10,
    'asia_vs_south_america': 0.95,
    'asia_vs_north_america': 1.05,
    'asia_vs_oceania': 1.20,
    
    # 欧洲 (UEFA) 对阵
    'europe_vs_asia': 0.90,
    'europe_vs_africa': 0.95,
    'europe_vs_south_america': 1.05,
    'europe_vs_north_america': 1.10,
    'europe_vs_oceania': 1.25,
    
    # 非洲 (CAF) 对阵
    'africa_vs_asia': 1.05,
    'africa_vs_europe': 1.05,
    'africa_vs_south_america': 0.90,
    'africa_vs_north_america': 1.10,
    'africa_vs_oceania': 1.20,
    
    # 南美 (CONMEBOL) 对阵
    'south_america_vs_asia': 1.15,
    'south_america_vs_europe': 1.05,
    'south_america_vs_africa': 1.10,
    'south_america_vs_north_america': 1.10,
    'south_america_vs_oceania': 1.25,
    
    # 北美 (CONCACAF) 对阵
    'north_america_vs_asia': 1.05,
    'north_america_vs_europe': 0.85,
    'north_america_vs_africa': 0.90,
    'north_america_vs_south_america': 0.85,
    'north_america_vs_oceania': 1.15,
    
    # 大洋洲 (OFC) 对阵 - 最弱
    'oceania_vs_asia': 0.80,
    'oceania_vs_europe': 0.75,
    'oceania_vs_africa': 0.80,
    'oceania_vs_south_america': 0.75,
    'oceania_vs_north_america': 0.85,
    
    'neutral': 1.0
}

# ============================================================
# 2026世界杯新军球队分类 (Newbie Factor)
# 来源: Yahoo Sports 2026-04-01 官方确认
# ============================================================

NEWBIE_CLASSIFICATION_2026 = {
    # 首次参赛 - 0次世界杯经验 (Debutants)
    'debutants': {
        'description': '首次晋级世界杯，完全零经验',
        'factor': 0.85,
        'teams': {
            'JORDAN': {
                'region': 'asia',
                'confederation': 'AFC',
                'note': '2026年首次晋级，西亚球队'
            },
            'UZBEKISTAN': {
                'region': 'asia',
                'confederation': 'AFC',
                'note': '2026年首次晋级，中亚球队'
            },
            'CAPE VERDE': {
                'region': 'africa',
                'confederation': 'CAF',
                'note': '2026年首次晋级，非洲岛国'
            },
            'CURACAO': {
                'region': 'north_america',
                'confederation': 'CONCACAF',
                'note': '2026年首次晋级，人口最少参赛国(16万)'
            }
        }
    },
    
    # 长期缺席回归 (20年+)
    'long_absent': {
        'description': '历史多次参赛但超20年未出现',
        'factor': 0.90,
        'teams': {
            'SCOTLAND': {
                'region': 'europe',
                'confederation': 'UEFA',
                'appearances': 8,
                'last_appearance': 1998,
                'gap_years': 28,
                'note': '8次参赛但缺席28年'
            },
            'NORWAY': {
                'region': 'europe',
                'confederation': 'UEFA',
                'appearances': 3,
                'last_appearance': 1998,
                'gap_years': 28,
                'note': '3次参赛但缺席28年'
            },
            'HAITI': {
                'region': 'north_america',
                'confederation': 'CONCACAF',
                'appearances': 1,
                'last_appearance': 1974,
                'gap_years': 52,
                'note': '1974年唯一一次，时隔52年'
            },
            'DR CONGO': {
                'region': 'africa',
                'confederation': 'CAF',
                'appearances': 1,
                'last_appearance': 1974,
                'gap_years': 52,
                'note': '1974年唯一一次，时隔52年'
            }
        }
    },
    
    # 近期回归 (10-20年)
    'recent_return': {
        'description': '近期回归但经验有限',
        'factor': 0.95,
        'teams': {
            'CZECHIA': {
                'region': 'europe',
                'confederation': 'UEFA',
                'appearances': 9,
                'last_appearance': 2006,
                'gap_years': 20,
                'note': '缺席20年回归'
            },
            'SWEDEN': {
                'region': 'europe',
                'confederation': 'UEFA',
                'appearances': 12,
                'last_appearance': 2018,
                'gap_years': 8,
                'note': '2018年后缺席，8年回归'
            },
            'TUNISIA': {
                'region': 'africa',
                'confederation': 'CAF',
                'appearances': 6,
                'last_appearance': 2022,
                'gap_years': 4,
                'note': '2022参赛，连续参赛'
            }
        }
    }
}

# 经验球队 (experienced = 1.0) - 无需额外扣分
EXPERIENCED_TEAMS_2026 = {
    'europe': [
        'AUSTRIA', 'BELGIUM', 'BOSNIA AND HERZEGOVINA', 'CROATIA',
        'ENGLAND', 'FRANCE', 'GERMANY', 'NETHERLANDS', 'PORTUGAL',
        'SPAIN', 'SWITZERLAND', 'TURKIYE'
    ],
    'south_america': [
        'ARGENTINA', 'BRAZIL', 'COLOMBIA', 'ECUADOR', 'PARAGUAY', 'URUGUAY'
    ],
    'africa': [
        'ALGERIA', 'EGYPT', 'GHANA', 'MOROCCO', 'SENEGAL', 'SOUTH AFRICA'
    ],
    'asia': [
        'AUSTRALIA', 'IR IRAN', 'JAPAN', 'KOREA REPUBLIC', 'QATAR', 'SAUDI ARABIA', 'IRAQ'
    ],
    'north_america': [
        'CANADA', 'MEXICO', 'USA', 'PANAMA'
    ],
    'oceania': [
        'NEW ZEALAND'
    ]
}

# 新军因子速查函数
def get_newbie_factor(team_name):
    """获取球队的新军因子"""
    for category, data in NEWBIE_CLASSIFICATION_2026.items():
        if team_name.upper() in data['teams']:
            return data['factor']
    return 1.0

def is_newbie(team_name):
    """判断是否为广义新军"""
    for category, data in NEWBIE_CLASSIFICATION_2026.items():
        if team_name.upper() in data['teams']:
            return True
    return False

# ============================================================
# 2022世界杯冷门案例的区域分析
# ============================================================

UPSET_CASES_2022 = {
    'ARGENTINA vs SAUDI ARABIA': {
        'home_region': 'south_america',
        'away_region': 'asia',
        'factor': 'south_america_vs_asia = 1.15',
        'result': '1-2 (冷门)',
        'note': '南美技术流 vs 亚洲防反，但沙特爆了'
    },
    'GERMANY vs JAPAN': {
        'home_region': 'europe',
        'away_region': 'asia',
        'factor': 'europe_vs_asia = 0.90',
        'result': '1-2 (冷门)',
        'note': '欧洲控球多但转化率低'
    },
    'MOROCCO vs SPAIN': {
        'home_region': 'africa',
        'away_region': 'europe',
        'factor': 'africa_vs_europe = 1.05',
        'result': '0-0 (点球胜)',
        'note': '非洲身体对抗强，欧洲不轻松'
    },
    'CROATIA vs BRAZIL': {
        'home_region': 'europe',
        'away_region': 'south_america',
        'factor': 'europe_vs_south_america = 1.05',
        'result': '1-1 (点球胜)',
        'note': '欧洲对攻南美，进球不少'
    }
}

# ============================================================
# 使用建议
# ============================================================

USAGE_GUIDE = """
使用新军因子 (--home-exp / --away-exp):

1. 纯新军 (factor=0.85):
   Jordan, Uzbekistan, Cape Verde, Curacao
   
2. 长期缺席 (factor=0.90):
   Scotland, Norway, Haiti, DR Congo
   
3. 近期回归 (factor=0.95):
   Czechia, Sweden, Tunisia
   
4. 经验球队 (factor=1.0, 默认):
   其余40支球队

注意：
- 新军因子同时影响进攻和防守
- 新军进球减少(0.85)，同时被进球增加(1.15)
- 新军更容易出现保守战术和紧张失误

使用区域因子 (--home-region / --away-region):
- 6大洲际联合会: asia, europe, south_america, africa, north_america, oceania
- 完整30种组合因子已覆盖
"""

# 与区域因子的交互效果
REGIONAL_NEWBIE_INTERACTION = {
    'note': '新军效应与区域效应叠加',
    'example_1': 'Jordan(新军0.85) vs Germany(欧洲1.0)',
    'effect_1': 'lambda 大幅降低(0.85) + 欧洲控球(0.90) = 0.765',
    'example_2': 'Curacao(新军0.85) vs Brazil(南美1.0)',
    'effect_2': 'lambda 极低(0.85) + 南美技术(1.15) = 0.98，但巴西太强实际更低'
}

# ============================================================
# 2026世界杯分组 (官方确认)
# ============================================================

GROUPS_2026 = {
    'A': ['Mexico', 'South Korea', 'South Africa', 'Czechia'],
    'B': ['Canada', 'Switzerland', 'Qatar', 'Bosnia and Herzegovina'],
    'C': ['Brazil', 'Morocco', 'Scotland', 'Haiti'],
    'D': ['USA', 'Australia', 'Paraguay', 'Turkiye'],
    'E': ['Germany', 'Ecuador', 'Ivory Coast', 'Curacao'],
    'F': ['Netherlands', 'Japan', 'Tunisia', 'Sweden'],
    'G': ['Belgium', 'Iran', 'Egypt', 'New Zealand'],
    'H': ['Spain', 'Uruguay', 'Saudi Arabia', 'Cape Verde'],
    'I': ['France', 'Senegal', 'Norway', 'Iraq'],
    'J': ['Argentina', 'Austria', 'Algeria', 'Jordan'],
    'K': ['Portugal', 'Colombia', 'Uzbekistan', 'DR Congo'],
    'L': ['England', 'Croatia', 'Panama', 'Ghana']
}
