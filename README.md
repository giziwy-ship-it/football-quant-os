# Football Quant OS — 机构级足球量化预测系统 **v6.3**

> **"我们不预测比赛，我们计算概率。我们不赌博，我们投资期望值。"** 🏎️⚽📊

一款融合 **12 家顶级量化机构方法论** 的足球赛事量化分析与投注决策系统，采用 **六层 Agent 架构**、**Kelly 最优注码**、**无偏差回测框架** 和 **实时合规监控**，覆盖全球主流联赛与杯赛。

## 版本亮点 (v6.3)

v6.3 在 v6.0 基础上完成了 **P1 高级引擎整合** 和 **组合投注系统扩展**：

| 维度 | v6.0 | v6.3 | 提升 |
|------|------|------|------|
| 自进化能力 | N/A | ✅ | **新增** |
| 市场微结构 | N/A | ✅ | **新增** |
| 组合投注 | 基础 | 完整 | +100% |
| 投资系统 | N/A | ✅ | **新增** |
| 体能AI | N/A | ✅ | **新增** |
| HT/FT预测 | N/A | ✅ | **新增** |

### v6.3 新增模块

| 模块 | 版本 | 核心能力 | 文件 |
|------|------|----------|------|
| **SelfEvolution** | v4.0 | 贝叶斯在线学习 + 滚动窗口回测 + 梯度下降更新 | `v4/core/evolution.py` |
| **MarketMicrostructure** | v4.0 | 赔率变动深层解读 + 诱盘识别 + 市场偏差检测 | `v4/core/market_micro.py` |
| **CombinationBetting** | v5.1 | 单场多市场2串1/3串1 + 多场比赛2串1/3串1/4串1 | `scripts/combination_betting.py` |
| **InvestmentSystem** | v2.0 | 4模块集成(DataScout/Analyst/Committee/RiskControl) | `scripts/investment_system.py` |
| **PhysicalAI** | v4.0 | 力学/场域/熵/量子四层物理模型 | `v4/core/physical_ai.py` |
| **HT/FT Data** | v1.0 | 半全场数据框架 + 双维度预测 | `features/htft_data_framework.py` |

### v6.0 新增 12 个融合模块

| 模块 | 注入机构 | 核心能力 | 文件 |
|------|----------|----------|------|
| **DataFetcher v3.0** | 00 数据清洗 | 数据清洗管道 + 质量验证 + 异常检测 | `data/data_fetcher_v3.py` |
| **BacktestEngine v2.0** | 02 文艺复兴 | BiasChecker + WalkForward + MonteCarlo | `backtest/engine_v2.py` |
| **RiskGuardian v2.0** | 03 Two Sigma | 压力测试(5场景) + VaR + 回撤控制 | `agents/risk_guardian_v2.py` |
| **FactorMonitor v1.0** | 05.5 因子监控 | 8因子健康巡检 + 衰减预警 + 自动降级 | `agents/factor_monitor.py` |
| **UpsetDetector v3.0** | 04 Citadel | 信号IC + 拥挤度 + 制度检测 | `agents/upset_detector_v3.py` |
| **ModelEnsemble v2.0** | 06 AQR | 风险平价 + IC加权 + 动态再平衡 | `models/ensemble_v2.py` |
| **HeuristicModel v2.0** | 08 Bridgewater | 四象限制度分类 + 动态校准 | `models/heuristic_model_v2.py` |
| **WorldCupDataEngineer v2.0** | 11 Point72 | SHAP解释 + 时序CV + 漂移监控 | `agents/worldcup_data_engineer_v2.py` |
| **TradingAgent v2.0** | 10 Virtu | 订单拆分 + 滑点监控 + 对账引擎 | `agents/trading_v2.py` |
| **AttributionAgent v1.0** | 13.5 归因 | 因子/策略/成本归因 + 运气vs技能 | `agents/attribution_agent.py` |
| **TreasuryAgent v2.0** | 12 Man Group | Black-Litterman + 风险平价 + 约束 | `agents/treasury_v2.py` |
| **ComplianceAgent v1.0** | 15 高盛合规 | 交易前检查 + 异常检测 + 审计追踪 | `agents/compliance_agent.py` |

## 六层 Agent 架构 (v6.0)

```
┌─────────────────────────────────────────────────────┐
│  P0 定价与资金层                                      │
│  ├── OddsPricingAgent v1.1  (7种盘口 + 套利检测)      │
│  ├── TreasuryAgent v2.0     (Black-Litterman)         │
│  └── IntelligenceAgent v1.0 (5级情报源 + NLP)         │
├─────────────────────────────────────────────────────┤
│  P1 执行与风控层                                      │
│  ├── TradingAgent v2.0      (订单拆分 + 滑点控制)      │
│  ├── RiskGuardian v2.0      (压力测试 + VaR)          │
│  └── ComplianceAgent v1.0   (合规 + 审计)             │
├─────────────────────────────────────────────────────┤
│  P2 绩效与归因层 (NEW v6.0)                           │
│  └── AttributionAgent v1.0  (因子/策略/成本归因)       │
├─────────────────────────────────────────────────────┤
│  P3 冷门雷达层                                        │
│  ├── UpsetDetector v3.0     (信号IC + 拥挤度)          │
│  ├── CoachFactor v1.0       (48强教练因子)             │
│  └── FactorMonitor v1.0     (因子健康监控)             │
├─────────────────────────────────────────────────────┤
│  P4 数据与模型层                                      │
│  ├── WorldCupDataEngineer v2.0 (SHAP + 时序CV)       │
│  ├── ModelEnsemble v2.0     (风险平价权重)              │
│  ├── HeuristicModel v2.0    (四象限制度)              │
│  ├── PoissonModel v2.2      (5因子优化)               │
│  └── BacktestEngine v2.0    (无偏差回测)              │
├─────────────────────────────────────────────────────┤
│  P5 数据基础设施层                                     │
│  └── DataFetcher v3.0       (清洗 + 验证)              │
└─────────────────────────────────────────────────────┘
```

### 关键算法

- **Kelly Criterion**: 最优注码比例 `f* = (bp - q) / b`，最大化对数财富期望
- **Poisson 建模**: 进球期望 → 比分概率矩阵
- **蒙特卡洛模拟**: 10,000 次赛事模拟生成置信区间
- **Elo 动态评级**: 实时球队实力评分更新
- **108 矩阵模型**: 首目标后 108 种连锁反应情景

## 覆盖范围

- **主流联赛**: 英超、西甲、德甲、意甲、法甲、欧冠、欧联
- **亚洲市场**: 中超、J联赛、K联赛、澳超
- **杯赛**: 世界杯、欧洲杯、美洲杯、亚洲杯
- **双模式**: 单场比赛深度分析 + 多场比赛组合优化

## 自我进化

- **自动预测日志累积**: 每笔预测自动记录，形成数据库
- **偏差模式识别**: 识别模型系统性偏差，自动预警
- **动态权重调整**: 根据历史表现调整各模型权重
- **基因引擎优化**: 基于交易记录的遗传算法策略进化

## 快速入门 (v6.0)

### 单场比赛预测 (新入口)
```bash
# 基础预测 (兼容 v5)
python scripts/predict_v6.py --home Germany --away Japan --odds 1.8 3.4 4.2

# 完整 v6 流水线 (全模块启用)
python scripts/predict_v6.py --home Germany --away Japan --odds 1.8 3.4 4.2 --full-pipeline

# 合规检查模式
python scripts/predict_v6.py --home Germany --away Japan --odds 1.8 3.4 4.2 --compliance-check

# 批量预测
python scripts/predict_v6.py --batch matches.json --output results.json
```

### 实时赔率监控
```bash
"抓取拜仁 vs 巴黎的最新赔率"
"检查有没有套利机会"
```

### 回测验证 (v6 增强)
```bash
# 无偏差回测
python backtest/engine_v2.py --data matches.json --walk-forward

# 蒙特卡洛模拟
python backtest/engine_v2.py --data matches.json --monte-carlo 10000
```

### 组合投注优化
```bash
"优化今晚3场比赛的组合投注"
"控制总风险敞口在5%以内"
```

## 每份分析报告包含

- **比赛基础**: 联赛排名、积分差距、战意分析
- **阵容预测**: 首发预测、伤病/停赛报告
- **近期状态**: 近5场走势、主客场表现、半场领先优势
- **高级指标面板**: xG / PSxG / PPDA / Elo 评级
- **四层概率修正**: L1-L4 完整修正流程
- **Kelly 最优注码**: 推荐注码金额 + 风险评级
- **四种模型评分**: Poisson / Elo / 108矩阵 / 软因子
- **半场+全场预测**: 主要方案 + 备选方案
- **风险提示**: 弱点警告、关键不确定性因素
- **诱盘检测**: T-index 评分、反向信号识别

## 这是给谁的？

- **理性投注者**: 追求长期正期望值，拒绝赌博心态
- **量化投资者**: 将体育博彩视为另类投资品种
- **数据分析师**: 需要高质量足球数据源和模型框架
- **内容创作者**: 需要数据驱动的赛前分析素材
- **战术爱好者**: 研究比赛背后的概率逻辑

## 重要提示

- **语言**: 所有分析结果均以中文呈现
- **数据源**: ESPN API + Football-Data.org + OddsPortal + 500.com
- **风险提示**: 本系统仅供研究学习，不构成投注建议
- **合规**: 请遵守当地法律法规，理性对待
- **年龄限制**: 未成年人禁止使用

## 技术栈

- **Python 3.10+**
- **FastAPI** - Web API 框架
- **Pandas/NumPy** - 数据处理
- **Scikit-learn** - 机器学习
- **SQLite** - 数据存储
- **WebSocket** - 实时数据推送

## 项目结构 (v6.0)

```
football_quant_os/
├── agents/              # 智能体模块 (P0-P3)
│   ├── odds_pricing.py
│   ├── treasury.py              # v1.0 (保留兼容)
│   ├── treasury_v2.py           # v2.0 Man Group 组合优化
│   ├── intelligence.py
│   ├── trading.py               # v1.0 (保留兼容)
│   ├── trading_v2.py            # v2.0 Virtu 执行优化
│   ├── risk_guardian.py         # v1.0 (保留兼容)
│   ├── risk_guardian_v2.py      # v2.0 Two Sigma 风控
│   ├── upset_detector.py        # v2.0 (保留兼容)
│   ├── upset_detector_v3.py     # v3.0 Citadel 信号
│   ├── coach_factor.py
│   ├── factor_monitor.py        # v1.0 NEW
│   ├── attribution_agent.py     # v1.0 NEW
│   ├── compliance_agent.py      # v1.0 NEW
│   └── worldcup_data_engineer_v2.py  # v2.0 NEW
├── models/              # 预测模型
│   ├── base_model.py
│   ├── heuristic_model.py       # v4.3 (保留兼容)
│   ├── heuristic_model_v2.py    # v2.0 Bridgewater 制度
│   ├── poisson_model.py         # v2.2
│   ├── ensemble.py              # v1.0 (保留兼容)
│   ├── ensemble_v2.py           # v2.0 AQR 因子模型
│   ├── xgboost_*.pkl            # 6 XGBoost ensemble
│   └── kelly_integration.py
├── data/                # 数据层
│   ├── data_fetcher.py          # v2.0 (保留兼容)
│   └── data_fetcher_v3.py       # v3.0 清洗+验证 NEW
├── backtest/            # 回测系统
│   ├── engine.py                # v1.0 (保留兼容)
│   └── engine_v2.py             # v2.0 文艺复兴 NEW
├── features/            # 特征工程
│   ├── feature_engineer.py
│   └── group_stage_context.py
├── scripts/             # 执行脚本
│   ├── predict.py               # v5.0 (保留兼容)
│   ├── predict_pipeline.py      # v5.0 (保留兼容)
│   └── predict_v6.py            # v6.0 统一入口 NEW
├── reports/             # 报告生成
├── references/          # 知识库
└── tests/               # 测试套件
```

## 安装

```bash
# 方式1: ClawHub 安装
clawhub install football-quant-os

# 方式2: 手动克隆
git clone https://github.com/giziwy-ship-it/football-quant-os.git
cd football-quant-os
pip install -r requirements.txt
```

## 配置

在 `~/.openclaw/openclaw.json` 中添加:

```json
{
  "skills": {
    "entries": {
      "football-quant-os": {
        "enabled": true,
        "config": {
          "bankroll": 10000,
          "currency": "CNY",
          "data_sources": ["espn", "football-data", "oddsportal"],
          "use_browser": true,
          "headless": true,
          "max_concurrent_matches": 5,
          "risk_limits": {
            "single_bet_max": 0.05,
            "daily_loss_limit": 0.10,
            "consecutive_loss_stop": 3
          }
        }
      }
    }
  }
}
```

## 版本历史

| 版本 | 日期 | 核心变更 |
|------|------|----------|
| **v6.3** | **2026-06-19** | **P1高级引擎整合(SelfEvolution+MarketMicrostructure)，组合投注系统(单场多市场+多场2/3/4串1)，InvestmentSystem/PhysicalAI/HTFT整合** |
| v6.0 | 2026-06-19 | 机构级量化方法论融合，12模块落地，predict_v6.py |
| v5.2 | 2026-06-16 | 小组赛上下文特征模块，xG增强，48强赛制适配 |
| v5.0 | 2026-06-14 | P0-P4层Agent架构，Kelly集成，DataFetcher抽象层 |
| v4.3 | 2026-06-12 | 九智能体架构，四层概率修正器，XGBoost模型 |
| v3.0 | 2026-05 | Poisson大小球模型，回测引擎 |
| v2.0 | 2026-04 | 基础预测引擎，Kelly注码 |
| v1.0 | 2026-03 | 项目启动，核心框架 |

## 许可证

MIT License

## 作者

GitHub: [@giziwy-ship-it](https://github.com/giziwy-ship-it)

---

**"用数据说话，让概率成为你的朋友。"** ⚽📊
