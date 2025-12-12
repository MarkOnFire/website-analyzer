# Contributing to Website Analyzer

We welcome contributions from users and developers! Here's how you can help.

---

## For Users

### Report Bugs

Found an issue? Please create a GitHub issue with:

1. **What you did**: The command you ran
2. **What you expected**: What should have happened
3. **What happened**: What actually happened (error message, unexpected output)
4. **Example URLs**: If applicable, the URLs you were analyzing
5. **Environment**: Your Python version, OS, and how you installed the tool

**Example issue:**
```
Title: Bug Finder fails on large sites (5000+ pages)

Description:
When running:
python -m src.analyzer.cli bug-finder scan \
  --example-url "https://example.com/bug" \
  --site "https://example.com" \
  --max-pages 5000

Error: MemoryError after scanning ~3000 pages

Environment:
- Python 3.11.2
- macOS 12.6
- Installed via: ./init.sh
```

### Request Features

Have an idea? Open a GitHub discussion or issue with:

1. **What you want to do**: The use case
2. **How you want to do it**: The interface or workflow
3. **Why you need it**: The business value or problem it solves

**Example feature request:**
```
Title: Support for Slack notifications of scan results

Use Case:
I want to automatically notify my team in Slack when a scan completes with findings.

Proposed Interface:
python -m src.analyzer.cli bug-finder scan \
  --example-url "..." \
  --site "..." \
  --slack-webhook "https://hooks.slack.com/services/..."
```

### Contribute Patterns

Discovered a useful regex pattern? Share it!

1. **Test it thoroughly** against your site
2. **Document it clearly** with examples
3. **Submit as an issue** or PR to add it to the pattern library

**Example pattern submission:**
```
Pattern Name: wordpress_broken_shortcode
Purpose: Find WordPress shortcodes that failed to render
Regex: \[wp_\w+\].*?\[\/wp_\w+\]
Example Match: [wp_gallery albums="123"] on WPR.org
Use Case: Track broken gallery shortcodes after theme update
```

---

## For Developers

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/yourusername/website-analyzer.git
cd website-analyzer

# Create virtual environment
python3.11 -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -r requirements.txt
python -m playwright install chromium

# Install development dependencies
pip install pytest black flake8 pytest-asyncio
```

### Code Style

We follow Python standards:

```bash
# Format code
python -m black src/ tests/

# Lint code
python -m flake8 src/ tests/ --max-line-length=100

# Run tests
python -m pytest tests/ -v
```

### Making Changes

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/my-feature
   # or
   git checkout -b fix/issue-123
   ```

2. **Make your changes**:
   - Keep commits focused and atomic
   - Write clear commit messages
   - Update documentation as needed

3. **Test your changes**:
   ```bash
   # Run tests
   python -m pytest tests/ -v

   # Test manually with a real site
   python -m src.analyzer.cli bug-finder scan \
     --example-url "..." \
     --site "..."
   ```

4. **Submit a pull request**:
   - Describe what your PR does
   - Reference related issues (#123)
   - Ensure CI checks pass

### Commit Message Format

Follow this format:

```
fix: Brief description of the fix

More detailed explanation if needed.

Fixes #123
```

**Types:**
- `fix:` - Bug fix
- `feat:` - New feature
- `docs:` - Documentation
- `test:` - Test additions/changes
- `refactor:` - Code reorganization (no behavior change)
- `perf:` - Performance improvements
- `chore:` - Build, dependencies, etc.

### Adding New Features

1. **Identify the component** where your feature belongs:
   - `src/analyzer/bug_finder.py` - Bug detection logic
   - `src/analyzer/cli.py` - CLI commands
   - `src/analyzer/crawler.py` - Web crawling
   - `src/analyzer/plugins/` - Test plugins
   - `src/analyzer/reporter.py` - Report generation

2. **Write tests first** (TDD approach):
   ```python
   # tests/test_my_feature.py
   def test_my_feature():
       # Test your feature
       result = my_feature("input")
       assert result == "expected output"
   ```

3. **Implement the feature**:
   ```python
   # src/analyzer/my_module.py
   def my_feature(input_data):
       """Do something useful with input_data."""
       return output_data
   ```

4. **Update documentation**:
   - Add to `docs/` if it's a user-facing feature
   - Add docstrings to functions
   - Update README if needed

5. **Test thoroughly**:
   ```bash
   python -m pytest tests/test_my_feature.py -v
   ```

### Adding a New Test Plugin

To create a new test plugin (e.g., `link-checker`):

1. **Create the plugin**:
   ```python
   # src/analyzer/plugins/link_checker.py
   from src.analyzer.test_plugin import TestPlugin

   class LinkChecker(TestPlugin):
       name = "link-checker"
       description = "Check for broken links"

       async def run(self, workspace, snapshot_dir, config):
           """Check all links in the snapshot."""
           # Your implementation
           return {
               "status": "pass" or "fail",
               "summary": "...",
               "details": {...}
           }
   ```

2. **Register the plugin** in `src/analyzer/plugin_loader.py`

3. **Write tests**:
   ```python
   # tests/test_link_checker.py
   @pytest.mark.asyncio
   async def test_link_checker_finds_broken_links():
       plugin = LinkChecker()
       # Test your plugin
   ```

4. **Document it** in relevant guide files

### Version Control

We follow workspace conventions:

- **Main branch**: `main` - stable, production-ready code
- **Feature branches**: `feature/*` - new features
- **Bug branches**: `fix/*` - bug fixes
- **All AI-generated commits** include `[Agent: <name>]` after subject line

See [workspace conventions](../../workspace_ops/conventions/COMMIT_CONVENTIONS.md) for details.

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_bug_finder.py -v

# Run specific test function
python -m pytest tests/test_bug_finder.py::test_pattern_generation -v

# Run with coverage
python -m pytest tests/ --cov=src/analyzer
```

### Documentation Standards

All public functions should have docstrings:

```python
def analyze_page(url: str, patterns: List[str]) -> Dict[str, Any]:
    """
    Analyze a web page for pattern matches.

    Args:
        url: The URL to analyze
        patterns: List of regex patterns to search for

    Returns:
        Dictionary with:
        - 'matches': List of matched patterns
        - 'count': Total number of matches
        - 'context': Lines around each match

    Raises:
        ValueError: If patterns are invalid
        requests.RequestException: If URL cannot be fetched
    """
    # Implementation
```

### Performance Considerations

When optimizing:

1. **Profile first**: Use `cProfile` to identify bottlenecks
2. **Benchmark changes**: Compare before/after performance
3. **Document tradeoffs**: Note any memory/speed tradeoffs
4. **Test at scale**: Verify changes work on large sites (5000+ pages)

### Security

- **Never hardcode credentials**: Use environment variables or config files
- **Validate user input**: Check patterns, URLs, and configuration
- **Be careful with regex**: Avoid catastrophic backtracking
- **Report security issues privately**: Email security@example.com instead of public issues

---

## Getting Help

- **Questions**: Open a GitHub discussion
- **Issues**: Check existing issues before creating new ones
- **Documentation**: Read the guides in `docs/`
- **Examples**: See real-world examples in `docs/examples/`

---

## Code of Conduct

Please be respectful and constructive:

- Welcome newcomers and help them get started
- Assume good intentions
- Focus on ideas, not personalities
- Help others learn and grow

---

## Development Roadmap

See [feature_list.json](feature_list.json) for the complete list of 127 planned features across 5 phases:

- **Phase 1: Foundation** - Basic scanning and reporting
- **Phase 2: Intelligence** - LLM-powered recommendations
- **Phase 3: Integration** - MCP, CI/CD, notifications
- **Phase 4: Enterprise** - Multi-user, API, webhooks
- **Phase 5: Polish** - Performance, stability, docs

Contributions to any phase are welcome!

---

## Recognition

Contributors are recognized in:
- GitHub commit history
- `CONTRIBUTORS.md` (coming soon)
- Monthly contributor report

Thank you for helping make Website Analyzer better! 🚀

---

**Questions?** Open an issue or start a discussion on GitHub.
