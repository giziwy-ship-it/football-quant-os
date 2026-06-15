# scripts/ - 测试与工具脚本

## 说明

此目录包含 `football_quant_os` 项目的测试脚本、数据分析工具和独立运行工具。

这些脚本**不是生产代码**的一部分，仅用于：
- 快速测试 API
- 分析单场比赛
- 批量抓取数据
- 回测验证
- 调试排查

## 文件分类

### 分析脚本 (analyze_*)
- `analyze_*.py` - 分析单场比赛并生成预测报告
- 示例: `analyze_arsenal_psg.py`, `analyze_bundesliga_batch.py`

### 回测脚本 (backtest_2022*)
- `backtest_2022*.py` - 使用 2022 世界杯数据验证预测模型
- 包含多种策略回测（Elo/完整系统/宽松版）

### 数据抓取 (fetch_*, scrape_*, search_*)
- `fetch_*.py` - 从 ESPN 获取数据
- `scrape_*.py` - 从 500.com/OddsPortal 抓取赔率
- `search_*.py` - 搜索特定比赛

### 测试脚本 (test_*, verify_*, check_*)
- `test_*.py` - 集成测试
- `verify_*.py` - 验证概率传递链
- `check_*.py` - 检查 API/赛程

### 工具脚本 (run_*, list_*, predict_*)
- `run_*.py` - 运行比赛预测
- `list_*.py` - 列出今日比赛
- `predict_*.py` - 预测特定比赛

### 其他
- `worldcup_main.py` - 世界杯系统独立入口
- `workflow_demo.py` - 工作流演示
- `dashboard.py` - 旧版仪表盘
- `full_prediction_v3.py` - 旧版预测入口
- `football_data_api.py` - 足球数据 API 工具
- `odds_api.py` - 赔率 API 工具

## 使用方式

```python
# 在 scripts/ 目录下运行
python analyze_mexico_rsa.py

# 或从项目根目录运行
python scripts/analyze_mexico_rsa.py
```

## 注意

⚠️ 这些脚本**不应该**被生产代码导入。它们是独立的、可丢弃的辅助工具。

如需将某个脚本功能化，请将其重构为 `agents/` 或 `core/` 中的正式模块。

---
*最后整理: 2026-06-11*
