---
name: football-quant-os
description: 基于九智能体架构的足球赛事量化分析与投注决策系统，支持实时赔率抓取、Kelly最优注码、回测引擎与自进化
slug: football-quant-os
version: 1.0.0
author: "@giziwy-ship-it"
license: MIT
---

# Football Quant OS — 体育量化分析 Skill

---

## 一句话描述

基于九智能体架构 + 四层概率修正器的足球赛事量化分析与投注决策系统，支持实时赔率抓取、Kelly 最优注码、回测引擎与自进化。

---

## 适用场景

| 场景 | 说明 |
|------|------|
| 赛前分析 | 输入对阵双方，输出概率分布 + 推荐赛果 + Kelly 注码 |
| 实时赔率监控 | 抓取 19+ 家博彩公司赔率变化，识别价值投注 |
| 套利检测 | 跨盘口 odds 差异扫描，发现无风险套利机会 |
| 回测验证 | 用历史数据验证模型准确率，优化参数 |
| 组合投注 | 多场比赛组合优化，控制总风险敞口 |

---

## 核心能力

### 九智能体系统 (Nine-Agent)

```
DataScout      → 数据采集与快速决策
Analyst        → 深度统计建模
Arbitrage      → 价值投注识别
TeamValue      → 长期球队估值
Legal          → 合规与风险隔离
Committee      → 共识加权决策
RiskControl    → 极端场景压力测试
Execution      → 执行策略与注码分配
Evolution      → 交易记录自学习优化
```

### 四层概率修正器

| 层级 | 修正因子 | 权重 |
|------|---------|------|
| L1 | 基础实力概率 (输入) | 基准 |
| L2 | 时间因子 + 战意因子 + 联赛偏差 | ±8% |
| L3 | 盘口结构 + 临场信息 | ±5% |
| L4 | 诱盘检测 (T-index) | ±3% |

### 关键算法

- **Kelly Criterion**: 最优注码比例 `f* = (bp - q) / b`
- **Poisson 建模**: 进球期望 → 比分概率矩阵
- **蒙特卡洛模拟**: 10,000 次赛事模拟生成置信区间
- **Elo 动态评级**: 实时球队实力评分更新

---

## 安装

```bash
# 方式1: ClawHub 安装
clawhub install football-quant-os

# 方式2: 手动克隆
git clone https://github.com/giziwy-ship-it/football-quant-os.git ~/.openclaw/skills/football-quant-os
cd ~/.openclaw/skills/football-quant-os
pip install -r requirements.txt
```

---

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

---

## 使用方式

### 方式1: 自然语言调用 (推荐)

```
"分析今晚皇马 vs 拜仁的欧冠比赛"
"抓取拜仁 vs 巴黎的最新赔率"
"用 Kelly 公式计算这场应该下注多少"
"回测我上周的5场推荐"
"检查有没有套利机会"
```

### 方式2: 命令式调用

```bash
# 完整赛事分析
openclaw skill football-quant-os analyze --home "Real Madrid" --away "Bayern Munich" --league "UCL"

# 实时赔率
openclaw skill football-quant-os odds --match-id 12345

# Kelly 计算
openclaw skill football-quant-os kelly --probability 0.38 --odds 2.18 --bankroll 10000

# 回测
openclaw skill football-quant-os backtest --days 30 --strategy "kelly_half"

# 套利扫描
openclaw skill football-quant-os arbitrage --markets "1x2,asian_handicap,over_under"
```

### 方式3: JavaScript API

```javascript
const { FootballQuantOS } = require('football-quant-os');

const quant = new FootballQuantOS({
  bankroll: 10000,
  data_sources: ['espn', 'football-data']
});

// 分析比赛
const analysis = await quant.analyze({
  home_team: 'Real Madrid',
  away_team: 'Bayern Munich',
  league: 'Champions League',
  market_odds: { home: 2.18, draw: 3.55, away: 3.32 }
});

console.log(analysis.final_decision);
// {
//   recommended_outcome: 'home_win',
//   confidence: 0.72,
//   kelly_recommendation: { bet_amount: 380, fraction: 0.038 },
//   risk_rating: 'medium',
//   expected_value: 0.052
// }
```

---

## 目录结构

```
football-quant-os/
├── SKILL.md                    # 本文件
├── README.md                   # 详细文档
├── requirements.txt            # Python 依赖
├── package.json                # Node.js 依赖 (可选)
│
├── core/                       # 核心引擎
│   ├── config.py               # 配置管理
│   ├── config_loader.py        # 配置加载器
│   ├── event_bus.py            # 事件总线
│   └── scheduler.py            # 任务调度
│
├── agents/                     # 九智能体
│   ├── datascout.py            # 数据采集
│   ├── datascout_v2.py         # 数据采集 v2
│   ├── analyst.py              # 分析师
│   ├── analyst_v2.py           # 分析师 v2
│   ├── committee.py            # 委员会
│   ├── committee_v2.py         # 委员会 v2
│   ├── risk_control.py         # 风控
│   ├── risk_control_v2.py      # 风控 v2
│   └── gene_engine.py          # 进化引擎
│
├── models/                     # 量化模型
│   ├── kelly.py                # Kelly 准则
│   ├── matrix_108.py           # 108 矩阵模型
│   └── historical_odds.py      # 历史赔率分析
│
├── data/                       # 数据目录
│   ├── fixtures/               # 赛程数据
│   └── odds/                   # 赔率数据
│
├── fixtures/                   # 数据源客户端
│   ├── espn_client.py          # ESPN API 客户端
│   └── models.py               # 数据模型
│
├── app/                        # Web 服务
│   ├── api.py                  # REST API
│   ├── tasks.py                # 异步任务
│   └── main.py                 # 入口
│
├── backtest/                   # 回测引擎
│   └── engine.py               # 回测框架
│
├── scripts/                    # 脚本工具
│   ├── scrape_500.py           # 500 网抓取
│   ├── scrape_oddsportal.py    # OddsPortal 抓取
│   ├── full_prediction_v3.py    # 完整预测 v3
│   └── workflow_demo.py        # 工作流演示
│
└── references/                 # 参考资料
    ├── INTEGRATION_REPORT.md   # 集成报告
    └── PROBABILITY_CHAIN.md    # 概率链文档
```

---

## 数据源

| 数据源 | 类型 | 覆盖范围 | 更新频率 |
|--------|------|---------|---------|
| ESPN API | 官方 | 全球主要联赛 | 实时 |
| Football-Data.co.uk | 历史 | 欧洲五大联赛 | 每日 |
| OddsPortal | 赔率 | 50+ 博彩公司 | 15分钟 |
| 500.com | 亚洲盘口 | 亚盘/大小球 | 实时 |

---

## 风险声明

⚠️ **本 Skill 仅供研究学习使用，不构成任何投注建议。**

- 体育博彩存在极高风险，可能导致资金全部损失
- 过往回测结果不代表未来表现
- 请遵守当地法律法规，理性对待
- 未成年人禁止使用

---

## 更新日志

### v1.0.0 (2026-05-16)
- 九智能体架构完整实现
- 四层概率修正器上线
- 支持 19+ 博彩公司赔率抓取
- Kelly 最优注码计算
- 回测引擎 v1
- 自进化基因引擎

---

## 相关链接

- **GitHub**: https://github.com/giziwy-ship-it/football-quant-os
- **Issue 反馈**: https://github.com/giziwy-ship-it/football-quant-os/issues

---

_"用数据说话，让概率成为你的朋友。"_ 🏎️⚽📊
