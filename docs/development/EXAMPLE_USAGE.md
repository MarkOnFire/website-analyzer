# Enhanced HTML Export - Practical Example

## Complete Integration Example

This example shows how to use the enhanced HTML export with root cause analysis and proposed fixes.

### Setup

```python
from pathlib import Path
from datetime import datetime
from bug_finder_export import export_to_html
```

### Sample Data

```python
# Bug scan results from your crawler
matches = [
    {
        'url': 'https://example.com/blog/article-1',
        'total_matches': 3,
        'priority': 'critical',
        'patterns': {
            'jQuery .live() deprecated': 2,
            'IE8 compatibility issue': 1
        }
    },
    {
        'url': 'https://example.com/products',
        'total_matches': 2,
        'priority': 'high',
        'patterns': {
            'jQuery .live() deprecated': 2
        }
    },
    {
        'url': 'https://example.com/contact',
        'total_matches': 1,
        'priority': 'medium',
        'patterns': {
            'Outdated JavaScript API': 1
        }
    }
]

# Scan metadata
metadata = {
    'site_scanned': 'example.com',
    'example_url': 'https://example.com/blog/article-1',
    'pages_scanned': 3,
    'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
}
```

### Root Cause Analysis

Provide detailed explanations for each bug type:

```python
root_causes = {
    'jQuery .live() deprecated': (
        'The .live() method was deprecated in jQuery 1.7 and completely removed in '
        'jQuery 1.9. This method was used for event delegation on dynamically added '
        'elements before the modern .on() method became standard. Pages using this '
        'will experience JavaScript errors in newer jQuery versions.'
    ),

    'IE8 compatibility issue': (
        'Internet Explorer 8 reached end-of-life in 2016. The codebase contains '
        'IE8-specific workarounds (conditional comments, polyfills) that add '
        'unnecessary complexity and can be safely removed. Modern browsers handle '
        'these cases natively.'
    ),

    'Outdated JavaScript API': (
        'This code uses deprecated APIs from older JavaScript specifications that '
        'have been superseded by modern equivalents. These APIs may be removed from '
        'browsers in future versions and have performance implications.'
    )
}
```

### Proposed Fixes

Define fix options with code samples and effort estimates:

```python
fixes = {
    'jQuery .live() deprecated': [
        {
            'title': 'Migrate to .on() method (Recommended)',
            'description': (
                'Replace all .live() calls with .on() using event delegation. '
                'This is the modern standard approach and has identical functionality. '
                'The .on() method works with both existing and dynamically added elements.'
            ),
            'code_sample': '''// Before (deprecated - no longer works in jQuery 1.9+):
$('.delete-btn').live('click', function() {
    deleteItem($(this).data('id'));
});

// After (modern - works with jQuery 1.7+):
$(document).on('click', '.delete-btn', function() {
    deleteItem($(this).data('id'));
});

// Or using event delegation on specific parent:
$('#items').on('click', '.delete-btn', function() {
    deleteItem($(this).data('id'));
});''',
            'language': 'javascript',
            'effort': '2-4 hours',
            'priority': 'critical'
        },
        {
            'title': 'Remove jQuery dependency entirely (Long-term)',
            'description': (
                'For modern applications, consider replacing jQuery event delegation '
                'with vanilla JavaScript using event.target.matches(). This reduces '
                'external dependencies and improves page load performance.'
            ),
            'code_sample': '''// Vanilla JavaScript equivalent:
document.addEventListener('click', function(e) {
    if (e.target.matches('.delete-btn')) {
        deleteItem(e.target.dataset.id);
    }
});

// Or with closest() for more specific selectors:
document.addEventListener('click', function(e) {
    const btn = e.target.closest('.delete-btn');
    if (btn) {
        deleteItem(btn.dataset.id);
    }
});''',
            'language': 'javascript',
            'effort': '8-16 hours',
            'priority': 'high'
        }
    ],

    'IE8 compatibility issue': [
        {
            'title': 'Remove IE8 conditional comments and polyfills',
            'description': (
                'Remove all IE8-specific code paths, conditional comments, and '
                'polyfills. Update .htaccess or server configuration to remove '
                'IE8-targeting headers. This simplifies the codebase significantly.'
            ),
            'code_sample': '''<!-- Before: Multiple IE-specific stylesheets -->
<!--[if IE 8]><link rel="stylesheet" href="ie8.css"><![endif]-->
<!--[if lt IE 9]><script src="html5shiv.js"></script><![endif]-->

<!-- After: Only modern browser stylesheets -->
<link rel="stylesheet" href="styles.css">

// Remove IE-specific JavaScript checks:
// DELETE: if (typeof XDomainRequest !== "undefined") { ... }
// DELETE: document.all checks
// DELETE: IE-specific event handling''',
            'language': 'html',
            'effort': '1-2 hours',
            'priority': 'medium'
        }
    ],

    'Outdated JavaScript API': [
        {
            'title': 'Update to modern ECMAScript equivalents',
            'description': (
                'Replace deprecated APIs with modern JavaScript features. '
                'Consult MDN documentation for each deprecated method. '
                'Modern equivalents often have better performance.'
            ),
            'code_sample': '''// Example updates:

// Old: Array conversion
var arr = Array.prototype.slice.call(nodeList);
// New: Array.from()
const arr = Array.from(nodeList);

// Old: Object.keys workaround
for (var key in obj) { if (obj.hasOwnProperty(key)) { ... } }
// New: Object.keys()
Object.keys(obj).forEach(key => { ... });

// Old: String methods
var trimmed = str.replace(/^\\s+|\\s+$/g, '');
// New: String.trim()
const trimmed = str.trim();''',
            'language': 'javascript',
            'effort': '4-6 hours',
            'priority': 'medium'
        }
    ]
}
```

### Generate Report

```python
# Generate the enhanced HTML report
export_to_html(
    matches=matches,
    output_file=Path('bug_report_enhanced.html'),
    metadata=metadata,
    include_fixes=True,
    root_causes=root_causes,
    fixes=fixes
)

print("Enhanced HTML report generated: bug_report_enhanced.html")
```

## HTML Output Structure

The generated HTML includes these sections:

### 1. Header
- Site name and report title
- Gradient background (purple)

### 2. Quick Summary
- Bugs found count
- Pages scanned
- Scan date
- Example URL

### 3. Executive Summary (NEW)
```
Total Issues: 6
Critical: 1    High: 1    Medium: 1    Low: 0

Recommended Timeline: Immediate action required - critical issues detected
```

### 4. Affected Pages Table (Enhanced)
Columns: #, URL, Matches, Patterns, Priority, Fix Available
- Sortable by any column
- Color-coded priority levels
- Check marks indicate fix availability

### 5. Root Cause Analysis & Proposed Fixes (NEW)
For each bug type:
- Root cause explanation
- Multiple fix options (collapsible)
- Code samples with syntax highlighting
- Effort estimates
- Priority badges

### 6. Footer
- Generation timestamp
- Credit to Bug Finder tool

## Visual Features

### Colors
- **Critical** (Red #e74c3c): Immediate action needed
- **High** (Orange #e67e22): Address within 1-2 weeks
- **Medium** (Yellow #f39c12): Schedule in next sprint
- **Low** (Green #27ae60): Monitor for future releases

### Interactive Elements
- Click bug type headers to expand/collapse details
- Click column headers to sort table
- Hover effects for better UX
- First bug type auto-expands on page load

### Code Display
- Dark theme syntax highlighting
- Monospace font for readability
- Horizontal scrolling for long code
- HTML entity escaping for safety

## Integration Points

### With RootCauseAnalyzer (Agent 1)
The analyzer should return a dictionary:
```python
root_causes = RootCauseAnalyzer.analyze(bug_patterns)
# Returns: {pattern_name: explanation_string}
```

### With FixGenerator (Agent 2)
The generator should return a dictionary:
```python
fixes = FixGenerator.generate_fixes(bug_patterns)
# Returns: {pattern_name: [fix_option_dict, ...]}
```

### Combined Usage
```python
from root_cause_analyzer import RootCauseAnalyzer
from fix_generator import FixGenerator
from bug_finder_export import export_to_html

# 1. Run bug detection
matches = run_bug_scan(urls)

# 2. Analyze root causes
root_causes = RootCauseAnalyzer.analyze(matches)

# 3. Generate fixes
fixes = FixGenerator.generate_fixes(matches)

# 4. Export enhanced report
export_to_html(
    matches,
    Path('final_report.html'),
    metadata,
    include_fixes=True,
    root_causes=root_causes,
    fixes=fixes
)
```

## Best Practices

1. **Root Cause Descriptions**
   - Be specific about why the bug exists
   - Include impact assessment
   - Reference documentation or standards
   - Keep to 2-3 sentences per cause

2. **Fix Options**
   - Provide multiple approaches when applicable
   - Order by priority or complexity
   - Include realistic effort estimates
   - Add code samples when helpful

3. **Effort Estimates**
   - Use human-readable formats: "2-4 hours", "1-2 days", "1 week"
   - Include effort for testing and review
   - Account for deployment/rollback time
   - Be conservative in estimates

4. **Code Samples**
   - Show before and after when migrating
   - Keep samples focused and readable
   - Add comments for clarity
   - Test samples before including

5. **Priority Assignment**
   - **Critical**: Breaks functionality or security issue
   - **High**: Deprecated in current versions, will break soon
   - **Medium**: Deprecated but still works, performance improvement possible
   - **Low**: Legacy code, nice to have improvements

## Troubleshooting

### Code samples not displaying correctly
- Ensure code_sample is a string, not HTML
- Check for HTML special characters (<, >, &, ")
- Verify language parameter is set

### Colors not showing
- Ensure CSS is fully loaded
- Check browser compatibility (modern browsers recommended)
- Verify priority values are lowercase

### Sections not collapsing
- Ensure JavaScript is enabled
- Check browser console for errors
- Verify toggleBugType() function is defined

## File Size Notes

- Basic report: ~14 KB
- Enhanced report with fixes: ~23 KB
- Scales with number of bug types and fix options
- Minification can reduce size by 30-40%
