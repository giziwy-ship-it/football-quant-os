# Football Quant OS v4.3.2 - 完整系统架构

**版本**: 4.3.2
**日期**: 2026-06-14
**核心升级**: 数据集成框架 + 多源数据融合

---

## 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    Football Quant OS v4.3.2                   │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 数据层 (Data Layer)                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐ │
│  │ football-   │ │ API-Football│ │   Kaggle    │ │OpenFoot│ │
│  │data.co.uk   │ │  (实时+xG)  │ │  (数据集)   │ │ball    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘ │
│         │               │               │              │       │
│         └───────────────┴───────────────┴──────────────┘       │
│                           │                                    │
│                  ┌────────┴────────┐                          │
│                  │ data_integration  │ ← 统一入口              │
│                  │    .py            │                          │
│                  └────────┬────────┘                          │
├───────────────────────────┼──────────────────────────────────┤
│  Layer 2: 预测层 (Prediction)                                 │
│                  │                                            │
│  ┌───────────────┼───────────────┐                          │
│  │   predict.py   │ multi_market  │                          │
│  │   (v0.4.3)     │ _predictor.py │                          │
│  │                │  (v4.2.1-naga)│                          │
│  │ • 数据驱动概率 │ • 6市场预测   │                          │
│  │ • 阶段调整     │ • Kelly集成   │                          │
│  │ • Edge计算     │ • 冷门评分    │                          │
│  └───────────────┴───────────────┘                          │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: 执行层 (Execution)                                  │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ odds_fetcher│ │   kelly.py  │ │  backtest_  │            │
│  │  (_smart)   │ │  (v1.0)     │ │  worldcup   │            │
│  │  智能抓取    │ │ 仓位管理    │ │  (v0.2)     │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
├─────────────────────────────────────────────────────────────┤
│  Layer 4: 输出层 (Output)                                     │
│  ┌─────────────┐ ┌─────────────┐                             │
│  │report_gener │ │  PDF报告    │                             │
│  │   ator.py   │ │  (多种风格) │                             │
│  │  文本+PDF   │ │ Goldman/    │                             │
│  │             │ │ McKinsey/   │                             │
│  │             │ │ Google风格  │                             │
│  └─────────────┘ └─────────────┘                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 核心文件清单

### 数据层 (Data Layer)

| 文件 | 版本 | 说明 |
|------|------|------|
| `scripts/data_integration.py` | v1.0 | 多源数据统一入口 |
| `scripts/data_football_data_co_uk.py` | v1.0 | football-data.co.uk 历史赔率 |
| `scripts/data_api_football.py` | v1.0 | API-Football 实时+xG |
| `scripts/data_kaggle.py` | v1.0 | Kaggle 数据集 |
| `scripts/data_openfootball.py` | v1.0 | OpenFootball 结构化数据 |

### 预测层 (Prediction)

| 文件 | 版本 | 说明 |
|------|------|------|
| `scripts/predict.py` | v0.4.3 | 主预测脚本（数据驱动概率） |
| `agents/multi_market_predictor.py` | v4.2.1-naga | 6市场预测引擎 |
| `scripts/kelly.py` | v1.0 | Kelly仓位管理 |

### 执行层 (Execution)

| 文件 | 版本 | 说明 |
|------|------|------|
| `scripts/odds_fetcher.py` | v0.3 | requests轻量版 |
| `scripts/odds_fetcher_playwright.py` | v0.1 | Playwright高鲁棒性 |
| `scripts/odds_fetcher_smart.py` | v1.0 | 智能抓取(fallback) |
| `scripts/backtest_worldcup.py` | v0.2 | 回测框架 |

### 输出层 (Output)

| 文件 | 版本 | 说明 |
|------|------|------|
| `scripts/report_generator.py` | v0.2 | 文本+PDF输出 |
| `scripts/mckinsey_pdf_report.py` | v2.0 | 麦肯锡风格PDF |
| `scripts/mckinsey_pdf_report_cn.py` | v3.0 | Google Material风格 |

### 参考文档

| 文件 | 说明 |
|------|------|
| `references/DATA_SOURCES.md` | 数据源接入指南 |
| `references/WORLDCUP_GUIDE.md` | 世界杯专属规则 |
| `references/worldcup_historical.json` | 2014/2018/2022历史数据 |
| `references/MARKET_GUIDE.md` | 6市场规则说明 |
| `references/KELLY_GUIDE.md` | Kelly资金管理指南 |

---

## 关键特性

### 1. 数据驱动预测 (v4.3.3)
```python
# 基于历史爆冷率动态调整概率
def estimate_true_probability(market_prob, stage="group"):
    historical_upset_rate = get_historical_upset_rate(stage)
    if stage == "knockout":
        # 淘汰赛：爆冷率更高，模型更激进
        return market_prob * 0.91 * adjustment_strength + 0.04
    # ...
```

### 2. Kelly仓位管理 (v1.0)
```python
from kelly import get_kelly_suggestion, portfolio_kelly

# 单注
kelly = get_kelly_suggestion(probability=0.58, odds=2.10, risk_level="standard")
# → {'stake': 793, 'recommended_fraction': 0.0793}

# 组合
portfolio = portfolio_kelly(bets, total_bankroll=10000)
# → {'total_stake': 1193, 'remaining_bankroll': 8807}
```

### 3. 多源数据融合
```python
from data_integration import DataIntegration

data = DataIntegration(api_key="your_key")

# 历史赔率
df = data.get_historical_odds("WC", 2022)

# 实时比赛
fixtures = data.get_live_fixtures("WC", 2026)

# 特征融合
features = data.get_multi_source_features("Brazil", "Serbia", "WC", 2022)
# → {'sources': {'football_data': True, 'api_football': True}, 'features': {...}}
```

---

## 使用示例

### 基础预测
```bash
python scripts/predict.py --home 巴西 --away 摩洛哥 \
  --odds-home 1.65 --odds-draw 3.78 --odds-away 5.48 --stage group
```

### 回测验证
```bash
python scripts/backtest_worldcup.py
```

### 数据下载
```bash
# football-data.co.uk
python scripts/data_football_data_co_uk.py

# API-Football (需要API Key)
python scripts/data_api_football.py
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| v4.2.1 | 2026-06-12 | 基础系统（6市场预测） |
| v4.3.0 | 2026-06-14 | 世界杯阶段调整 + 赔率抓取 |
| v4.3.1 | 2026-06-14 | Kelly仓位管理 + 回测框架 |
| v4.3.2 | 2026-06-14 | **数据集成框架** + 多源数据 |

---

## 短期/中长期规划

### 短期（1-2 周内）✅

1. **从 football-data.co.uk 下载近 3-4 届世界杯 CSV**
   - 2022、2018、2014（已下载2022）
   - 提取关键字段：结果、赔率、球队

2. **提取历史爆冷率，替换硬编码系数**
   - 当前：`mod_home = mod_home * 0.96 + 0.02`（硬编码）
   - 目标：基于真实数据动态计算最优系数
   - 文件：`predict.py` + `worldcup_historical.json`

3. **在 `WORLDCUP_GUIDE.md` 补充真实统计数据**
   - 已包含基础数据，需补充更详细的阶段分析

4. **完善回测框架 ROI 计算**
   - `backtest_worldcup.py` 已能运行，需加入实际收益计算

### 中长期（1-2 月）📅

- **根据历史数据动态拟合阶段调整参数**
  - 用线性回归/贝叶斯优化找到最优调整系数
  - 而非目前的 if-else 硬编码

- **接入 FBref xG 数据**
  - 构建预期进球模型
  - 提升预测准确率

- **构建机器学习模型**
  - 基于 Kaggle 数据集训练
  - 替代目前的启发式规则

- **实时数据流水线**
  - 自动化赔率抓取 → 预测 → 下注建议
  - 减少人工干预

### 数据优先级矩阵

| 目标 | 首选数据源 | 备选 | 时间节点 |
|------|------------|------|----------|
| 验证模型 Edge/ROI | football-data.co.uk | Kaggle | 本周 |
| 构建历史爆冷率 | football-data.co.uk | OpenFootball | 本周 |
| 获取实时赔率 | API-Football | odds_fetcher_playwright | 持续 |
| 训练 ML 模型 | Kaggle | football-data.co.uk | 1月内 |
| 获取 xG 数据 | FBref | API-Football | 2月内 |
| 结构化数据导入 | OpenFootball | Kaggle | 2周内 |

---

*系统架构文档 v1.1*
*最后更新: 2026-06-14 12:00*
*基于用户数据源分析补充*
