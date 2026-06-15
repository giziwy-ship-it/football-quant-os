#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
异步并发调度器 - Naga Core v4.1 (修复版)
使用 asyncio 实现真正的并发 Agent 执行
修复: Phase 3 数据传递
"""

import asyncio
from typing import Dict, List, Any, Optional


# 默认超时配置 (秒)
DEFAULT_TIMEOUTS = {
    'agent': 30,      # 单个 Agent 超时
    'phase1': 60,     # 第一阶段超时
    'phase2': 30,     # 第二阶段超时
    'phase3': 30,     # 第三阶段超时
    'total': 120,     # 总流水线超时
}
class AsyncScheduler:
    """
    异步并发调度器
    
    核心升级：从 ThreadPoolExecutor 升级到 asyncio.gather
    优势：
    - IO密集型任务（API调用、数据获取）效率更高
    - 更轻量的并发（协程 vs 线程）
    - 天然适合 FastAPI 异步框架
    """
    
    def __init__(self, agents: List[Any]):
        self.agents = agents
    
    async def run(self, match_data: Dict[str, Any], timeout: int = None) -> Dict[str, Any]:
        """
        并发执行所有 Agent（带超时控制）
        
        Args:
            match_data: 比赛数据
            timeout: 单个 Agent 超时（秒），默认 30s
            
        Returns:
            合并后的 Agent 结果字典
        """
        timeout = timeout or DEFAULT_TIMEOUTS['agent']
        tasks = [self._run_agent_with_timeout(agent, match_data, timeout) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        merged = {}
        for agent, result in zip(self.agents, results):
            agent_name = getattr(agent, 'name', agent.__class__.__name__)
            
            if isinstance(result, asyncio.TimeoutError):
                merged[agent_name] = {
                    "error": f"Agent timeout ({timeout}s)",
                    "status": "timeout"
                }
            elif isinstance(result, Exception):
                merged[agent_name] = {
                    "error": str(result),
                    "status": "failed"
                }
            else:
                merged[agent_name] = result
        
        return merged
    
    async def _run_agent_with_timeout(self, agent: Any, match_data: Dict[str, Any], 
                                       timeout: int) -> Any:
        """带超时的 Agent 执行"""
        run_method = getattr(agent, 'run', None) or getattr(agent, 'analyze', None)
        
        if asyncio.iscoroutinefunction(run_method):
            return await asyncio.wait_for(run_method(match_data), timeout=timeout)
        else:
            # 同步方法放入线程池执行，避免阻塞事件循环
            loop = asyncio.get_event_loop()
            return await asyncio.wait_for(
                loop.run_in_executor(None, run_method, match_data),
                timeout=timeout
            )


class PipelineScheduler:
    """
    流水线调度器
    
    用于需要分阶段执行的场景：
    Phase 1: 独立 Agent 并行分析
    Phase 2: Committee 综合（依赖 Phase 1）
    Phase 3: RiskControl + Execution（依赖 Phase 2）
    """
    
    def __init__(self):
        self.phase1_agents = []
        self.phase2_agents = []
        self.phase3_agents = []
    
    def add_phase1(self, agents: List[Any]):
        """添加第一阶段 Agent（并行独立执行）"""
        self.phase1_agents.extend(agents)
    
    def add_phase2(self, agent: Any):
        """添加第二阶段 Agent（依赖第一阶段结果）"""
        self.phase2_agents.append(agent)
    
    def add_phase3(self, agents: List[Any]):
        """添加第三阶段 Agent（依赖第二阶段结果）"""
        self.phase3_agents.extend(agents)
    
    async def run(self, match_data: Dict[str, Any], total_timeout: int = None) -> Dict[str, Any]:
        """执行三阶段流水线（带总超时控制）"""
        total_timeout = total_timeout or DEFAULT_TIMEOUTS['total']
        
        try:
            return await asyncio.wait_for(self._run_pipeline(match_data), timeout=total_timeout)
        except asyncio.TimeoutError:
            print(f"[Pipeline] 总流水线超时 ({total_timeout}s)")
            return {
                'phase1': {},
                'phase2': {'Committee': {'error': 'Pipeline timeout', 'status': 'timeout'}},
                'phase3': {'RiskControl': {'error': 'Pipeline timeout', 'status': 'timeout'}}
            }
    
    async def _run_pipeline(self, match_data: Dict[str, Any]) -> Dict[str, Any]:
        """实际流水线执行（内部方法）"""
        
        # 打印传入的 match_data 中的概率（调试用）
        print(f"[Pipeline] 传入概率: 主{match_data.get('home_win', 40)}% 平{match_data.get('draw', 30)}% 客{match_data.get('away_win', 30)}%")
        
        # Phase 1: 并行独立分析（带超时）
        scheduler = AsyncScheduler(self.phase1_agents)
        phase1_results = await scheduler.run(match_data, timeout=DEFAULT_TIMEOUTS['phase1'])
        
        # Phase 2: 综合决策（带超时）
        phase2_results = {}
        for agent in self.phase2_agents:
            agent_name = getattr(agent, 'name', agent.__class__.__name__)
            
            # 将 Phase 1 结果注入需要综合决策的 Agent
            if hasattr(agent, 'receive_other_opinions'):
                opinions = [r for r in phase1_results.values() if not isinstance(r, dict) or 'error' not in r]
                agent.receive_other_opinions(opinions)
            
            run_method = getattr(agent, 'run', None) or getattr(agent, 'analyze', None)
            try:
                if asyncio.iscoroutinefunction(run_method):
                    result = await asyncio.wait_for(run_method(match_data), timeout=DEFAULT_TIMEOUTS['phase2'])
                else:
                    loop = asyncio.get_event_loop()
                    result = await asyncio.wait_for(
                        loop.run_in_executor(None, run_method, match_data),
                        timeout=DEFAULT_TIMEOUTS['phase2']
                    )
                phase2_results[agent_name] = result
                
                # 打印 Committee 的输出概率
                if agent_name == 'Committee' and 'prediction' in phase2_results[agent_name]:
                    pred = phase2_results[agent_name]['prediction']
                    print(f"[Pipeline] Committee 输出: 主{pred.get('home_win', 0)}% 平{pred.get('draw', 0)}% 客{pred.get('away_win', 0)}%")
            except asyncio.TimeoutError:
                phase2_results[agent_name] = {'error': 'Agent timeout', 'status': 'timeout'}
                print(f"[Pipeline] {agent_name} 超时")
        
        # Phase 3: 风险控制和执行（带超时）
        # 将前两阶段结果合并到 match_data
        enriched_data = match_data.copy()
        enriched_data['_phase1_results'] = phase1_results
        enriched_data['_phase2_results'] = phase2_results
        
        # 修复：确保 money_flow_analysis 在顶层可用
        if '_phase1_results' in enriched_data:
            analyst_result = enriched_data['_phase1_results'].get('Analyst', {})
            if 'money_flow_analysis' in analyst_result:
                enriched_data['money_flow_analysis'] = analyst_result['money_flow_analysis']
                print(f"[Pipeline] Phase 3 资金数据传递: 已提取 money_flow_analysis")
        
        scheduler3 = AsyncScheduler(self.phase3_agents)
        phase3_results = await scheduler3.run(enriched_data, timeout=DEFAULT_TIMEOUTS['phase3'])
        
        return {
            'phase1': phase1_results,
            'phase2': phase2_results,
            'phase3': phase3_results
        }
