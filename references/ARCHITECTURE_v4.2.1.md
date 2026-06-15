# Football Quant OS v4.2.1-naga 架构图

**生成时间**: 2026-06-13 18:46
**版本**: Football Quant OS v4.2.1-naga
**Naga Core**: v5.0

---

## 核心洞察

> **"顶级博彩机构 = 预测 + 定价 + 交易 + 资金 闭环"**
> 
> 我们从「预测引擎」升级为「预测+定价+交易+资金」量化交易公司。

---

## 顶层架构

```
+--------------------------------------------------------------------+
|                     Naga Core v5.0 - 六层架构整合层               |
|                     (Layer 0-5: Identity/Context/State/Constraint/  |
|                      Self-Check/Output)                             |
+--------------------------------------------------------------------+
                              |
                              v
+--------------------------------------------------------------------+
|                    Football Quant OS v4.2.1-naga                  |
|              "以足球比赛为标的资产的量化交易公司"                      |
+--------------------------------------------------------------------+
|                                                                     |
|  P0 层 - 定价与资金层 (Pricing + Treasury)                         |
|  +----------------+  +----------------+  +----------------+          |
|  | OddsPricing    |  | Treasury       |  | Intelligence   |          |
|  | Agent v1.1     |  | Agent v1.1     |  | Agent v1.0     |          |
|  |                |  |                |  |                |          |
|  | 7种盘口        |  | 多币种资金     |  | 5级情报源      |          |
|  | 多博彩聚合     |  | Kelly注码      |  | 13类分类       |          |
|  | 套利检测       |  | 蒙特卡洛VaR    |  | NLP情绪分析    |          |
|  | 赔率历史       |  | 回撤管理       |  | 7类风控触发    |          |
|  +----------------+  +----------------+  +----------------+          |
|                                                                     |
|  P1 层 - 执行与风控层 (Trading + Risk)                              |
|  +----------------+  +----------------+                             |
|  | TradingAgent   |  | RiskGuardian   |                             |
|  | v1.0           |  | v1.0           |                             |
|  |                |  |                |                             |
|  | 7交易所路由    |  | 8维监控        |                             |
|  | 5策略执行      |  | 5级熔断        |                             |
|  | 智能评分       |  | 6种熔断动作    |                             |
|  | 智能路由       |  | 订单网关       |                             |
|  +----------------+  +----------------+                             |
|                                                                     |
|  P2 层 - 结算层 (Settler) [WAITING]                                 |
|  +----------------+                                                  |
|  | Settler        |  自动结算 + 资金划转 + 报表生成                  |
|  | [WAITING]      |                                                  |
|  +----------------+                                                  |
|                                                                     |
|  P3 层 - 冷门雷达层 (Upset Detection)                               |
|  +----------------+  +----------------+                             |
|  | UpsetDetector  |  | CoachFactor    |                             |
|  | v1.0           |  | v1.0           |                             |
|  |                |  |                |                             |
|  | 市场定价错误   |  | 48强教练DB     |                             |
|  | 100分冷门评分  |  | 6维CRI + 4因子 |                             |
|  | 大比分预测     |  | CBM            |                             |
|  | 价值投注识别   |  | 互联网同步     |                             |
|  +----------------+  +----------------+                             |
|                                                                     |
|  P4 层 - 数据工程与模型训练层 (Data Engineering)                     |
|  +----------------+  +----------------+                             |
|  | WorldCupData   |  | PromptEngine   |                             |
|  | Engineer v1.0  |  | v1.0           |                             |
|  |                |  |                |                             |
|  | 三届世界杯     |  | 可复用模板     |                             |
|  | 特征工程       |  | 数据/预测/     |                             |
|  | AI预测模型     |  | 策略Prompt     |                             |
|  | 冷门识别       |  |                |                             |
|  +----------------+  +----------------+                             |
|                                                                     |
|  +---------------------------------------------------------------+  |
|  |            9-Agent Pipeline (Core Prediction Engine)            |  |
|  |  DataScout -> GeneEngine -> Analyst -> Committee -> RiskControl  |  |
|  |  Execution -> Arbitrage -> TeamValue -> Legal -> Evolution       |  |
|  |                                                                 |  |
|  |  Output: 108 Matrix Probabilities + Multi-Market Predictions    |  |
|  |          + Capital Allocation + Risk Warnings                   |  |
|  +---------------------------------------------------------------+  |
|                                                                     |
|  +---------------------------------------------------------------+  |
|  |            Multi-Market Predictor (Updated)                      |  |
|  |  1X2 | Asian Handicap | HT/FT | Correct Score | Over/Under      |  |
|  |  NEW: venue_type field (neutral/home/away)                     |  |
|  +---------------------------------------------------------------+  |
|                                                                     |
|  +---------------------------------------------------------------+  |
|  |            Reports Layer                                         |  |
|  |  reports/gen_pdf.py              - Chrome headless PDF         |  |
|  |  reports/generate_pdf_report.py    - Goldman Style PDF (NEW)     |  |
|  +---------------------------------------------------------------+  |
|                                                                     |
+--------------------------------------------------------------------+
                              |
                              v
+--------------------------------------------------------------------+
|                          External Data Sources                       |
+--------------------------------------------------------------------+
|  500.com    |  OddsPortal   |  Betfair Exchange |  FIFA Official   |
|  ESPN API   |  BBC Sport    |  Sina/NetEase     |  Transfermarkt   |
|  Wikipedia  |  FBref        |  Football-Data    |  Social Media     |
+--------------------------------------------------------------------+
```

---

## 关键架构决策

| 决策 | 时间 | 说明 |
|------|------|------|
| 3层架构够用 | 2026-06-13 14:00 | FIFA + Coach + WorldCup，不增加层数 |
| FIFA官方数据为基准 | 2026-06-13 16:30 | 第三方数据全部验证，4个重大修正 |
| 数据分层策略 | 2026-06-13 17:28 | 客观字段可互联网自动化；主观字段需专家评估 |
| Prediction vs Value Bet 区分 | 2026-06-13 18:22 | 最可能结果 vs 赔率被低估的方向 |
| 系统整合清理 | 2026-06-13 18:42 | 临时脚本移至 _trash_20260613，PDF整合至 reports/ |

---

## 系统状态

| 组件 | 状态 | 版本 |
|------|------|------|
| OddsPricingAgent | PROD | v1.1 |
| TreasuryAgent | PROD | v1.1 |
| IntelligenceAgent | PROD | v1.0 |
| TradingAgent | PROD | v1.0 |
| RiskGuardian | PROD | v1.0 |
| UpsetDetector | PROD | v1.0 |
| CoachFactor | PROD | v1.0 |
| WorldCupDataEngineer | PROD | v1.0 |
| 9-Agent Pipeline | PROD | v4.2 |
| Multi-Market Predictor | PROD | v4.2.1 |
| PDF Report Generator | PROD | v1.0 (Goldman Style) |
| Settler | WAITING | - |
| Redis Cache | READY | - |
| Naga Core Bridge | READY | v4.2.1-naga |

---

*Football Quant OS v4.2.1-naga | Naga Core v5.0 | Generated by Naga*
