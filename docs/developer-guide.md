# Developer Guide

Guide for developers who want to create custom test plugins or contribute to the Website Analyzer project.

## Table of Contents

1. [Overview](#overview)
2. [Plugin Architecture](#plugin-architecture)
3. [Creating a Test Plugin](#creating-a-test-plugin)
4. [TestPlugin Protocol](#testplugin-protocol)
5. [Working with Snapshots](#working-with-snapshots)
6. [Testing Patterns](#testing-patterns)
7. [Advanced Topics](#advanced-topics)
8. [Contributing](#contributing)

## Overview

Website Analyzer uses a plugin-based architecture for extensibility. Test plugins are the core analysis units that examine site snapshots and generate structured findings.

Key concepts:
- **TestPlugin protocol**: Interface all plugins must implement
- **SiteSnapshot**: Immutable snapshot of crawled website data
- **TestResult**: Structured output from plugin execution
- **Plugin loader**: Automatic discovery and instantiation

## Plugin Architecture

### Plugin Discovery

Plugins are automatically discovered from `src/analyzer/plugins/` using Python's `pkgutil` module.

Discovery process:
1. Scan `src.analyzer.plugins` package for modules
2. Import each module
3. Find classes implementing `TestPlugin` protocol
4. Instantiate with no-arg constructor
5. Add to available plugins list

### Plugin Lifecycle

```
Load -> Configure -> Analyze -> Report
```

1. **Load**: Plugin class instantiated by plugin loader
2. **Configure**: Runner extracts plugin-specific config from global config
3. **Analyze**: Runner calls `analyze(snapshot, **config)` method
4. **Report**: Plugin returns `TestResult` with findings

### Directory Structure

```
src/analyzer/
├── plugins/
│   ├── __init__.py          # Empty (required for package)
│   ├── migration_scanner.py # Example plugin
│   ├── seo_optimizer.py     # Example plugin
│   ├── llm_optimizer.py     # Example plugin
│   └── security_audit.py    # Example plugin
├── test_plugin.py           # Protocol definition
├── plugin_loader.py         # Discovery system
└── runner.py                # Execution orchestration
```

## Creating a Test Plugin

### Minimal Plugin Example

```python
"""My custom test plugin."""
from src.analyzer.test_plugin import SiteSnapshot, TestResult, TestPlugin


class MyPlugin(TestPlugin):
    """Check for specific issues on website."""

    # Required class attributes
    name: str = "my-plugin"
    description: str = "Checks for my specific issues"

    async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
        """Run analysis on snapshot.

        Args:
            snapshot: Site snapshot with pages, sitemap, summary
            **kwargs: Plugin-specific configuration

        Returns:
            TestResult with findings
        """
        # Extract configuration
        threshold = kwargs.get("threshold", 100)

        # Analyze pages
        issues = []
        for page in snapshot.pages:
            content = page.get_markdown()

            # Your analysis logic here
            if len(content) < threshold:
                issues.append({
                    "url": page.url,
                    "content_length": len(content),
                    "threshold": threshold
                })

        # Generate result
        if issues:
            return TestResult(
                plugin_name=self.name,
                status="fail",
                summary=f"Found {len(issues)} pages below threshold",
                details={
                    "threshold": threshold,
                    "issues": issues
                }
            )
        else:
            return TestResult(
                plugin_name=self.name,
                status="pass",
                summary="All pages meet content threshold",
                details={"threshold": threshold, "pages_checked": len(snapshot.pages)}
            )
```

### Plugin Registration

No registration required. Simply:
1. Create file in `src/analyzer/plugins/`
2. Define class implementing `TestPlugin` protocol
3. Plugin loader will discover it automatically

### Running Your Plugin

```bash
# List plugins to verify discovery
python -m src.analyzer.cli test list-plugins

# Run your plugin
python -m src.analyzer.cli test run example-com --test my-plugin

# Pass configuration
python -m src.analyzer.cli test run example-com \
  --test my-plugin \
  --config 'my-plugin:{"threshold":200}'
```

## TestPlugin Protocol

### Protocol Definition

```python
from typing import Protocol, runtime_checkable
from src.analyzer.test_plugin import SiteSnapshot, TestResult


@runtime_checkable
class TestPlugin(Protocol):
    """Protocol for analysis plugins."""

    name: str
    description: str

    async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
        ...
```

### Required Attributes

#### `name: str`

Unique plugin identifier. Used for:
- Command-line `--test` arguments
- Configuration keys
- Result tracking
- Issue attribution

Naming conventions:
- Use lowercase with hyphens
- Be specific and descriptive
- Avoid generic names like "checker" or "scanner"

Examples: `seo-optimizer`, `migration-scanner`, `security-audit`

#### `description: str`

Short summary of plugin's purpose. Shown in:
- `test list-plugins` output
- CLI help messages
- Generated documentation

Guidelines:
- One sentence, under 80 characters
- Start with verb (Checks, Finds, Analyzes, etc.)
- Be specific about what is checked

Examples:
- "Checks for deprecated code patterns"
- "Analyzes on-page SEO factors"
- "Identifies security vulnerabilities"

### Required Method

#### `async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult`

Core analysis method. Must:
- Be async (use `async def`)
- Accept `SiteSnapshot` as first argument
- Accept `**kwargs` for configuration
- Return `TestResult` instance

Method signature:
```python
async def analyze(
    self,
    snapshot: SiteSnapshot,
    **kwargs: Any
) -> TestResult:
    """Analyze site snapshot for issues.

    Args:
        snapshot: Immutable site snapshot
        **kwargs: Plugin-specific configuration

    Returns:
        TestResult with status and findings

    Raises:
        ValueError: For configuration errors
        RuntimeError: For analysis failures
    """
```

## Working with Snapshots

### SiteSnapshot Structure

```python
class SiteSnapshot(BaseModel):
    """Represents a full website snapshot."""

    snapshot_dir: Path           # Path to snapshot directory
    timestamp: str               # Snapshot timestamp
    root_url: str                # Starting URL
    pages: List[PageData]        # All crawled pages
    sitemap: Dict[str, Any]      # Discovered URLs
    summary: Dict[str, Any]      # Crawl statistics
```

### Accessing Pages

```python
async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
    # Iterate all pages
    for page in snapshot.pages:
        url = page.url
        status = page.status_code
        title = page.title
        links = page.links

        # Read content
        raw_html = page.get_content()
        cleaned_html = page.get_cleaned_html()
        markdown = page.get_markdown()
```

### PageData Structure

```python
class PageData(BaseModel):
    """Represents a single crawled page."""

    url: str                     # Page URL
    status_code: int             # HTTP status
    timestamp: str               # Crawl timestamp
    title: Optional[str]         # Page title
    links: List[str]             # Internal links found
    headers: Optional[Dict]      # HTTP response headers
    directory: Path              # Page data directory

    # Content access methods
    def get_content(self) -> str:        # Raw HTML
    def get_cleaned_html(self) -> str:   # Cleaned HTML
    def get_markdown(self) -> str:       # Markdown conversion
```

### Using Sitemap and Summary

```python
async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
    # Access sitemap
    root_url = snapshot.sitemap.get("root")
    all_urls = snapshot.sitemap.get("pages", [])

    # Access crawl summary
    total_pages = snapshot.summary.get("total_pages", 0)
    errors = snapshot.summary.get("errors", [])
    duration = snapshot.summary.get("duration_seconds", 0)
```

### Parsing HTML Content

Recommended libraries:
- **BeautifulSoup4**: For HTML parsing
- **lxml**: For faster parsing
- **re**: For regex pattern matching

Example with BeautifulSoup:
```python
from bs4 import BeautifulSoup


async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
    for page in snapshot.pages:
        html = page.get_cleaned_html()
        soup = BeautifulSoup(html, 'lxml')

        # Find elements
        title = soup.find('title')
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        h1_tags = soup.find_all('h1')
        images = soup.find_all('img')

        # Extract text
        if title:
            title_text = title.get_text()

        if meta_desc:
            desc_content = meta_desc.get('content', '')
```

## Testing Patterns

### Pattern 1: Presence Checks

Check if elements exist:

```python
async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
    issues = []

    for page in snapshot.pages:
        html = page.get_cleaned_html()
        soup = BeautifulSoup(html, 'lxml')

        # Check for title tag
        if not soup.find('title'):
            issues.append({
                "url": page.url,
                "issue": "Missing title tag"
            })

        # Check for meta description
        if not soup.find('meta', attrs={'name': 'description'}):
            issues.append({
                "url": page.url,
                "issue": "Missing meta description"
            })

    return self._create_result(issues)
```

### Pattern 2: Quality Checks

Check element quality:

```python
async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
    issues = []

    for page in snapshot.pages:
        html = page.get_cleaned_html()
        soup = BeautifulSoup(html, 'lxml')

        title = soup.find('title')
        if title:
            title_text = title.get_text().strip()

            # Check length
            if len(title_text) < 30:
                issues.append({
                    "url": page.url,
                    "issue": "Title too short",
                    "length": len(title_text),
                    "min_length": 30
                })
            elif len(title_text) > 60:
                issues.append({
                    "url": page.url,
                    "issue": "Title too long",
                    "length": len(title_text),
                    "max_length": 60
                })

    return self._create_result(issues)
```

### Pattern 3: Pattern Matching

Find patterns in content:

```python
import re


async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
    patterns = kwargs.get("patterns", {})
    findings = []

    for page in snapshot.pages:
        content = page.get_markdown()

        for pattern_name, pattern_regex in patterns.items():
            try:
                regex = re.compile(pattern_regex, re.IGNORECASE)
                matches = regex.finditer(content)

                for match in matches:
                    findings.append({
                        "url": page.url,
                        "pattern": pattern_name,
                        "match": match.group(),
                        "position": match.start()
                    })
            except re.error as e:
                # Handle invalid regex
                return TestResult(
                    plugin_name=self.name,
                    status="error",
                    summary=f"Invalid regex pattern: {pattern_name}",
                    details={"error": str(e)}
                )

    return self._create_result(findings)
```

### Pattern 4: Aggregation

Aggregate data across pages:

```python
async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
    # Collect all titles
    titles = []
    for page in snapshot.pages:
        html = page.get_cleaned_html()
        soup = BeautifulSoup(html, 'lxml')
        title = soup.find('title')
        if title:
            titles.append((page.url, title.get_text().strip()))

    # Find duplicates
    title_counts = {}
    for url, title in titles:
        if title not in title_counts:
            title_counts[title] = []
        title_counts[title].append(url)

    duplicates = {
        title: urls
        for title, urls in title_counts.items()
        if len(urls) > 1
    }

    if duplicates:
        return TestResult(
            plugin_name=self.name,
            status="fail",
            summary=f"Found {len(duplicates)} duplicate titles",
            details={"duplicates": duplicates}
        )
    else:
        return TestResult(
            plugin_name=self.name,
            status="pass",
            summary="All titles are unique",
            details={"total_pages": len(titles)}
        )
```

### Pattern 5: Scoring

Calculate quality scores:

```python
async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
    scores = []

    for page in snapshot.pages:
        html = page.get_cleaned_html()
        soup = BeautifulSoup(html, 'lxml')

        score = 10.0  # Start with perfect score
        issues = []

        # Check title
        title = soup.find('title')
        if not title:
            score -= 2.0
            issues.append("Missing title")
        elif len(title.get_text().strip()) < 30:
            score -= 1.0
            issues.append("Short title")

        # Check meta description
        meta = soup.find('meta', attrs={'name': 'description'})
        if not meta:
            score -= 2.0
            issues.append("Missing meta description")

        # Check H1
        h1_count = len(soup.find_all('h1'))
        if h1_count == 0:
            score -= 1.5
            issues.append("Missing H1")
        elif h1_count > 1:
            score -= 0.5
            issues.append("Multiple H1 tags")

        scores.append({
            "url": page.url,
            "score": max(0.0, score),
            "issues": issues
        })

    avg_score = sum(s["score"] for s in scores) / len(scores) if scores else 0

    return TestResult(
        plugin_name=self.name,
        status="pass" if avg_score >= 7.0 else "fail",
        summary=f"Average score: {avg_score:.1f}/10",
        details={
            "average_score": avg_score,
            "page_scores": scores
        }
    )
```

## Advanced Topics

### Handling Configuration

```python
async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
    # Extract with defaults
    threshold = kwargs.get("threshold", 100)
    strict_mode = kwargs.get("strict", False)
    patterns = kwargs.get("patterns", {})

    # Validate configuration
    if threshold < 0:
        return TestResult(
            plugin_name=self.name,
            status="error",
            summary="Invalid configuration: threshold must be >= 0",
            details={"threshold": threshold}
        )

    # Use configuration
    # ...
```

### Error Handling

```python
async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
    try:
        # Your analysis logic
        results = self._analyze_pages(snapshot.pages)

        return TestResult(
            plugin_name=self.name,
            status="pass",
            summary="Analysis complete",
            details=results
        )

    except ValueError as e:
        # Configuration errors
        return TestResult(
            plugin_name=self.name,
            status="error",
            summary=f"Configuration error: {str(e)}",
            details={"error_type": "ValueError"}
        )

    except Exception as e:
        # Unexpected errors
        import traceback
        return TestResult(
            plugin_name=self.name,
            status="error",
            summary=f"Analysis failed: {str(e)}",
            details={
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc()
            }
        )
```

### Using External APIs

```python
import httpx


class LLMAnalyzer(TestPlugin):
    name = "llm-analyzer"
    description = "Uses LLM API to analyze content quality"

    async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
        api_key = kwargs.get("api_key")
        if not api_key:
            return TestResult(
                plugin_name=self.name,
                status="error",
                summary="API key required",
                details={"message": "Pass api_key in config"}
            )

        async with httpx.AsyncClient() as client:
            results = []

            for page in snapshot.pages:
                content = page.get_markdown()[:1000]  # Limit size

                # Call API
                response = await client.post(
                    "https://api.example.com/analyze",
                    json={"content": content},
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=30.0
                )

                if response.status_code == 200:
                    results.append({
                        "url": page.url,
                        "analysis": response.json()
                    })

        return TestResult(
            plugin_name=self.name,
            status="pass",
            summary=f"Analyzed {len(results)} pages",
            details={"results": results}
        )
```

### Caching and Performance

```python
from functools import lru_cache


class OptimizedPlugin(TestPlugin):
    name = "optimized-plugin"
    description = "Example with performance optimization"

    @staticmethod
    @lru_cache(maxsize=128)
    def _parse_html(html: str):
        """Cache parsed HTML to avoid re-parsing."""
        return BeautifulSoup(html, 'lxml')

    async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
        # Process pages in batches
        batch_size = kwargs.get("batch_size", 10)

        for i in range(0, len(snapshot.pages), batch_size):
            batch = snapshot.pages[i:i+batch_size]

            # Process batch
            for page in batch:
                html = page.get_cleaned_html()
                soup = self._parse_html(html)
                # ...

        # Return result
```

## Contributing

### Code Style

Follow project conventions:
- Python 3.11+ syntax
- Type hints on all function signatures
- Docstrings for all public classes and methods
- PEP 8 style (enforced by linters)

### Testing

Write tests for your plugin:

```python
# tests/test_my_plugin.py
import pytest
from pathlib import Path
from src.analyzer.test_plugin import SiteSnapshot
from src.analyzer.plugins.my_plugin import MyPlugin


@pytest.mark.asyncio
async def test_plugin_basic(tmp_path: Path):
    # Create test snapshot
    snapshot = create_test_snapshot(tmp_path)

    # Run plugin
    plugin = MyPlugin()
    result = await plugin.analyze(snapshot)

    # Assert results
    assert result.plugin_name == "my-plugin"
    assert result.status in ["pass", "fail", "warning", "error"]
    assert isinstance(result.details, dict)


def create_test_snapshot(base_dir: Path) -> SiteSnapshot:
    # Helper to create minimal snapshot for testing
    # ...
```

### Documentation

Document your plugin:
- Add docstring to class
- Document configuration options
- Provide usage examples
- List any external dependencies

### Pull Requests

1. Fork the repository
2. Create feature branch: `git checkout -b feature/my-plugin`
3. Add plugin and tests
4. Update documentation
5. Run tests: `pytest tests/`
6. Submit pull request

### Plugin Guidelines

- Keep plugins focused on single responsibility
- Avoid side effects (file writes, external state changes)
- Handle errors gracefully
- Provide helpful error messages
- Make configuration optional with sensible defaults
- Document all configuration options
- Include examples in docstring

### Example Plugin Template

```python
"""
Plugin name: my-plugin
Purpose: Brief description of what this plugin checks

Configuration:
    option1 (str): Description of option1. Default: 'value'
    option2 (int): Description of option2. Default: 100

Example:
    python -m src.analyzer.cli test run example-com \\
        --test my-plugin \\
        --config 'my-plugin:{"option1":"custom","option2":200}'

Author: Your Name
"""
from typing import Any, Dict, List
from bs4 import BeautifulSoup

from src.analyzer.test_plugin import SiteSnapshot, TestResult, TestPlugin


class MyPlugin(TestPlugin):
    """Brief one-line description."""

    name: str = "my-plugin"
    description: str = "Brief one-line description"

    async def analyze(self, snapshot: SiteSnapshot, **kwargs: Any) -> TestResult:
        """Analyze site snapshot for specific issues.

        Args:
            snapshot: Site snapshot with crawled pages
            **kwargs: Configuration options
                option1 (str): Description
                option2 (int): Description

        Returns:
            TestResult with findings
        """
        # Extract configuration
        option1 = kwargs.get("option1", "default_value")
        option2 = kwargs.get("option2", 100)

        # Validate configuration
        if option2 < 0:
            return self._error_result("option2 must be >= 0")

        # Analyze pages
        findings = []
        for page in snapshot.pages:
            # Your analysis logic
            pass

        # Return result
        if findings:
            return TestResult(
                plugin_name=self.name,
                status="fail",
                summary=f"Found {len(findings)} issues",
                details={"findings": findings}
            )
        else:
            return TestResult(
                plugin_name=self.name,
                status="pass",
                summary="No issues found",
                details={"pages_checked": len(snapshot.pages)}
            )

    def _error_result(self, message: str) -> TestResult:
        """Helper to create error result."""
        return TestResult(
            plugin_name=self.name,
            status="error",
            summary=message,
            details={}
        )
```

## Additional Resources

- [User Guide](user-guide.md) - Using the analyzer
- [Test Plugin Protocol](../src/analyzer/test_plugin.py) - Source code
- [Example Plugins](../src/analyzer/plugins/) - Built-in plugins
- [Test Suite](../tests/) - Test examples
- [Contributing Guide](../CONTRIBUTING.md) - Contribution process
