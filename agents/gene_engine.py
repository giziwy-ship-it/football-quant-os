#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
球队实力评定 + 基因体系 - Naga Core v4.1
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from core.config import config


class StrengthLevel(Enum):
    STRONG = "强队"
    MEDIUM = "中等"
    WEAK = "弱队"


class TeamGene(Enum):
    COMEBACK = "逆转基因"
    EQUALIZER = "追平基因"
    HOLD_LEAD = "守住基因"
    BLOW_LEAD = "痛失好局基因"
    GIVE_UP_LEAD = "被追平基因"
    DRAW_MASTER = "平局大师基因"


@dataclass
class TeamStrength:
    team_name: str
    league: str
    league_rank: int
    base_level: StrengthLevel
    adjusted_level: StrengthLevel
    strength_score: float = 0.0
    recent_form_bonus: int = 0
    european_coefficient: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_name": self.team_name,
            "league": self.league,
            "league_rank": self.league_rank,
            "base_level": self.base_level.value,
            "adjusted_level": self.adjusted_level.value,
            "strength_score": round(self.strength_score, 2),
            "recent_form_bonus": self.recent_form_bonus,
            "european_coefficient": round(self.european_coefficient, 2)
        }


@dataclass
class GeneProfile:
    team_name: str
    genes: Dict[TeamGene, float] = field(default_factory=dict)
    dominant_gene: TeamGene = None
    gene_description: str = ""
    
    def __post_init__(self):
        if not self.genes:
            self.genes = {gene: 0.0 for gene in TeamGene}
        if self.dominant_gene is None:
            self._update_dominant()
    
    def _update_dominant(self):
        if self.genes:
            self.dominant_gene = max(self.genes, key=self.genes.get)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "team_name": self.team_name,
            "genes": {gene.value: round(score, 3) for gene, score in self.genes.items()},
            "dominant_gene": self.dominant_gene.value if self.dominant_gene else None,
            "gene_description": self.gene_description
        }


class TeamEvaluator:
    """球队实力评定器"""
    
    def __init__(self):
        self.teams: Dict[str, TeamStrength] = {}
    
    def evaluate(self, team_name: str, league: str, league_rank: int,
                 recent_5: Optional[List[str]] = None,
                 custom_coeff: Optional[float] = None) -> TeamStrength:
        
        if league_rank <= 4:
            base = StrengthLevel.STRONG
        elif league_rank <= 12:
            base = StrengthLevel.MEDIUM
        else:
            base = StrengthLevel.WEAK
        
        form_bonus = 0
        if recent_5:
            wins = recent_5.count("W")
            losses = recent_5.count("L")
            if wins == 5:
                form_bonus = -1
            elif losses == 5:
                form_bonus = 2
            elif wins >= 4:
                form_bonus = -1
            elif losses >= 4:
                form_bonus = 1
        
        coeff = custom_coeff or config.LEAGUE_COEFFICIENTS.get(league, 70.0)
        rank_score = max(0, (20 - league_rank) * 5)
        european_bonus = min(20, coeff / 5)
        strength_score = (coeff * 0.4) + (rank_score * 0.4) + (european_bonus * 0.2)
        
        level_map = {StrengthLevel.STRONG: 1, StrengthLevel.MEDIUM: 2, StrengthLevel.WEAK: 3}
        adjusted_num = max(1, min(3, level_map[base] + form_bonus))
        reverse_map = {1: StrengthLevel.STRONG, 2: StrengthLevel.MEDIUM, 3: StrengthLevel.WEAK}
        adjusted = reverse_map[adjusted_num]
        
        team = TeamStrength(
            team_name=team_name,
            league=league,
            league_rank=league_rank,
            base_level=base,
            adjusted_level=adjusted,
            strength_score=strength_score,
            recent_form_bonus=form_bonus,
            european_coefficient=coeff
        )
        self.teams[team_name] = team
        return team
    
    def matchup(self, home_team: str, away_team: str) -> Dict[str, Any]:
        home = self.teams.get(home_team)
        away = self.teams.get(away_team)
        
        if not home or not away:
            return {"error": "Missing team data"}
        
        diff = home.strength_score - away.strength_score
        home_with_advantage = home.strength_score * 1.08
        adjusted_diff = home_with_advantage - away.strength_score
        
        if adjusted_diff >= 18:
            matchup_type = "强vs弱"
            advantage = home_team
        elif adjusted_diff <= -18:
            matchup_type = "弱vs强"
            advantage = away_team
        elif abs(adjusted_diff) >= 8:
            matchup_type = "中vs弱/强vs中"
            advantage = home_team if adjusted_diff > 0 else away_team
        else:
            matchup_type = "实力接近"
            advantage = None
        
        return {
            "home_team": home.to_dict(),
            "away_team": away.to_dict(),
            "score_diff": round(diff, 2),
            "adjusted_diff": round(adjusted_diff, 2),
            "matchup_type": matchup_type,
            "advantage_team": advantage,
            "matrix_gap": self._to_matrix_gap(matchup_type)
        }
    
    def _to_matrix_gap(self, matchup_type: str) -> str:
        mapping = {
            "强vs弱": "strong_vs_weak",
            "弱vs强": "strong_vs_weak",
            "中vs弱/强vs中": "medium_gap",
            "实力接近": "even"
        }
        return mapping.get(matchup_type, "even")


class GeneEngine:
    """球队基因引擎"""
    
    GENE_DESC = {
        TeamGene.COMEBACK: "落后时爆发力强，擅长下半场逆转",
        TeamGene.EQUALIZER: "先丢球后心态稳定，追平能力强",
        TeamGene.HOLD_LEAD: "领先后控球稳健，防守纪律性强",
        TeamGene.BLOW_LEAD: "领先后容易松懈，常被对手翻盘",
        TeamGene.GIVE_UP_LEAD: "领先后进攻冒进，容易被追平",
        TeamGene.DRAW_MASTER: "领先时收缩过度，最终变成平局"
    }
    
    def __init__(self):
        self.profiles: Dict[str, GeneProfile] = {}
    
    def evaluate(self, team_name: str, match_history: List[Dict] = None,
                 manual_scores: Dict[str, float] = None) -> GeneProfile:
        if manual_scores:
            genes = {gene: 0.0 for gene in TeamGene}
            for name, score in manual_scores.items():
                for gene in TeamGene:
                    if gene.value == name:
                        genes[gene] = max(0.0, min(1.0, score))
                        break
            dominant = max(genes, key=genes.get)
            profile = GeneProfile(team_name=team_name, genes=genes, dominant_gene=dominant,
                                  gene_description=self.GENE_DESC[dominant])
        elif match_history:
            profile = self._from_history(team_name, match_history)
        else:
            profile = GeneProfile(team_name=team_name, gene_description="数据不足，待观察")
        
        self.profiles[team_name] = profile
        return profile
    
    def _from_history(self, team_name: str, history: List[Dict]) -> GeneProfile:
        comeback = len([m for m in history if m.get('went_behind') and m.get('comeback')])
        equalizer = len([m for m in history if m.get('went_behind') and m.get('final_result') in ['draw', 'win']])
        hold = len([m for m in history if m.get('scored_first') and m.get('final_result') == 'win'])
        blow = len([m for m in history if m.get('scored_first') and m.get('final_result') == 'loss'])
        give_up = len([m for m in history if m.get('scored_first') and m.get('final_result') == 'draw'])
        draw_master = len([m for m in history if m.get('halftime_lead') and m.get('final_result') == 'draw'])
        
        behind = max(1, len([m for m in history if m.get('went_behind')]))
        first = max(1, len([m for m in history if m.get('scored_first')]))
        ht_lead = max(1, len([m for m in history if m.get('halftime_lead')]))
        
        genes = {
            TeamGene.COMEBACK: comeback / behind,
            TeamGene.EQUALIZER: equalizer / behind,
            TeamGene.HOLD_LEAD: hold / first,
            TeamGene.BLOW_LEAD: blow / first,
            TeamGene.GIVE_UP_LEAD: give_up / first,
            TeamGene.DRAW_MASTER: draw_master / ht_lead
        }
        
        dominant = max(genes, key=genes.get)
        return GeneProfile(
            team_name=team_name,
            genes=genes,
            dominant_gene=dominant,
            gene_description=self.GENE_DESC[dominant]
        )
    
    def analyze_matchup(self, home_team: str, away_team: str) -> Dict[str, Any]:
        home = self.profiles.get(home_team)
        away = self.profiles.get(away_team)
        
        if not home or not away:
            return {"error": "Missing gene data"}
        
        return {
            "home_team": home.to_dict(),
            "away_team": away.to_dict(),
            "insight": self._generate_insight(home, away)
        }
    
    def _generate_insight(self, home: GeneProfile, away: GeneProfile) -> str:
        insights = []
        if home.dominant_gene == TeamGene.HOLD_LEAD and away.dominant_gene == TeamGene.COMEBACK:
            insights.append("矛与盾对决：主队领先后稳健，客队擅长逆转")
        if home.dominant_gene == TeamGene.BLOW_LEAD:
            insights.append(f"主队有痛失好局基因，领先后需警惕")
        if away.dominant_gene == TeamGene.HOLD_LEAD:
            insights.append("客队领先后很难被翻盘")
        return "；".join(insights) if insights else "两队基因特征无明显相克"
