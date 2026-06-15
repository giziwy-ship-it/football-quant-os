---
name: football-quant-os
description: 当用户询问足球比赛预测、赔率分析、价值投注、让球推荐、大小球推荐、比赛结果预测、世界杯分析、投注策略、Kelly注码、冷门雷达、数据集成、特征工程等足球量化分析问题时使用。触发关键词：预测、赔率、投注、让球、大小球、比赛分析、世界杯、欧洲杯、价值、冷门、Kelly、资金配置、模型概率、足球分析、quant、数据源、特征、回测。
metadata:
  version: "4.3.4"
  author: Naga Quantitative
  tags: [football, betting, odds, prediction, kelly, quantitative, backtest, data, xg]
---

# Football Quant OS - 足球量化分析技能 (v4.3.2)

专业足球量化分析与价值投注决策技能。已集成：
- 多市场预测模型（1X2 + 让球 + 大小球 + 半全场 + 比分）
- Kelly 仓位管理（全Kelly/半Kelly/组合注码）
- 实时赔率抓取框架（requests + Playwright fallback）
- 世界杯阶段动态调整（历史数据校准）
- **数据集成框架**（多源数据融合）
- 清晰的 Edge + 冷门评分 + 推荐逻辑

## 当前实现状态

| 模块 | 状态 | 说明 |
|------|------|------|
| predict.py | ✅ v4.3.4 | 支持 1X2 + **xG增强版** + **数据驱动阶段调整** + 世界杯阶段调整 |
| multi_market_predictor.py | ✅ v4.2.1-naga | 6市场预测 + Kelly + 阶段调整 |
| kelly.py | ✅ v1.0 | Kelly仓位管理（全/半/组合） |
| odds_fetcher.py | ✅ v0.3 | requests 轻量版 |
| odds_fetcher_playwright.py | ✅ v0.1 | Playwright 基础版 |
| **odds_fetcher_playwright_pro.py** | ✅ **v2.0** | **Playwright 专业版（Stealth + 拦截 + 重试）** |
| odds_fetcher_smart.py | ✅ v1.0 | 智能抓取器（自动 fallback） |
| report_generator.py | ✅ v0.2 | 文本 + PDF 输出 |
| **data_integration.py** | ✅ v1.0 | **多源数据统一入口** |
| **data_football_data_co_uk.py** | ✅ v1.0 | **历史赔率数据** |
| **data_api_football.py** | ✅ v1.0 | **实时数据 + xG** |
| **data_kaggle.py** | ✅ v1.0 | **Kaggle数据集** |
| **data_openfootball.py** | ✅ v1.0 | **开源结构化数据** |
| **backtest_worldcup.py** | ✅ v0.2 | **回测框架** |
| 完整工作流集成 | ✅ v4.3.2 | 数据集成已加入 |

**核心原则**：永远基于具体赔率计算 Edge → 给出推荐/避开 + 风险提示

## 数据集成（v4.3.2 新增）

### 已接入数据源

| 数据源 | 类型 | 优先级 | 状态 |
|--------|------|--------|------|
| football-data.co.uk | 历史赔率 + 结果 | P0 | ✅ 可用 |
| API-Football | 实时 + xG + 统计 | P1 | ✅ 可用（需API Key） |
| Kaggle | 历史数据集 | P1 | ✅ 可用（需CLI） |
| OpenFootball | 开源结构化数据 | P2 | ✅ 可用 |

### 统一入口
```python
from data_integration import DataIntegration

data = DataIntegration(api_key="your_api_key")

# 获取历史赔率
df = data.get_historical_odds("WC", 2022)

# 获取实时比赛
fixtures = data.get_live_fixtures("WC", 2026)

# 多源特征融合
features = data.get_multi_source_features("Brazil", "Serbia", "WC", 2022)
```

## Playwright 高级抓取（v2.0 新增）

### 专业版特性
- **Stealth 模式**：隐藏 Playwright 特征，绕过反爬
- **请求拦截**：拦截图片/字体，加速加载80-90%
- **智能重试**：指数退避 + 错误截图
- **Context Manager**：自动管理浏览器生命周期
- **模拟人类行为**：随机鼠标移动 + 滚动

### 使用方式
```python
# 快捷函数（自动管理）
from odds_fetcher_playwright_pro import fetch_odds
result = fetch_odds("1359233", stealth=True, max_retries=3)

# Context Manager 模式
from odds_fetcher_playwright_pro import OddsFetcherPlaywrightPro, FetcherConfig
config = FetcherConfig(headless=True, stealth=True, intercept_resources=True)
with OddsFetcherPlaywrightPro(config) as fetcher:
    result = fetcher.get_odds("1359233")
```

### 高级技巧文档
详见 `references/PLAYWRIGHT_ADVANCED_TECHNIQUES.md`
- Stealth / 反检测
- 随机延迟 + 鼠标轨迹（贝塞尔曲线）
- 请求拦截策略
- 多标签页 / Context 并发
- 截图 + PDF 调试
- 状态保存（cookies / localStorage）

## Playwright Pro 集成到工作流

### 1. 智能抓取器 (odds_fetcher_smart.py)
自动选择最优策略：
- 默认：先尝试轻量 requests，失败再 fallback 到 Playwright Pro
- `--pro`：直接使用 Playwright Pro 专业版
- `--stealth` / `--no-stealth`：控制 Stealth 模式
- `--intercept` / `--no-intercept`：控制资源拦截
- `--max-retries`：设置最大重试次数

```bash
# 使用 Pro 版
python scripts/odds_fetcher_smart.py --match-id 1359233 --pro

# 混合模式（默认）
python scripts/odds_fetcher_smart.py --match-id 1359233

# 调试模式（有头 + 截图）
python scripts/odds_fetcher_smart.py --match-id 1359233 --pro --no-headless --screenshot-on-error
```

### 2. 多市场预测器 (multi_market_predictor.py)
支持直接从 500.com 创建 Match 对象：

```python
# 方式1: 从 500.com 创建（Pro 版）
from agents.multi_market_predictor import create_match_from_500
match = create_match_from_500('1359233', use_pro=True, stealth=True)

# 方式2: 使用工厂方法
from agents.multi_market_predictor import MultiMarketPredictor
predictor = MultiMarketPredictor.from_500(
    '1359233',
    venue_type='group',
    use_pro=True,
    stealth=True,
    intercept=True
)

# 方式3: CLI 使用
python agents/multi_market_predictor.py --match-id 1359233 --mode pro --stage group
```

### 3. 数据集成框架 (data_integration.py)
支持 Playwright Pro 抓取实时数据：

```python
from scripts.data_integration import DataIntegration

data = DataIntegration()

# 获取 2022 比赛详细数据
match_data = data.get_2022_match_data('ARGENTINA', 'SAUDI ARABIA')
print(f"xG: {match_data['home_xg']} vs {match_data['away_xg']}")
print(f"控球率: {match_data['home_poss']}% vs {match_data['away_poss']}%")
```

### 完整工作流示例
```bash
# Step 1: 抓取赔率
python scripts/odds_fetcher_smart.py --match-id 1359233 --pro

# Step 2: 生成预测
python agents/multi_market_predictor.py --match-id 1359233 --mode pro --stage group

# Step 3: 生成报告
python scripts/report_generator.py --input predictions.json --format pdf
```

## 世界杯专属增强（v4.3.0+）
- 已接入 `worldcup_historical.json`，实现动态调整
- 数据驱动概率估计（基于历史爆冷率）
- 新增 `references/WORLDCUP_GUIDE.md` + `worldcup_historical.json`
- 回测框架 `backtest_worldcup.py` 验证模型表现

**调用示例**：
```bash
python scripts/predict.py --home 法国 --away 阿根廷 \
  --odds-home 2.10 --odds-draw 3.30 --odds-away 3.50 \
  --stage knockout
```
