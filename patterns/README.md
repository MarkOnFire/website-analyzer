# Pattern Library

This directory contains reusable bug pattern definitions for the website analyzer's bug-finder tool.

## What is a Pattern?

A pattern is a JSON file that defines how to detect a specific type of bug or issue on a website. Each pattern contains:

- **name**: Unique identifier for the pattern
- **description**: Human-readable explanation of what the pattern detects
- **patterns**: List of regular expressions to match bug indicators
- **severity**: Impact level (low, medium, high, critical)
- **examples**: Sample HTML/text where the pattern appears
- **tags**: Optional categorization tags
- **author**: Who created the pattern
- **notes**: Additional context and remediation advice

## Available Patterns

### wordpress_embed_bug.json
Detects WordPress embed field arrays rendered as visible text instead of embedded content. Common in sites with improper field serialization.

### broken_image_tag.json
Identifies malformed img tags with missing src attributes or invalid syntax that cause rendering issues.

### missing_alt_text.json
Detects images without alt text attributes, which impacts accessibility and SEO compliance.

### deprecated_html_tags.json
Finds usage of deprecated HTML tags like `<center>`, `<font>`, `<marquee>` that should use semantic HTML or CSS instead.

## Creating a New Pattern

### Method 1: Using the CLI

```bash
python -m src.analyzer.cli bug-finder patterns add
```

This launches an interactive wizard to create a new pattern.

### Method 2: Manual JSON Creation

Create a new `.json` file in this directory:

```json
{
  "name": "my_pattern",
  "description": "What this pattern detects",
  "patterns": [
    "regex_pattern_1",
    "regex_pattern_2"
  ],
  "severity": "medium",
  "examples": [
    "Example 1",
    "Example 2"
  ],
  "tags": ["category", "tags"],
  "author": "Your Name",
  "notes": "Optional notes about usage and fixes"
}
```

### Method 3: From Pattern Template

```bash
python -m src.analyzer.cli bug-finder patterns template
```

Gets a template you can fill in and save.

## Pattern Structure Details

### name
- Required: String (no spaces, lowercase with underscores)
- Example: `wordpress_embed_bug`

### description
- Required: String (50-200 characters recommended)
- Should clearly explain what bug/issue is detected

### patterns
- Required: Array of valid regex strings
- Each regex is tested against page HTML content
- Regexes are compiled with `re.IGNORECASE` and `re.DOTALL` flags
- Tip: Test your regexes in an online regex tool first

### severity
- Required: One of: `low`, `medium`, `high`, `critical`
- `low`: Minor issues, cosmetic concerns
- `medium`: Functional problems, accessibility issues
- `high`: Major bugs, broken features
- `critical`: Security issues, data corruption

### examples
- Required: Array of at least one example
- Show actual HTML or text where the pattern appears
- Helps others understand what the pattern detects

### tags
- Optional: Array of category tags
- Examples: `accessibility`, `seo`, `security`, `html`, `css`, `js`
- Useful for organizing and discovering patterns

### author
- Optional: String
- Name of the person/team who created the pattern

### notes
- Optional: String
- Can include remediation advice or implementation details

## Testing Patterns

### Test a Pattern on Content

```bash
python -m src.analyzer.cli bug-finder patterns test \
  --pattern wordpress_embed_bug \
  --content "<div>field[0]</div>"
```

### Test a Pattern on a URL

```bash
python -m src.analyzer.cli bug-finder patterns test \
  --pattern missing_alt_text \
  --url https://example.com/page
```

## Using Patterns in Scans

### Load a Single Pattern

```bash
python -m src.analyzer.cli bug-finder scan \
  --example-url https://archive.org/web/*/example.com/page \
  --site https://example.com \
  --pattern-file wordpress_embed_bug
```

### Load Multiple Patterns

```bash
python -m src.analyzer.cli bug-finder scan \
  --site https://example.com \
  --pattern-file wordpress_embed_bug \
  --pattern-file missing_alt_text \
  --pattern-file deprecated_html_tags
```

### Load All Patterns

```bash
python -m src.analyzer.cli bug-finder scan \
  --site https://example.com \
  --load-all-patterns
```

## Regex Tips

Good practices for writing pattern regexes:

1. **Be specific**: Avoid overly broad patterns that match unrelated content
2. **Test first**: Use an online regex tester before adding to pattern
3. **Use character classes**: `[a-z]`, `\d`, `\s` instead of `.` when possible
4. **Escape special chars**: `.` → `\.`, `[` → `\[`, etc.
5. **Non-greedy matching**: Use `.*?` instead of `.*` when matching around delimiters
6. **Case insensitive**: Patterns compile with IGNORECASE, so case doesn't matter

### Common Patterns

```
# Match HTML tags
<tagname[^>]*>

# Match quoted strings
[\"']([^\"']*)[\"']

# Match brackets/braces
\[([^\]]*)\]
\{([^}]*)\}

# Match URLs
https?://[^\s<>"{}|\\^`\[\]]*

# Match escaped content
\\\\[0-9A-Fa-f]{2}

# Match field arrays
field\[[^\]]*\]
```

## Sharing Patterns

To share a pattern:

1. Ensure it's well-documented with clear examples
2. Test it thoroughly on real websites
3. Add meaningful tags for discoverability
4. Include notes about when it's useful and how to fix issues
5. Commit to git with a clear commit message

Example:
```bash
git add patterns/my_new_pattern.json
git commit -m "feat: add pattern for detecting issue X"
```

## Community Patterns

Community-contributed patterns should:
- Have clear, descriptive names
- Include comprehensive examples
- Be well-tested on real websites
- Have author attribution
- Include remediation guidance in notes

## Troubleshooting

### Pattern Not Loading

```bash
python -m src.analyzer.cli bug-finder patterns list
```

Shows any validation errors for problematic patterns.

### Pattern Matching Too Much

1. Check your regex - it may be too broad
2. Add boundary checks: `(?<!\w)..(?!\w)`
3. Be more specific about context

### Pattern Not Matching Anything

1. Verify the test content actually contains what you're looking for
2. Check regex flags - patterns ignore case by default
3. Test regex in isolation to confirm it works

## Pattern Validation

All patterns are validated when:
- Added via CLI
- Listed with the list command
- Loaded for scanning

Validation checks:
- Required fields present (name, description, patterns, severity, examples)
- Severity is valid enum value
- All regex patterns compile successfully
- Examples list is non-empty
- No duplicate pattern names in library
