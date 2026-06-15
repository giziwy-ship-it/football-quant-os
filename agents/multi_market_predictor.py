#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Naga Quant System - 多维度预测引擎 v4.2.1-naga
CoachFactor Integrated | Venue-aware | Value Bet Distinction
针对比赛预测5个市场：
1. 胜平负 (1X2)
2. 让球胜平负 (Asian Handicap)
3. 半全场 (HT/FT)
4. 比分 (Correct Score)
5. 大小球 (Over/Under)

数据源：
- OddsPortal / 500.com / Betfair Exchange
- FIFA官方: 世界排名/近期战绩
- CoachFactor: 48强教练CRI (已集成)
- UpsetDetector: 大比分/冷门检测
"""

import sys
sys.path.insert(0, 'D:\\openclaw-workspace\\football_quant_os')

from typing import Dict, List, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

# 导入 Kelly 模块
from scripts.kelly import get_kelly_suggestion, portfolio_kelly

# ============================================================
# 数据模型
# ============================================================

@dataclass
class Match:
    home: str
    away: str
    competition: str
    date: str
    home_fifa_rank: int
    away_fifa_rank: int
    home_recent_form: List[str]  # W/D/L
    away_recent_form: List[str]
    home_goals_scored: int
    home_goals_conceded: int
    away_goals_scored: int
    away_goals_conceded: int
    odds_1x2: Tuple[float, float, float]  # home, draw, away
    odds_ah: Dict[str, Tuple[float, float]]  # handicap: (home_odds, away_odds)
    odds_ou: Dict[str, Tuple[float, float]]  # line: (over, under)
    coach_home_cri: float
    coach_away_cri: float
    venue_type: str = "neutral"  # "neutral" | "home" | "away"
    stage: str = "group"  # "group" | "knockout" | "final"

@dataclass
class Prediction:
    market: str
    prediction: str
    confidence: float
    edge: float
    recommended: bool
    reasoning: str

# ============================================================
# 从 500.com 抓取数据创建 Match 对象
# ============================================================

def create_match_from_500(match_id: str, use_pro: bool = False, 
                           stealth: bool = True, intercept: bool = True) -> Match:
    """
    从 500.com 抓取数据并创建 Match 对象
    
    Args:
        match_id: 500.com 比赛ID
        use_pro: 是否使用 Playwright Pro 专业版
        stealth: 是否启用 Stealth 模式
        intercept: 是否拦截资源加速
    """
    import sys
    from pathlib import Path
    scripts_dir = str(Path(__file__).parent.parent / 'scripts')
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    
    if use_pro:
        from odds_fetcher_playwright_pro import fetch_odds
        result = fetch_odds(
            match_id,
            headless=True,
            stealth=stealth,
            intercept_resources=intercept,
            max_retries=3
        )
    else:
        from odds_fetcher_smart import get_odds_smart
        result = get_odds_smart(match_id)
    
    if not result.get('success'):
        raise ValueError(f"Failed to fetch odds for match {match_id}: {result.get('error')}")
    
    avg = result['average']
    odds = (avg['home'], avg['draw'], avg['away'])
    
    # 构建 Match 对象（简化版，其他字段需要补充）
    return Match(
        home=result.get('home_team', 'Home'),
        away=result.get('away_team', 'Away'),
        competition='World Cup',
        date='2026-06-14',
        home_fifa_rank=50,
        away_fifa_rank=30,
        home_recent_form=['W', 'L', 'D', 'W', 'L'],
        away_recent_form=['W', 'W', 'D', 'W', 'W'],
        home_goals_scored=8,
        home_goals_conceded=7,
        away_goals_scored=15,
        away_goals_conceded=5,
        odds_1x2=odds,
        odds_ah={
            '+1.5': (1.85, 1.95),
            '+1': (2.05, 1.75),
        },
        odds_ou={
            '2.5': (1.90, 1.90),
            '3.0': (1.75, 2.05),
        },
        coach_home_cri=5.0,
        coach_away_cri=3.5,
        stage='group'
    )

# ============================================================
# 核心预测引擎
# ============================================================

class MultiMarketPredictor:
    """
    多市场预测引擎
    
    整合数据源：
    - 赔率隐含概率 (市场信号)
    - FIFA排名/近期战绩 (实力对比)
    - CoachFactor CRI (冷门因子)
    - UpsetDetector (大比分/冷门检测)
    """
    
    def __init__(self, match: Match, use_pro: bool = False, 
                 stealth: bool = True, intercept: bool = True):
        """
        Args:
            match: Match数据对象
            use_pro: 是否使用 Playwright Pro 专业版抓取
            stealth: 是否启用 Stealth 模式
            intercept: 是否拦截资源加速
        """
        self.match = match
        self.predictions = []
        self.use_pro = use_pro
        self.stealth = stealth
        self.intercept = intercept
    
    @staticmethod
    def from_500(match_id: str, venue_type: str = None, 
                  use_pro: bool = False, stealth: bool = True, intercept: bool = True) -> 'MultiMarketPredictor':
        """从 500.com 创建预测器"""
        match = create_match_from_500(match_id, use_pro=use_pro, stealth=stealth, intercept=intercept)
        return MultiMarketPredictor(match, use_pro, stealth, intercept)
    
    def fetch_500_odds(self, match_id: str) -> dict:
        """抓取 500.com 赔率，支持 Pro 版"""
        import sys
        from pathlib import Path
        scripts_dir = str(Path(__file__).parent.parent / 'scripts')
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        
        if self.use_pro:
            from odds_fetcher_playwright_pro import fetch_odds
            return fetch_odds(
                match_id,
                headless=True,
                stealth=self.stealth,
                intercept_resources=self.intercept,
                max_retries=3
            )
        else:
            from odds_fetcher_smart import get_odds_smart
            return get_odds_smart(match_id)
    
    def _calculate_implied_prob(self, odds: float) -> float:
        """赔率转隐含概率"""
        return 1 / odds if odds > 0 else 0
    
    def _calculate_margin(self, odds_tuple: Tuple[float, float, float]) -> float:
        """计算博彩公司 margin"""
        return sum(1/o for o in odds_tuple if o > 0) - 1
    
    def _remove_margin(self, odds_tuple: Tuple[float, float, float]) -> Tuple[float, float, float]:
        """去除margin，得到真实概率"""
        margin = self._calculate_margin(odds_tuple)
        probs = [1/o for o in odds_tuple]
        total = sum(probs)
        return tuple(p / total * (1 - margin) for p in probs)
    
    # ============================================================
    # 世界杯阶段调整 (v4.3.0)
    # ============================================================
    
    def adjust_for_worldcup_stage(self, mod_home: float, mod_away: float, upset_score: int) -> tuple:
        """根据历史数据动态调整模型概率"""
        stage = self.match.stage
        if stage == "group":
            mod_home = mod_home * 0.96 + 0.02
            mod_away = 1 - mod_home
            upset_score = int(upset_score * 0.85)
        elif stage == "knockout":
            factor = 1.20
            mod_home = mod_home * 0.93
            mod_away = 1 - mod_home
            upset_score = int(upset_score * factor)
        elif stage == "final":
            mod_home = mod_home * 0.97
            mod_away = 1 - mod_home
            upset_score = int(upset_score * 1.05)
        return round(mod_home, 3), round(mod_away, 3), min(upset_score, 65)
    
    # ============================================================
    # 市场1: 胜平负 (1X2)
    # ============================================================
    
    def predict_1x2(self) -> Prediction:
        """
        胜平负预测
        
        模型：
        P_model = 0.4 * 赔率隐含概率 + 0.3 * FIFA排名模型 + 0.2 * 近期状态 + 0.1 * 冷门因子
        """
        h, d, a = self.match.odds_1x2
        
        # 1. 赔率隐含概率 (去margin)
        implied_h, implied_d, implied_a = self._remove_margin((h, d, a))
        
        # 2. FIFA排名模型 (ELO近似)
        rank_diff = self.match.away_fifa_rank - self.match.home_fifa_rank
        # 排名差越大，强队胜率越高
        elo_prob = 1 / (1 + 10 ** (-rank_diff / 400))
        
        # 场地修正：中立场地不调整，主场/客场调整
        venue_adjust = 1.0
        if self.match.venue_type == "home":
            venue_adjust = 1.15  # 主场加成15%
        elif self.match.venue_type == "away":
            venue_adjust = 0.85  # 客场削弱15%
        
        # 调整elo_prob：如果是home venue，增加home胜概率；如果是away venue，降低home胜概率
        if self.match.venue_type == "home":
            elo_prob = elo_prob * 0.85  # 主队更强，所以强队胜率降低（elo_prob偏向强队）
        elif self.match.venue_type == "away":
            elo_prob = elo_prob * 1.15  # 客队更强，所以强队胜率增加
        # 注意：elo_prob在这里是
        # 重新计算：如果home是卡塔尔，away是瑞士，瑞士排名更高
        # 假设瑞士排名15，卡塔尔排名50
        # 瑞士胜的概率应该高
        
        # 3. 近期状态
        home_form_pts = self._form_points(self.match.home_recent_form)
        away_form_pts = self._form_points(self.match.away_recent_form)
        form_prob = away_form_pts / (home_form_pts + away_form_pts + 0.1)
        
        # 4. 冷门因子 (CoachFactor CRI)
        # CRI 差 = 客队教练 - 主队教练
        # 差值越大，说明客队教练更强，主队爆冷概率越高
        cri_diff = self.match.coach_away_cri - self.match.coach_home_cri
        # 归一化到 [0, 1] 范围：差值范围约 -4 到 +4
        coach_factor = 0.5 + cri_diff * 0.05  # 中性=0.5，每差1分偏移5%
        coach_factor = max(0.2, min(0.8, coach_factor))  # 限制在20%-80%
        
        # 融合模型
        # coach_factor: 偏向 1 表示主队更强（客队教练弱），偏向 0 表示客队更强
        model_home = 0.4 * implied_h + 0.3 * (1 - elo_prob) + 0.2 * (1 - form_prob) + 0.1 * coach_factor
        model_draw = 0.4 * implied_d + 0.3 * 0.15 + 0.2 * 0.2 + 0.1 * (1 - abs(coach_factor - 0.5))  # 平局受教练差影响小
        model_away = 0.4 * implied_a + 0.3 * elo_prob + 0.2 * form_prob + 0.1 * (1 - coach_factor)
        
        # 归一化
        total = model_home + model_draw + model_away
        model_home /= total
        model_draw /= total
        model_away /= total
        
        # 世界杯阶段调整 (v4.3.0)
        upset_score = 15
        if self.match.stage in ["group", "knockout", "final"]:
            model_home, model_away, upset_score = self.adjust_for_worldcup_stage(model_home, model_away, upset_score)
            model_draw = 1 - model_home - model_away
        
        # Edge计算
        edge_h = model_home - implied_h
        edge_d = model_draw - implied_d
        edge_a = model_away - implied_a
        
        # 最可能结果（概率最高）
        probs = {'主胜': model_home, '平局': model_draw, '客胜': model_away}
        most_likely = max(probs, key=probs.get)
        most_likely_prob = probs[most_likely]
        
        # 最大 edge 方向（价值投注）
        edges = {'主胜': edge_h, '平局': edge_d, '客胜': edge_a}
        value_bet = max(edges, key=edges.get)
        best_edge = edges[value_bet]
        value_bet_prob = probs[value_bet]
        
        # 推荐：如果最大 edge > 5% 且有意义
        recommended = best_edge > 0.05
        
        # Kelly 注码计算 (v4.3.0)
        kelly_info = ""
        if recommended and value_bet in ['主胜', '平局', '客胜']:
            odds_map = {'主胜': h, '平局': d, '客胜': a}
            prob_map = {'主胜': model_home, '平局': model_draw, '客胜': model_away}
            kelly = get_kelly_suggestion(
                probability=prob_map[value_bet],
                odds=odds_map[value_bet],
                risk_level="standard",
                current_bankroll=10000
            )
            kelly_info = f" | Kelly: 注码{kelly['stake']}EUR ({kelly['recommended_fraction']*100:.1f}%) [{kelly['risk_level']}]"
        
        # 置信度
        confidence = abs(best_edge) * 100 + 50
        confidence = min(95, max(55, confidence))
        
        return Prediction(
            market='胜平负',
            prediction=most_likely,
            confidence=confidence,
            edge=best_edge,
            recommended=recommended,
            reasoning=f"预测结果: {most_likely}（概率{most_likely_prob:.1%}）| 价值投注: {value_bet}（Edge{best_edge:+.1%}）| 市场隐含: 主{implied_h:.1%} 平{implied_d:.1%} 客{implied_a:.1%} | CoachFactor: 主CRI={self.match.coach_home_cri:.1f} 客CRI={self.match.coach_away_cri:.1f} | 阶段: {self.match.stage}{kelly_info}"
        )
    
    def _form_points(self, form: List[str]) -> float:
        """近期状态转分数"""
        points = {'W': 3, 'D': 1, 'L': 0}
        return sum(points.get(r, 0) for r in form)
    
    # ============================================================
    # 市场2: 让球胜平负 (Asian Handicap)
    # ============================================================
    
    def predict_ah(self) -> List[Prediction]:
        """
        让球预测
        
        基于1X2预测转换，加上让球线调整
        """
        predictions = []
        
        # 获取1X2预测
        pred_1x2 = self.predict_1x2()
        
        for handicap, (home_odds, away_odds) in self.match.odds_ah.items():
            # 解析让球数
            h_value = float(handicap.replace('+', '').replace('-', ''))
            h_sign = -1 if '-' in handicap else 1
            
            # 简化的让球概率模型
            # 如果预测客胜，考虑让球后的价值
            if pred_1x2.prediction == '客胜':
                # 强队让球，看让球后的价值
                if h_sign < 0:  # 强队让球（负 handicap 对强队）
                    # 瑞士让球，如果瑞士赢面大，让球后可能仍有机会
                    edge = pred_1x2.confidence / 100 - 0.6  # 简单估计
                    predictions.append(Prediction(
                        market=f'让球 {handicap}',
                        prediction='客队让球胜',
                        confidence=min(90, pred_1x2.confidence - 10),
                        edge=edge,
                        recommended=edge > 0.02,
                        reasoning=f'基于1X2客胜预测，强队让球后仍有价值'
                    ))
            elif pred_1x2.prediction == '主胜':
                if h_sign > 0:  # 弱队受让
                    edge = pred_1x2.confidence / 100 - 0.55
                    predictions.append(Prediction(
                        market=f'让球 {handicap}',
                        prediction='主队受让胜',
                        confidence=min(85, pred_1x2.confidence - 5),
                        edge=edge,
                        recommended=edge > 0.02,
                        reasoning=f'弱队受让，主场有机会'
                    ))
        
        return predictions
    
    # ============================================================
    # 市场3: 半全场 (HT/FT)
    # ============================================================
    
    def predict_htft(self) -> Prediction:
        """
        半全场预测
        
        模型：
        - 如果实力差距大，强队可能半场就领先
        - 如果冷门因子高，可能半场平局/落后
        """
        pred_1x2 = self.predict_1x2()
        
        # 简化的半全场逻辑
        if pred_1x2.prediction == '客胜':
            # 瑞士赢，如果实力差距大，可能半场就领先
            htft = '半场平/全场客胜'  # 最可能：先试探，后拿下
            confidence = 65
            edge = 0.05
        elif pred_1x2.prediction == '主胜':
            htft = '半场平/全场主胜'  # 冷门，上半场胶着
            confidence = 55
            edge = 0.03
        else:
            htft = '半场平/全场平'
            confidence = 50
            edge = 0.02
        
        return Prediction(
            market='半全场',
            prediction=htft,
            confidence=confidence,
            edge=edge,
            recommended=edge > 0.02,
            reasoning=f'基于全场预测{pred_1x2.prediction}，强队上半场可能试探'
        )
    
    # ============================================================
    # 市场4: 比分 (Correct Score)
    # ============================================================
    
    def predict_score(self) -> List[Prediction]:
        """
        比分预测
        
        基于泊松分布 + xG近似
        """
        # 估计预期进球
        home_xg = self.match.home_goals_scored / max(1, len(self.match.home_recent_form))
        away_xg = self.match.away_goals_scored / max(1, len(self.match.away_recent_form))
        
        # CoachFactor 调整：教练CRI差影响攻防效率
        # 主队教练CRI高 → 进攻提升，防守稳固
        # 客队教练CRI高 → 客队进攻提升，主队防守受压
        cri_diff = self.match.coach_home_cri - self.match.coach_away_cri  # 正=主队教练更强
        home_xg *= (1 + cri_diff * 0.03)  # 每差1分，xG调整3%
        away_xg *= (1 - cri_diff * 0.03)
        home_xg = max(0.1, home_xg)  # 最低0.1
        away_xg = max(0.1, away_xg)
        
        # 根据赔率调整
        h, d, a = self.match.odds_1x2
        # 如果客胜赔率很低（1.33），客队预期进球高
        if a < 1.5:
            away_xg *= 1.5
            home_xg *= 0.7
        
        # 泊松分布计算常见比分
        scores = []
        for home_goals in range(5):
            for away_goals in range(5):
                prob = self._poisson_prob(home_goals, home_xg) * self._poisson_prob(away_goals, away_xg)
                scores.append((home_goals, away_goals, prob))
        
        scores.sort(key=lambda x: x[2], reverse=True)
        
        predictions = []
        for i, (hg, ag, prob) in enumerate(scores[:5]):
            predictions.append(Prediction(
                market='比分',
                prediction=f'{hg}:{ag}',
                confidence=prob * 100,
                edge=prob - 0.05,  # 假设市场给这个比分的概率
                recommended=i < 2 and prob > 0.08,
                reasoning=f'泊松概率: {prob:.1%} | 预期进球: 主{home_xg:.1f} 客{away_xg:.1f}'
            ))
        
        return predictions
    
    def _poisson_prob(self, k: int, lam: float) -> float:
        """泊松概率"""
        import math
        return math.exp(-lam) * (lam ** k) / math.factorial(k)
    
    # ============================================================
    # 市场5: 大小球 (Over/Under)
    # ============================================================
    
    def predict_ou(self) -> List[Prediction]:
        """
        大小球预测
        
        基于预期总进球
        """
        # 估计预期进球
        home_xg = self.match.home_goals_scored / max(1, len(self.match.home_recent_form))
        away_xg = self.match.away_goals_scored / max(1, len(self.match.away_recent_form))
        
        # CoachFactor 调整：教练CRI差影响攻防效率
        cri_diff = self.match.coach_home_cri - self.match.coach_away_cri
        home_xg *= (1 + cri_diff * 0.03)
        away_xg *= (1 - cri_diff * 0.03)
        home_xg = max(0.1, home_xg)
        away_xg = max(0.1, away_xg)
        total_xg = home_xg + away_xg
        
        predictions = []
        
        for line, (over_odds, under_odds) in self.match.odds_ou.items():
            line_val = float(line)
            
            # 模型：总进球 vs 盘口线
            if total_xg > line_val + 0.5:
                prediction = '大球'
                prob = min(0.7, total_xg / line_val * 0.5)
            elif total_xg < line_val - 0.5:
                prediction = '小球'
                prob = min(0.7, line_val / total_xg * 0.5)
            else:
                prediction = '大球' if over_odds < under_odds else '小球'
                prob = 0.55
            
            implied_over = 1 / over_odds
            implied_under = 1 / under_odds
            total = implied_over + implied_under
            implied_over /= total
            implied_under /= total
            
            if prediction == '大球':
                edge = prob - implied_over
            else:
                edge = prob - implied_under
            
            predictions.append(Prediction(
                market=f'大小球 {line}',
                prediction=prediction,
                confidence=prob * 100,
                edge=edge,
                recommended=edge > 0.03,
                reasoning=f'预期总进球: {total_xg:.1f} | 盘口: {line} | 模型概率: {prob:.1%}'
            ))
        
        return predictions
    
    # ============================================================
    # 执行所有预测
    # ============================================================
    
    def predict_all(self) -> Dict[str, List[Prediction]]:
        """执行所有市场预测"""
        return {
            '1X2': [self.predict_1x2()],
            'AH': self.predict_ah(),
            'HT/FT': [self.predict_htft()],
            'Score': self.predict_score(),
            'O/U': self.predict_ou(),
        }

# ============================================================
# 演示：从 500.com 抓取并预测
# ============================================================

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description="多市场预测引擎")
    parser.add_argument('--match-id', default='1359233', help='500.com 比赛ID')
    parser.add_argument('--mode', choices=['pro', 'hybrid', 'requests'], default='hybrid',
                        help='抓取模式: pro=Playwright Pro, hybrid=轻量→Pro, requests=仅轻量')
    parser.add_argument('--stage', choices=['group', 'knockout', 'final'], default='group',
                        help='比赛阶段')
    parser.add_argument('--no-stealth', action='store_true', help='禁用 Stealth')
    parser.add_argument('--no-intercept', action='store_true', help='禁用资源拦截')
    args = parser.parse_args()
    
    print("=" * 60)
    print("Naga Quant System - Multi-Market Prediction Engine")
    print(f"Mode: {args.mode}, Stage: {args.stage}")
    print("=" * 60)
    print()
    
    # 从 500.com 抓取数据
    print(f"[Demo] 从 500.com 抓取数据 (match_id={args.match_id})...")
    
    use_pro = (args.mode == 'pro')
    if args.mode == 'hybrid':
        use_pro = False  # 先尝试轻量
    
    try:
        match = create_match_from_500(
            args.match_id,
            use_pro=use_pro,
            stealth=not args.no_stealth,
            intercept=not args.no_intercept
        )
        print(f"[Demo] 抓取成功: {match.home} vs {match.away}")
    except Exception as e:
        if args.mode == 'hybrid':
            print(f"[Demo] 轻量失败，切换到 Pro: {e}")
            match = create_match_from_500(
                args.match_id,
                use_pro=True,
                stealth=not args.no_stealth,
                intercept=not args.no_intercept
            )
            print(f"[Demo] Pro版抓取成功: {match.home} vs {match.away}")
        else:
            raise
    
    print(f"[Demo] Odds: {match.odds_1x2}")
    print()
    
    # 执行预测
    predictor = MultiMarketPredictor(match)
    predictions = predictor.predict_all()
    
    # Kelly 组合注码计算 (v4.3.0)
    value_bets = []
    for market, preds in predictions.items():
        for p in preds:
            if p.recommended and p.edge > 0.05:
                # 提取赔率和概率（简化处理）
                odds = 2.0
                if '让球' in p.market:
                    odds = 2.0
                elif '大小球' in p.market:
                    odds = 1.9
                elif '1X2' in p.market:
                    odds_map = {'主胜': match.odds_1x2[0], '平局': match.odds_1x2[1], '客胜': match.odds_1x2[2]}
                    odds = odds_map.get(p.prediction, 2.0)
                value_bets.append({
                    'selection': f"{p.market}: {p.prediction}",
                    'probability': p.confidence / 100,
                    'odds': odds,
                    'edge': p.edge
                })
    
    if len(value_bets) > 1:
        portfolio = portfolio_kelly(value_bets, 10000, "standard")
        print("=" * 60)
        print("KELLY PORTFOLIO ALLOCATION")
        print("=" * 60)
        print(f"  总注码: {portfolio['total_stake']} EUR ({portfolio['total_fraction']*100:.1f}%)")
        print(f"  剩余资金: {portfolio['remaining_bankroll']} EUR")
        for b in portfolio['bets']:
            print(f"  - {b['selection']}: {b['stake']:.0f} EUR")
        print()
    elif len(value_bets) == 1:
        kelly = get_kelly_suggestion(value_bets[0]['probability'], value_bets[0]['odds'], "standard", 10000)
        print("=" * 60)
        print("KELLY SUGGESTION")
        print("=" * 60)
        print(f"  推荐注码: {kelly['stake']} EUR ({kelly['recommended_fraction']*100:.1f}%)")
        print(f"  风险等级: {kelly['risk_description']}")
        print(f"  {kelly['notes']}")
        print()
    
    print("=" * 60)
    print("PREDICTIONS")
    print("=" * 60)
    print()
    
    for market, preds in predictions.items():
        print(f"[{market}]")
        for p in preds:
            rec = "[RECOMMENDED]" if p.recommended else "[Neutral]"
            print(f"  {p.prediction:20} | Confidence: {p.confidence:.0f}% | Edge: {p.edge:+.1%} | {rec}")
            print(f"    {p.reasoning}")
        print()
    
    print("=" * 60)
    print("Disclaimer: This is a research model. Not financial advice.")
    print("=" * 60)
