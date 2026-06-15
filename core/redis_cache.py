#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 缓存层 - Naga Core v4.1 (生产级)
赔率缓存、赛程缓存、结果缓存
"""

import json
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import redis


class RedisCache:
    """
    Redis 缓存管理器
    
    缓存策略:
    - 赔率数据: TTL 5分钟（高频变动）
    - 赛程数据: TTL 1小时（相对稳定）
    - 预测结果: TTL 24小时（可复用）
    - 球队信息: TTL 7天（极少变动）
    """
    
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self.host = host
        self.port = port
        self.redis_client = None
        self._connected = False
        
        try:
            self.redis_client = redis.Redis(
                host=host, port=port, db=db, password=password,
                decode_responses=True, socket_connect_timeout=2
            )
            self.redis_client.ping()
            self._connected = True
            print(f"[RedisCache] Connected to {host}:{port}")
        except Exception as e:
            print(f"[RedisCache] Connection failed: {e}, using fallback")
            self._fallback_cache = {}
    
    def _key(self, prefix: str, *args) -> str:
        """生成缓存键"""
        key_data = ':'.join(str(a) for a in args)
        return f"fqos:{prefix}:{hashlib.md5(key_data.encode()).hexdigest()[:12]}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if self._connected and self.redis_client:
            data = self.redis_client.get(key)
            if data:
                return json.loads(data)
            return None
        else:
            return self._fallback_cache.get(key, {}).get('value')
    
    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        """设置缓存"""
        if self._connected and self.redis_client:
            self.redis_client.setex(key, ttl_seconds, json.dumps(value, ensure_ascii=False))
        else:
            self._fallback_cache[key] = {
                'value': value,
                'expires': datetime.now() + timedelta(seconds=ttl_seconds)
            }
    
    def delete(self, key: str):
        """删除缓存"""
        if self._connected and self.redis_client:
            self.redis_client.delete(key)
        elif key in self._fallback_cache:
            del self._fallback_cache[key]
    
    # ──────────────────────────────────────────────
    # 业务缓存方法
    # ──────────────────────────────────────────────
    
    def cache_odds(self, home: str, away: str, odds: Dict[str, float], source: str = "500.com"):
        """缓存赔率数据 (TTL 5分钟)"""
        key = self._key("odds", source, home, away)
        self.set(key, {
            'home': odds.get('home'),
            'draw': odds.get('draw'),
            'away': odds.get('away'),
            'source': source,
            'cached_at': datetime.now().isoformat()
        }, ttl_seconds=300)
    
    def get_odds(self, home: str, away: str, source: str = "500.com") -> Optional[Dict]:
        """获取缓存的赔率"""
        key = self._key("odds", source, home, away)
        return self.get(key)
    
    def cache_fixtures(self, date: str, fixtures: List[Dict]):
        """缓存赛程数据 (TTL 1小时)"""
        key = self._key("fixtures", date)
        self.set(key, {
            'fixtures': fixtures,
            'count': len(fixtures),
            'cached_at': datetime.now().isoformat()
        }, ttl_seconds=3600)
    
    def get_fixtures(self, date: str) -> Optional[List[Dict]]:
        """获取缓存的赛程"""
        key = self._key("fixtures", date)
        data = self.get(key)
        return data.get('fixtures') if data else None
    
    def cache_prediction(self, match_id: str, prediction: Dict):
        """缓存预测结果 (TTL 24小时)"""
        key = self._key("pred", match_id)
        self.set(key, {
            'prediction': prediction,
            'cached_at': datetime.now().isoformat()
        }, ttl_seconds=86400)
    
    def get_prediction(self, match_id: str) -> Optional[Dict]:
        """获取缓存的预测"""
        key = self._key("pred", match_id)
        data = self.get(key)
        return data.get('prediction') if data else None
    
    def cache_team_info(self, team: str, info: Dict):
        """缓存球队信息 (TTL 7天)"""
        key = self._key("team", team)
        self.set(key, {
            'info': info,
            'cached_at': datetime.now().isoformat()
        }, ttl_seconds=604800)
    
    def get_team_info(self, team: str) -> Optional[Dict]:
        """获取缓存的球队信息"""
        key = self._key("team", team)
        data = self.get(key)
        return data.get('info') if data else None
    
    # ──────────────────────────────────────────────
    # 统计和监控
    # ──────────────────────────────────────────────
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        if not self._connected or not self.redis_client:
            return {
                'mode': 'fallback_memory',
                'fallback_keys': len(self._fallback_cache)
            }
        
        info = self.redis_client.info('memory')
        return {
            'mode': 'redis',
            'connected': True,
            'used_memory_human': info.get('used_memory_human'),
            'keys': self.redis_client.dbsize(),
            'hit_rate': 'N/A'  # 需要实现计数器
        }
    
    def flush_all(self):
        """清空所有缓存（慎用）"""
        if self._connected and self.redis_client:
            self.redis_client.flushdb()
        else:
            self._fallback_cache.clear()
