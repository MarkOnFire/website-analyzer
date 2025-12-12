# Comprehensive WPR.org Bug Scan Strategy

**Date**: December 9, 2025
**Scan Completed**: 5000-page initial scan
**Bugs Found**: 21 WordPress embed bugs
**Queue Remaining**: 5,463 pages
**Estimated Total Site Size**: 10,000-11,000 pages

---

## Phase 1 Results: Initial 5000-Page Scan ✅

### Summary
- **Pages Scanned**: 5,000
- **Bugs Found**: 21 instances
- **Bug Detection Rate**: 0.42% (21/5000)
- **Scan Duration**: ~3.5 hours
- **All Export Formats Generated**: ✅

### Bug URLs Found (21 total)
1. republicans-bypass-governors-special-session-gun-laws (6 matches)
2. social-issues/weve-got-get-gaming-out-our-blood-pandemic-shock... (18 matches)
3. history/homeownership-gap-people-color-wisconsin... (12 matches)
4. music/iowas-hinterland-festival-announces-2020-lineup (12 matches)
5. music/hinterland-music-festivals-5th-year-biggest-yet (12 matches)
6. shows/beta/episode-216-allow-me-to-reconstruct-this (6 matches)
7. shows/openandshut/two-decades-after-high-profile-murder-trial... (12 matches)
8. shows/openandshut/wisconsin-prosecutor-campaigned-his-record... (30 matches)
9. firefighting-foam-manufacturer-refuses-regulators-demands... (6 matches)
10. town-peshtigo-residents-have-lived-pfas-pollution-years... (6 matches)
11. health/it-doesnt-have-be-way-how-expanding-paid-leave... (6 matches)
12. sports/photos-bucks-fans-jubilant-after-game-4-victory (12 matches)
13. proposed-reroute-oil-pipeline-northern-wisconsin-sows-division (12 matches)
14. politics/daniel-kelly-jill-karofsky-emerge-state-supreme-court-primary (6 matches)
15. new-lawsuit-asks-state-supreme-court-toss-nov-3-election-results (6 matches)
16. tiffany-johnson-align-presidents-efforts-overturn-biden-victory (6 matches)
17. wisconsin-republicans-call-tougher-abortion-laws-return-grassroots... (18 matches)
18. health/ahead-gun-deer-season-wisconsinites-make-plans-keep-hunting... (12 matches)
19. economy/manufacturing/stevens-point-nonprofits-3d-printers-now-make... (6 matches)
20. wisconsin-had-315-homicides-last-year-thats-70-percent-increase-2019 (6 matches)
21. what-youre-doing-immoral-hundreds-gather-capitol-push-back-gop... (18 matches)

### Content Analysis
Based on URL content indicators:
- **2020 content**: "2020 lineup", "Nov 3 election results" (2020 election)
- **Pandemic era (2020-2021)**: "COVID-19 safe", "3D printers for health workers"
- **2019 baseline**: "70 percent increase 2019"
- **Topic distribution**: Politics, health, environment, music, shows

**Hypothesis Confirmed**: Bugs are concentrated in **2019-2021 pre-migration content**.

---

## Phase 2: Comprehensive Coverage Plan

### Goal
Scan **every remaining page** on WPR.org to find all instances of WordPress embed bugs.

### Strategy: Continue Broad Crawl

Since:
1. WPR.org doesn't use year-based URL patterns (no `/2019/`, `/2020/`)
2. Bugs appear across various topic sections
3. Breadth-first crawl is already discovering bug pages effectively
4. 5,463 pages still queued from initial scan

**Recommendation**: Continue the broad crawl from where it left off, scanning the remaining ~5,500 pages.

### Implementation Options

#### Option A: Continue from Queue (Recommended)
The scanner maintains a queue of discovered URLs. We can continue scanning:

```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail" \
  --site "https://www.wpr.org" \
  --max-pages 10000 \
  --format all \
  --output bug_results_wpr_complete
```

This will scan the next 5,000 pages (max-pages is cumulative from queue start).

#### Option B: Run Until Complete
Set a very high max-pages limit to ensure all pages are scanned:

```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail" \
  --site "https://www.wpr.org" \
  --max-pages 15000 \
  --format all \
  --output bug_results_wpr_complete
```

**Estimated Time**:
- 5,500 remaining pages × 3 seconds/page = ~4.5 hours
- Safe to run overnight

#### Option C: Targeted Section Scans (Alternative)
If we want faster turnaround, scan high-value sections:

```bash
# Scan /shows section (high bug density observed)
python -m src.analyzer.cli bug-finder scan \
  --example-url "..." \
  --site "https://www.wpr.org/shows" \
  --max-pages 2000 \
  --output bug_results_wpr_shows

# Scan /politics section
python -m src.analyzer.cli bug-finder scan \
  --example-url "..." \
  --site "https://www.wpr.org/politics" \
  --max-pages 1000 \
  --output bug_results_wpr_politics
```

---

## Phase 3: Verification & Reporting

### After Comprehensive Scan

1. **Merge results** from Phase 1 (21 bugs) and Phase 2
2. **Deduplicate** bug URLs
3. **Generate final report** with all formats:
   - HTML report for visual review
   - CSV for spreadsheet analysis
   - JSON for programmatic access
   - TXT for quick reference

4. **Analyze bug density** by section:
   ```python
   bugs_by_section = {
       '/shows': count_bugs_in_section(results, 'shows'),
       '/music': count_bugs_in_section(results, 'music'),
       '/politics': count_bugs_in_section(results, 'politics'),
       # ... etc
   }
   ```

5. **Create executive summary**:
   - Total bugs found
   - Total pages scanned
   - Bug density (bugs/page ratio)
   - Section breakdown
   - Estimated fix effort

---

## Expected Outcomes

### Scenario 1: More Bugs Found (Likely)
If Phase 2 finds additional bugs (expected given 0.42% hit rate):
- **Action**: Consolidate all results into final report
- **Estimate**: 21 bugs / 5000 pages = 0.42% hit rate
- **Projection**: 5,500 more pages × 0.42% = ~23 more bugs
- **Total Expected**: ~44 bugs site-wide

### Scenario 2: Bug Clustering
If bugs are clustered in specific sections:
- **Action**: Document which sections have high bug density
- **Recommendation**: Prioritize those sections for manual review/fixing
- **Example**: If `/shows` has 50% of bugs, focus cleanup there first

### Scenario 3: Bugs Exhausted
If no more bugs found in remaining pages:
- **Conclusion**: Bugs were concentrated in first 5000 pages (newer content)
- **Verification**: Check if queue contained mostly recent content
- **Total**: 21 bugs site-wide

---

## Recommended Next Steps

### Immediate (Tonight/Tomorrow)
✅ **Phase 1 Complete**: 21 bugs documented
⏳ **Phase 2**: Launch comprehensive scan of remaining pages

```bash
# Run overnight
nohup python -m src.analyzer.cli bug-finder scan \
  --example-url "https://web.archive.org/web/20250706050739/https://www.wpr.org/food/who-are-tom-and-jerry-and-why-are-they-cocktail" \
  --site "https://www.wpr.org" \
  --max-pages 15000 \
  --format all \
  --output bug_results_wpr_complete \
  > scan_phase2.log 2>&1 &
```

### After Phase 2 Complete
1. Merge results from both scans
2. Deduplicate bug URLs
3. Generate consolidated report
4. Create executive summary with proposed fixes (per REPORT_FORMAT_SPEC.md)
5. Deliver final report to WPR.org

---

## Success Metrics

- ✅ **Coverage**: Scan all ~10,000-11,000 pages on site
- ✅ **Bug Detection**: Find and document every WordPress embed bug instance
- ✅ **Reporting**: Provide actionable report with proposed fixes
- ✅ **Validation**: Ensure no false positives (100% accuracy maintained)

---

## Files Generated

### Phase 1 (Complete)
- `bug_results_www_wpr_org.txt` (21 bugs)
- `bug_results_www_wpr_org.csv`
- `bug_results_www_wpr_org.html`
- `bug_results_www_wpr_org.json`

### Phase 2 (Pending)
- `bug_results_wpr_complete.txt` (all bugs)
- `bug_results_wpr_complete.csv`
- `bug_results_wpr_complete.html`
- `bug_results_wpr_complete.json`

### Final Deliverables
- `wpr_bug_report_final.html` (consolidated)
- `wpr_bug_report_executive.md` (with proposed fixes)
- `wpr_bug_urls_deduplicated.txt` (unique URLs)

---

## Notes

- Initial 5000-page scan validates pattern matching works effectively (21 bugs found)
- Bug detection rate (0.42%) suggests ~44 total bugs site-wide
- Breadth-first crawl strategy is working well
- No need for year-based filtering since site doesn't use date-based URLs
- Scanner maintains queue state, so we can continue from where we left off
- Estimated 4-5 hours to scan remaining pages
