#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent 对象池 - Football Quant OS v4.2
减少重复创建 Agent 实例的内存开销
"""

from typing import Dict, Any, List, Optional
import copy


class AgentPool:
    """
    Agent 对象池
    
    复用 Agent 实例，减少频繁创建/销毁的内存开销
    适用于需要高频预测的场景（如滚球投注、批量赛程预测）
    """
    
    def __init__(self, max_pool_size: int = 5):
        self.max_pool_size = max_pool_size
        self._pools: Dict[str, List] = {}  # agent_name -> [instance, ...]
        self._templates: Dict[str, Any] = {}  # agent_name -> class
    
    def register(self, name: str, agent_class, *args, **kwargs):
        """注册 Agent 类型"""
        self._templates[name] = (agent_class, args, kwargs)
        self._pools[name] = []
    
    def get(self, name: str) -> Optional[Any]:
        """从池中获取 Agent 实例"""
        # 检查池中是否有可用实例
        if name in self._pools and self._pools[name]:
            return self._pools[name].pop()
        
        # 创建新实例
        if name in self._templates:
            agent_class, args, kwargs = self._templates[name]
            return agent_class(*args, **kwargs)
        
        return None
    
    def release(self, name: str, agent: Any):
        """将 Agent 归还池中"""
        if name in self._pools and len(self._pools[name]) < self.max_pool_size:
            # 重置状态（如果 Agent 支持 reset）
            if hasattr(agent, 'reset'):
                agent.reset()
            self._pools[name].append(agent)
    
    def stats(self) -> Dict[str, Any]:
        """获取池状态"""
        return {
            name: {
                'available': len(pool),
                'max_size': self.max_pool_size
            }
            for name, pool in self._pools.items()
        }
    
    def clear(self):
        """清空所有池"""
        self._pools.clear()


# 全局 Agent 池实例
agent_pool = AgentPool()


def init_agent_pool():
    """初始化全局 Agent 池"""
    from agents.datascout_v2 import DataScout
    from agents.analyst_v2 import Analyst
    from agents.worldcup_analyst import WorldCupAnalyst
    from agents.committee_v2 import Committee
    from agents.risk_control_v2 import RiskControl
    
    agent_pool.register('DataScout', DataScout)
    agent_pool.register('Analyst', Analyst)
    agent_pool.register('WorldCupAnalyst', WorldCupAnalyst)
    agent_pool.register('Committee', Committee)
    agent_pool.register('RiskControl', RiskControl)
    
    # 预创建常用 Agent（2个实例）
    for _ in range(2):
        for name in ['DataScout', 'Analyst', 'Committee', 'RiskControl']:
            agent = agent_pool.get(name)
            agent_pool.release(name, agent)
    
    print(f"[AgentPool] 初始化完成: {agent_pool.stats()}")


# 上下文管理器（推荐用法）
class AgentContext:
    """Agent 上下文管理器 - 自动获取和释放"""
    
    def __init__(self, name: str):
        self.name = name
        self.agent = None
    
    def __enter__(self):
        self.agent = agent_pool.get(self.name)
        return self.agent
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.agent:
            agent_pool.release(self.name, self.agent)
        return False
