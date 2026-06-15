#!/usr/bin/env python3
"""
Football Quant OS - 每日比赛结果自动抓取
=====================================
每天中午12点运行，抓取前一日和当日已完成的官方比赛结果

数据源优先级:
1. football-data.org (免费, 高稳定性)
2. API-Football (免费100次/天, 实时数据丰富)

输出: data/daily_results/YYYY-MM-DD.json

使用 cron 每日12:00运行:
    0 12 * * * cd /path/to/football_quant_os && python scripts/fetch_daily_results.py
"""

import os
import sys
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# 设置路径
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from config.api_config import get_config_manager, check_api_status

# 日志配置
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'daily_results.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('DailyResults')


# 输出目录
OUTPUT_DIR = BASE_DIR / 'data' / 'daily_results'
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


class MatchResultFetcher:
    """比赛结果抓取器"""
    
    def __init__(self):
        self.config = get_config_manager().get_config()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FootballQuantOS/5.2.0 (Research)',
            'Accept': 'application/json'
        })
        self.results: List[Dict] = []
        self.errors: List[str] = []
    
    # ============================================================
    # Source 1: football-data.org
    # ============================================================
    def fetch_football_data_org(self, date_str: str) -> List[Dict]:
        """
        从 football-data.org 抓取比赛结果
        免费版限制: 10 calls/minute
        """
        if not self.config.football_data_org_key:
            logger.info("[football-data.org] API key not configured, skipping")
            return []
        
        url = f"{self.config.football_data_org_base_url}/matches"
        headers = {'X-Auth-Token': self.config.football_data_org_key}
        params = {'dateFrom': date_str, 'dateTo': date_str}
        
        try:
            logger.info(f"[football-data.org] Fetching matches for {date_str}")
            resp = self.session.get(url, headers=headers, params=params, timeout=30)
            
            if resp.status_code == 429:
                logger.warning("[football-data.org] Rate limited, waiting 10s...")
                time.sleep(10)
                resp = self.session.get(url, headers=headers, params=params, timeout=30)
            
            resp.raise_for_status()
            data = resp.json()
            
            matches = data.get('matches', [])
            logger.info(f"[football-data.org] Got {len(matches)} matches")
            
            return self._format_fdo_matches(matches)
            
        except requests.exceptions.RequestException as e:
            self.errors.append(f"football-data.org error: {e}")
            logger.error(f"[football-data.org] Request failed: {e}")
            return []
        except Exception as e:
            self.errors.append(f"football-data.org unexpected: {e}")
            logger.error(f"[football-data.org] Unexpected error: {e}")
            return []
    
    def _format_fdo_matches(self, matches: List[Dict]) -> List[Dict]:
        """格式化 football-data.org 数据"""
        results = []
        for m in matches:
            status = m.get('status', 'SCHEDULED')
            
            # 只保留已完成的比赛
            if status not in ('FINISHED', 'AWARDED', 'PAUSED'):
                continue
            
            home_team = m.get('homeTeam', {})
            away_team = m.get('awayTeam', {})
            score = m.get('score', {}).get('fullTime', {})
            
            results.append({
                'match_id': str(m.get('id')),
                'source': 'football-data.org',
                'competition': m.get('competition', {}).get('name', 'Unknown'),
                'competition_id': str(m.get('competition', {}).get('id', '')),
                'season': m.get('season', {}).get('startDate', '')[:4],
                'date': m.get('utcDate', '')[:10],
                'time': m.get('utcDate', '')[11:16],
                'status': status,
                'stage': m.get('stage', ''),
                'group': m.get('group', ''),
                'matchday': m.get('matchday', ''),
                'home_team': {
                    'name': home_team.get('name', ''),
                    'id': str(home_team.get('id', '')),
                    'short_name': home_team.get('shortName', ''),
                    'tla': home_team.get('tla', '')
                },
                'away_team': {
                    'name': away_team.get('name', ''),
                    'id': str(away_team.get('id', '')),
                    'short_name': away_team.get('shortName', ''),
                    'tla': away_team.get('tla', '')
                },
                'score': {
                    'home': score.get('home', 0),
                    'away': score.get('away', 0)
                },
                'winner': m.get('score', {}).get('winner', ''),
                'duration': m.get('score', {}).get('duration', 'REGULAR'),
                'referee': m.get('referees', [{}])[0].get('name', '') if m.get('referees') else '',
                'venue': m.get('venue', ''),
                'fetched_at': datetime.now().isoformat()
            })
        
        return results
    
    # ============================================================
    # Source 2: API-Football
    # ============================================================
    def fetch_api_football(self, date_str: str) -> List[Dict]:
        """
        从 API-Football 抓取比赛结果
        免费版限制: 100 calls/day
        """
        if not self.config.api_football_key:
            logger.info("[API-Football] API key not configured, skipping")
            return []
        
        url = f"{self.config.api_football_base_url}/fixtures"
        headers = {'x-apisports-key': self.config.api_football_key}
        params = {'date': date_str}
        
        try:
            logger.info(f"[API-Football] Fetching fixtures for {date_str}")
            resp = self.session.get(url, headers=headers, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            if data.get('errors'):
                logger.warning(f"[API-Football] API errors: {data['errors']}")
                return []
            
            fixtures = data.get('response', [])
            logger.info(f"[API-Football] Got {len(fixtures)} fixtures")
            
            return self._format_af_matches(fixtures)
            
        except requests.exceptions.RequestException as e:
            self.errors.append(f"API-Football error: {e}")
            logger.error(f"[API-Football] Request failed: {e}")
            return []
        except Exception as e:
            self.errors.append(f"API-Football unexpected: {e}")
            logger.error(f"[API-Football] Unexpected error: {e}")
            return []
    
    def _format_af_matches(self, fixtures: List[Dict]) -> List[Dict]:
        """格式化 API-Football 数据"""
        results = []
        for f in fixtures:
            fixture = f.get('fixture', {})
            league = f.get('league', {})
            teams = f.get('teams', {})
            goals = f.get('goals', {})
            
            status_short = fixture.get('status', {}).get('short', '')
            
            # 只保留已完成的比赛
            if status_short not in ('FT', 'AET', 'PEN', 'AWD'):
                continue
            
            home = teams.get('home', {})
            away = teams.get('away', {})
            
            results.append({
                'match_id': str(fixture.get('id', '')),
                'source': 'api-football',
                'competition': league.get('name', 'Unknown'),
                'competition_id': str(league.get('id', '')),
                'season': str(league.get('season', '')),
                'date': fixture.get('date', '')[:10],
                'time': fixture.get('date', '')[11:16],
                'status': status_short,
                'stage': league.get('round', ''),
                'group': '',
                'matchday': '',
                'home_team': {
                    'name': home.get('name', ''),
                    'id': str(home.get('id', '')),
                    'short_name': home.get('name', '')[:3],
                    'tla': ''
                },
                'away_team': {
                    'name': away.get('name', ''),
                    'id': str(away.get('id', '')),
                    'short_name': away.get('name', '')[:3],
                    'tla': ''
                },
                'score': {
                    'home': goals.get('home', 0) if goals.get('home') is not None else 0,
                    'away': goals.get('away', 0) if goals.get('away') is not None else 0
                },
                'winner': 'HOME_TEAM' if home.get('winner') else ('AWAY_TEAM' if away.get('winner') else 'DRAW'),
                'duration': 'EXTRA_TIME' if status_short == 'AET' else ('PENALTIES' if status_short == 'PEN' else 'REGULAR'),
                'referee': fixture.get('referee', ''),
                'venue': fixture.get('venue', {}).get('name', ''),
                'fetched_at': datetime.now().isoformat()
            })
        
        return results
    
    # ============================================================
    # Main Logic
    # ============================================================
    def run(self, target_date: Optional[str] = None, days_back: int = 1) -> Dict:
        """
        执行抓取
        
        Args:
            target_date: 目标日期 (YYYY-MM-DD), None=昨天到今天
            days_back: 往前抓几天 (默认1天=昨天到今天)
        
        Returns:
            抓取结果统计
        """
        if target_date:
            dates = [target_date]
        else:
            today = datetime.now().date()
            dates = [(today - timedelta(days=i)).isoformat() for i in range(days_back, -1, -1)]
        
        logger.info(f"=" * 60)
        logger.info(f"Daily Results Fetcher Started")
        logger.info(f"Dates: {dates}")
        logger.info(f"API Status: {check_api_status()}")
        logger.info(f"=" * 60)
        
        all_results = []
        
        for date_str in dates:
            logger.info(f"\n--- Fetching for {date_str} ---")
            
            # Source 1: football-data.org
            fdo_results = self.fetch_football_data_org(date_str)
            all_results.extend(fdo_results)
            
            # Source 2: API-Football
            if not fdo_results:  # 如果 source1 没数据, 尝试 source2
                af_results = self.fetch_api_football(date_str)
                all_results.extend(af_results)
            
            # 请求间隔 (遵守速率限制)
            time.sleep(self.config.rate_limit_delay)
        
        # 去重 (按 match_id)
        seen = set()
        unique_results = []
        for r in all_results:
            mid = r.get('match_id', '')
            if mid and mid not in seen:
                seen.add(mid)
                unique_results.append(r)
        
        # 保存结果
        output_file = self._save_results(unique_results, dates)
        
        # 统计
        stats = {
            'run_time': datetime.now().isoformat(),
            'dates': dates,
            'total_fetched': len(all_results),
            'unique_matches': len(unique_results),
            'sources_used': list(set(r.get('source', '') for r in unique_results)),
            'errors': self.errors,
            'output_file': str(output_file),
            'api_status': check_api_status()
        }
        
        logger.info(f"\n{'=' * 60}")
        logger.info(f"Fetch Complete: {stats['unique_matches']} unique matches")
        logger.info(f"Sources: {stats['sources_used']}")
        logger.info(f"Output: {output_file}")
        if self.errors:
            logger.warning(f"Errors: {len(self.errors)}")
        logger.info(f"{'=' * 60}")
        
        return stats
    
    def _save_results(self, results: List[Dict], dates: List[str]) -> Path:
        """保存结果到文件"""
        # 文件名: daily_results_2026-06-15.json
        date_label = dates[-1] if dates else datetime.now().strftime('%Y-%m-%d')
        filename = f"daily_results_{date_label}.json"
        filepath = OUTPUT_DIR / filename
        
        data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'system': 'Football Quant OS v5.2.0',
                'dates_covered': dates,
                'total_matches': len(results),
                'sources': list(set(r.get('source', '') for r in results))
            },
            'matches': results
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Results saved to: {filepath}")
        return filepath


def main():
    """入口函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fetch daily football match results')
    parser.add_argument('--date', type=str, help='Target date (YYYY-MM-DD), default: yesterday-today')
    parser.add_argument('--days-back', type=int, default=1, help='How many days back to fetch (default: 1)')
    parser.add_argument('--dry-run', action='store_true', help='Print stats without saving')
    args = parser.parse_args()
    
    fetcher = MatchResultFetcher()
    stats = fetcher.run(target_date=args.date, days_back=args.days_back)
    
    if args.dry_run:
        print(f"\n[Dry Run] Would save {stats['unique_matches']} matches to:")
        print(f"  {stats['output_file']}")
    
    return stats


if __name__ == '__main__':
    main()
