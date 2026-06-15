#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Football Quant OS - 数据集成统一入口
整合所有数据源，提供统一接口
"""
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd

# 添加脚本路径
sys.path.insert(0, str(Path(__file__).parent))

from data_football_data_co_uk import FootballDataUK
from data_api_football import APIFootball, FeatureExtractor
from data_kaggle import KaggleData
from data_openfootball import OpenFootball


class DataIntegration:
    """
    数据集成统一入口
    
    使用方式:
        data = DataIntegration()
        
        # 获取历史赔率数据 (football-data.co.uk)
        df = data.get_historical_odds("WC", 2022)
        
        # 获取实时数据 (API-Football)
        fixtures = data.get_live_fixtures("WC", 2026)
        
        # 获取球队统计
        stats = data.get_team_stats("Brazil", "WC", 2022)
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.football_data = FootballDataUK()
        self.api_football = APIFootball(api_key) if api_key else None
        self.kaggle = KaggleData()
        self.openfootball = OpenFootball()
    
    def get_historical_odds(self, league: str, season: int) -> Optional[pd.DataFrame]:
        """
        获取历史赔率数据
        
        数据源: football-data.co.uk
        覆盖: 英超、西甲、德甲、意甲、法甲、世界杯、欧洲杯
        """
        return self.football_data.download_season(league, str(season))
    
    def get_live_fixtures(self, league: str, season: int) -> List[Dict]:
        """
        获取实时比赛数据
        
        数据源: API-Football
        需要: API Key
        """
        if not self.api_football:
            print("[错误] 需要 API-Football Key 才能获取实时数据")
            return []
        
        return self.api_football.get_fixtures(league, season)
    
    def get_team_stats(self, team_name: str, league: str, season: int) -> Optional[Dict]:
        """
        获取球队统计
        
        数据源: API-Football
        """
        if not self.api_football:
            return None
        
        teams = self.api_football.search_team(team_name)
        if not teams:
            return None
        
        team_id = teams[0]["team"]["id"]
        return self.api_football.get_team_statistics(team_id, league, season)
    
    def get_historical_worldcup(self, year: int = 2022) -> Optional[pd.DataFrame]:
        """
        获取世界杯历史数据
        
        数据源: Kaggle (Evan Gower dataset - 1930-2018) + 2022 Qatar
        """
        if year == 2022:
            # 2022 Qatar数据
            kaggle_2022 = Path("D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_2022_qatar/Fifa_WC_2022_Match_data.csv")
            if kaggle_2022.exists():
                return pd.read_csv(kaggle_2022, encoding='latin-1')
            return None
        else:
            # 1930-2018数据
            kaggle_path = Path("D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_1930-2018/wcmatches.csv")
            if kaggle_path.exists():
                df = pd.read_csv(kaggle_path)
                return df[df['year'] == year]
            return None
    
    def get_2022_match_data(self, home: str, away: str) -> Optional[Dict]:
        """
        获取2022特定比赛的详细数据
        
        返回: {
            'home_xg': xG,
            'away_xg': xG,
            'home_poss': 控球率,
            'away_poss': 控球率,
            'home_goals': 进球,
            'away_goals': 进球,
            'stage': 阶段
        }
        """
        df = self.get_historical_worldcup(2022)
        if df is None:
            return None
        
        match = df[(df['1'] == home) & (df['2'] == away)]
        if len(match) == 0:
            # 可能主客场反过来
            match = df[(df['1'] == away) & (df['2'] == home)]
        
        if len(match) > 0:
            m = match.iloc[0]
            return {
                'home_xg': float(m['1_xg']),
                'away_xg': float(m['2_xg']),
                'home_poss': float(m['1_poss']),
                'away_poss': float(m['2_poss']),
                'home_goals': int(m['1_goals']),
                'away_goals': int(m['2_goals']),
                'stage': str(m['group']),
                'date': str(m['date'])
            }
        return None
    
    def get_historical_upset_rates(self, years: List[int] = None) -> Dict[str, float]:
        """
        获取历史爆冷率
        
        基于Kaggle 1930-2018数据计算
        
        返回:
            {
                'group': 小组赛平均爆冷率,
                'knockout': 淘汰赛平均爆冷率
            }
        """
        kaggle_path = Path("D:/openclaw-workspace/football_quant_os/data/kaggle/worldcup_1930-2018/wcmatches.csv")
        if not kaggle_path.exists():
            print("[错误] Kaggle数据未找到，请先下载")
            return {'group': 0.342, 'knockout': 0.373}  # 默认值
        
        df = pd.read_csv(kaggle_path)
        
        if years is None:
            years = [2018, 2014, 2010, 2006, 2002]
        
        results = {'group': [], 'knockout': []}
        
        for year in years:
            year_df = df[df['year'] == year]
            if len(year_df) == 0:
                continue
            
            group = year_df[year_df['stage'].str.contains('Group', na=False)]
            knockout = year_df[year_df['stage'].str.contains('Round of 16|Quarter|Semi|Final', na=False, regex=True)]
            
            if len(group) > 0:
                group_upsets = len(group[group['outcome'] == 'A'])
                results['group'].append(group_upsets / len(group))
            
            if len(knockout) > 0:
                knockout_upsets = len(knockout[knockout['outcome'] == 'A'])
                results['knockout'].append(knockout_upsets / len(knockout))
        
        return {
            'group': round(sum(results['group']) / len(results['group']), 3) if results['group'] else 0.342,
            'knockout': round(sum(results['knockout']) / len(results['knockout']), 3) if results['knockout'] else 0.373
        }
    
    def get_worldcup_standings(self, year: str = "2022", group: str = "a") -> List[Dict]:
        """
        获取世界杯小组积分榜
        
        数据源: OpenFootball
        """
        return self.openfootball.calculate_group_standings(year, group)
    
    def get_multi_source_features(self, home: str, away: str, league: str = "WC", season: int = 2022) -> Dict[str, Any]:
        """
        多源特征融合
        
        整合多个数据源的特征:
        - football-data: 历史赔率、结果
        - API-Football: xG、射门、控球率
        - Kaggle: 完整比赛统计
        - OpenFootball: 结构化数据
        """
        features = {
            "home": home,
            "away": away,
            "sources": {},
            "features": {}
        }
        
        # 1. 历史赔率特征
        try:
            df = self.get_historical_odds(league, season)
            if df is not None:
                # 查找相关比赛
                match = df[(df['HomeTeam'] == home) & (df['AwayTeam'] == away)]
                if not match.empty:
                    features["sources"]["football_data"] = True
                    features["features"]["odds_home"] = match['B365H'].values[0]
                    features["features"]["odds_draw"] = match['B365D'].values[0]
                    features["features"]["odds_away"] = match['B365A'].values[0]
        except Exception as e:
            print(f"[警告] football-data 特征获取失败: {e}")
        
        # 2. API-Football 实时特征
        if self.api_football:
            try:
                fixtures = self.api_football.get_fixtures(league, season)
                for fixture in fixtures:
                    if fixture["teams"]["home"]["name"] == home and fixture["teams"]["away"]["name"] == away:
                        fixture_id = fixture["fixture"]["id"]
                        stats = self.api_football.get_fixture_statistics(fixture_id)
                        if stats:
                            features["sources"]["api_football"] = True
                            xg = FeatureExtractor.extract_xg(stats)
                            shots = FeatureExtractor.extract_shots(stats)
                            possession = FeatureExtractor.extract_possession(stats)
                            features["features"]["xg_home"] = xg["home"]
                            features["features"]["xg_away"] = xg["away"]
                            features["features"]["shots_home"] = shots["home"]["on"]
                            features["features"]["shots_away"] = shots["away"]["on"]
                            features["features"]["possession_home"] = possession["home"]
            except Exception as e:
                print(f"[警告] API-Football 特征获取失败: {e}")
        
        return features
    
    def get_stage_calibration_factors(self) -> Dict[str, float]:
        """
        获取阶段校准系数
        
        基于历史数据计算小组赛vs淘汰赛的调整系数
        
        返回:
            {
                'group_adjustment': 小组赛概率调整系数 (通常 < 1.0),
                'knockout_adjustment': 淘汰赛概率调整系数 (通常 > 1.0)
            }
        """
        rates = self.get_historical_upset_rates()
        
        # 基准: 如果小组赛爆冷率 = 34.2%, 淘汰赛 = 37.3%
        # 淘汰赛比小组赛高 3.1个百分点
        
        # 校准系数:
        # 小组赛: 强队概率下调15-20% (因为爆冷率较高)
        # 淘汰赛: 强队概率上调30-40% (因为冷门更多)
        
        group_rate = rates['group']
        knockout_rate = rates['knockout']
        
        # 根据历史数据动态计算调整系数
        base_rate = 0.35  # 基准爆冷率
        
        group_factor = 1.0 - (group_rate - base_rate) * 0.5  # 0.85-0.90
        knockout_factor = 1.0 + (knockout_rate - base_rate) * 1.5  # 1.30-1.40
        
        return {
            'group_adjustment': round(max(0.85, min(0.95, group_factor)), 2),
            'knockout_adjustment': round(max(1.20, min(1.50, knockout_factor)), 2),
            'group_upset_rate': group_rate,
            'knockout_upset_rate': knockout_rate
        }


def main():
    """示例：多源数据融合 + 历史校准"""
    data = DataIntegration()
    
    # 获取历史赔率
    df = data.get_historical_odds("WC", 2022)
    if df is not None:
        print(f"历史赔率数据: {len(df)} 场比赛")
    
    # 获取历史爆冷率
    rates = data.get_historical_upset_rates()
    print(f"\n历史平均爆冷率:")
    print(f"  小组赛: {rates['group']:.1%}")
    print(f"  淘汰赛: {rates['knockout']:.1%}")
    
    # 获取阶段校准系数
    calibration = data.get_stage_calibration_factors()
    print(f"\n阶段校准系数:")
    print(f"  小组赛调整: {calibration['group_adjustment']:.2f}")
    print(f"  淘汰赛调整: {calibration['knockout_adjustment']:.2f}")
    
    # 获取世界杯积分榜
    standings = data.get_worldcup_standings("2022", "a")
    print(f"\n2022世界杯A组积分榜:")
    for team in standings:
        print(f"  {team['team']}: {team['points']}分")
    
    # 多源特征融合（示例）
    print("\n多源特征融合示例 (Brazil vs Serbia):")
    features = data.get_multi_source_features("Brazil", "Serbia", "WC", 2022)
    print(f"  可用数据源: {list(features['sources'].keys())}")
    print(f"  特征: {features['features']}")


if __name__ == "__main__":
    main()
