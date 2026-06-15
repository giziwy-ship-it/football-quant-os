# 教练数据实时抓取 - 数据源地图
## 生成时间: 2026-06-13

## 数据字段 × 来源矩阵

| 字段 | FIFA官方 | Wikipedia | Transfermarkt | FBref | RSS新闻 | 可自动化? |
|------|----------|-----------|---------------|-------|---------|----------|
| **姓名** | ✅ PDF | ✅ API | ✅ 爬虫 | ❌ | ❌ | ✅ 100% |
| **国籍** | ✅ PDF | ✅ API | ✅ 爬虫 | ❌ | ❌ | ✅ 100% |
| **年龄** | ❌ | ✅ API | ✅ 爬虫 | ❌ | ❌ | ✅ 100% |
| **世界杯经验** | ❌ | ✅ API | ✅ 爬虫 | ❌ | ❌ | ✅ 95% |
| **欧洲杯经验** | ❌ | ✅ API | ✅ 爬虫 | ❌ | ❌ | ✅ 95% |
| **执教比赛数** | ❌ | ❌ | ✅ 爬虫 | ✅ API | ❌ | ✅ 90% |
| **常用阵型** | ❌ | ❌ | ✅ 爬虫 | ❌ | ❌ | ✅ 80% |
| **场均进球** | ❌ | ❌ | ❌ | ✅ API | ❌ | ✅ 100% |
| **场均失球** | ❌ | ❌ | ❌ | ✅ API | ❌ | ✅ 100% |
| **情绪稳定性** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ **专家评估** |
| **媒体影响力** | ❌ | ❌ | ❌ | ❌ | ✅ 文本分析 | ⚠️ 50% |
| **崩盘事故** | ❌ | ❌ | ❌ | ❌ | ✅ 文本分析 | ⚠️ 60% |
| **轮换倾向** | ❌ | ❌ | ✅ 爬虫 | ❌ | ❌ | ⚠️ 70% |
| **策略极端性** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ **专家评估** |
| **突发事件** | ❌ | ❌ | ❌ | ❌ | ✅ RSS | ✅ 实时 |

## 数据源详细配置

### 1. FIFA官方 (100%权威)
```
来源: FIFA Squad Lists PDF
URL: https://fdp.fifa.org/assetspublic/ce281/pdf/SquadLists-English.pdf
获取: 手动下载 + PDF解析
更新: 大赛前1天
成本: 免费
数据: 姓名、国籍、球队
```

### 2. Wikipedia (免费API)
```
API: https://en.wikipedia.org/api/rest_v1/page/summary/{name}
文档: https://www.mediawiki.org/wiki/API:Main_page
限制: 100 req/min
获取: 年龄、国籍、简要履历
代码: 见 coach_data_sync.py WikipediaFetcher
```

### 3. Transfermarkt (爬虫)
```
URL: https://www.transfermarkt.com/{coach}/profil
限制: 5 req/min (严格反爬)
获取: 完整执教履历、球队历史、比赛数、阵型
代码: 见 coach_data_sync.py TransfermarktFetcher
依赖: beautifulsoup4
注意: 需要User-Agent，可能被Cloudflare拦截
```

### 4. FBref (免费API)
```
API: https://api.fbref.com/v1/teams/{id}/stats/{season}
注册: https://www.sports-reference.com/api/
限制: 10 req/min
获取: 比赛统计、进球数据、高级指标
代码: 见 coach_data_sync.py FBrefFetcher
```

### 5. RSS新闻 (实时)
```
BBC Sport: https://feeds.bbci.co.uk/sport/football/rss.xml
ESPN: https://www.espn.com/espn/rss/soccer/news
Transfermarkt: https://www.transfermarkt.com/rss/news
获取: 突发事件、下课传闻、伤病新闻
代码: 见 coach_data_sync.py RSSNewsFetcher
更新: 每15分钟
```

## 实时抓取架构

```
┌─────────────────────────────────────────────────────────────┐
│                    CoachDataSync (主控器)                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐     │
│   │ Wikipedia   │   │Transfermarkt│   │  RSS News   │     │
│   │  Fetcher    │   │  Fetcher    │   │  Fetcher    │     │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘     │
│          │                   │                  │           │
│          └───────────────────┴──────────────────┘           │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │  Fusion   │  ← 多源数据融合            │
│                    │  Engine   │  ← 冲突解决、优先级排序    │
│                    └─────┬─────┘                            │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │  Change   │  ← 变化检测               │
│                    │ Detector  │  ← 只推送更新              │
│                    └─────┬─────┘                            │
│                          │                                  │
│                    ┌─────┴─────┐                            │
│                    │  Output   │  ← CoachDataSnapshot      │
│                    │  Format   │  ← 标准数据格式            │
│                    └───────────┘                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 执行计划

### 赛前批量更新 (大赛前1周)
```python
sync = CoachDataSync()
results = sync.sync_all_coaches([
    ("Lionel Scaloni", "Argentina"),
    ("Didier Deschamps", "France"),
    # ... 48 teams
])
# 耗时: ~48 teams × 5s = ~4分钟
# 触发: 手动执行 (大赛前)
```

### 每日自动更新
```python
# 检查新闻、阵容变化
articles = sync.rss.fetch_feed('bbc_sport')
changes = sync.detect_changes(old_data, new_data)
for change in changes:
    if change['severity'] == 'high':
        alert(f"URGENT: {change}")
```

### 实时事件监控
```python
# 每15分钟检查RSS
# 检测到: 教练下课、伤病、战术变化
# 触发: 即时告警 + 数据更新
```

## 存储与带宽

| 操作 | 本地存储 | 网络带宽 | 耗时 |
|------|----------|----------|------|
| 赛前全量更新 | 25 KB | ~500 KB | ~4分钟 |
| 每日RSS检查 | 0 KB | ~50 KB | ~10秒 |
| 实时事件 | 0 KB | ~10 KB | ~2秒 |
| 单个教练查询 | 0 KB | ~20 KB | ~5秒 |

## 成本

| 数据源 | 成本 | 限制 |
|--------|------|------|
| FIFA官方 | 免费 | 手动 |
| Wikipedia | 免费 | 100 req/min |
| Transfermarkt | 免费 | 5 req/min |
| FBref | 免费 | 10 req/min |
| RSS | 免费 | 无限制 |
| **总计** | **$0** | 需控制速率 |

## 推荐配置

```python
# 生产环境配置
sync = CoachDataSync(
    fbref_api_key="YOUR_KEY"  # 可选，不填也能用基础功能
)

# 赛前更新 (手动触发)
results = sync.sync_all_coaches(coach_list)

# 每日监控 (cron定时)
changes = sync.detect_changes(yesterday_data, today_data)

# 实时告警 (每15分钟)
urgent_news = sync.rss.search_coach_mentions(coach_name, articles)
```

## 代码文件

| 文件 | 说明 | 大小 |
|------|------|------|
| `coach_data_sync.py` | 完整抓取引擎 | 24 KB |
| `coach_types.py` | 数据类型定义 | 3.4 KB |
| `worldcup_2026_full_coaches.py` | 48强数据库 | 25 KB |

---
*数据源地图 v1.0 - Naga Core 🐉*
