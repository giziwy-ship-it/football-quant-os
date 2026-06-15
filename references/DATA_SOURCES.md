# Football Quant OS - 公开数据源接入指南 (v2.0)

**按实用性排序 | 含短期/中长期规划**

---

## 数据源排名（实用性从高到低）

### 🥇 1. football-data.co.uk（最推荐）

| 维度 | 详情 |
|------|------|
| 链接 | https://www.football-data.co.uk/ |
| 类型 | 历史比赛结果 + 历史赔率（最有价值） |
| 覆盖范围 | 英超、德甲、意甲、西甲、法甲 + 世界杯、欧洲杯 |
| 数据格式 | CSV，可下载 |
| 费用 | 免费，无需注册 |
| 推荐指数 | ★★★★★ |

**关键字段**（对Edge回测最有价值）：
- `FTHG` = 全场主队进球
- `FTAG` = 全场客队进球
- `FTR` = 全场结果 (H/D/A)
- `B365H/B365D/B365A` = Bet365 赔率
- `BWH/BWD/BWA` = Betway 赔率
- `IWH/IWD/IWA` = Interwetten 赔率

**推荐用途**：
- 构建历史 Edge 分布（验证模型预测 vs 实际结果）
- 验证当前模型在世界杯的实际表现（ROI计算）
- 提取不同阶段（小组赛 vs 淘汰赛）的真实爆冷率

**下载方式**：
```bash
# 2022世界杯
wget https://www.football-data.co.uk/worldcup2022.csv
# 2018世界杯
wget https://www.football-data.co.uk/worldcup2018.csv
# 2014世界杯
wget https://www.football-data.co.uk/worldcup2014.csv
```

**Python集成**：
```python
from data_football_data_co_uk import FootballDataUK

fd = FootballDataUK()
df = fd.download_season("WC", "2022")
df = fd.calculate_implied_probs(df, "B365")
# df 现在包含 imp_home, imp_draw, imp_away（去除margin后的真实概率）
```

---

### 🥈 2. Kaggle World Cup Datasets

| 数据集 | 内容 | 推荐指数 | 备注 |
|--------|------|----------|------|
| FIFA World Cup 2022 | 完整比赛结果、进球、球员数据 | ★★★★★ | 最新一届，数据最全 |
| FIFA World Cup (All Years) | 1930–2018 历史数据 | ★★★★ | 适合长期趋势分析 |
| International football results | 1872年至今所有国家队比赛 | ★★★★ | 数据量大，适合训练模型 |

**推荐用途**：
- 做冷门分析、强队表现统计
- 构建简单预测特征（进球数、控球率等）
- 训练机器学习模型

**获取方式**：
```bash
pip install kaggle
kaggle datasets download -d datasets/fifa-world-cup-2022
```

**Python集成**：
```python
from data_kaggle import KaggleData

kg = KaggleData()
df = kg.load_worldcup_2022()
features = kg.get_feature_columns(df)
```

---

### 🥉 3. openfootball (GitHub)

| 维度 | 详情 |
|------|------|
| 链接 | https://github.com/openfootball |
| 类型 | 结构化 JSON / CSV / TXT / YAML |
| 特点 | 开源、结构清晰，包含多届世界杯完整数据 |
| 推荐指数 | ★★★★ |

**推荐用途**：
- 直接导入技能中使用（比CSV更结构化）
- 计算小组积分榜、淘汰赛对阵树
- 结构化数据便于程序解析

**获取方式**：
```bash
git clone https://github.com/openfootball/worldcup.git
```

**Python集成**：
```python
from data_openfootball import OpenFootball

of = OpenFootball()
matches = of.get_group_matches("2022", "a")
standings = of.calculate_group_standings("2022", "a")
```

---

### 4. FBref.com（StatsBomb）

| 维度 | 详情 |
|------|------|
| 链接 | https://fbref.com/ |
| 类型 | 详细比赛统计（xG、控球、射门等） |
| 特点 | 数据质量很高，但需要爬虫或手动下载 |
| 推荐指数 | ★★★★ |

**推荐用途**：
- 后期做更高级的特征工程（当前模型还用不到）
- xG数据可用于预期进球模型

---

### 5. 其他值得关注的免费来源

| 数据源 | 特点 | 免费程度 | 备注 |
|--------|------|----------|------|
| **Understat** | xG 数据优秀 | 免费 | 可用于高级模型 |
| **API-Football** | 有免费额度 | 有限免费（100 req/day） | 适合实时 + 历史查询 |
| **FiveThirtyEight** | SPI 评分 + 预测模型 | 免费 | 可作为参考基准 |
| **UEFA / FIFA 官网** | 官方统计 | 免费 | 数据较干净但较少 |

---

## 实用建议：如何接入你的技能

### 短期（1-2 周内）✅

1. **从 football-data.co.uk 下载近 3-4 届世界杯的 CSV 文件**
   - 2022、2018、2014（已下载）
   - 提取关键字段：结果、赔率、球队

2. **提取关键字段，整理成 `references/worldcup_historical.json`**
   - 已部分完成，需补充更多字段

3. **在 `WORLDCUP_GUIDE.md` 中补充真实数据**
   - 已创建，需补充具体统计数字

4. **把历史爆冷率统计替换目前写死的调整系数**
   - `predict.py` v0.4.3 已部分实现
   - 需用真实数据校准 `estimate_true_probability()` 中的参数

### 中长期（1-2 月）📅

- **根据历史数据动态计算不同阶段的调整参数**，而不是硬编码
  - 当前：`if stage == "group": mod_home = mod_home * 0.96 + 0.02`
  - 目标：基于历史数据拟合最优调整系数

- **加入简单的回测功能**（验证模型在过去世界杯的 Edge 表现）
  - `backtest_worldcup.py` 已创建，需完善ROI计算

- **接入FBref xG数据**，构建更高级特征

- **构建机器学习模型**（基于Kaggle数据集）

---

## 数据质量对比

| 维度 | football-data | Kaggle | OpenFootball | FBref | API-Football |
|------|---------------|--------|--------------|-------|--------------|
| 历史赔率 | ★★★★★ | ★★ | ★ | ★ | ★★★★ |
| 比赛结果 | ★★★★★ | ★★★★★ | ★★★★ | ★★★★★ | ★★★★★ |
| xG | ★ | ★★ | ★ | ★★★★★ | ★★★★ |
| 结构化程度 | ★★★★ | ★★★★ | ★★★★★ | ★★★ | ★★★★ |
| 易获取性 | ★★★★★ | ★★★★ | ★★★★ | ★★★ | ★★★ |
| 实时性 | ★ | ★ | ★ | ★★ | ★★★★★ |

---

## 推荐优先级矩阵

| 目标 | 首选数据源 | 备选数据源 |
|------|------------|------------|
| 验证模型Edge/ROI | football-data.co.uk | Kaggle |
| 构建历史爆冷率 | football-data.co.uk | OpenFootball |
| 获取实时赔率 | API-Football | odds_fetcher_playwright |
| 训练ML模型 | Kaggle | football-data.co.uk |
| 获取xG数据 | FBref | API-Football |
| 结构化数据导入 | OpenFootball | Kaggle |

---

*文档版本: v2.0*
*最后更新: 2026-06-14*
*基于用户提供的详细分析整理*
