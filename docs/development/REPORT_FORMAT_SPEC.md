# Bug Finder Report Format Specification

## Overview

The bug finder should generate comprehensive reports that include not just bug locations, but also:
- Root cause analysis
- Proposed fixes
- Impact assessment
- Priority recommendations

## Report Structure

### 1. Executive Summary
- Total bugs found
- Severity classification
- Overall impact assessment
- Recommended action timeline

### 2. Bug Categories
Each bug type gets its own section with:
- **Description**: What the bug is
- **Root Cause**: Why it's happening
- **Affected Pages**: List with severity scores
- **Proposed Fix**: Specific code/CSS changes
- **Implementation Effort**: Time estimate
- **Priority**: Critical/High/Medium/Low

### 3. Detailed Findings

For each bug instance:

```markdown
## Bug #1: WordPress Embed Code Visible

**Type**: Content Rendering
**Severity**: High
**Pages Affected**: 12 pages
**First Detected**: 2025-12-08

### Description
WordPress embed codes are displaying as raw JSON instead of rendered media embeds.

### Example
**URL**: https://www.wpr.org/food/example-page
**Pattern**: [[{"fid":"1101026″,"view_mode":"full_width",...}}]]

### Root Cause
Content was migrated from old CMS (pre-2023) with WordPress shortcodes that are
no longer processed by the current theme. The double-bracket syntax [[...]] is not
recognized by the new rendering engine.

### Affected URLs
1. https://www.wpr.org/food/page-1 (18 instances)
2. https://www.wpr.org/culture/page-2 (12 instances)
... (see full list in CSV export)

### Proposed Fix

**Option 1: Database Migration** (Recommended)
```sql
-- Find and replace embed codes with proper shortcodes
UPDATE wp_posts
SET post_content = REPLACE(
  post_content,
  '[[{"fid"',
  '[embed id="'
)
WHERE post_content LIKE '%[[{"fid"%';
```

**Option 2: Theme Filter**
```php
// Add to functions.php
add_filter('the_content', 'fix_legacy_embeds', 10);

function fix_legacy_embeds($content) {
    // Parse [[{...}]] patterns
    $pattern = '/\[\[\{.*?"fid":"(\d+)".*?\}\]\]/';
    $content = preg_replace_callback($pattern, function($matches) {
        $fid = $matches[1];
        return do_shortcode("[embed id=\"{$fid}\"]");
    }, $content);
    return $content;
}
```

**Option 3: Manual Review**
For the 12 affected pages, manually re-embed the media using the current
WordPress media library.

### Implementation Effort
- **Option 1**: 2-4 hours (includes testing)
- **Option 2**: 1-2 hours (includes testing)
- **Option 3**: 4-6 hours (12 pages × 20-30 min each)

### Priority
**High** - Visual bug visible to all users, impacts content readability

### Testing Plan
1. Apply fix to staging environment
2. Test affected pages render correctly
3. Verify media embeds are responsive
4. Check no other content is affected
5. Deploy to production during low-traffic window
```

---

## Bug #2: Footer Social Links Showing Bullets

**Type**: CSS Styling
**Severity**: Low
**Pages Affected**: Site-wide (all pages)
**First Detected**: 2025-12-08

### Description
Social media icons in footer display with list bullets next to them.

### Root Cause
Recent popup/modal implementation introduced global CSS reset that overrides
WordPress block library styles. The `.wp-block-social-links` class loses its
`list-style: none` property.

### Proposed Fix

**Option 1: Add Specific CSS Override** (Recommended)
```css
/* Add to theme CSS or custom.css */
.site-footer-info__social-links,
.wp-block-social-links {
  list-style: none !important;
  list-style-type: none !important;
  padding-left: 0 !important;
  margin-left: 0 !important;
}

.wp-block-social-links li {
  list-style: none !important;
}
```

**Option 2: Review Popup CSS**
Audit the popup/modal CSS to ensure it doesn't apply global resets:
```css
/* AVOID this in popup CSS */
ul {
  list-style: disc; /* Too broad! */
}

/* PREFER this */
.popup-content ul {
  list-style: disc; /* Scoped to popup only */
}
```

### Implementation Effort
- **Option 1**: 15 minutes (add CSS, test)
- **Option 2**: 1-2 hours (audit and refactor popup CSS)

### Priority
**Low** - Cosmetic issue, doesn't break functionality

### Verification
- Check footer on multiple pages
- Verify social icons render correctly
- Test across browsers (Chrome, Firefox, Safari, Edge)
```

---

## Export Format Enhancements

### Current Formats
- ✅ TXT: Plain text list
- ✅ CSV: Spreadsheet-ready
- ✅ HTML: Visual report
- ✅ JSON: Machine-readable

### Proposed New Format: Executive Report (PDF/HTML)

**Structure**:
```
┌─────────────────────────────────────┐
│   Bug Analysis Report               │
│   WPR.org - December 8, 2025        │
└─────────────────────────────────────┘

Executive Summary
─────────────────
✓ Pages Scanned: 5,000
✓ Bugs Found: 12 instances (2 types)
✓ Critical: 0 | High: 1 | Medium: 0 | Low: 1

Priority Actions
────────────────
1. [HIGH] Fix WordPress embed codes (12 pages)
   → Est. 2-4 hours | Affects content readability

2. [LOW] Fix footer social bullets (site-wide)
   → Est. 15 minutes | Cosmetic only

Detailed Findings
─────────────────
[Full bug details with proposed fixes...]

Appendix
────────
A. Affected URL List
B. Code Samples
C. Testing Checklist
```

### Implementation Plan

**Phase 1: Enhanced Bug Detection**
```python
class BugReport:
    def __init__(self, bug_type, severity, urls, root_cause):
        self.bug_type = bug_type
        self.severity = severity  # critical, high, medium, low
        self.urls = urls
        self.root_cause = root_cause
        self.proposed_fixes = []
        self.implementation_effort = None
        self.priority = None

    def add_fix(self, option_name, description, code_sample, effort_hours):
        self.proposed_fixes.append({
            'name': option_name,
            'description': description,
            'code': code_sample,
            'effort_hours': effort_hours
        })

    def generate_markdown(self):
        # Generate detailed markdown report
        pass

    def generate_pdf(self):
        # Generate PDF with formatting
        pass
```

**Phase 2: Root Cause Analyzer**
```python
class RootCauseAnalyzer:
    """Analyze bug patterns to suggest likely root causes"""

    def analyze_wordpress_embeds(self, bug_text, url):
        """
        Detect WordPress embed bugs and provide context:
        - Migration era (pre-2023 content)
        - Shortcode patterns
        - Theme compatibility
        """
        pass

    def analyze_css_issues(self, html, css_files):
        """
        Detect CSS conflicts:
        - Missing styles
        - Override issues
        - Specificity problems
        """
        pass
```

**Phase 3: Fix Generator**
```python
class FixGenerator:
    """Generate code fixes for common bug types"""

    def generate_wordpress_embed_fix(self, fid_pattern):
        """Generate PHP filter or SQL migration"""
        return {
            'option_1_database': generate_sql_migration(),
            'option_2_filter': generate_php_filter(),
            'option_3_manual': generate_manual_steps()
        }

    def generate_css_fix(self, selector, property):
        """Generate CSS override with proper specificity"""
        return generate_css_override(selector, property)
```

## Report Templates

### Template 1: WordPress Migration Bugs
- Pattern: `[[{...}]]` in content
- Root Cause: Pre-2023 migration
- Fix: Database update or theme filter
- Priority: High (content readability)

### Template 2: CSS Styling Issues
- Pattern: Visual rendering problems
- Root Cause: CSS conflicts, missing styles
- Fix: CSS override with specificity
- Priority: Low-Medium (cosmetic)

### Template 3: JavaScript Errors
- Pattern: Broken functionality
- Root Cause: Script conflicts, missing dependencies
- Fix: Script update or conflict resolution
- Priority: High-Critical (functionality)

### Template 4: Accessibility Issues
- Pattern: Missing alt text, poor contrast, etc.
- Root Cause: Content entry or theme defaults
- Fix: Bulk update or template modification
- Priority: Medium-High (legal/UX)

## Implementation Checklist

**Bug Finder Enhancements**:
- [ ] Add severity classification to BugAnalysis
- [ ] Create RootCauseAnalyzer class
- [ ] Create FixGenerator class
- [ ] Add report templates
- [ ] Generate executive PDF/HTML report
- [ ] Include implementation effort estimates
- [ ] Add priority recommendations
- [ ] Create testing checklists

**Export Format Updates**:
- [ ] Enhanced HTML report with fixes section
- [ ] PDF generation (using ReportLab or similar)
- [ ] Executive summary at top of all reports
- [ ] Code samples with syntax highlighting
- [ ] Implementation effort estimates
- [ ] Priority matrix visualization

**CLI Updates**:
```bash
# Generate comprehensive report with fixes
python -m src.analyzer.cli bug-finder scan \
  --example-url "..." \
  --site "..." \
  --format executive \
  --include-fixes \
  --include-effort-estimates
```

## Success Metrics

**Report Quality**:
- ✅ Actionable fixes for each bug type
- ✅ Clear implementation steps
- ✅ Effort estimates (hours)
- ✅ Priority recommendations
- ✅ Testing checklists

**User Value**:
- ✅ Non-technical stakeholders understand impact
- ✅ Developers have clear implementation path
- ✅ Project managers can estimate timeline
- ✅ QA teams have testing plans

## Example Output

```bash
$ python -m src.analyzer.cli bug-finder scan ... --format executive

✓ Scan complete: 12 bugs found

📊 Executive Report Generated:
  - bug_report_executive.html (with fixes)
  - bug_report_executive.pdf (printable)
  - bug_fixes_code_samples.zip (implementation code)
  - testing_checklist.md (QA plan)

📋 Summary:
  HIGH priority: 1 bug (WordPress embeds) - 2-4 hours to fix
  LOW priority: 1 bug (Footer bullets) - 15 min to fix

  Total implementation effort: 2-4.25 hours
  Recommended order: Fix WordPress embeds first
```

## Notes

- This enhancement builds on existing export system
- Backwards compatible (current formats still work)
- Requires LLM integration for root cause analysis (optional)
- Can start with template-based fixes, expand to AI-generated later
- PDF generation is optional (HTML + print CSS works too)
