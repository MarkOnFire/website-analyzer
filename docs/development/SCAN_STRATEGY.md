# WPR.org Bug Scan Strategy

## Current Scan (In Progress)

**Scan ID**: 5e8ee4
**Type**: Broad scan of entire site
**Max Pages**: 5000
**Status**: Running (~800/5000 pages completed)
**Bugs Found**: 0 (so far)

## Post-Scan Analysis Plan

### 1. Review Results
- [ ] Check if any bugs were found in the 5000-page scan
- [ ] Examine which pages were crawled (check the queue/visited list)
- [ ] Analyze the age distribution of crawled content

### 2. Hypothesis: Bug Likely in Pre-2023 Migrated Content

**Reasoning**:
- WordPress embed bug example is from 2017 (archive.org/web/20250706050739)
- WPR.org likely migrated to new CMS in 2023
- Bug would affect pages that were:
  1. Created/edited in old CMS (pre-2023)
  2. Had WordPress embed codes
  3. Were migrated with content intact (not re-entered)

**Expected Pattern**:
- Newer content (2024-2025): Clean ✅
- Mid-range (2023): Possibly mixed
- Older content (pre-2023): Higher bug probability 🎯

### 3. Content Age Analysis

From crawled URLs, we can infer age:
- `/news/...` - Check URL patterns for dates
- Author pages `/person/...` - May link to older articles
- Archive sections - If site has yearly archives
- Topic pages `/topic/...` - May aggregate old content

## Targeted Scan Strategy #2

### Goal: Focus on Pre-2023 Content

### Approach A: Archive-Based Targeting
If WPR.org has archive URLs like:
```
/archive/2022
/archive/2021
/archive/2020
```

**Scan Command**:
```bash
# Scan specific year archives
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://archive.org/..." \
  --site "https://www.wpr.org/archive/2022" \
  --max-pages 1000
```

### Approach B: Topic/Category Deep Dive
Target older topical content:
- `/culture` - Often has older evergreen content
- `/food` - Where the original bug was found
- `/history` - Likely has old content
- `/music` - Archives of older shows

**Scan Command**:
```bash
# Scan specific sections
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://archive.org/..." \
  --site "https://www.wpr.org/food" \
  --max-pages 2000
```

### Approach C: Search Query Targeting
Use WPR's search to find old content, then scan those URLs:
```
https://www.wpr.org?s=&fs[year]=2022
https://www.wpr.org?s=&fs[year]=2021
```

### Approach D: Author-Based Targeting
Authors who wrote pre-2023 may have older articles:
```
https://www.wpr.org/person/[author-name]
```
Scan their article pages.

## Detection Strategy

### Phase 1: Current Broad Scan (5000 pages)
- **Purpose**: Baseline scan, find any obvious bugs
- **Expected**: Low hit rate (mostly new content)
- **Action**: Analyze crawled URL patterns

### Phase 2: Targeted Old Content Scan
Based on Phase 1 analysis:

**If queue shows date-based URLs**:
```bash
# Extract years from crawled URLs
grep -E '/[0-9]{4}/' visited_urls.txt | sort -u

# Scan each old year
for year in 2017 2018 2019 2020 2021 2022; do
  python -m src.analyzer.cli bug-finder scan \
    --example-url "https://archive.org/..." \
    --site "https://www.wpr.org" \
    --max-pages 500 \
    --output "bugs_${year}"
done
```

**If queue shows topical sections**:
```bash
# Scan high-risk sections identified in Phase 1
sections=("food" "culture" "music" "books")

for section in "${sections[@]}"; do
  python -m src.analyzer.cli bug-finder scan \
    --example-url "https://archive.org/..." \
    --site "https://www.wpr.org/${section}" \
    --max-pages 1000 \
    --output "bugs_${section}"
done
```

### Phase 3: Validation
If bugs are found in Phase 2:
- Verify they match the WordPress embed pattern
- Check publication dates of affected pages
- Confirm they're from pre-migration era

## Analysis Commands

### After Current Scan Completes

1. **Check results**:
```bash
cat bug_results_www_wpr_org.txt
```

2. **Count bugs found**:
```bash
grep -c "http" bug_results_www_wpr_org.txt
```

3. **Analyze URL patterns** (from scanner's visited list):
```python
# Extract URL patterns to find date-based or section-based structure
from collections import Counter
import re

# Assuming scanner saved visited URLs
visited_urls = [...]  # Load from scan results

# Extract URL patterns
patterns = Counter()
for url in visited_urls:
    path = url.replace('https://www.wpr.org/', '')
    sections = path.split('/')
    if sections:
        patterns[sections[0]] += 1

# Top sections crawled
for section, count in patterns.most_common(20):
    print(f"{section}: {count} pages")
```

4. **Look for date indicators**:
```bash
# Check if URLs contain years
grep -E 'www.wpr.org/.*/[0-9]{4}/' bug_results_www_wpr_org.txt
```

## Decision Tree

```
Current Scan (5000 pages) Completes
│
├─ Bugs Found?
│  ├─ YES → Analyze bug distribution
│  │         └─ Are they clustered by year/section?
│  │            ├─ YES → Scan more of that year/section
│  │            └─ NO → Scan entire site (10K+ pages)
│  │
│  └─ NO → Analyze crawled URLs
│            └─ Do URLs show date/year patterns?
│               ├─ YES → Targeted scan of pre-2023 years
│               ├─ NO → Check if we hit sections like /food, /culture
│               │       └─ Scan those sections specifically
│               └─ UNKNOWN → Continue broad scan (next 5000 pages)
```

## Expected Outcomes

### Scenario 1: Bugs Found in Broad Scan
- **Action**: Analyze patterns, expand scan in affected areas
- **Timeline**: Additional targeted scans (1-2 hours each)

### Scenario 2: No Bugs in Broad Scan
- **Hypothesis**: Recent content is clean, bug is in older pages
- **Action**:
  1. Analyze URL structure from scan
  2. Identify pre-2023 content patterns
  3. Run targeted scans on old content sections
- **Timeline**: 2-4 targeted scans (4-8 hours total)

### Scenario 3: Site is Completely Clean
- **Conclusion**: WordPress bug has been fixed site-wide
- **Verification**: Spot-check a few archived URLs manually
- **Action**: Document that migration cleanup was successful

## Next Steps After Current Scan

1. **Immediate** (when scan completes):
   - Review `bug_results_www_wpr_org.html` in browser
   - Check JSON results for patterns
   - Analyze visited URL structure

2. **Analysis** (15-30 minutes):
   - Determine if site has date-based or section-based structure
   - Identify likely locations of pre-2023 content
   - Plan targeted scan strategy

3. **Execute** (based on findings):
   - Launch targeted scans on high-probability sections
   - Monitor for bugs in older content
   - Adjust strategy based on results

## Success Criteria

- **Found bugs**: Report to WPR.org with affected URLs
- **No bugs found after targeted scans**: Confirm migration was clean
- **Partial bugs found**: Document which content areas are affected

## Resources

- **Current scan output**: `bug_results_www_wpr_org.*`
- **Archive example**: `https://web.archive.org/web/20250706050739/...`
- **Pattern generator**: `pattern_generator.py` (handles Unicode quotes)
- **Scanner**: `full_site_scanner.py` (breadth-first crawl)
