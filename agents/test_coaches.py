#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WORLD_CUP_2026_FULL_COACHES - 2026 World Cup 48 Teams Full Coach Database
"""

from agents.coach_factor import CoachProfile, TacticalStyle

WORLD_CUP_2026_FULL_COACHES = {
    'USA': CoachProfile(name='Mauricio Pochettino', nationality='Argentina', age=54, tactical_style=TacticalStyle.PRESS, formation_flexibility=3.5, avg_formations_per_tournament=2.5, world_cup_experience=0, euro_experience=0, knockout_stage_wins=0, emotional_stability=7.0, media_influence_susceptibility=4.0, team_meltdown_incidents=0, rotation_tendency=4.0, vs_strong_team_strategy='balanced', vs_weak_team_strategy='aggressive', strategy_extremity=3.0, avg_goals_per_match=1.9, avg_conceded_per_match=1.2),
    'Mexico': CoachProfile(name='Javier Aguirre', nationality='Mexico', age=66, tactical_style=TacticalStyle.COUNTER, formation_flexibility=3.0, avg_formations_per_tournament=2.0, world_cup_experience=2, euro_experience=0, knockout_stage_wins=2, emotional_stability=6.0, media_influence_susceptibility=5.0, team_meltdown_incidents=1, rotation_tendency=4.0, vs_strong_team_strategy='defensive', vs_weak_team_strategy='aggressive', strategy_extremity=3.5, avg_goals_per_match=1.5, avg_conceded_per_match=1.2),
}
