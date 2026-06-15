# Football Quant OS - File Version Audit & Cleanup Plan
## Generated: 2026-06-14 00:03
## Auditor: Naga Core v5.0

---

## Executive Summary

| Category | Count | Action |
|----------|-------|--------|
| Versioned Files | 124 | KEEP |
| Unversioned Files | 38 | REVIEW |
| **→ Marked DELETE** | 31 | Delete |
| **→ Marked REVIEW** | 4 | Manual review |
| **→ Marked KEEP** | 3 | Keep |
| **→ Marked ARCHIVE** | 0 | Archive |

---

## 1. Files Marked DELETE (Safe to Remove)

> These files are temporary scripts, test files, or empty files with no imports and no version history.

| File | Lines | Functions | Classes | Reason |
|------|-------|-----------|---------|--------|
| `fix_intelligence_method.py` | 85 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `fix_intelligence_method2.py` | 87 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `fix_method_final.py` | 80 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `test_chinese_intelligence.py` | 25 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `test_chinese_intelligence_file.py` | 36 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `test_full_pipeline.py` | 48 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `test_hub_chinese.py` | 35 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `test_sina_scrape.py` | 61 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `test_sina_scrape2.py` | 38 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `agents\fifa_official_coaches.py` | 2 | 0 | 0 | Empty or near-empty file |
| `agents\fifa_test.py` | 1 | 0 | 0 | Empty or near-empty file |
| `agents\test_fifa.py` | 1 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\analyze_500_multi.py` | 184 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\analyze_bundesliga_batch.py` | 116 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\analyze_fio_betis.py` | 31 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\analyze_inter_barca.py` | 31 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\analyze_next_day_batch.py` | 103 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\analyze_psg_arsenal.py` | 30 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\analyze_psg_arsenal_500.py` | 51 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\check_fixtures.py` | 9 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\extract_touzhu.py` | 13 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\fetch_arsenal_psg.py` | 33 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\fetch_full_odds.py` | 52 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\fix_fifa_coaches.py` | 34 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\get_real_odds.py` | 45 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\list_all_today.py` | 14 | 0 | 0 | No functions or classes - likely data/config file |
| `scripts\predict_fio_laz.py` | 105 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\predict_full.py` | 98 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\search_fio_betis.py` | 96 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\test_bridge.py` | 15 | 0 | 0 | Temporary script - no imports, no version, likely one-time use |
| `scripts\_trash_20260613\predict_qatar_swiss_final.py` | 167 | 1 | 0 | Temporary script - no imports, no version, likely one-time use |

### DELETE Commands (Copy-Paste Ready)

```powershell
# Run from football_quant_os directory
Remove-Item 'fix_intelligence_method.py' -Force
Remove-Item 'fix_intelligence_method2.py' -Force
Remove-Item 'fix_method_final.py' -Force
Remove-Item 'test_chinese_intelligence.py' -Force
Remove-Item 'test_chinese_intelligence_file.py' -Force
Remove-Item 'test_full_pipeline.py' -Force
Remove-Item 'test_hub_chinese.py' -Force
Remove-Item 'test_sina_scrape.py' -Force
Remove-Item 'test_sina_scrape2.py' -Force
Remove-Item 'agents\fifa_official_coaches.py' -Force
Remove-Item 'agents\fifa_test.py' -Force
Remove-Item 'agents\test_fifa.py' -Force
Remove-Item 'scripts\analyze_500_multi.py' -Force
Remove-Item 'scripts\analyze_bundesliga_batch.py' -Force
Remove-Item 'scripts\analyze_fio_betis.py' -Force
Remove-Item 'scripts\analyze_inter_barca.py' -Force
Remove-Item 'scripts\analyze_next_day_batch.py' -Force
Remove-Item 'scripts\analyze_psg_arsenal.py' -Force
Remove-Item 'scripts\analyze_psg_arsenal_500.py' -Force
Remove-Item 'scripts\check_fixtures.py' -Force
Remove-Item 'scripts\extract_touzhu.py' -Force
Remove-Item 'scripts\fetch_arsenal_psg.py' -Force
Remove-Item 'scripts\fetch_full_odds.py' -Force
Remove-Item 'scripts\fix_fifa_coaches.py' -Force
Remove-Item 'scripts\get_real_odds.py' -Force
Remove-Item 'scripts\list_all_today.py' -Force
Remove-Item 'scripts\predict_fio_laz.py' -Force
Remove-Item 'scripts\predict_full.py' -Force
Remove-Item 'scripts\search_fio_betis.py' -Force
Remove-Item 'scripts\test_bridge.py' -Force
Remove-Item 'scripts\_trash_20260613\predict_qatar_swiss_final.py' -Force
```

---

## 2. Files Marked REVIEW (Needs Manual Decision)

> These files have no version, no docstring, and are not imported by other files. They may be valuable one-off scripts or dead code.

| File | Lines | Functions | Classes | Importers | Reason |
|------|-------|-----------|---------|-----------|--------|
| `scripts\backtest_2022_hybrid.py` | 341 | 13 | 2 | 0 | No version, no docstring, no imports - needs manual review |
| `scripts\backtest_2022_loose.py` | 328 | 13 | 2 | 0 | No version, no docstring, no imports - needs manual review |
| `scripts\fa_cup_final_odds.py` | 100 | 0 | 0 | 0 | No version, no docstring, no imports - needs manual review |
| `scripts\run_match_mun_lee.py` | 71 | 0 | 0 | 0 | No version, no docstring, no imports - needs manual review |

### Review Checklist

For each REVIEW file, check:
- [ ] Is this script still used by any workflow?
- [ ] Does it contain valuable logic that should be moved to a core module?
- [ ] Is it a duplicate of another script?
- [ ] Can it be merged into an existing module?

---

## 3. Files Marked KEEP (Required by System)

> These files are either imported by other modules, core infrastructure, or have clear purpose.

| File | Lines | Functions | Classes | Importers | Reason |
|------|-------|-----------|---------|-----------|--------|
| `test_odds_api.py` | 48 | 0 | 0 | 1 | Imported by 1 file(s): scripts\odds_api.py |
| `reports\gen_pdf.py` | 141 | 0 | 0 | 1 | Imported by 1 file(s): scripts\file_version_audit.py |
| `scripts\search_fa_cup.py` | 64 | 0 | 0 | 1 | Imported by 1 file(s): scripts\search_500_fa_cup.py |

---

## 4. Versioned Files (Reference)

> These files have explicit version markers and are considered maintained.

| File | Version Marker | Docstring |
|------|---------------|-----------|
| `agents\analyst_v2.py` | Yes | Yes |
| `agents\chinese_sports_fetcher.py` | Yes | Yes |
| `agents\coach_data_sync.py` | Yes | Yes |
| `agents\coach_factor.py` | Yes | Yes |
| `agents\coach_factor_bridge.py` | Yes | Yes |
| `agents\coach_types.py` | No | Yes |
| `agents\committee_v2.py` | Yes | Yes |
| `agents\datascout_v2.py` | Yes | Yes |
| `agents\free_intelligence_sources.py` | Yes | Yes |
| `agents\gene_engine.py` | Yes | Yes |
| `agents\intelligence.py` | Yes | Yes |
| `agents\multi_market_predictor.py` | Yes | Yes |
| `agents\odds_pricing.py` | Yes | Yes |
| `agents\risk_control.py` | Yes | Yes |
| `agents\risk_control_v2.py` | Yes | Yes |
| `agents\risk_guardian.py` | Yes | Yes |
| `agents\test_coaches.py` | No | Yes |
| `agents\trading.py` | Yes | Yes |
| `agents\treasury.py` | Yes | Yes |
| `agents\upset_detector.py` | Yes | Yes |
| `agents\worldcup_2026_full_coaches.py` | Yes | Yes |
| `agents\worldcup_analyst.py` | Yes | Yes |
| `agents\worldcup_data_engineer.py` | Yes | Yes |
| `app\api.py` | Yes | Yes |
| `app\auth.py` | No | Yes |
| `app\main.py` | Yes | Yes |
| `app\tasks.py` | Yes | Yes |
| `app\worldcup_api.py` | Yes | Yes |
| `backtest\engine.py` | Yes | Yes |
| `core\agent_pool.py` | Yes | Yes |
| `core\config.py` | Yes | Yes |
| `core\config_loader.py` | Yes | Yes |
| `core\event_bus.py` | Yes | Yes |
| `core\logger.py` | No | Yes |
| `core\odds_client.py` | Yes | Yes |
| `core\redis_cache.py` | Yes | Yes |
| `core\scheduler.py` | Yes | Yes |
| `core\worldcup_integrator.py` | Yes | Yes |
| `data\worldcup2026_data.py` | Yes | Yes |
| `data\worldcup_fixtures.py` | Yes | Yes |
| `data\worldcup_format.py` | Yes | Yes |
| `fixtures\__init__.py` | Yes | Yes |
| `fixtures\espn_client.py` | Yes | Yes |
| `fixtures\models.py` | Yes | Yes |
| `models\historical_odds.py` | Yes | Yes |
| `models\kelly.py` | No | Yes |
| `models\matrix_108.py` | Yes | Yes |
| `reports\generate_pdf_report.py` | Yes | Yes |
| `scripts\_trash_20260613\generate_final_v3.py` | Yes | Yes |
| `scripts\_trash_20260613\generate_pdf_report.py` | Yes | Yes |
| `scripts\_trash_20260613\generate_revised_pdf.py` | Yes | No |
| `scripts\_trash_20260613\predict_qatar_swiss_real.py` | Yes | No |
| `scripts\analyze_500_prediction.py` | Yes | Yes |
| `scripts\analyze_bayern_psg.py` | Yes | No |
| `scripts\analyze_can_bih.py` | Yes | Yes |
| `scripts\analyze_chelsea_manutd.py` | Yes | Yes |
| `scripts\analyze_chn_cze.py` | Yes | Yes |
| `scripts\analyze_chn_cze_full.py` | Yes | Yes |
| `scripts\analyze_kor_cze_full.py` | Yes | Yes |
| `scripts\analyze_kor_cze_oddsportal.py` | Yes | Yes |
| `scripts\analyze_roma_atalanta.py` | Yes | Yes |
| `scripts\analyze_usa_par.py` | Yes | Yes |
| `scripts\audit_system.py` | Yes | Yes |
| `scripts\backtest_2022.py` | Yes | Yes |
| `scripts\backtest_2022_fullsystem.py` | Yes | Yes |
| `scripts\backtest_2022_v2.py` | No | Yes |
| `scripts\check_fixtures_date.py` | Yes | No |
| `scripts\check_response.py` | No | Yes |
| `scripts\coach_factor_report.py` | Yes | No |
| `scripts\complete_prediction_usa_par.py` | Yes | Yes |
| `scripts\core_conclusion_proof.py` | No | Yes |
| `scripts\dashboard.py` | Yes | No |
| `scripts\debug_api.py` | No | Yes |
| `scripts\demo_coach_factor_integration.py` | Yes | Yes |
| `scripts\demo_intelligence.py` | No | Yes |
| `scripts\demo_p0_agents.py` | Yes | Yes |
| `scripts\demo_p0_agents_v1.1.py` | Yes | Yes |
| `scripts\demo_refresh.py` | No | Yes |
| `scripts\demo_upset_detector.py` | Yes | No |
| `scripts\file_version_audit.py` | Yes | Yes |
| `scripts\fix_exceptions.py` | Yes | Yes |
| `scripts\football_data_api.py` | Yes | Yes |
| `scripts\full_audit.py` | Yes | No |
| `scripts\full_prediction_v3.py` | Yes | Yes |
| `scripts\generate_corrected_report.py` | Yes | No |
| `scripts\generate_p0_pdf_report.py` | Yes | Yes |
| `scripts\generate_pdf_can_bih.py` | Yes | Yes |
| `scripts\generate_pdf_usa_par.py` | Yes | Yes |
| `scripts\list_today_matches.py` | Yes | No |
| `scripts\mckinsey_pdf_report.py` | Yes | Yes |
| `scripts\mckinsey_pdf_report_cn.py` | Yes | Yes |
| `scripts\naga_integration.py` | Yes | Yes |
| `scripts\odds_api.py` | Yes | Yes |
| `scripts\predict_bayern_psg.py` | Yes | Yes |
| `scripts\refresh_coaches.py` | Yes | Yes |
| `scripts\research_espn_deep.py` | No | Yes |
| `scripts\research_fixtures.py` | No | Yes |
| `scripts\run_fio_laz.py` | Yes | No |
| `scripts\run_match_real_data.py` | Yes | No |
| `scripts\scrape_500.py` | No | Yes |
| `scripts\scrape_500_fa_cup.py` | No | Yes |
| `scripts\scrape_500_multi_usa_par.py` | No | Yes |
| `scripts\scrape_500_simple.py` | No | Yes |
| `scripts\scrape_oddsportal.py` | No | Yes |
| `scripts\search_500_fa_cup.py` | No | Yes |
| `scripts\six_dimension_report_usa_par.py` | Yes | Yes |
| `scripts\test_500_can_bih.py` | No | Yes |
| `scripts\test_500_touzhu.py` | No | Yes |
| `scripts\test_datascout_usa_par.py` | Yes | No |
| `scripts\test_fixtures.py` | Yes | Yes |
| `scripts\test_historical_odds.py` | Yes | Yes |
| `scripts\test_integration.py` | Yes | Yes |
| `scripts\test_integration_v2.py` | Yes | Yes |
| `scripts\upset_detector_can_bih.py` | Yes | No |
| `scripts\upset_detector_usa_par.py` | Yes | No |
| `scripts\upset_detector_usa_par_en.py` | Yes | No |
| `scripts\upset_detector_usa_par_updated.py` | Yes | No |
| `scripts\verify_actual_data.py` | Yes | Yes |
| `scripts\verify_probability_chain.py` | Yes | Yes |
| `scripts\wc2026_day1_comparison.py` | Yes | No |
| `scripts\workflow_demo.py` | Yes | Yes |
| `scripts\worldcup_main.py` | Yes | Yes |
| `test_chinese_output.py` | Yes | No |
| `tests\test_core.py` | Yes | Yes |

---

## 5. Cleanup Script

```powershell
# Safe delete (moves to _archive_20260614 instead of deleting)
$archive = '_archive_20260614'
New-Item -ItemType Directory -Force -Path $archive

Copy-Item 'fix_intelligence_method.py' $archive/ 2>$null; Remove-Item 'fix_intelligence_method.py' -Force
Copy-Item 'fix_intelligence_method2.py' $archive/ 2>$null; Remove-Item 'fix_intelligence_method2.py' -Force
Copy-Item 'fix_method_final.py' $archive/ 2>$null; Remove-Item 'fix_method_final.py' -Force
Copy-Item 'test_chinese_intelligence.py' $archive/ 2>$null; Remove-Item 'test_chinese_intelligence.py' -Force
Copy-Item 'test_chinese_intelligence_file.py' $archive/ 2>$null; Remove-Item 'test_chinese_intelligence_file.py' -Force
Copy-Item 'test_full_pipeline.py' $archive/ 2>$null; Remove-Item 'test_full_pipeline.py' -Force
Copy-Item 'test_hub_chinese.py' $archive/ 2>$null; Remove-Item 'test_hub_chinese.py' -Force
Copy-Item 'test_sina_scrape.py' $archive/ 2>$null; Remove-Item 'test_sina_scrape.py' -Force
Copy-Item 'test_sina_scrape2.py' $archive/ 2>$null; Remove-Item 'test_sina_scrape2.py' -Force
Copy-Item 'agents\fifa_official_coaches.py' $archive/ 2>$null; Remove-Item 'agents\fifa_official_coaches.py' -Force
Copy-Item 'agents\fifa_test.py' $archive/ 2>$null; Remove-Item 'agents\fifa_test.py' -Force
Copy-Item 'agents\test_fifa.py' $archive/ 2>$null; Remove-Item 'agents\test_fifa.py' -Force
Copy-Item 'scripts\analyze_500_multi.py' $archive/ 2>$null; Remove-Item 'scripts\analyze_500_multi.py' -Force
Copy-Item 'scripts\analyze_bundesliga_batch.py' $archive/ 2>$null; Remove-Item 'scripts\analyze_bundesliga_batch.py' -Force
Copy-Item 'scripts\analyze_fio_betis.py' $archive/ 2>$null; Remove-Item 'scripts\analyze_fio_betis.py' -Force
Copy-Item 'scripts\analyze_inter_barca.py' $archive/ 2>$null; Remove-Item 'scripts\analyze_inter_barca.py' -Force
Copy-Item 'scripts\analyze_next_day_batch.py' $archive/ 2>$null; Remove-Item 'scripts\analyze_next_day_batch.py' -Force
Copy-Item 'scripts\analyze_psg_arsenal.py' $archive/ 2>$null; Remove-Item 'scripts\analyze_psg_arsenal.py' -Force
Copy-Item 'scripts\analyze_psg_arsenal_500.py' $archive/ 2>$null; Remove-Item 'scripts\analyze_psg_arsenal_500.py' -Force
Copy-Item 'scripts\check_fixtures.py' $archive/ 2>$null; Remove-Item 'scripts\check_fixtures.py' -Force
Copy-Item 'scripts\extract_touzhu.py' $archive/ 2>$null; Remove-Item 'scripts\extract_touzhu.py' -Force
Copy-Item 'scripts\fetch_arsenal_psg.py' $archive/ 2>$null; Remove-Item 'scripts\fetch_arsenal_psg.py' -Force
Copy-Item 'scripts\fetch_full_odds.py' $archive/ 2>$null; Remove-Item 'scripts\fetch_full_odds.py' -Force
Copy-Item 'scripts\fix_fifa_coaches.py' $archive/ 2>$null; Remove-Item 'scripts\fix_fifa_coaches.py' -Force
Copy-Item 'scripts\get_real_odds.py' $archive/ 2>$null; Remove-Item 'scripts\get_real_odds.py' -Force
Copy-Item 'scripts\list_all_today.py' $archive/ 2>$null; Remove-Item 'scripts\list_all_today.py' -Force
Copy-Item 'scripts\predict_fio_laz.py' $archive/ 2>$null; Remove-Item 'scripts\predict_fio_laz.py' -Force
Copy-Item 'scripts\predict_full.py' $archive/ 2>$null; Remove-Item 'scripts\predict_full.py' -Force
Copy-Item 'scripts\search_fio_betis.py' $archive/ 2>$null; Remove-Item 'scripts\search_fio_betis.py' -Force
Copy-Item 'scripts\test_bridge.py' $archive/ 2>$null; Remove-Item 'scripts\test_bridge.py' -Force
Copy-Item 'scripts\_trash_20260613\predict_qatar_swiss_final.py' $archive/ 2>$null; Remove-Item 'scripts\_trash_20260613\predict_qatar_swiss_final.py' -Force
```

---

## 6. After Cleanup Stats

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Python Files | 162 | 131 | -31 |
| Lines of Code | 2819 | 1093 | -1726 |
| Unversioned Files | 38 | 7 | -31 |

---

## 7. Recommendations

### Immediate (This Week)
1. **Delete all DELETE-marked files** - Safe, no dependencies
2. **Review all REVIEW-marked files** - Decide keep/archive/delete
3. **Add version markers to all KEEP files** - Prevent future ambiguity

### Short Term (This Month)
4. **Consolidate duplicate scripts** - Many analyze_*.py may be similar
5. **Move reusable logic to core modules** - Scripts should be thin wrappers
6. **Add module-level docstrings** - All files should have documentation

### Long Term (Next Quarter)
7. **Implement semantic versioning** - All modules should have __version__
8. **Add deprecation warnings** - For transitional scripts
9. **Create script inventory** - Document what each script does

---

*File Version Audit | Football Quant OS v4.2.1-naga | {datetime.now().strftime('%Y-%m-%d %H:%M')}*
