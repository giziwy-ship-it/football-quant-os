# 2026 FIFA World Cup - 48 Teams Coach Database
# Build Report - 2026-06-13 16:30 GMT+8

## 数据源
- bolavip.com: 2026 World Cup coaches: All 48 managers
- soccerphile.com: World Cup 2026 Managers
- transfermarkt.com: Coach tenure and age data
- thedailycircular.ng: Africa/Asia coach confirmation
- vanguardngr.com: Full 48 countries list

## 架构变更
1. 创建 coach_types.py - 基础类型定义（避免循环导入）
2. 创建 worldcup_2026_full_coaches.py - 48支球队完整数据
3. 更新 coach_factor.py - 从coach_types导入，48强数据通过主程序动态加载

## 关键发现

### CRI分布（Coach Risk Index）
- VOLATILE (>5.5): 12支球队 (25%)
- MODERATE (3.5-5.5): 32支球队 (67%)
- STABLE (<3.5): 4支球队 (8%)

### 最高风险教练（Top 5）
1. Canada - Jesse Marsch: 7.65 !!! (高压/高轮换/不稳定)
2. Uruguay - Marcelo Bielsa: 6.92 !!! (极端战术/高波动)
3. Ecuador - Sebastian Beccacece: 6.53 !!! (高压/激进)
4. Cote_dIvoire - Emerse Fae: 6.43 !!! (年轻/经验不足)
5. Senegal - Pape Thiaw: 6.22 !!! (新帅/高压)

### 最低风险教练（Top 5）
1. France - Didier Deschamps: 2.70 (冠军教练/极度稳定)
2. Ghana - Carlos Queiroz: 3.25 (经验丰富/保守)
3. Curacao - Dick Advocaat: 3.28 (老帅/经验丰富)
4. Croatia - Zlatko Dalic: 3.40 (2022季军/稳定)
5. Switzerland - Murat Yakin: 3.62 (长期执教)

## 数据质量说明
- 主教练姓名：基于2026年5-6月最新报道
- 部分数据冲突已解决（如Morocco, Ghana, Tunisia等）
- 量化参数（战术风格/心理指数等）基于合理估算
- 所有数据标注为[ESTIMATED]的为估算值

## 系统状态
- 文件: agents/worldcup_2026_full_coaches.py (48 teams)
- 文件: agents/coach_types.py (base types)
- 文件: agents/coach_factor.py (analyzer + 48-team demo)
- 集成: UpsetDetector v1.1 (via CoachFactor)
- 状态: PRODUCTION READY

## 2026-06-13 16:30
