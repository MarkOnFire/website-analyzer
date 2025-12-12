# FixGenerator - Bug Fix Code Generator

## Overview

The `FixGenerator` class provides template-based generation of actionable code fixes for common CMS bugs detected by the website-analyzer tool. It generates multiple implementation approaches with pros/cons analysis and realistic effort estimates.

## Files

- **`bug_finder_fix_generator.py`** (570 lines) - Main implementation
- **`test_fix_generator.py`** - Comprehensive test suite
- **`integration_test_fix_generator.py`** - Real-world usage examples

## Features

### 1. WordPress Embed Code Fixes
Generates 3 fix options for malformed Drupal/WordPress embed codes appearing as JSON in visible text:

1. **Database Migration (SQL)** - 2-4 hours
   - Direct database replacement using SQL UPDATE
   - Permanent fix affecting all pages
   - Pros: Complete fix, no runtime overhead
   - Cons: Requires database access, needs backup, higher risk

2. **PHP Content Filter** - 1-2 hours (RECOMMENDED)
   - Uses WordPress filter hook to fix on-the-fly
   - No database changes needed
   - Pros: Safe, reversible, easy to test
   - Cons: Slight performance impact, display-only fix

3. **Manual Fix** - 5 min - 2 hours per 10 pages
   - Step-by-step instructions for manual post editing
   - Full control and verification
   - Pros: Zero risk, transparent
   - Cons: Not scalable for many pages

Example:
```python
generator = FixGenerator()
bug_pattern = '''[[{"fid":"1101026″,"view_mode":"full_width",...}]]'''
result = generator.generate_wordpress_embed_fix(bug_pattern)

# Returns dict with 3 options, including:
# - SQL with safe SELECT/UPDATE queries
# - PHP filter code ready to paste
# - Manual step-by-step instructions
```

### 2. CSS Rendering Fixes
Generates CSS overrides with proper specificity for common styling issues (e.g., footer bullets, missing styles).

Example:
```python
result = generator.generate_css_fix(
    selector='footer ul',
    property_name='list-style',
    context={'bug_type': 'css_rendering_issue', 'issue_count': 5}
)

# Returns CSS with 3 specificity levels:
# - Simple override with !important
# - More specific selector variant
# - Minimal fix without !important
```

### 3. Effort Estimation
Returns human-readable effort estimates:
- "15 minutes"
- "1-2" (hours)
- "2-4" (hours)
- "5 minutes - 2 hours (per 10 pages)"

```python
effort = generator.estimate_effort(fix_option)
# Returns: "1-2" or "15 minutes" etc.
```

### 4. Priority Assignment
Assigns priority level based on bug type and page count:

```python
priority = generator.assign_priority("wordpress_malformed_embed", 47)
# Returns: "critical"

# Priority matrix:
# - Critical: High-impact bug types (embed, missing content) or 50+ pages
# - High: Medium-impact types or 10-50 pages affected
# - Medium: Low-impact types or 5-10 pages
# - Low: Cosmetic issues affecting few pages
```

### 5. Complete Fix Reports
Generates comprehensive reports with all options, priority, and next steps:

```python
report = generator.generate_fix_report(
    bug_type="wordpress_malformed_embed",
    bug_pattern=bug_pattern,
    page_count=47,
    affected_pages=["https://...", "https://..."]
)
```

## Return Format

All fix generation methods return structured dictionaries ready for JSON serialization:

```python
{
    "options": [
        {
            "name": "Database Migration",
            "description": "Find and replace embed codes...",
            "code": "UPDATE wp_posts SET...",
            "language": "sql",  # sql, php, css, markdown
            "effort_hours": "2-4",
            "pros": ["Permanent fix", "Affects all pages"],
            "cons": ["Requires database access", "Needs backup"]
        },
        # ... 2 more options
    ],
    "recommended": 0,  # index of recommended option
    "severity": "high",
    "notes": [...]
}
```

## API Reference

### FixGenerator Methods

#### `__init__()`
Initialize the fix generator with pattern templates.

#### `generate_wordpress_embed_fix(bug_pattern: str) -> dict`
Generate fixes for WordPress/Drupal embed code bugs.

**Args:**
- `bug_pattern`: The detected malformed embed code (e.g., `[[{"fid":"..."}]]`)

**Returns:** Dict with 3 fix options and metadata

#### `generate_css_fix(selector: str, property_name: str, context: dict) -> dict`
Generate CSS overrides for rendering issues.

**Args:**
- `selector`: CSS selector (e.g., "footer ul")
- `property_name`: CSS property to fix (e.g., "list-style")
- `context`: Dict with `bug_type`, `description`, `issue_count`

**Returns:** Dict with CSS fix options

#### `estimate_effort(fix_option: dict) -> str`
Extract effort estimate from a fix option.

**Args:**
- `fix_option`: A fix option dict from generate_*_fix methods

**Returns:** Effort string (e.g., "1-2" hours, "15 minutes")

#### `assign_priority(bug_type: str, page_count: int) -> str`
Assign priority based on bug type and impact.

**Args:**
- `bug_type`: Type of bug ("wordpress_malformed_embed", "css_rendering_issue", etc.)
- `page_count`: Number of affected pages

**Returns:** Priority level ("critical", "high", "medium", "low")

#### `generate_fix_report(bug_type: str, bug_pattern: str, page_count: int, affected_pages: List[str]) -> dict`
Generate comprehensive fix report with all options and next steps.

**Args:**
- `bug_type`: Classification of the bug
- `bug_pattern`: The detected bug pattern
- `page_count`: Number of affected pages
- `affected_pages`: Optional list of affected page URLs

**Returns:** Complete report dict with summary, options, and action items

## Integration with Bug Finder

The FixGenerator integrates with `bug_finder_cli.py` workflow:

1. **Bug Detection** (`bug_finder_cli.py`)
   - Identifies bug patterns on example page
   - Generates search patterns
   - Scans entire site for matches

2. **Fix Generation** (`bug_finder_fix_generator.py`)
   - Takes detected pattern
   - Generates multiple fix approaches
   - Assigns priority and effort estimate

3. **Implementation**
   - User selects preferred fix option
   - Copy/paste code into environment
   - Test on staging → deploy to production

## Real-World Example: WPR Bug

**Scenario:** WPR (Wisconsin Public Radio) website has 47 articles showing raw Drupal embed JSON instead of images.

**Bug Pattern:**
```
[[{"fid":"1101026″,"view_mode":"full_width","fields":{...}}]]
```

**Generated Fixes:**

1. **SQL Migration** (2-4 hours)
   - Requires: Database access, backup
   - Pros: Permanent, affects all pages
   - Cons: Risky without database knowledge

2. **PHP Filter** (1-2 hours) ✓ RECOMMENDED
   - Requires: Theme/plugin file access
   - Pros: Safe, reversible, testable
   - Cons: Slight performance impact

3. **Manual** (5-10 hours)
   - Requires: WordPress admin access
   - Pros: Full control, zero risk
   - Cons: Not scalable for 47 pages

**Recommended:** Option 2 (PHP Filter)
- Quick implementation (1-2 hours)
- Fully reversible if issues occur
- Can deploy without downtime
- Can migrate to database fix later if desired

## Testing

Run the test suite to verify all functionality:

```bash
python3.11 test_fix_generator.py
```

Tests include:
- WordPress embed fix generation (3 options)
- CSS fix generation
- Effort estimation
- Priority assignment (9 test cases)
- Complete report generation
- JSON serialization

Run integration test with real-world scenario:

```bash
python3.11 integration_test_fix_generator.py
```

## Design Principles

1. **Template-Based**: No LLM calls, deterministic output
2. **Multiple Options**: Always provide 2-3 approaches (DB, code, manual)
3. **Realistic Estimates**: Based on actual implementation experience
4. **Risk-Aware**: Flag high-risk operations and require backups
5. **Actionable Code**: Include complete, copy-paste-ready code snippets
6. **Pros/Cons Analysis**: Help users make informed decisions
7. **Reversible Defaults**: Recommend safe, reversible approaches first

## Future Extensions

- Support for more CMS platforms (Joomla, Drupal core, etc.)
- Automated code formatting for different languages
- Integration with version control for safe testing
- Automated rollback capabilities
- Performance impact analysis
- Database-specific optimizations (PostgreSQL, SQLite, etc.)

## Notes

- All code examples include safety checks and error handling
- SQL examples include verification queries
- PHP code includes logging for debugging
- Manual fixes include detailed step-by-step instructions
- Effort estimates are conservative (on the higher end)
