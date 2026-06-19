# 机构流水线集成文档
# Football Quant OS v4.4 —— Institutional Pipeline

---

## 新增组件

| 文件 | 大小 | 说明 |
|------|------|------|
| `agents/strategist_goldman.py` | 23KB | 高盛风格策略架构师 —— 机构级策略顶层设计 |
| `core/pipeline_orchestrator.py` | 23KB | 流水线编排器 —— 15节点DAG，分层并行执行 |
| `prompts/institutional_roles_part1.md` | 11KB | Prompt模板（角色1-8） |
| `prompts/institutional_roles_part2.md` | 11KB | Prompt模板（角色9-15 + 使用指南） |

---

## 快速开始

### 1. 使用策略架构师

```python
from agents.strategist_goldman import StrategistGoldman, create_default_strategy

# 创建策略
memo = create_default_strategy(capital=100000, risk_tolerance="medium")

# 查看策略摘要
strategist = StrategistGoldman()
strategist.memo = memo
print(strategist.generate_execution_summary())

# 验证策略
valid, errors = memo.validate()
print(f"验证结果: {valid}")

# 导出JSON
print(memo.to_json())
```

### 2. 运行机构流水线

```python
import asyncio
from core.pipeline_orchestrator import run_pipeline

# 运行完整流水线
result = asyncio.run(run_pipeline(
    capital=100000,
    risk_tolerance="medium",
    target_leagues=["WC2026", "Premier League"]
))

print(f"成功: {result['success']}/{result['total_nodes']}")
```

### 3. 使用Prompt模板

直接复制 `prompts/institutional_roles_part1.md` 或 `part2.md` 中对应角色的 System Prompt 到 Claude，填入你的情况即可。

---

## 流水线DAG

```
Layer 1: 高盛策略架构师
    ↓
Layer 2: 彭博数据管道
    ↓
Layer 3:  Citadel Alpha  |  AQR因子  |  Point72 ML  (并行)
    ↓           ↓              ↓
Layer 4: D.E.Shaw套利  |  Jane Street做市  |  Bridgewater宏观  (并行)
    ↓
Layer 5: Man Group组合优化
    ↓
Layer 6: 文艺复兴回测  |  Dimensional因子回测  (并行)
    ↓
Layer 7: Two Sigma风控
    ↓
Layer 8: Virtu执行算法
    ↓
Layer 9: Millennium实时系统
    ↓
Layer 10: 高盛合规
```

---

## 架构升级说明

### 新增层：策略顶层设计

以前系统直接是 DataScout -> Analyst -> Committee -> RiskControl，缺少"为什么要这样做"的顶层设计。

现在新增 `StrategistGoldman` 作为最高层：
- 定义策略论题、Alpha来源
- 设定信号体系架构
- 制定进出场规则
- 配置风险参数
- 所有下游Agent必须满足策略要求

### 新增层：流水线编排

以前Agent是硬编码调用顺序，现在通过 `PipelineOrchestrator` 动态编排：
- DAG拓扑排序自动生成执行顺序
- 无依赖节点自动并行
- 输入/输出契约校验
- 错误回滚与状态管理

### 新增层：机构Prompt模板

15个角色的完整System Prompt，可以直接复制到Claude使用：
- 每个角色有明确的职责边界
- 输出格式标准化
- 输入/输出契约清晰
- 足球量化场景深度适配

---

## 下一步

1. **策略迭代**：用 `strategist_goldman.py` 设计你的专属策略
2. **回测升级**：参考文艺复兴Prompt，重建严格回测框架
3. **信号挖掘**：用Citadel Prompt，系统性地发现新Alpha
4. **风控强化**：用Two Sigma Prompt，建立完整风险管理体系
5. **执行优化**：用Virtu Prompt，优化投注执行质量

---

*文档版本: v4.4*
*最后更新: 2026-06-19*
*作者: 小娜迦*
