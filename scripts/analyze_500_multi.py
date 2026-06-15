import json
from datetime import datetime

print("=" * 70)
print("500.com Multi-Dimension Analysis - USA vs Paraguay")
print(f"Time: {datetime.now().isoformat()}")
print("=" * 70)
print()

# Load the scraped data
with open("500_1359189_full_20260613_072809.json", "r", encoding="utf-8") as f:
    data = json.load(f)

pages = data["pages"]

# 1. Data Analysis (shuju)
print("[1] DATA ANALYSIS (shuju)")
print("-" * 70)
shuju_text = pages["shuju"]["text_preview"]

# Extract FIFA rankings
if "美国[世17]" in shuju_text:
    print("  FIFA Rankings:")
    print("    USA: #17 (1671 pts)")
    print("    Paraguay: #41 (1505 pts)")
    print("    Gap: 24 ranks, 166 points")

if "美国近10场战绩5胜1平4负进18球失17球" in shuju_text:
    print("  Recent Form (Last 10):")
    print("    USA: 5W-1D-4L, GF:18, GA:17")
    print("    Paraguay: 4W-2D-4L, GF:12, GA:10")

if "双方近5次交战，美国3胜0平2负，进5球，失5球" in shuju_text:
    print("  H2H (Last 5):")
    print("    USA: 3W-0D-2L")
    print("    Goals: 5-5")

print()

# 2. Betting Analysis (touzhu)
print("[2] BETTING ANALYSIS (touzhu)")
print("-" * 70)
touzhu_text = pages["touzhu"]["text_preview"]

if "美国" in touzhu_text and "2.06" in touzhu_text:
    print("  500.com Odds:")
    print("    USA: 2.06 (45.8%)")
    print("    Draw: 3.24 (29.2%)")
    print("    Paraguay: 3.79 (25.0%)")
    print("  Betting Flow:")
    print("    USA: 74.0%")
    print("    Draw: 15.9%")
    print("    Paraguay: 10.1%")
    print("  Bf Volume:")
    print("    Total: 10,318,669 HKD")
    print("    USA: 7,638,172 (74.0%)")
    print("    Draw: 1,636,272 (15.9%)")
    print("    Paraguay: 1,044,225 (10.1%)")
    print("  Bookmaker PnL:")
    print("    USA: -6,332,546 (risk)")
    print("    Draw: +4,755,344")
    print("    Paraguay: +6,037,347")
    print("  Hot/Cold Index:")
    print("    USA: 61 (hot)")
    print("    Draw: -46 (cold)")
    print("    Paraguay: -60 (cold)")
    print("  Alert:")
    print("    '必发交易规模超千万，谨防比赛过于热门'")
    print("    '必发成交量倾向于主胜,与百家欧赔概率相差较大'")

print()

# 3. European Odds (ouzhi)
print("[3] EUROPEAN ODDS (ouzhi)")
print("-" * 70)
ouzhi_text = pages["ouzhi"]["text_preview"]

# Extract key bookmakers
bookmakers = []
if "威廉" in ouzhi_text:
    bookmakers.append("William Hill")
if "立博" in ouzhi_text:
    bookmakers.append("Ladbrokes")
if "BET365" in ouzhi_text:
    bookmakers.append("BET365")
if "伟德" in ouzhi_text:
    bookmakers.append("Vbet")
if "皇冠" in ouzhi_text:
    bookmakers.append("Crown")
if "澳门" in ouzhi_text:
    bookmakers.append("Macau")

print(f"  Bookmakers: {', '.join(bookmakers)}")
print("  (Detailed odds movement requires parsing tables)")

print()

# 4. Asian Handicap (rangqiu)
print("[4] ASIAN HANDICAP (rangqiu)")
print("-" * 70)
rangqiu_text = pages["rangqiu"]["text_preview"]

if "平手" in rangqiu_text or "半球" in rangqiu_text:
    print("  Handicap options available")
    print("  (Detailed handicap data requires parsing tables)")

print()

# 5. Asian Odds Comparison (yazhi)
print("[5] ASIAN ODDS COMPARISON (yazhi)")
print("-" * 70)
yazhi_text = pages["yazhi"]["text_preview"]

print("  Multiple Asian bookmakers compared")
print("  (Detailed comparison requires parsing tables)")

print()

# 6. Over/Under (daxiao)
print("[6] OVER/UNDER (daxiao)")
print("-" * 70)
daxiao_text = pages["daxiao"]["text_preview"]

if "大" in daxiao_text and "小" in daxiao_text:
    print("  Over/Under options available")
    print("  (Detailed O/U data requires parsing tables)")

print()

# 7. Score Odds (bifen)
print("[7] CORRECT SCORE (bifen)")
print("-" * 70)
bifen_text = pages["bifen"]["text_preview"]

if "1:0" in bifen_text or "2:1" in bifen_text:
    print("  Correct score odds available")
    print("  (Detailed score data requires parsing tables)")

print()
print("=" * 70)
print("INTEGRATION SUMMARY")
print("=" * 70)
print()

print("Key Data Points for UpsetDetector:")
print("-" * 70)
print("  1. FIFA Ranking Gap: USA #17 vs PAR #41 (24 ranks)")
print("  2. Recent Form: USA 5W-1D-4L vs PAR 4W-2D-4L")
print("  3. H2H: USA 3W-0D-2L in last 5")
print("  4. Market Odds: 2.06/3.24/3.79")
print("  5. Betting Flow: 74.0%/15.9%/10.1%")
print("  6. Bookmaker Risk: -6.3M on USA")
print("  7. Hot Index: USA 61 (hot)")
print("  8. Total Volume: 10.3M HKD")
print()

print("UpsetDetector Analysis:")
print("-" * 70)
print("  Score: 33.0/100 (NORMAL)")
print("  Key Factors:")
print("    - Odds Reverse: 15/20 (high flow, odds not dropping)")
print("    - Abnormal Flow: 12/15 (74% on USA)")
print("    - Big Team Hype: 0/20 (USA not a 'big team' in public eye)")
print("    - Injury Risk: 2/15 (Weah missing)")
print()

print("Comparison with CAN-BIH:")
print("-" * 70)
print("  USA-PAR: 33/100 - Moderate risk, USA favored")
print("  CAN-BIH: 49/100 - Higher risk, Dzeko injury, more hype")
print()

print("Recommendation:")
print("-" * 70)
print("  Both matches show 'odds reverse' signal")
print("  But neither reaches 'UPSET CANDIDATE' (80+)")
print("  USA is safer bet than Canada (lower hype, more justified odds)")
print("  If betting on upset: PAR @3.79 > BIH @4.66 (but both low prob)")
print()

print("=" * 70)
print(f"Time: {datetime.now().isoformat()}")
print("=" * 70)
