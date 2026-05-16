#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据侦察 Agent v2.0 - Football Quant OS
增强功能：500网投注分析数据抓取 + 手工投喂双模式
"""

import re
import json
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class MoneyFlowData:
    """资金流向数据模型"""
    # 基础信息
    match_id: str
    home_team: str
    away_team: str
    match_time: str
    
    # 百家欧赔
    euro_home_odds: float
    euro_draw_odds: float
    euro_away_odds: float
    euro_home_prob: float
    euro_draw_prob: float
    euro_away_prob: float
    
    # 必发数据
    bf_home_price: float
    bf_draw_price: float
    bf_away_price: float
    bf_home_volume: int
    bf_draw_volume: int
    bf_away_volume: int
    bf_total_volume: int
    
    # 庄家盈亏
    bookmaker_home_pnl: int
    bookmaker_draw_pnl: int
    bookmaker_away_pnl: int
    
    # 指数
    profit_index_home: int
    profit_index_draw: int
    profit_index_away: int
    cold_hot_index_home: Optional[int]
    cold_hot_index_draw: Optional[int]
    cold_hot_index_away: Optional[int]
    
    # 大额交易
    large_transactions: List[Dict[str, Any]]
    
    # 元数据
    data_source: str  # "500_auto" | "manual"
    fetch_time: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DataScout:
    """数据侦察 Agent v2.0"""
    
    name = "DataScout"
    version = "2.0"
    
    # 500网投注分析页面URL模板
    _500_URL_TEMPLATE = "https://odds.500.com/fenxi/touzhu-{match_id}.shtml"
    
    def __init__(self):
        self.money_flow_cache: Dict[str, MoneyFlowData] = {}
    
    def run(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        主运行方法
        
        Args:
            match_data: 比赛数据字典
                - home_team: 主队名
                - away_team: 客队名
                - match_id: 500网比赛ID (可选)
                - money_flow_manual: 手工投喂的资金流向数据 (可选)
        
        Returns:
            包含基础预测和资金流向数据的分析结果
        """
        home = match_data.get('home_team', '')
        away = match_data.get('away_team', '')
        match_id = match_data.get('match_id')
        
        # 1. 基础数据分析
        base_result = self._analyze_base(match_data)
        
        # 2. 资金流向数据获取
        money_flow = None
        
        # 优先使用手工投喂数据
        if 'money_flow_manual' in match_data:
            money_flow = self._parse_manual_money_flow(
                match_data['money_flow_manual'],
                home, away
            )
        # 其次尝试自动抓取
        elif match_id:
            money_flow = self._fetch_500_money_flow(match_id, home, away)
        
        # 3. 组装结果
        result = {
            "agent": self.name,
            "version": self.version,
            "prediction": base_result["prediction"],
            "confidence": base_result["confidence"],
            "recommendation": base_result["recommendation"],
            "key_factors": base_result["key_factors"],
        }
        
        if money_flow:
            result["money_flow"] = money_flow.to_dict()
            result["key_factors"].append(f"资金流向：已加载 ({money_flow.data_source})")
        else:
            result["key_factors"].append("资金流向：未获取")
        
        return result
    
    def _analyze_base(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """基础数据分析（原有逻辑）"""
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
            "key_factors": [f"基础推荐：{recommendation}", "快速决策模式"]
        }
    
    def _fetch_500_money_flow(self, match_id: str, home_team: str, away_team: str) -> Optional[MoneyFlowData]:
        """
        从500网抓取资金流向数据
        
        注意：实际抓取需要使用浏览器自动化或requests+解析
        这里提供数据结构和解析逻辑框架
        """
        url = self._500_URL_TEMPLATE.format(match_id=match_id)
        
        # TODO: 实现实际抓取逻辑
        # 方案1: 使用 requests + BeautifulSoup/正则
        # 方案2: 使用 Playwright/Selenium 浏览器自动化
        
        # 示例：返回模拟数据（实际实现时替换为真实抓取）
        # return self._parse_500_html(html_content, match_id, home_team, away_team)
        
        return None  # 暂未实现自动抓取
    
    def _parse_500_html(self, html: str, match_id: str, home: str, away: str) -> MoneyFlowData:
        """
        解析500网HTML提取资金流向数据
        
        基于页面结构：
        - 热度分析表格：百家欧赔、交易比例、必发成交、指数分析
        - 必发交易区域：成交量、成交走势
        - 大额交易明细：综合、属性、成交量、交易时间、交易比例
        """
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # 提取比赛时间
        match_time = self._extract_match_time(soup)
        
        # 提取热度分析表格数据
        heat_data = self._extract_heat_table(soup)
        
        # 提取必发交易数据
        bf_data = self._extract_betfair_data(soup)
        
        # 提取大额交易明细
        large_trans = self._extract_large_transactions(soup)
        
        return MoneyFlowData(
            match_id=match_id,
            home_team=home,
            away_team=away,
            match_time=match_time,
            
            # 百家欧赔
            euro_home_odds=heat_data.get('euro_home_odds', 0),
            euro_draw_odds=heat_data.get('euro_draw_odds', 0),
            euro_away_odds=heat_data.get('euro_away_odds', 0),
            euro_home_prob=heat_data.get('euro_home_prob', 0),
            euro_draw_prob=heat_data.get('euro_draw_prob', 0),
            euro_away_prob=heat_data.get('euro_away_prob', 0),
            
            # 必发数据
            bf_home_price=bf_data.get('bf_home_price', 0),
            bf_draw_price=bf_data.get('bf_draw_price', 0),
            bf_away_price=bf_data.get('bf_away_price', 0),
            bf_home_volume=bf_data.get('bf_home_volume', 0),
            bf_draw_volume=bf_data.get('bf_draw_volume', 0),
            bf_away_volume=bf_data.get('bf_away_volume', 0),
            bf_total_volume=bf_data.get('bf_total_volume', 0),
            
            # 庄家盈亏
            bookmaker_home_pnl=bf_data.get('bookmaker_home_pnl', 0),
            bookmaker_draw_pnl=bf_data.get('bookmaker_draw_pnl', 0),
            bookmaker_away_pnl=bf_data.get('bookmaker_away_pnl', 0),
            
            # 指数
            profit_index_home=bf_data.get('profit_index_home', 0),
            profit_index_draw=bf_data.get('profit_index_draw', 0),
            profit_index_away=bf_data.get('profit_index_away', 0),
            cold_hot_index_home=bf_data.get('cold_hot_index_home'),
            cold_hot_index_draw=bf_data.get('cold_hot_index_draw'),
            cold_hot_index_away=bf_data.get('cold_hot_index_away'),
            
            # 大额交易
            large_transactions=large_trans,
            
            data_source="500_auto",
            fetch_time=datetime.now().isoformat()
        )
    
    def _parse_manual_money_flow(self, manual_data: Dict[str, Any], home: str, away: str) -> MoneyFlowData:
        """解析手工投喂的资金流向数据"""
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
            cold_hot_index_home=manual_data.get('cold_hot_index_home'),
            cold_hot_index_draw=manual_data.get('cold_hot_index_draw'),
            cold_hot_index_away=manual_data.get('cold_hot_index_away'),
            
            large_transactions=manual_data.get('large_transactions', []),
            
            data_source="manual",
            fetch_time=datetime.now().isoformat()
        )
    
    def _extract_match_time(self, soup) -> str:
        """提取比赛时间"""
        # 从页面标题或比赛信息区域提取
        time_elem = soup.find('p', string=re.compile(r'比赛时间'))
        if time_elem:
            match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2})', time_elem.text)
            if match:
                return match.group(1)
        return ""
    
    def _extract_heat_table(self, soup) -> Dict[str, Any]:
        """提取热度分析表格数据"""
        data = {}
        
        # 查找热度分析表格
        heat_heading = soup.find('h4', string='热度分析')
        if heat_heading:
            table = heat_heading.find_next('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 11:
                        label = cells[0].text.strip()
                        if '水晶宫' in label or '主' in label:
                            data['euro_home_odds'] = self._parse_float(cells[1].text)
                            data['euro_home_prob'] = self._parse_percent(cells[2].text)
                        elif '平局' in label or '平' in label:
                            data['euro_draw_odds'] = self._parse_float(cells[1].text)
                            data['euro_draw_prob'] = self._parse_percent(cells[2].text)
                        elif '西汉姆' in label or '客' in label:
                            data['euro_away_odds'] = self._parse_float(cells[1].text)
                            data['euro_away_prob'] = self._parse_percent(cells[2].text)
        
        return data
    
    def _extract_betfair_data(self, soup) -> Dict[str, Any]:
        """提取必发交易数据"""
        data = {}
        
        # 查找必发交易区域
        bf_heading = soup.find('h4', string='必发交易')
        if bf_heading:
            # 提取总交易量
            total_elem = bf_heading.find_next('em')
            if total_elem:
                data['bf_total_volume'] = self._parse_volume(total_elem.text)
            
            # 查找必发交易表格
            table = bf_heading.find_next('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        label = cells[0].text.strip()
                        if '主胜' in label:
                            data['bf_home_volume'] = self._parse_volume(cells[1].text)
                            data['bf_home_price'] = self._parse_float(cells[2].text)
                        elif '平局' in label:
                            data['bf_draw_volume'] = self._parse_volume(cells[1].text)
                            data['bf_draw_price'] = self._parse_float(cells[2].text)
                        elif '客胜' in label:
                            data['bf_away_volume'] = self._parse_volume(cells[1].text)
                            data['bf_away_price'] = self._parse_float(cells[2].text)
        
        # 查找庄家盈亏表格
        pnl_table = soup.find('table', text=re.compile('庄家盈亏'))
        if pnl_table:
            rows = pnl_table.find_all('tr')
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    label = cells[0].text.strip()
                    pnl = self._parse_int(cells[1].text.replace(',', ''))
                    profit_idx = self._parse_int(cells[2].text)
                    if '主胜' in label:
                        data['bookmaker_home_pnl'] = pnl
                        data['profit_index_home'] = profit_idx
                    elif '平局' in label:
                        data['bookmaker_draw_pnl'] = pnl
                        data['profit_index_draw'] = profit_idx
                    elif '客胜' in label:
                        data['bookmaker_away_pnl'] = pnl
                        data['profit_index_away'] = profit_idx
        
        return data
    
    def _extract_large_transactions(self, soup) -> List[Dict[str, Any]]:
        """提取大额交易明细"""
        transactions = []
        
        # 查找大额交易明细表格
        large_heading = soup.find('h4', string='必发大额交易明细')
        if large_heading:
            table = large_heading.find_next('table')
            if table:
                rows = table.find_all('tr')[1:]  # 跳过表头
                for row in rows[:10]:  # 只取前10条
                    cells = row.find_all('td')
                    if len(cells) >= 5:
                        transactions.append({
                            'direction': cells[0].text.strip(),  # 主/平/客
                            'type': cells[1].text.strip(),       # 买/卖
                            'volume': self._parse_float(cells[2].text),
                            'time': cells[3].text.strip(),
                            'ratio': cells[4].text.strip()
                        })
        
        return transactions
    
    @staticmethod
    def _parse_float(text: str) -> float:
        """解析浮点数"""
        try:
            return float(text.strip().replace(',', ''))
        except:
            return 0.0
    
    @staticmethod
    def _parse_int(text: str) -> int:
        """解析整数"""
        try:
            return int(text.strip().replace(',', ''))
        except:
            return 0
    
    @staticmethod
    def _parse_percent(text: str) -> float:
        """解析百分比"""
        try:
            return float(text.strip().replace('%', ''))
        except:
            return 0.0
    
    @staticmethod
    def _parse_volume(text: str) -> int:
        """解析成交量（处理逗号分隔符）"""
        try:
            return int(text.strip().replace(',', ''))
        except:
            return 0


# ============ 手工投喂数据模板 ============

MANUAL_INPUT_TEMPLATE = {
    "match_id": "1202700",
    "match_time": "2026-04-21 03:00",
    
    # 百家欧赔
    "euro_home_odds": 2.55,
    "euro_draw_odds": 3.30,
    "euro_away_odds": 2.80,
    "euro_home_prob": 37.3,
    "euro_draw_prob": 28.8,
    "euro_away_prob": 33.9,
    
    # 必发数据
    "bf_home_price": 2.72,
    "bf_draw_price": 3.5,
    "bf_away_price": 2.92,
    "bf_home_volume": 866675,
    "bf_draw_volume": 554147,
    "bf_away_volume": 887415,
    "bf_total_volume": 2308237,
    
    # 庄家盈亏
    "bookmaker_home_pnl": -49119,
    "bookmaker_draw_pnl": 368723,
    "bookmaker_away_pnl": -283015,
    
    # 指数
    "profit_index_home": -3,
    "profit_index_draw": 15,
    "profit_index_away": -13,
    "cold_hot_index_home": None,
    "cold_hot_index_draw": -17,
    "cold_hot_index_away": 13,
    
    # 大额交易
    "large_transactions": [
        {"direction": "客", "type": "买", "volume": 8470.0, "time": "2026-04-20 21:57", "ratio": "38.2%"},
        {"direction": "主", "type": "卖", "volume": 12522.0, "time": "2026-04-20 21:57", "ratio": "39.7%"},
    ]
}


if __name__ == "__main__":
    # 测试代码
    scout = DataScout()
    
    # 测试1：基础模式（无资金流向）
    result1 = scout.run({
        "home_team": "水晶宫",
        "away_team": "西汉姆联",
        "home_win": 40,
        "draw": 30,
        "away_win": 30
    })
    print("=== 测试1：基础模式 ===")
    print(json.dumps(result1, ensure_ascii=False, indent=2))
    
    # 测试2：手工投喂模式
    result2 = scout.run({
        "home_team": "水晶宫",
        "away_team": "西汉姆联",
        "home_win": 40,
        "draw": 30,
        "away_win": 30,
        "money_flow_manual": MANUAL_INPUT_TEMPLATE
    })
    print("\n=== 测试2：手工投喂模式 ===")
    print(json.dumps(result2, ensure_ascii=False, indent=2))
