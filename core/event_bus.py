#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Redis 事件总线 - Naga Core v4.1
用于 Agent 间解耦通信和外部系统集成
"""

import json
import os
from typing import Optional, Callable, Any


class EventBus:
    """
    事件总线基类
    
    支持两种模式：
    1. Redis Pub/Sub（生产环境）
    2. 内存队列（开发/测试环境）
    """
    
    def __init__(self, use_redis: bool = False, redis_host: str = "localhost", redis_port: int = 6379):
        self.use_redis = use_redis
        self.redis_host = redis_host
        self.redis_port = redis_port
        self._redis = None
        self._memory_subscribers: dict = {}
        
        if use_redis:
            try:
                import redis as redis_lib
                self._redis = redis_lib.Redis(host=redis_host, port=redis_port, decode_responses=True)
                self._redis.ping()
                print(f"[EventBus] Redis connected: {redis_host}:{redis_port}")
            except Exception as e:
                print(f"[EventBus] Redis connection failed: {e}, falling back to memory mode")
                self.use_redis = False
    
    def publish(self, channel: str, data: Any):
        """发布事件"""
        payload = json.dumps(data, ensure_ascii=False)
        
        if self.use_redis and self._redis:
            self._redis.publish(channel, payload)
        else:
            # 内存模式：直接分发给订阅者
            if channel in self._memory_subscribers:
                for callback in self._memory_subscribers[channel]:
                    try:
                        callback(json.loads(payload))
                    except Exception as e:
                        print(f"[EventBus] Memory dispatch error: {e}")
    
    def subscribe(self, channel: str, callback: Callable[[Any], None]):
        """订阅事件（内存模式）"""
        if channel not in self._memory_subscribers:
            self._memory_subscribers[channel] = []
        self._memory_subscribers[channel].append(callback)
    
    def get_redis_pubsub(self, channel: str):
        """获取 Redis Pub/Sub 对象（仅 Redis 模式）"""
        if self.use_redis and self._redis:
            pubsub = self._redis.pubsub()
            pubsub.subscribe(channel)
            return pubsub
        return None


# 全局事件总线实例
event_bus = EventBus(use_redis=False)

# 预定义频道
CHANNELS = {
    'MATCH_ANALYZED': 'fqos:match:analyzed',
    'AGENT_OPINION': 'fqos:agent:opinion',
    'TRADE_EXECUTED': 'fqos:trade:executed',
    'RISK_ALERT': 'fqos:risk:alert',
    'SYSTEM_LOG': 'fqos:system:log'
}
