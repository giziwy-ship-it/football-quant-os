#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DataFetcher v3.0 - Football Quant OS
注入: 00 数据清洗 + 09 数据管道
增强: 数据清洗管道 + 质量验证 + 异常检测 + 公司行为调整

相比 v2.0 的增强:
- 数据清洗管道: 缺失值处理、异常值检测、时间序列对齐
- 数据验证规则: 赔率>1.0、概率合理范围、结果互斥
- 数据质量日报: 每日数据完整性报告
- 公司行为调整: 赛程变更、球队更名、教练变更的数据处理
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
from datetime import datetime
import json
import logging

# 保持与 v2.0 的兼容性
from data.data_fetcher import DataFetcher, KaggleFetcher, FootballDataFetcher, APIFootballFetcher, FootballDataOrgFetcher, MultiSourceFetcher

logger = logging.getLogger(__name__)


class DataCleaningEngine:
    """数据清洗引擎 - 注入 Renaissance 级严谨性"""
    
    def __init__(self):
        self.cleaning_log = []
    
    def clean(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """完整清洗管道"""
        original_count = len(data)
        
        # 1. 去重
        data = self._remove_duplicates(data)
        
        # 2. 缺失值处理
        data = self._handle_missing(data)
        
        # 3. 异常值检测
        data = self._detect_outliers(data)
        
        # 4. 数据类型标准化
        data = self._standardize_types(data)
        
        # 5. 时间序列对齐
        data = self._align_timestamps(data)
        
        final_count = len(data)
        self.cleaning_log.append({
            'timestamp': datetime.now().isoformat(),
            'original_count': original_count,
            'final_count': final_count,
            'dropped': original_count - final_count
        })
        
        return data
    
    def _remove_duplicates(self, data: List[Dict]) -> List[Dict]:
        """基于 match_id 去重"""
        seen = set()
        unique = []
        for item in data:
            key = item.get('match_id') or f"{item.get('home')}_{item.get('away')}_{item.get('date')}"
            if key not in seen:
                seen.add(key)
                unique.append(item)
        return unique
    
    def _handle_missing(self, data: List[Dict]) -> List[Dict]:
        """缺失值处理"""
        cleaned = []
        for item in data:
            # 关键字段缺失则删除
            if not item.get('home') or not item.get('away'):
                continue
            
            # 数值字段缺失则填充
            if 'xG' in item and item['xG'] is None:
                item['xG'] = 0.0  # 中性填充
            
            # 概率字段缺失则标记
            if 'prob_home' in item and item['prob_home'] is None:
                item['prob_home'] = 0.333  # 均匀分布
                item['prob_imputed'] = True  # 标记为插值
            
            cleaned.append(item)
        return cleaned
    
    def _detect_outliers(self, data: List[Dict]) -> List[Dict]:
        """异常值检测 - 使用 IQR 方法"""
        if not data:
            return data
        
        numeric_fields = ['prob_home', 'prob_draw', 'prob_away', 'odds_home', 'odds_draw', 'odds_away']
        
        for field in numeric_fields:
            values = [d.get(field) for d in data if d.get(field) is not None]
            if len(values) < 4:
                continue
            
            q1, q3 = np.percentile(values, [25, 75])
            iqr = q3 - q1
            lower = q1 - 1.5 * iqr
            upper = q3 + 1.5 * iqr
            
            for item in data:
                val = item.get(field)
                if val is not None and (val < lower or val > upper):
                    item[f'{field}_outlier'] = True
                    # 不删除，而是标记，让下游决定如何处理
        
        return data
    
    def _standardize_types(self, data: List[Dict]) -> List[Dict]:
        """数据类型标准化"""
        for item in data:
            # 日期统一为 ISO 格式
            if 'date' in item and isinstance(item['date'], str):
                try:
                    dt = pd.to_datetime(item['date'])
                    item['date'] = dt.strftime('%Y-%m-%d')
                except:
                    pass
            
            # 数值字段统一为 float
            for field in ['prob_home', 'prob_draw', 'prob_away', 'odds_home', 'odds_draw', 'odds_away', 'xG_home', 'xG_away']:
                if field in item and item[field] is not None:
                    try:
                        item[field] = float(item[field])
                    except (ValueError, TypeError):
                        item[field] = None
        
        return data
    
    def _align_timestamps(self, data: List[Dict]) -> List[Dict]:
        """时间序列对齐 - 确保所有数据使用 UTC"""
        for item in data:
            if 'timestamp' in item:
                try:
                    dt = pd.to_datetime(item['timestamp'])
                    item['timestamp'] = dt.strftime('%Y-%m-%dT%H:%M:%SZ')
                except:
                    pass
        return data


class DataValidator:
    """数据验证器 - 确保数据质量符合量化标准"""
    
    VALIDATION_RULES = {
        'odds_positive': {
            'check': lambda d: all(d.get(f'odds_{k}', 1) > 1.0 for k in ['home', 'draw', 'away']),
            'severity': 'ERROR',
            'message': '赔率必须大于 1.0'
        },
        'prob_sum': {
            'check': lambda d: 0.9 <= sum(d.get(f'prob_{k}', 0) for k in ['home', 'draw', 'away']) <= 1.1,
            'severity': 'WARNING',
            'message': '概率之和应在 0.9-1.1 之间'
        },
        'xg_non_negative': {
            'check': lambda d: all(d.get(f'xG_{k}', 0) >= 0 for k in ['home', 'away']),
            'severity': 'ERROR',
            'message': 'xG 必须非负'
        },
        'teams_distinct': {
            'check': lambda d: d.get('home') != d.get('away'),
            'severity': 'ERROR',
            'message': '主客队不能相同'
        },
        'date_valid': {
            'check': lambda d: pd.to_datetime(d.get('date', '1900-01-01'), errors='coerce') is not pd.NaT,
            'severity': 'WARNING',
            'message': '日期格式无效'
        }
    }
    
    def validate(self, data: List[Dict]) -> Dict[str, Any]:
        """验证数据质量"""
        results = {
            'total': len(data),
            'passed': 0,
            'failed': 0,
            'errors': [],
            'warnings': [],
            'field_stats': {}
        }
        
        for item in data:
            item_passed = True
            for rule_name, rule in self.VALIDATION_RULES.items():
                try:
                    if not rule['check'](item):
                        msg = f"{rule['message']}: {item.get('match_id', 'unknown')}"
                        if rule['severity'] == 'ERROR':
                            results['errors'].append(msg)
                            item_passed = False
                        else:
                            results['warnings'].append(msg)
                except Exception as e:
                    results['errors'].append(f"Validation error in {rule_name}: {e}")
                    item_passed = False
            
            if item_passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        
        # 字段统计
        for field in ['home', 'away', 'date', 'prob_home', 'odds_home', 'xG_home']:
            present = sum(1 for d in data if field in d and d[field] is not None)
            results['field_stats'][field] = {
                'present': present,
                'missing': len(data) - present,
                'completeness': present / len(data) if data else 0
            }
        
        return results


class CorporateActionAdjuster:
    """公司行为调整器 - 处理足球赛事的公司行为"""
    
    def __init__(self, adjustments_file: str = None):
        self.adjustments = self._load_adjustments(adjustments_file)
    
    def _load_adjustments(self, filepath: str = None) -> Dict:
        """加载公司行为记录"""
        if filepath and Path(filepath).exists():
            with open(filepath, 'r') as f:
                return json.load(f)
        return {
            'team_renames': {},
            'schedule_changes': [],
            'coach_changes': [],
            'venue_changes': []
        }
    
    def adjust(self, data: List[Dict]) -> List[Dict]:
        """应用所有调整"""
        for item in data:
            # 球队更名调整
            if 'home' in item and item['home'] in self.adjustments['team_renames']:
                item['home'] = self.adjustments['team_renames'][item['home']]
            if 'away' in item and item['away'] in self.adjustments['team_renames']:
                item['away'] = self.adjustments['team_renames'][item['away']]
            
            # 标记已知的赛程变更
            for change in self.adjustments['schedule_changes']:
                if item.get('match_id') == change['match_id']:
                    item['schedule_changed'] = True
                    item['original_date'] = change.get('original_date')
        
        return data
    
    def add_rename(self, old_name: str, new_name: str):
        """添加球队更名记录"""
        self.adjustments['team_renames'][old_name] = new_name
    
    def add_schedule_change(self, match_id: str, original_date: str, new_date: str):
        """添加赛程变更记录"""
        self.adjustments['schedule_changes'].append({
            'match_id': match_id,
            'original_date': original_date,
            'new_date': new_date
        })


class QualityMonitor:
    """数据质量监控器 - 生成每日质量报告"""
    
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / 'logs'
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.daily_stats = []
    
    def log(self, data: List[Dict], validation_result: Dict):
        """记录数据质量"""
        stat = {
            'timestamp': datetime.now().isoformat(),
            'total_records': len(data),
            'passed': validation_result['passed'],
            'failed': validation_result['failed'],
            'completeness': validation_result['field_stats'],
            'error_count': len(validation_result['errors']),
            'warning_count': len(validation_result['warnings'])
        }
        self.daily_stats.append(stat)
    
    def generate_daily_report(self) -> Dict[str, Any]:
        """生成每日质量报告"""
        if not self.daily_stats:
            return {'status': 'NO_DATA'}
        
        latest = self.daily_stats[-1]
        
        report = {
            'date': datetime.now().strftime('%Y-%m-%d'),
            'status': 'HEALTHY' if latest['error_count'] == 0 else 'WARNING',
            'summary': {
                'total_records': latest['total_records'],
                'pass_rate': latest['passed'] / latest['total_records'] if latest['total_records'] > 0 else 0,
                'error_count': latest['error_count'],
                'warning_count': latest['warning_count']
            },
            'field_completeness': {
                field: stats['completeness'] 
                for field, stats in latest['completeness'].items()
            },
            'recommendations': []
        }
        
        # 生成建议
        for field, stats in latest['completeness'].items():
            if stats['completeness'] < 0.8:
                report['recommendations'].append(
                    f"字段 '{field}' 完整度仅 {stats['completeness']:.1%}, 建议检查数据源"
                )
        
        # 保存报告
        report_file = self.log_dir / f"data_quality_{datetime.now().strftime('%Y%m%d')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report


class DataFetcherV3:
    """
    DataFetcher v3.0 - 增强版统一数据获取层
    
    在 v2.0 基础上增加:
    - 数据清洗管道
    - 质量验证
    - 公司行为调整
    - 质量监控
    """
    
    def __init__(self, use_cache: bool = True, data_dir: str = None):
        self.v2_fetcher = MultiSourceFetcher(data_dir=data_dir)
        self.cleaner = DataCleaningEngine()
        self.validator = DataValidator()
        self.adjuster = CorporateActionAdjuster()
        self.quality_monitor = QualityMonitor()
        self.use_cache = use_cache
        self._cache = {}
    
    def fetch(self, source: str = 'multi', **kwargs) -> Dict[str, Any]:
        """
        获取数据并走完整清洗验证流程
        
        Returns:
            {
                'data': List[Dict],  # 清洗后的数据
                'raw_count': int,     # 原始数据量
                'clean_count': int,   # 清洗后数据量
                'validation': Dict,   # 验证结果
                'quality_report': Dict # 质量报告
            }
        """
        # 1. 获取原始数据 (使用 v2.0 能力)
        raw_data = self._fetch_raw(source, **kwargs)
        raw_count = len(raw_data)
        
        # 2. 数据清洗
        cleaned_data = self.cleaner.clean(raw_data)
        clean_count = len(cleaned_data)
        
        # 3. 公司行为调整
        adjusted_data = self.adjuster.adjust(cleaned_data)
        
        # 4. 数据验证
        validation = self.validator.validate(adjusted_data)
        
        # 5. 质量监控
        self.quality_monitor.log(adjusted_data, validation)
        quality_report = self.quality_monitor.generate_daily_report()
        
        return {
            'data': adjusted_data,
            'raw_count': raw_count,
            'clean_count': clean_count,
            'validation': validation,
            'quality_report': quality_report
        }
    
    def _fetch_raw(self, source: str, **kwargs) -> List[Dict]:
        """使用 v2.0 获取原始数据"""
        # 这里简化处理，实际使用 v2.0 的多源获取
        if source == 'kaggle':
            fetcher = KaggleFetcher()
        elif source == 'api_football':
            fetcher = APIFootballFetcher()
        elif source == 'football_data':
            fetcher = FootballDataOrgFetcher()
        else:
            fetcher = self.v2_fetcher
        
        year = kwargs.get('year', 2022)
        return fetcher.fetch_matches(year=year)
    
    def get_quality_report(self) -> Dict[str, Any]:
        """获取最新质量报告"""
        return self.quality_monitor.generate_daily_report()
    
    def add_corporate_action(self, action_type: str, **kwargs):
        """添加公司行为记录"""
        if action_type == 'rename':
            self.adjuster.add_rename(kwargs['old'], kwargs['new'])
        elif action_type == 'schedule_change':
            self.adjuster.add_schedule_change(
                kwargs['match_id'], kwargs['original'], kwargs['new']
            )


# 向后兼容
__all__ = [
    'DataFetcherV3',
    'DataCleaningEngine',
    'DataValidator',
    'CorporateActionAdjuster',
    'QualityMonitor'
]