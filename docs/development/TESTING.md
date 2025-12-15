# Bug Finder Test Suite - Getting Started

Welcome to the comprehensive test suite for the bug-finder tool. This document provides a quick reference to get you started with testing.

## Quick Links

- **Main Test File:** `/tests/test_bug_finder.py` (983 lines, 57 tests)
- **Test Configuration:** `/tests/conftest.py` (305 lines, 30+ fixtures)
- **Detailed Documentation:** `/tests/TEST_SUITE_README.md` (506 lines)
- **Overview & Summary:** `/BUG_FINDER_TEST_SUITE.md` (514 lines)
- **CI/CD Workflow:** `/.github/workflows/test.yml`

## Test Suite Overview

| Component | Tests | Status |
|-----------|-------|--------|
| Pattern Matching | 11 | ✅ PASSING |
| Configuration | 9 | ✅ PASSING |
| Export Formats | 8 | ✅ PASSING |
| Incremental Output | 6 | ✅ PASSING |
| Error Handling | 12 | ✅ PASSING |
| Async Integration | 4 | ✅ PASSING |
| Integration | 4 | ✅ PASSING |
| Data Validation | 4 | ✅ PASSING |
| **TOTAL** | **57** | **✅ PASSING** |

## Install & Run Tests

### One-Time Setup

```bash
cd /Users/mriechers/Developer/website-analyzer
source .venv/bin/activate
pip install pytest pytest-asyncio pytest-cov
```

### Run All Tests

```bash
pytest tests/test_bug_finder.py -v
```

### Common Commands

```bash
# Run specific test class
pytest tests/test_bug_finder.py::TestPatternMatching -v

# Run with coverage
pytest tests/test_bug_finder.py --cov=. --cov-report=html

# Run with print output visible
pytest tests/test_bug_finder.py -v -s

# Run and show slowest tests
pytest tests/test_bug_finder.py -v --durations=10

# Run only async tests
pytest tests/test_bug_finder.py::TestAsyncIntegration -v

# Run only integration tests
pytest tests/test_bug_finder.py::TestIntegration -v
```

## What's Tested

### Pattern Matching (11 tests)
- Basic `[[{` pattern detection
- Field matching: `fid`, `view_mode`, `type`
- Unicode quote character handling (various quotation marks)
- Negative tests (no false positives on clean HTML)
- Multiline and overlapping patterns
- Case insensitivity

### Configuration (9 tests)
- JSON file loading and parsing
- Required field validation
- Default value application
- Configuration merging and overrides
- URL format validation
- Nested structure handling

### Export Formats (8 tests)
- JSON export with metadata
- CSV export for spreadsheets
- HTML export for reports
- Markdown export
- Format consistency
- Special character handling
- Large datasets (1000+ records)

### Incremental Output (6 tests)
- Partial file creation (`.partial.json`)
- Atomic write patterns
- File recovery from interruptions
- Progress tracking
- Conversion from partial to final

### Error Handling (12 tests)
- Invalid URL detection
- Network failures
- Timeout errors
- Malformed HTML parsing
- Empty responses
- Regex errors
- File permission errors
- Missing configuration files
- Invalid JSON
- Retry logic
- Graceful degradation

### Async Integration (4 tests)
- Async crawler response handling
- Concurrent operations
- Failure handling
- Pattern matching on async results

### Integration (4 tests)
- End-to-end scan workflows
- Multi-format exports
- Error recovery
- Configuration-driven execution

### Data Validation (4 tests)
- URL list validation
- Result structure validation
- Metadata validation
- Consistency checks

## Key Features

### 100% No Network Access
- All external APIs mocked
- Runs completely offline
- No Crawl4AI calls needed
- CI/CD friendly

### 30+ Test Fixtures
- Mock Crawl4AI responses
- Sample HTML with various bugs
- Configuration examples
- Temporary test directories
- Error scenarios

### Well-Organized Code
- 8 logical test classes
- Clear naming conventions
- Docstrings for all tests
- Fixture reference documentation
- Arrange-Act-Assert pattern

### Production Ready
- GitHub Actions CI/CD included
- Coverage reporting
- Test artifact archival
- Ready for code review integration

## Test Fixtures (Sample Data)

Located in `/tests/fixtures/`:

- **with_wordpress_bug.html** - Single WordPress embed bug for basic testing
- **without_bug.html** - Clean HTML without any bugs (negative test)
- **multiple_bugs.html** - 5 different WordPress embed bugs
- **various_quotes.html** - Unicode quote character variations

## Pytest Fixtures (Test Setup)

Available in `conftest.py`:

**HTML Fixtures:**
- `sample_html_with_wordpress_embed` - HTML with bug
- `sample_html_without_bug` - Clean HTML
- `sample_html_multiple_bugs` - Multiple bugs
- `sample_html_various_quotes` - Quote variations

**Mock Responses:**
- `mock_crawler_response_with_bug` - AsyncMock with bug
- `mock_crawler_response_without_bug` - Clean AsyncMock response
- `mock_crawler_response_failure` - Network failure simulation

**Test Data:**
- `sample_patterns` - Pattern dictionary
- `sample_config` - Configuration example
- `sample_scan_results` - Example scan results
- `sample_scan_metadata` - Metadata example

**Directories:**
- `temp_results_dir` - Temporary output directory
- `temp_config_file` - Temporary config file
- `temp_html_fixtures` - Fixture HTML files

**Mocks:**
- `mock_async_crawler` - Mocked AsyncWebCrawler
- `mock_site_scanner` - Mocked SiteScanner
- `mock_pattern_generator` - Mocked PatternGenerator

## Performance

- **Total execution time:** 0.13-0.15 seconds
- **Test discovery:** 0.01 seconds
- **Individual test speed:** < 5ms (most)
- **Async tests:** ~0.05s total

## CI/CD Integration

GitHub Actions workflow (`.github/workflows/test.yml`):

1. Runs on push to `main` or `develop` branch
2. Runs on all pull requests
3. Tests on Python 3.11
4. Generates coverage reports
5. Archives test artifacts
6. Uploads to Codecov (optional)

## Documentation

### Comprehensive Guides

1. **BUG_FINDER_TEST_SUITE.md** - Executive summary and overview
2. **TEST_SUITE_README.md** - Complete reference documentation
3. **This file (TESTING.md)** - Quick start guide

### In the Code

- Docstrings on all test functions
- Comments explaining complex assertions
- Type hints in fixtures
- Clear variable names

## Troubleshooting

### Tests not discovered
```bash
# Check conftest.py location
ls tests/conftest.py

# Run discovery
pytest tests/test_bug_finder.py --collect-only
```

### Async test errors
```bash
# Install pytest-asyncio
pip install pytest-asyncio

# Verify it's loaded
pytest --version
```

### Import errors
```bash
# Add project to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/test_bug_finder.py -v
```

### File permission errors
```bash
# Fix fixture permissions
chmod 755 tests/fixtures
chmod 644 tests/fixtures/*.html
```

For more troubleshooting, see `TEST_SUITE_README.md`.

## Adding New Tests

1. **Choose a test class** (or create a new one)
2. **Use available fixtures** from `conftest.py`
3. **Follow the naming convention:** `test_<what>`
4. **Add a docstring** explaining the test
5. **Use Arrange-Act-Assert pattern**
6. **Run locally first**

Example:

```python
class TestNewFeature:
    """Test the new feature."""

    def test_basic_case(self, sample_config):
        """Test basic functionality."""
        # Arrange
        config = sample_config

        # Act
        result = process_config(config)

        # Assert
        assert result['success'] is True
```

## Next Steps

1. **Run the tests:** `pytest tests/test_bug_finder.py -v`
2. **Read the full docs:** `cat tests/TEST_SUITE_README.md`
3. **Check coverage:** `pytest tests/test_bug_finder.py --cov=.`
4. **Add tests for new features**
5. **Run before commits:** `pytest tests/test_bug_finder.py -v`

## Contact & Support

For questions about:
- **Running tests:** See `TEST_SUITE_README.md`
- **Adding tests:** See "Adding New Tests" above
- **Fixtures:** See `conftest.py` (documented)
- **Specific tests:** See docstrings in `test_bug_finder.py`

## Summary

You now have:
- ✅ 57 comprehensive tests
- ✅ All tests passing
- ✅ No network access required
- ✅ Ready for CI/CD
- ✅ Complete documentation
- ✅ Production-quality fixtures

**Get started:** Run `pytest tests/test_bug_finder.py -v`

---

**Last Updated:** December 11, 2024
**Test Suite Status:** Production Ready
**All Tests:** PASSING
