# 足球量化分析系统 (Football Quant OS)

> 体育量化分析系统 - 九智能体足球赛事分析与投注决策

## 系统概述

基于多智能体架构的足球赛事量化分析平台，整合数据采集、赔率分析、预测建模和投注决策支持。

## 核心架构

### 九智能体系统

| 智能体 | 职责 | 状态 |
|--------|------|------|
| 数据采集智能体 | 实时赛事数据采集 | ✅ 运行中 |
| 赔率分析智能体 | 赔率监控与异常检测 | ✅ 运行中 |
| 预测建模智能体 | 机器学习预测模型 | ✅ 运行中 |
| 风险评估智能体 | 投注风险评估 | ✅ 运行中 |
| 资金管理智能体 | 资金配置优化 | ✅ 运行中 |
| 回测验证智能体 | 策略回测验证 | ✅ 运行中 |
| 报告生成智能体 | 分析报告生成 | ✅ 运行中 |
| 监控预警智能体 | 实时监控预警 | ✅ 运行中 |
| 决策支持智能体 | 综合决策建议 | ✅ 运行中 |

## 技术栈

- **Python 3.10+**
- **FastAPI** - Web API 框架
- **Pandas/NumPy** - 数据处理
- **Scikit-learn** - 机器学习
- **SQLite** - 数据存储
- **WebSocket** - 实时数据推送

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 启动系统
python dashboard.py
```

## 项目结构

```
football_quant_os/
├── agents/          # 智能体模块
├── app/             # Web 应用
├── backtest/        # 回测系统
├── core/            # 核心引擎
├── data/            # 数据存储
├── fixtures/        # 测试数据
└── models/          # 预测模型
```

## 数据源

- ESPN API - 赛事数据
- Football-Data.org - 实时比分
- OddsPortal - 赔率数据

## 许可证

MIT License

## 作者

@giziwy-ship-it
