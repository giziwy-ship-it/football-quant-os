#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare FIFA vs xG-hybrid power mapping"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from v4.scripts.train_full_v4 import get_team_power
from v4.scripts.validate_xg_hybrid import get_team_power_xg

print("Team    FIFA_atk FIFA_def  Hybrid_atk Hybrid_def  xG_adj")
print("-" * 65)
for code in ['GER','BEL','NED','ECU','MEX','ESP','DEN','BRA','ARG','FRA','ENG']:
    fifa = get_team_power(code)
    hybrid = get_team_power_xg(code)
    atk_chg = hybrid['attack'] - fifa['attack']
    def_chg = hybrid['defense'] - fifa['defense']
    print(f"{code:6s}  {fifa['attack']:.3f}    {fifa['defense']:.3f}      {hybrid['attack']:.3f}      {hybrid['defense']:.3f}      {atk_chg:+.3f}/{def_chg:+.3f}")
