# Pattern Generation: Lessons Learned

## The Problem

When scanning for WordPress embed bugs on WPR.org, our initial 5000-page scan found **0 bugs** even though we knew bugs existed on the site (confirmed via archive.org).

## Root Cause

The bug example contained a **Unicode double prime character (″, U+2033)** instead of a regular quote:
```
[[{"fid":"1101026″  <-- This is U+2033, not U+0022
```

Our initial patterns only matched regular ASCII quotes (`"`), missing all instances with special characters.

## The Solution

### Before (Failed Pattern)
```python
PATTERNS = {
    "wordpress-fid-opening": r'\[\[{"fid":"[0-9]+"',  # Only matches ASCII "
}
```

### After (Working Pattern)
```python
QUOTE_PATTERN = r'["\'\u2018\u2019\u201C\u201D\u2033\u2034]'  # Matches 7 quote types

PATTERNS = {
    "wordpress_fid_numeric": (
        r'\[\[\s*\{\s*' + QUOTE_PATTERN + r'fid' + QUOTE_PATTERN +
        r'\s*:\s*' + QUOTE_PATTERN + r'[0-9]+'
    ),
}
```

### Supported Quote Characters
- `"` (U+0022) - Regular double quote
- `'` (U+0027) - Regular single quote
- `'` (U+2018) - Left single quotation mark
- `'` (U+2019) - Right single quotation mark
- `"` (U+201C) - Left double quotation mark
- `"` (U+201D) - Right double quotation mark
- `″` (U+2033) - Double prime (inches symbol)
- `‴` (U+2034) - Triple prime

## Verification Results

Testing on archived page with known bugs:
- **Before**: 0 matches (missed both instances)
- **After**: 10 matches (2 bug instances × 5 patterns each)

## Implications for Future Development

### Pattern Generation from User Examples

When a user provides a bug example (text or screenshot), we need to:

1. **Analyze character encoding**
   - Don't assume ASCII
   - Check for Unicode variations in quotes, dashes, spaces
   - Use `ord(char)` to inspect actual character codes

2. **Generate flexible structural patterns**
   - Match structure, not exact content
   - Use `\s*` for optional whitespace
   - Allow field order variations
   - Make content-specific parts optional

3. **Create multiple pattern variants**
   - Opening structure (most lenient)
   - Core structure with key fields
   - Complete structure (most strict)
   - Individual field patterns

4. **Test patterns before deploying**
   - Always test against the example that user provided
   - Verify on known-buggy pages
   - Report which patterns matched

### Screenshot-to-Pattern Workflow (Future)

For screenshot inputs:
1. OCR the screenshot text
2. Analyze extracted characters for Unicode variations
3. Identify structural markers (`[[`, `{{`, JSON keys, etc.)
4. Generate flexible regex patterns
5. Test against live pages
6. Allow user to refine if needed

### Current Limitation

The scanner currently requires manually updating `PATTERNS` dict in `full_site_scanner.py`.

**Next step**: Build a pattern generator that takes user input (text/screenshot) and automatically creates optimal regex patterns.

## Files Updated

- `full_site_scanner.py` - Updated with Unicode-aware patterns
- `improved_pattern_generator.py` - New module for pattern generation (prototype)
- `test_improved_patterns.py` - Validation script
- `SCANNING_GUIDE.md` - Documented the update

## Re-scan Recommendation

The original 5000-page scan of www.wpr.org should be **re-run** with improved patterns to verify whether current pages actually have bugs or if they've been fixed.

However, based on testing:
- **Archived pages (July 2025)**: Bugs present ✅
- **Current www.wpr.org pages**: Likely clean (bugs fixed)

The improved scanner is now ready for:
- Other sites with similar bugs
- Historical scans via archive.org
- Future bug pattern discovery
