"""
Football Quant OS - 统一数据获取抽象层 (DataFetcher)

解耦具体数据源实现，提供统一的接口:
- Kaggle 历史数据
- football-data.co.uk 赔率数据
- API-Football 实时数据
- OpenFootball 结构化数据
- 本地文件缓存

设计模式: Strategy + Factory
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json
import csv
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import pandas as pd


class DataFetcher(ABC):
    """
    数据获取抽象基类
    
    所有数据源必须实现此接口。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """数据源名称"""
        pass
    
    @property
    @abstractmethod
    def supports_historical(self) -> bool:
        """是否支持历史数据"""
        pass
    
    @property
    @abstractmethod
    def supports_live(self) -> bool:
        """是否支持实时数据"""
        pass
    
    @abstractmethod
    def fetch_matches(self, 
                     tournament: str = 'worldcup',
                     year: Optional[int] = None,
                     stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取比赛数据
        
        Args:
            tournament: 赛事名称 (worldcup, premier_league, etc.)
            year: 年份 (如 2022, 2026)
            stage: 阶段 (group, knockout, final)
        
        Returns:
            List[Dict]: 比赛数据列表
        """
        pass
    
    @abstractmethod
    def fetch_odds(self, 
                  match_id: str,
                  market: str = '1x2') -> Dict[str, Any]:
        """
        获取赔率数据
        
        Args:
            match_id: 比赛ID
            market: 市场类型 (1x2, over_under, asian_handicap)
        
        Returns:
            Dict: 赔率数据
        """
        pass
    
    @abstractmethod
    def fetch_teams(self,
                   tournament: str = 'worldcup',
                   year: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        获取球队数据
        
        Returns:
            List[Dict]: 球队信息列表
        """
        pass
    
    def validate_data(self, data: List[Dict[str, Any]]) -> Tuple[bool, List[str]]:
        """
        数据校验
        
        Returns:
            (是否通过, 错误信息列表)
        """
        errors = []
        if not data:
            errors.append("Empty data returned")
            return False, errors
        
        required_fields = ['home', 'away', 'stage']
        for i, match in enumerate(data):
            for field in required_fields:
                if field not in match:
                    errors.append(f"Match {i}: missing field '{field}'")
        
        return len(errors) == 0, errors


class KaggleFetcher(DataFetcher):
    """
    Kaggle 数据源
    
    支持:
    - 2022 Qatar: 64场 (xG/控球率/59列)
    - 1930-2018: 900场历史数据
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data' / 'kaggle'
        self.data_dir = Path(data_dir)
        self._cache = {}
    
    @property
    def name(self) -> str:
        return "KaggleFetcher"
    
    @property
    def supports_historical(self) -> bool:
        return True
    
    @property
    def supports_live(self) -> bool:
        return False
    
    def fetch_matches(self, 
                     tournament: str = 'worldcup',
                     year: Optional[int] = None,
                     stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """从Kaggle CSV加载比赛数据"""
        
        if year == 2022:
            file_path = self.data_dir / 'worldcup_2022_qatar' / 'Fifa_WC_2022_Match_data.csv'
        elif year and year < 2022:
            file_path = self.data_dir / 'worldcup_1930-2018' / 'wcmatches.csv'
        else:
            # 默认加载2022
            file_path = self.data_dir / 'worldcup_2022_qatar' / 'Fifa_WC_2022_Match_data.csv'
        
        if not file_path.exists():
            return []
        
        cache_key = f"kaggle_{year}_{stage}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        try:
            df = pd.read_csv(file_path)
            matches = df.to_dict('records')
            
            # 过滤阶段
            if stage:
                matches = [m for m in matches if m.get('stage', 'group') == stage]
            
            self._cache[cache_key] = matches
            return matches
        except Exception as e:
            print(f"KaggleFetcher error: {e}")
            return []
    
    def fetch_odds(self, match_id: str, market: str = '1x2') -> Dict[str, Any]:
        """Kaggle数据不包含实时赔率"""
        return {'error': 'Kaggle does not provide live odds'}
    
    def fetch_teams(self, tournament: str = 'worldcup', year: Optional[int] = None) -> List[Dict[str, Any]]:
        """从比赛数据提取球队列表"""
        matches = self.fetch_matches(tournament, year)
        teams = set()
        for match in matches:
            teams.add(match.get('home', match.get('home_team', '')))
            teams.add(match.get('away', match.get('away_team', '')))
        return [{'name': t} for t in teams if t]


class FootballDataFetcher(DataFetcher):
    """
    football-data.co.uk 数据源
    
    支持历史赔率数据
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent.parent / 'data' / 'football_data_uk'
        self.data_dir = Path(data_dir)
        self._cache = {}
    
    @property
    def name(self) -> str:
        return "FootballDataFetcher"
    
    @property
    def supports_historical(self) -> bool:
        return True
    
    @property
    def supports_live(self) -> bool:
        return False
    
    def fetch_matches(self, 
                     tournament: str = 'worldcup',
                     year: Optional[int] = None,
                     stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """从football-data.co.uk CSV加载"""
        
        if year == 2022:
            file_path = self.data_dir / 'worldcup2022.csv'
        else:
            return []
        
        if not file_path.exists():
            return []
        
        try:
            df = pd.read_csv(file_path)
            return df.to_dict('records')
        except Exception as e:
            print(f"FootballDataFetcher error: {e}")
            return []
    
    def fetch_odds(self, match_id: str, market: str = '1x2') -> Dict[str, Any]:
        """从历史数据获取赔率"""
        # 简化实现，实际应从CSV解析
        return {'market': market, 'odds': {}}
    
    def fetch_teams(self, tournament: str = 'worldcup', year: Optional[int] = None) -> List[Dict[str, Any]]:
        """提取球队列表"""
        matches = self.fetch_matches(tournament, year)
        teams = set()
        for match in matches:
            teams.add(match.get('home', ''))
            teams.add(match.get('away', ''))
        return [{'name': t} for t in teams if t]


class APIFootballFetcher(DataFetcher):
    """
    API-Football 实时数据源
    
    免费额度: 100次/天
    注册: https://www.api-football.com/
    文档: https://www.api-football.com/documentation-v3
    
    支持:
    - 实时比赛数据
    - 赔率数据
    - 球队信息
    - xG/控球率等高级统计
    """
    
    def __init__(self, api_key: str = None, base_url: str = None):
        from config.api_config import get_config_manager
        
        config = get_config_manager().get_config()
        self.api_key = api_key or config.api_football_key
        self.base_url = base_url or config.api_football_base_url
        self.timeout = config.request_timeout
        self.rate_limit = config.rate_limit_delay
        self._last_request_time = 0
        self._cache = {}
        self._request_count = 0
    
    @property
    def name(self) -> str:
        return "APIFootballFetcher"
    
    @property
    def supports_historical(self) -> bool:
        return True
    
    @property
    def supports_live(self) -> bool:
        return True
    
    def _make_request(self, endpoint: str, params: dict = None) -> dict:
        """
        发送 HTTP 请求到 API-Football
        
        Args:
            endpoint: API 端点 (如 'fixtures', 'odds')
            params: URL 参数
        
        Returns:
            JSON 响应
        """
        if not self.api_key:
            return {'error': 'API key not configured. Get free key at https://www.api-football.com/'}
        
        # 速率限制
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        
        # 构建 URL
        url = f"{self.base_url}/{endpoint}"
        if params:
            query = '&'.join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{query}"
        
        # 发送请求
        try:
            req = Request(url)
            req.add_header('x-apisports-key', self.api_key)
            req.add_header('Accept', 'application/json')
            
            with urlopen(req, timeout=self.timeout) as response:
                self._last_request_time = time.time()
                self._request_count += 1
                data = json.loads(response.read().decode('utf-8'))
                return data
                
        except HTTPError as e:
            if e.code == 429:
                return {'error': 'Rate limit exceeded (100 calls/day on free tier)'}
            return {'error': f'HTTP {e.code}: {e.reason}'}
        except URLError as e:
            return {'error': f'Network error: {e.reason}'}
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}
    
    def fetch_matches(self, 
                     tournament: str = 'worldcup',
                     year: Optional[int] = None,
                     stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取比赛数据
        
        API-Football 使用 league ID:
        - World Cup 2022: 1
        - World Cup 2026: 1 (future)
        """
        if not self.api_key:
            return [{'error': 'API key not configured'}]
        
        # 使用 league=1 (World Cup)
        params = {'league': 1, 'season': year or 2022}
        
        data = self._make_request('fixtures', params)
        
        if 'error' in data:
            return [data]
        
        if 'response' not in data:
            return [{'error': 'Invalid API response format'}]
        
        # 解析响应
        matches = []
        for fixture in data['response']:
            match = {
                'id': fixture.get('fixture', {}).get('id'),
                'home': fixture.get('teams', {}).get('home', {}).get('name'),
                'away': fixture.get('teams', {}).get('away', {}).get('name'),
                'stage': fixture.get('league', {}).get('round', 'group').lower(),
                'date': fixture.get('fixture', {}).get('date'),
                'venue': fixture.get('fixture', {}).get('venue', {}).get('name'),
                'status': fixture.get('fixture', {}).get('status', {}).get('short'),
                'home_score': fixture.get('goals', {}).get('home'),
                'away_score': fixture.get('goals', {}).get('away'),
            }
            
            # 过滤阶段
            if stage and stage not in match['stage']:
                continue
            
            matches.append(match)
        
        return matches
    
    def fetch_odds(self, match_id: str, market: str = '1x2') -> Dict[str, Any]:
        """
        获取赔率数据
        
        Args:
            match_id: 比赛ID
            market: 市场类型 (1x2, over_under)
        """
        if not self.api_key:
            return {'error': 'API key not configured'}
        
        params = {'fixture': match_id}
        
        data = self._make_request('odds', params)
        
        if 'error' in data:
            return data
        
        if 'response' not in data or not data['response']:
            return {'error': 'No odds data available'}
        
        # 解析赔率
        odds_data = data['response'][0]
        bookmakers = odds_data.get('bookmakers', [])
        
        if not bookmakers:
            return {'error': 'No bookmakers available'}
        
        # 取第一个博彩公司
        bookmaker = bookmakers[0]
        bets = bookmaker.get('bets', [])
        
        odds = {}
        for bet in bets:
            bet_name = bet.get('name', '').lower()
            if market == '1x2' and ('1x2' in bet_name or 'match winner' in bet_name):
                values = bet.get('values', [])
                for value in values:
                    label = value.get('value', '').lower()
                    if label in ['home', '1']:
                        odds['home'] = float(value.get('odd', 0))
                    elif label in ['draw', 'x']:
                        odds['draw'] = float(value.get('odd', 0))
                    elif label in ['away', '2']:
                        odds['away'] = float(value.get('odd', 0))
            
            elif market == 'over_under' and 'over/under' in bet_name:
                values = bet.get('values', [])
                for value in values:
                    label = value.get('value', '').lower()
                    odds[label] = float(value.get('odd', 0))
        
        return {
            'market': market,
            'bookmaker': bookmaker.get('name'),
            'odds': odds
        }
    
    def fetch_teams(self, tournament: str = 'worldcup', year: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取球队列表"""
        if not self.api_key:
            return [{'name': 'Example Team', 'error': 'API key not configured'}]
        
        # 通过 fixtures 获取球队
        matches = self.fetch_matches(tournament, year)
        
        if matches and 'error' in matches[0]:
            return [{'name': 'Error', 'error': matches[0]['error']}]
        
        teams = {}
        for match in matches:
            home = match.get('home')
            away = match.get('away')
            if home:
                teams[home] = {'name': home}
            if away:
                teams[away] = {'name': away}
        
        return list(teams.values())
    
    def get_request_stats(self) -> Dict[str, Any]:
        """获取请求统计"""
        return {
            'requests_made': self._request_count,
            'rate_limit': '100/day (free tier)',
            'remaining': max(0, 100 - self._request_count)
        }
    
    def _mock_data(self) -> List[Dict[str, Any]]:
        """模拟数据（无 API Key 时回退）"""
        return [
            {
                'home': 'Germany',
                'away': 'Japan',
                'stage': 'group',
                'home_xg': 2.3,
                'away_xg': 0.8,
                'home_score': 1,
                'away_score': 2
            }
        ]


class FootballDataOrgFetcher(DataFetcher):
    """
    Football-Data.org 数据源
    
    免费额度: 需要注册获取 API Key
    注册: https://www.football-data.org/
    文档: https://www.football-data.org/documentation/quickstart
    
    特点:
    - 高可靠性，几乎没有反爬限制
    - 适合历史数据和赛程
    - 支持赔率历史数据
    - 数据质量稳定
    
    推荐用途:
    - 历史数据特征工程
    - 大小球建模
    - 回测验证
    """
    
    def __init__(self, api_key: str = None, base_url: str = None):
        from config.api_config import get_config_manager
        
        config = get_config_manager().get_config()
        self.api_key = api_key or config.football_data_org_key
        self.base_url = base_url or config.football_data_org_base_url
        self.timeout = config.request_timeout
        self.rate_limit = config.rate_limit_delay
        self._last_request_time = 0
        self._cache = {}
        self._request_count = 0
    
    @property
    def name(self) -> str:
        return "FootballDataOrgFetcher"
    
    @property
    def supports_historical(self) -> bool:
        return True
    
    @property
    def supports_live(self) -> bool:
        return True
    
    def _make_request(self, endpoint: str) -> dict:
        """
        发送 HTTP 请求到 Football-Data.org
        
        Args:
            endpoint: API 端点 (如 'competitions', 'matches')
        
        Returns:
            JSON 响应
        """
        if not self.api_key:
            return {'error': 'API key not configured. Get free key at https://www.football-data.org/'}
        
        # 速率限制
        elapsed = time.time() - self._last_request_time
        if elapsed < self.rate_limit:
            time.sleep(self.rate_limit - elapsed)
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            req = Request(url)
            req.add_header('X-Auth-Token', self.api_key)
            req.add_header('Accept', 'application/json')
            
            with urlopen(req, timeout=self.timeout) as response:
                self._last_request_time = time.time()
                self._request_count += 1
                data = json.loads(response.read().decode('utf-8'))
                return data
                
        except HTTPError as e:
            if e.code == 429:
                return {'error': 'Rate limit exceeded'}
            return {'error': f'HTTP {e.code}: {e.reason}'}
        except URLError as e:
            return {'error': f'Network error: {e.reason}'}
        except Exception as e:
            return {'error': f'Request failed: {str(e)}'}
    
    def fetch_matches(self, 
                     tournament: str = 'worldcup',
                     year: Optional[int] = None,
                     stage: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取比赛数据
        
        Football-Data.org 使用 competitions:
        - World Cup: WC
        - Premier League: PL
        """
        if not self.api_key:
            return [{'error': 'API key not configured'}]
        
        # 获取比赛列表
        competition = 'WC' if tournament == 'worldcup' else tournament.upper()
        season = year or 2022
        
        data = self._make_request(f'competitions/{competition}/matches?season={season}')
        
        if 'error' in data:
            return [data]
        
        if 'matches' not in data:
            return [{'error': 'Invalid API response format'}]
        
        # 解析响应
        matches = []
        for match in data['matches']:
            stage_name = match.get('stage', 'GROUP_STAGE').lower()
            
            parsed = {
                'id': match.get('id'),
                'home': match.get('homeTeam', {}).get('name'),
                'away': match.get('awayTeam', {}).get('name'),
                'stage': 'group' if 'group' in stage_name else 'knockout',
                'date': match.get('utcDate'),
                'status': match.get('status'),
                'home_score': match.get('score', {}).get('fullTime', {}).get('home'),
                'away_score': match.get('score', {}).get('fullTime', {}).get('away'),
                'competition': match.get('competition', {}).get('name'),
            }
            
            # 过滤阶段
            if stage and parsed['stage'] != stage:
                continue
            
            matches.append(parsed)
        
        return matches
    
    def fetch_odds(self, match_id: str, market: str = '1x2') -> Dict[str, Any]:
        """
        获取赔率数据
        
        Football-Data.org 提供历史赔率
        """
        if not self.api_key:
            return {'error': 'API key not configured'}
        
        data = self._make_request(f'matches/{match_id}')
        
        if 'error' in data:
            return data
        
        # Football-Data.org 的 odds 在 match 详情中
        match_data = data.get('match', {})
        odds = match_data.get('odds', {})
        
        if not odds:
            return {'error': 'No odds data available for this match'}
        
        parsed_odds = {}
        
        if market == '1x2':
            home_win = odds.get('homeWin')
            draw = odds.get('draw')
            away_win = odds.get('awayWin')
            
            if home_win and draw and away_win:
                parsed_odds = {
                    'home': float(home_win),
                    'draw': float(draw),
                    'away': float(away_win)
                }
        
        return {
            'market': market,
            'odds': parsed_odds
        }
    
    def fetch_teams(self, tournament: str = 'worldcup', year: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取球队列表"""
        if not self.api_key:
            return [{'name': 'Example Team', 'error': 'API key not configured'}]
        
        competition = 'WC' if tournament == 'worldcup' else tournament.upper()
        
        data = self._make_request(f'competitions/{competition}/teams')
        
        if 'error' in data:
            return [{'name': 'Error', 'error': data['error']}]
        
        teams = data.get('teams', [])
        return [{'id': t.get('id'), 'name': t.get('name'), 'short': t.get('shortName')} 
                for t in teams]
    
    def get_competitions(self) -> List[Dict[str, Any]]:
        """获取可用的比赛列表"""
        if not self.api_key:
            return [{'error': 'API key not configured'}]
        
        data = self._make_request('competitions')
        
        if 'error' in data:
            return [data]
        
        competitions = data.get('competitions', [])
        return [{'id': c.get('id'), 'name': c.get('name'), 'code': c.get('code')} 
                for c in competitions]
    
    def get_request_stats(self) -> Dict[str, Any]:
        """获取请求统计"""
        return {
            'requests_made': self._request_count,
            'rate_limit': 'Depends on plan (free tier available)',
            'remaining': 'Unknown (free tier has no fixed limit)'
        }


class DataFetcherFactory:
    """
    数据获取工厂
    
    根据数据源名称创建对应的数据获取器
    """
    
    _fetchers = {
        'kaggle': KaggleFetcher,
        'football_data': FootballDataFetcher,
        'api_football': APIFootballFetcher,
        'football_data_org': FootballDataOrgFetcher,
    }
    
    @classmethod
    def create(cls, source: str, **kwargs) -> DataFetcher:
        """
        创建数据获取器
        
        Args:
            source: 数据源名称 (kaggle, football_data, api_football, football_data_org)
            **kwargs: 传递给数据获取器的参数
        
        Returns:
            DataFetcher: 数据获取器实例
        """
        if source not in cls._fetchers:
            raise ValueError(f"Unknown data source: {source}. Available: {list(cls._fetchers.keys())}")
        
        fetcher_class = cls._fetchers[source]
        return fetcher_class(**kwargs)
    
    @classmethod
    def register(cls, name: str, fetcher_class: type):
        """注册新的数据源"""
        cls._fetchers[name] = fetcher_class
    
    @classmethod
    def available_sources(cls) -> List[str]:
        """获取可用的数据源列表"""
        return list(cls._fetchers.keys())


class MultiSourceFetcher:
    """
    多数据源聚合器
    
    同时查询多个数据源，合并结果
    """
    
    def __init__(self, sources: List[str] = None):
        if sources is None:
            sources = ['kaggle', 'football_data']
        
        self.fetchers = {}
        for source in sources:
            try:
                self.fetchers[source] = DataFetcherFactory.create(source)
            except Exception as e:
                print(f"Failed to initialize {source}: {e}")
    
    def fetch_matches(self, **kwargs) -> List[Dict[str, Any]]:
        """从所有数据源获取并合并"""
        all_matches = []
        for name, fetcher in self.fetchers.items():
            try:
                matches = fetcher.fetch_matches(**kwargs)
                if matches and 'error' not in matches[0]:
                    all_matches.extend(matches)
            except Exception as e:
                print(f"{name} fetch error: {e}")
        
        return all_matches
    
    def fetch_odds(self, match_id: str, **kwargs) -> Dict[str, Any]:
        """优先返回实时数据源的数据"""
        # 优先实时数据源
        for name, fetcher in self.fetchers.items():
            if fetcher.supports_live:
                try:
                    odds = fetcher.fetch_odds(match_id, **kwargs)
                    if 'error' not in odds:
                        return odds
                except:
                    continue
        
        #  fallback 到历史数据源
        for name, fetcher in self.fetchers.items():
            try:
                odds = fetcher.fetch_odds(match_id, **kwargs)
                if 'error' not in odds:
                    return odds
            except:
                continue
        
        return {'error': 'No data available from any source'}


# ============================================================
# 便捷函数
# ============================================================

def get_data_fetcher(source: str = 'kaggle', **kwargs) -> DataFetcher:
    """快速获取数据获取器"""
    return DataFetcherFactory.create(source, **kwargs)


def get_multi_source_fetcher(sources: List[str] = None) -> MultiSourceFetcher:
    """快速获取多数据源聚合器"""
    return MultiSourceFetcher(sources)
