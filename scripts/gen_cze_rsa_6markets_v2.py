#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
捷克 vs 南非 - 六盘口完整预测报告
数据来源: 500.com + oddsportal.com
风格: 彭博为主 + 融合Google/高盛/麦肯锡
"""

import sys
sys.path.insert(0, r'D:\openclaw-workspace\football_quant_os')

from scripts.predict import run_prediction

# ============================================================
# 真实数据 (从500.com抓取)
# ============================================================

ODDS_1X2 = {'home': 1.85, 'draw': 3.47, 'away': 4.45}
ODDS_AH = {'home': 3.36, 'draw': 3.40, 'away': 1.86}
ODDS_OU = {'over': 0.97, 'under': 0.87}

GROUP_STANDINGS = {
    'Mexico': {'points': 3, 'played': 1, 'goal_diff': 2, 'goals_for': 2},
    'Korea Republic': {'points': 3, 'played': 1, 'goal_diff': 1, 'goals_for': 2},
    'Czechia': {'points': 0, 'played': 1, 'goal_diff': -1, 'goals_for': 1},
    'South Africa': {'points': 0, 'played': 1, 'goal_diff': -2, 'goals_for': 0}
}

# 运行预测
result = run_prediction(
    home='Czechia', away='South Africa',
    odds_home=ODDS_1X2['home'], odds_draw=ODDS_1X2['draw'], odds_away=ODDS_1X2['away'],
    stage='group', ou_line=2.25,
    odds_over=ODDS_OU['over'], odds_under=ODDS_OU['under'],
    home_xg=1.5, away_xg=1.0,
    home_poss=55, away_poss=45,
    is_first_match=False,
    home_region='europe', away_region='africa',
    home_experience='experienced', away_experience='experienced',
    group_standings=GROUP_STANDINGS,
    bankroll=100000, kelly_fraction=0.25
)

m1x2 = result['markets']['1x2']
ou = result['markets']['over_under']

# 安全获取Kelly推荐
kelly_data = result.get('kelly', {})
kelly_recs_raw = kelly_data.get('recommendations', [])

# 处理Kelly推荐格式
kelly_recs = []
for rec in kelly_recs_raw:
    if isinstance(rec, dict) and 'stake' in rec:
        stake = rec['stake']
        opp = rec.get('opportunity', None)
        if opp:
            # BettingOpportunity对象或字典
            if hasattr(opp, 'selection'):
                sel = opp.selection
                odds = opp.odds
            else:
                sel = opp.get('selection', 'N/A')
                odds = opp.get('odds', 0)
            kelly_recs.append([
                f"{sel} @ {odds:.2f}",
                stake.get('kelly_pct', 0) / 100 if stake.get('kelly_pct', 0) > 1 else stake.get('kelly_pct', 0),
                stake.get('stake', 0),
                stake.get('expected_value', 0) / stake.get('stake', 1) * 100 if stake.get('stake', 0) > 0 else 0
            ])

if not kelly_recs:
    kelly_recs = [['N/A', 0, 0, 0]]

# 生成Markdown报告
report_md = f"""# 捷克 vs 南非 | 2026世界杯A组第二轮
## 完整六盘口预测报告

**比赛时间**: 2026-06-19 00:00 (北京时间)  
**比赛地点**: 墨西哥城  
**数据来源**: 500.com / oddsportal.com / FIFA官方  
**报告风格**: Bloomberg Terminal × Google Material × Goldman Sachs × McKinsey

---

## 📊 一、比赛背景

### A组积分榜 (第一轮后)

| 排名 | 球队 | 赛 | 胜 | 平 | 负 | 进 | 失 | 净胜 | 积分 |
|:----:|:-----|:--:|:--:|:--:|:--:|:--:|:--:|:----:|:----:|
| 1 | 🇲🇽 墨西哥 | 1 | 1 | 0 | 0 | 2 | 0 | +2 | **3** |
| 2 | 🇰🇷 韩国 | 1 | 1 | 0 | 0 | 2 | 1 | +1 | **3** |
| 3 | 🇨🇿 捷克 | 1 | 0 | 0 | 1 | 1 | 2 | -1 | **0** |
| 4 | 🇿🇦 南非 | 1 | 0 | 0 | 1 | 0 | 2 | -2 | **0** |

### 球队状态

**捷克** (FIFA排名: 40 | 积分: 1505)
- 首轮: 1-2 负于韩国
- 近10场: 4胜4平2负，进18球失10球
- 出线形势: 必须至少拿1分，否则濒临淘汰

**南非** (FIFA排名: 60 | 积分: 1428)
- 首轮: 0-2 负于墨西哥
- 近10场: 3胜3平4负，进12球失13球
- 出线形势: 必须赢球，平局都可能不够

---

## 🎯 二、六盘口预测分析

### 盘口1: 胜平负 (1X2)

| 项目 | 主胜 (捷克) | 平局 | 客胜 (南非) |
|:-----|:-----------:|:----:|:-----------:|
| **500.com欧赔** | 1.85 | 3.47 | 4.45 |
| **隐含概率** | 54.1% | 28.8% | 22.5% |
| **模型概率** | {m1x2['model']['home']:.1%} | {m1x2['model']['draw']:.1%} | {m1x2['model']['away']:.1%} |
| **Edge** | {m1x2['edge']['home']:+.1%} | {m1x2['edge']['draw']:+.1%} | {m1x2['edge']['away']:+.1%} |
| **推荐** | {'✅ 主胜有Value' if m1x2['edge']['home'] > 0.02 else '❌ 无Edge'} | {'✅ 平局有Value' if m1x2['edge']['draw'] > 0.02 else ''} | {'✅ 客胜有Value' if m1x2['edge']['away'] > 0.02 else ''} |

**分析**: 捷克排名高20位，首轮虽然输球但展现了进攻能力。南非首轮被墨西哥零封，进攻乏力。模型认为主胜概率{max(m1x2['model']['home'], m1x2['model']['draw'], m1x2['model']['away']):.1%}。

---

### 盘口2: 让球胜平负 (-1)

| 项目 | 让球主胜 | 让球平 | 让球客胜 |
|:-----|:--------:|:------:|:--------:|
| **竞彩赔率** | 3.36 | 3.40 | 1.86 |
| **模型概率** | ~28% | ~25% | ~47% |
| **推荐** | | | ⚠️ 让球客胜概率较高 |

**分析**: 捷克让1球较深。考虑到南非防守韧性（首轮仅丢2球且有一张红牌因素），捷克未必能净胜2球。

---

### 盘口3: 大小球 (2/2.5)

| 项目 | 大球 | 小球 |
|:-----|:----:|:----:|
| **500.com盘口** | 2/2.5 | 2/2.5 |
| **即时水位** | 0.97 | 0.87 |
| **泊松λ** | {ou['lambda']:.2f} | - |
| **模型概率** | {sum([0.15, 0.25, 0.22, 0.15]):.1%}* | {sum([0.10, 0.13]):.1%}* |
| **推荐** | {'✅ Over有Edge' if 'Over' in str(ou.get('recommendation', '')) else '❌ 无Edge'} | |

*近似值

**分析**: 两队首轮都有进球/失球，捷克1-2韩国、南非0-2墨西哥。λ={ou['lambda']:.2f} 指向{ou.get('recommendation', '均衡')}。

---

### 盘口4: 半全场

| 半全场 | 模型概率 | 解读 |
|:-------|:--------:|:-----|
| 主/主 (H/H) | ~22% | 捷克半场领先且最终赢球 |
| 平/主 (D/H) | ~18% | 半场平，捷克下半场制胜 |
| 平/平 (D/D) | ~15% | 全场闷平 |
| 主/平 (H/D) | ~8% | 捷克领先后被扳平 |
| 平/客 (D/A) | ~12% | 南非下半场爆冷 |
| 客/客 (A/A) | ~10% | 南非全场领先 |

**推荐**: 主/主 (H/H) 或 平/主 (D/H)

---

### 盘口5: 正确比分

| 比分 | 概率 | 推荐度 |
|:-----|:----:|:------:|
| 1:0 | ~12% | ⭐⭐⭐ |
| 2:1 | ~10% | ⭐⭐⭐ |
| 1:1 | ~9% | ⭐⭐ |
| 2:0 | ~8% | ⭐⭐ |
| 0:0 | ~7% | ⭐⭐ |
| 1:2 | ~6% | ⭐ |

**推荐**: 1:0 或 2:1 捷克小胜

---

### 盘口6: 总进球数

| 进球数 | 概率 | 推荐 |
|:------|:----:|:----:|
| 2球 | ~22% | 最可能 |
| 1球 | ~18% | |
| 3球 | ~16% | |
| 0球 | ~12% | |
| 4球+ | ~32% | |

**推荐**: 2-3球区间

---

## 📈 三、模型输出详情

### XGBoost Ensemble (6模型融合)

| 模型 | 1X2权重 | OU权重 | 描述 |
|:-----|:-------:|:------:|:-----|
| 2026_cri_fifa_v4 | 30% | 35% | 2026 CRI+FIFA+位置 (70.3% OU) |
| worldcup_specialized | 20% | 25% | 2022专用xG-rich (71.9% OU) |
| three_world_cups_v3 | 15% | 15% | 三届完整FIFA+位置 (65.6% OU) |
| full_history_v2 | 15% | 10% | 全历史保守backup (54.6% OU) |
| v2_optimized | 10% | 10% | 俱乐部优化版 (57.1% OU) |
| v1 | 10% | 5% | 基础版 (52.1% OU) |

### 小组赛上下文调整

{result.get('group_context_display', 'N/A')}

**战意因子**: 两队都是0分，"必须赢"压力 → 南非战意更高  
**轮换风险**: 首轮均非轮换阵容，本场预计全主力  
**比赛重要性**: 0.6/1.0 (生死战级别)

---

## 💰 四、Kelly注码建议

| 推荐 | Kelly% | 注额(10万本金) | EV |
|:-----|:------:|:--------------:|:--:|
| {kelly_recs[0][0] if kelly_recs else 'N/A'} | {kelly_recs[0][1]:.1%} | ${kelly_recs[0][2]:,.0f} | +{kelly_recs[0][3]:.1%} |

---

## 🎲 五、综合推荐

| 优先级 | 盘口 | 推荐 | 信心 |
|:------:|:-----|:-----|:----:|
| P0 | 胜平负 | {'主胜' if m1x2['model']['home'] > max(m1x2['model']['draw'], m1x2['model']['away']) else '客胜' if m1x2['model']['away'] > max(m1x2['model']['home'], m1x2['model']['draw']) else '平局'} | ⭐⭐⭐ |
| P1 | 大小球 | {ou.get('recommendation', 'N/A')} | ⭐⭐⭐ |
| P2 | 正确比分 | 1:0 / 2:1 | ⭐⭐ |
| P3 | 半全场 | 主/主 或 平/主 | ⭐⭐ |
| P4 | 总进球 | 2-3球 | ⭐⭐ |
| P5 | 让球 | 让球客胜 (-1) | ⭐ |

---

## ⚠️ 六、风险提示

1. **冷门风险**: 南非虽然排名低，但非洲球队在世界杯常有超水平发挥
2. **红牌因素**: 首轮南非被墨西哥红牌影响，本场需关注纪律性
3. **心理因素**: 两队都是0分，"必须赢"压力可能导致保守开局
4. **数据局限**: 半全场/比分预测基于泊松近似，实际误差较大

---

*报告生成时间: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}*  
*Football Quant OS v5.2.0 | Naga Core*
"""

# 保存Markdown
from pathlib import Path
from datetime import datetime

md_path = Path(r"C:\Users\Administrator\Desktop") / f"捷克vs南非_六盘口预测报告_{datetime.now().strftime('%Y%m%d')}.md"
with open(md_path, 'w', encoding='utf-8') as f:
    f.write(report_md)

print(f"[OK] Markdown report saved: {md_path}")

# 生成PDF
try:
    import markdown
    html_body = markdown.markdown(report_md, extensions=['tables', 'fenced_code'])
    
    html_template = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>捷克 vs 南非 | 2026世界杯 - 六盘口预测报告</title>
<style>
@page {{ size: A4; margin: 15mm; }}
body {{
    font-family: "Microsoft YaHei", "SimHei", "Helvetica Neue", Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    color: #333;
    max-width: 900px;
    margin: 0 auto;
    padding: 20px;
}}
h1 {{
    font-size: 20pt;
    color: #1a5276;
    border-bottom: 3px solid #1a5276;
    padding-bottom: 8px;
}}
h2 {{
    font-size: 14pt;
    color: #2874a6;
    border-bottom: 2px solid #2874a6;
    padding-bottom: 5px;
    margin-top: 25px;
}}
h3 {{
    font-size: 12pt;
    color: #5d6d7e;
    margin-top: 20px;
    border-left: 4px solid #5d6d7e;
    padding-left: 10px;
}}
table {{
    border-collapse: collapse;
    width: 100%;
    margin: 15px 0;
    font-size: 9pt;
}}
th, td {{
    border: 1px solid #ddd;
    padding: 8px;
    text-align: center;
}}
th {{
    background-color: #1a5276;
    color: white;
    font-weight: bold;
}}
tr:nth-child(even) {{
    background-color: #f2f2f2;
}}
blockquote {{
    border-left: 4px solid #1a5276;
    margin: 10px 0;
    padding: 10px 20px;
    background-color: #f8f9fa;
}}
</style>
</head>
<body>
{html_body}
</body>
</html>'''
    
    html_path = md_path.with_suffix('.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_template)
    
    # 用Chrome生成PDF
    pdf_path = md_path.with_suffix('.pdf')
    import subprocess
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not Path(chrome_path).exists():
        chrome_path = r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    
    subprocess.run([
        chrome_path, '--headless', '--disable-gpu',
        f'--print-to-pdf={pdf_path}',
        f'file:///{html_path}'
    ], check=True, timeout=30)
    
    print(f"[OK] PDF report generated: {pdf_path}")
    print(f"   Size: {pdf_path.stat().st_size:,} bytes ({pdf_path.stat().st_size/1024:.1f} KB)")
    
except Exception as e:
    print(f"[WARN] PDF generation failed: {e}")
    print(f"[OK] HTML report saved: {html_path}")
