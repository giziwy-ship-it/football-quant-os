#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据侦察 Agent v3.0 - Football Quant OS (P1 修复)

整合数据源：
  1. The Odds API（官方赔率数据，自动获取）
  2. ESPN（免费赛程数据）
  3. 500.com（备用抓取，手工投喂）

v3.0 变更：
  - 实现自动抓取（不再依赖手工投喂）
  - 使用 UnifiedOddsClient 获取真实赔率
  - 支持缓存和错误处理
"""

import sys
import os
import json
import asyncio
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime

from core.config import config
from core.odds_client import UnifiedOddsClient, OddsData


@dataclass
class MoneyFlowData:
    """资金流向数据模型"""
    match_id: str
    home_team: str
    away_team: str
    match_time: str
    
    euro_home_odds: float
    euro_draw_odds: float
    euro_away_odds: float
    euro_home_prob: float
    euro_draw_prob: float
    euro_away_prob: float
    
    bf_home_price: float = 0
    bf_draw_price: float = 0
    bf_away_price: float = 0
    bf_home_volume: int = 0
    bf_draw_volume: int = 0
    bf_away_volume: int = 0
    bf_total_volume: int = 0
    
    bookmaker_home_pnl: int = 0
    bookmaker_draw_pnl: int = 0
    bookmaker_away_pnl: int = 0
    
    profit_index_home: int = 0
    profit_index_draw: int = 0
    profit_index_away: int = 0
    
    large_transactions: List[Dict[str, Any]] = None
    data_source: str = "auto"
    fetch_time: str = ""
    
    def __post_init__(self):
        if self.large_transactions is None:
            self.large_transactions = []
        if not self.fetch_time:
            self.fetch_time = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DataScout:
    """
    数据侦察 Agent v3.0
    
    自动获取赔率数据，无需手工投喂。
    支持多源数据融合，自动选择最佳数据源。
    """
    
    name = "DataScout"
    version = "3.0"
    
    def __init__(self):
        self.odds_client = UnifiedOddsClient()
        self.money_flow_cache: Dict[str, MoneyFlowData] = {}
        self._last_fetched: Dict[str, datetime] = {}
        self._cache_ttl = 300  # 5 分钟
    
    async def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        主运行方法
        
        Args:
            match_data: 比赛数据字典
                - home_team: 主队名
                - away_team: 客队名
                - league: 联赛名（用于匹配数据源）
                - match_id: 500网比赛ID（可选，用于备用抓取）
                - money_flow_manual: 手工投喂（可选，v3.0 不推荐）
        
        Returns:
            包含真实赔率 + 资金流向的分析结果
        """
        home = match_data.get('home_team', '')
        away = match_data.get('away_team', '')
        league = match_data.get('league', 'Unknown')
        match_id = match_data.get('match_id', '')
        
        # 1. 尝试自动获取赔率
        odds_data = await self._fetch_auto_odds(home, away, league)
        
        # 2. 如果自动获取失败，尝试手工投喂
        if not odds_data and 'money_flow_manual' in match_data:
            odds_data = self._parse_manual_money_flow(
                match_data['money_flow_manual'],
                home, away
            )
        
        # 3. 基础数据分析
        base_result = self._analyze_base(match_data)
        
        # 4. 组装结果
        result = {
            "agent": self.name,
            "version": self.version,
            "prediction": base_result["prediction"],
            "confidence": base_result["confidence"],
            "recommendation": base_result["recommendation"],
            "key_factors": base_result["key_factors"],
        }
        
        if odds_data:
            result["money_flow"] = odds_data.to_dict()
            result["market_odds"] = {
                "home_win": odds_data.euro_home_odds,
                "draw": odds_data.euro_draw_odds,
                "away_win": odds_data.euro_away_odds,
            }
            result["key_factors"].append(
                f"真实赔率已获取 ({odds_data.data_source})"
            )
            result["key_factors"].append(
                f"市场概率: 主{odds_data.euro_home_prob:.1%} "
                f"平{odds_data.euro_draw_prob:.1%} "
                f"客{odds_data.euro_away_prob:.1%}"
            )
        else:
            result["key_factors"].append("赔率数据未获取（使用默认值）")
        
        return result
    
    async def _fetch_auto_odds(
        self,
        home: str,
        away: str,
        league: str
    ) -> Optional[MoneyFlowData]:
        """自动获取赔率数据"""
        # 将联赛名映射到 The Odds API 的 sport 代码
        sport_map = {
            "Premier League": "soccer_epl",
            "EPL": "soccer_epl",
            "英超": "soccer_epl",
            "La Liga": "soccer_spain_la_liga",
            "西甲": "soccer_spain_la_liga",
            "Bundesliga": "soccer_germany_bundesliga",
            "德甲": "soccer_germany_bundesliga",
            "Serie A": "soccer_italy_serie_a",
            "意甲": "soccer_italy_serie_a",
            "Ligue 1": "soccer_france_ligue_one",
            "法甲": "soccer_france_ligue_one",
            "Champions League": "soccer_uefa_champs_league",
            "欧冠": "soccer_uefa_champs_league",
            "World Cup": "soccer_fifa_world_cup",
            "世界杯": "soccer_fifa_world_cup",
        }
        
        sport = sport_map.get(league, "soccer_epl")
        
        try:
            odds_list = await self.odds_client.get_odds(sport=sport)
            
            # 匹配比赛
            for odds in odds_list:
                if self._match_teams(odds, home, away):
                    return self._convert_to_money_flow(odds)
            
            print(f"[DataScout] 未找到匹配: {home} vs {away} [{league}]")
            return None
            
        except Exception as e:
            print(f"[DataScout] 自动获取失败: {e}")
            return None
    
    def _match_teams(self, odds: OddsData, home: str, away: str) -> bool:
        """匹配球队名（模糊匹配）"""
        home_lower = home.lower()
        away_lower = away.lower()
        
        odds_home = odds.home_team.lower()
        odds_away = odds.away_team.lower()
        
        # 直接包含匹配
        if home_lower in odds_home or odds_home in home_lower:
            if away_lower in odds_away or odds_away in away_lower:
                return True
        
        # 交换方向再匹配
        if home_lower in odds_away or odds_away in home_lower:
            if away_lower in odds_home or odds_home in away_lower:
                return True
        
        return False
    
    def _convert_to_money_flow(self, odds: OddsData) -> MoneyFlowData:
        """将 OddsData 转换为 MoneyFlowData"""
        return MoneyFlowData(
            match_id=odds.match_id,
            home_team=odds.home_team,
            away_team=odds.away_team,
            match_time=odds.match_time,
            euro_home_odds=odds.home_odds,
            euro_draw_odds=odds.draw_odds,
            euro_away_odds=odds.away_odds,
            euro_home_prob=odds.home_prob,
            euro_draw_prob=odds.draw_prob,
            euro_away_prob=odds.away_prob,
            data_source=odds.source,
        )
    
    def _parse_manual_money_flow(
        self,
        manual_data: Dict[str, Any],
        home: str,
        away: str
    ) -> MoneyFlowData:
        """解析手工投喂的资金流向数据（v3.0 向后兼容）"""
        return MoneyFlowData(
            match_id=manual_data.get('match_id', 'manual'),
            home_team=home,
            away_team=away,
            match_time=manual_data.get('match_time', ''),
            euro_home_odds=manual_data.get('euro_home_odds', 0),
            euro_draw_odds=manual_data.get('euro_draw_odds', 0),
            euro_away_odds=manual_data.get('euro_away_odds', 0),
            euro_home_prob=manual_data.get('euro_home_prob', 0),
            euro_draw_prob=manual_data.get('euro_draw_prob', 0),
            euro_away_prob=manual_data.get('euro_away_prob', 0),
            bf_home_price=manual_data.get('bf_home_price', 0),
            bf_draw_price=manual_data.get('bf_draw_price', 0),
            bf_away_price=manual_data.get('bf_away_price', 0),
            bf_home_volume=manual_data.get('bf_home_volume', 0),
            bf_draw_volume=manual_data.get('bf_draw_volume', 0),
            bf_away_volume=manual_data.get('bf_away_volume', 0),
            bf_total_volume=manual_data.get('bf_total_volume', 0),
            bookmaker_home_pnl=manual_data.get('bookmaker_home_pnl', 0),
            bookmaker_draw_pnl=manual_data.get('bookmaker_draw_pnl', 0),
            bookmaker_away_pnl=manual_data.get('bookmaker_away_pnl', 0),
            profit_index_home=manual_data.get('profit_index_home', 0),
            profit_index_draw=manual_data.get('profit_index_draw', 0),
            profit_index_away=manual_data.get('profit_index_away', 0),
            large_transactions=manual_data.get('large_transactions', []),
            data_source="manual",
        )
    
    def _analyze_base(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """基础数据分析"""
        home_win = match_data.get('home_win', 40)
        draw = match_data.get('draw', 30)
        away_win = match_data.get('away_win', 30)
        
        if home_win > 50:
            recommendation = "主胜"
        elif away_win > 45:
            recommendation = "客胜"
        else:
            recommendation = "平局"
        
        confidence = 0.8 if max(home_win, away_win, draw) > 55 else 0.75
        
        return {
            "prediction": {"home_win": home_win, "draw": draw, "away_win": away_win},
            "confidence": confidence,
            "recommendation": recommendation,
            "key_factors": [f"基础推荐：{recommendation}", "DataScout v3.0 自动模式"]
        }
    
    async def close(self):
        """关闭资源"""
        await self.odds_client.close()


# 向后兼容的同步接口
class DataScoutSync:
    """DataScout 同步包装器（用于旧代码兼容）"""
    
    def __init__(self):
        self._async_scout = DataScoutAsync()
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """同步运行接口"""
        try:
            # 检查是否已有事件循环
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = None
            
            if loop and loop.is_running():
                # 在已有事件循环中，使用 nest_asyncio 或线程池
                import nest_asyncio
                nest_asyncio.apply()
                return asyncio.run(self._async_scout.run(match_data))
            else:
                # 没有事件循环，直接创建
                return asyncio.run(self._async_scout.run(match_data))
                
        except Exception as e:
            print(f"[DataScoutSync] 异步运行失败，回退到基础模式: {e}")
            return self._fallback_result(e)
    
    def _fallback_result(self, error) -> Dict[str, Any]:
        """回退到基础模式"""
        return {
            "agent": "DataScout",
            "version": "3.0",
            "prediction": {"home_win": 40, "draw": 30, "away_win": 30},
            "confidence": 0.5,
            "recommendation": "平局",
            "key_factors": ["自动获取失败，使用默认", f"错误: {str(error)}"]
        }
    
    def close(self):
        pass


# 保持导入兼容性：DataScout 即同步包装器
# 旧代码: from agents.datascout_v2 import DataScout
# DataScout 现在就是 DataScoutSync，无需额外重命名

# 为向后兼容，添加别名
DataScoutAsync = DataScout

# 导出主类：DataScout = 同步包装器
DataScout = DataScoutSync
