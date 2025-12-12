# Bug Finder Test Suite Documentation

## Overview

Comprehensive test suite for the bug-finder tool with coverage for all major components:
- Pattern matching logic
- Configuration loading and merging
- Export formats (JSON, HTML, CSV, Markdown)
- Incremental output and atomic writes
- Error handling
- Async operations and Crawl4AI integration
- End-to-end integration scenarios

**Total Test Coverage:** 60+ test cases across 8 test classes

## Test Files

### Core Test Files

- **`tests/test_bug_finder.py`** - Main comprehensive test suite (60+ tests)
- **`tests/conftest.py`** - Pytest fixtures and mock data
- **`tests/fixtures/`** - Sample HTML files for testing

### Fixture Files

- **`with_wordpress_bug.html`** - HTML with single WordPress embed bug
- **`without_bug.html`** - Clean HTML without bugs
- **`multiple_bugs.html`** - HTML with 5 different WordPress embed bugs
- **`various_quotes.html`** - Tests Unicode quote character variations

## Test Classes and Coverage

### 1. TestPatternMatching (10 tests)
Tests regex pattern matching and bug detection logic.

**Tests:**
- `test_basic_wordpress_pattern` - Basic `[[{` pattern detection
- `test_fid_field_pattern` - Detects 'fid' field in embed code
- `test_view_mode_pattern` - Detects 'view_mode' field
- `test_multi_field_pattern` - Comprehensive multi-field detection
- `test_pattern_with_various_quotes` - Unicode quote variations
- `test_pattern_no_match_in_clean_html` - Negative test for clean HTML
- `test_multiple_bugs_detection` - Detects multiple bugs in single HTML
- `test_pattern_case_insensitivity` - Case-insensitive matching
- `test_pattern_with_special_characters` - Special characters in patterns
- `test_pattern_multiline_matching` - Patterns across multiple lines
- `test_overlapping_patterns` - Multiple overlapping patterns

**Key Assertions:**
- Pattern matches found in correct locations
- No false positives on clean HTML
- Multiple patterns match the same content
- Unicode quote characters handled correctly

### 2. TestConfigurationHandling (9 tests)
Tests configuration loading, validation, and merging.

**Tests:**
- `test_load_json_config` - Load JSON config file
- `test_config_validation_required_fields` - Validates required fields
- `test_config_default_values` - Default values applied
- `test_config_override_defaults` - Config values override defaults
- `test_config_pattern_merging` - Pattern config merging
- `test_config_yaml_parsing` - YAML config parsing
- `test_config_validation_url_format` - URL format validation
- `test_config_integer_validation` - Integer field validation
- `test_config_nested_merge` - Nested structure merging

**Key Assertions:**
- Config fields loaded correctly
- Defaults applied where appropriate
- Values override defaults when specified
- Merging preserves all values
- Validation rejects invalid formats

### 3. TestExportFormats (8 tests)
Tests export functionality for different file formats.

**Tests:**
- `test_export_json_format` - JSON export with metadata
- `test_export_csv_format` - CSV export for spreadsheet import
- `test_export_html_format` - HTML export with tables
- `test_export_markdown_format` - Markdown export with tables
- `test_export_format_consistency` - Same data in all formats
- `test_export_handles_special_characters` - Special characters in exports
- `test_export_empty_results` - Empty result handling
- `test_export_large_dataset` - Large dataset export (1000+ results)

**Key Assertions:**
- Files created with correct structure
- Data preserved across all formats
- Special characters escaped properly
- Large datasets handled efficiently
- All URLs included in exports

### 4. TestIncrementalOutput (6 tests)
Tests incremental output and atomic write patterns.

**Tests:**
- `test_partial_file_creation` - `.partial.json` creation
- `test_partial_to_final_conversion` - Conversion from partial to final
- `test_atomic_write_simulation` - Atomic write via temp + move
- `test_incremental_append_to_file` - Incremental result appending
- `test_partial_file_recovery` - Recovery from interrupted scans
- `test_progress_tracking` - Progress tracking in metadata

**Key Assertions:**
- Partial files created with correct structure
- Partial files can be recovered
- Atomic writes complete successfully
- Progress metadata updated correctly
- Final conversion works without data loss

### 5. TestErrorHandling (12 tests)
Tests error handling and graceful degradation.

**Tests:**
- `test_invalid_url_detection` - Invalid URL detection
- `test_network_failure_handling` - Network failure handling
- `test_timeout_error_handling` - Timeout error handling
- `test_malformed_html_handling` - Graceful HTML parsing
- `test_empty_response_handling` - Empty response handling
- `test_pattern_compilation_error` - Invalid regex detection
- `test_file_write_error_handling` - File write permission errors
- `test_config_file_not_found` - Missing config file
- `test_json_decode_error` - Invalid JSON parsing
- `test_retry_logic` - Retry mechanism for failures
- `test_graceful_degradation` - Fallback mechanisms

**Key Assertions:**
- Invalid URLs rejected
- Network errors caught and reported
- Timeouts handled appropriately
- Malformed HTML doesn't crash
- Empty responses handled gracefully
- Invalid patterns caught at compile time
- File errors properly reported
- Retry logic executes correctly

### 6. TestAsyncIntegration (4 tests)
Tests async operations and Crawl4AI integration.

**Tests:**
- `test_async_crawl_response` - Async crawler response handling
- `test_async_crawl_failure` - Crawler failure handling
- `test_concurrent_crawl_simulation` - Concurrent crawls
- `test_pattern_matching_on_crawl_results` - Pattern matching on crawled HTML

**Requirements:** `pytest-asyncio` for async test support

**Key Assertions:**
- Async operations complete successfully
- Response metadata handled correctly
- Multiple concurrent operations work
- Failure states handled appropriately

### 7. TestIntegration (3 tests)
End-to-end integration workflows.

**Tests:**
- `test_simple_scan_workflow` - Basic scan workflow
- `test_multi_format_export_workflow` - Export to multiple formats
- `test_error_recovery_workflow` - Recovery from partial failures
- `test_config_driven_workflow` - Configuration-driven workflow

**Key Assertions:**
- Complete workflows execute successfully
- Multiple export formats created
- Error recovery works as expected
- Config values properly applied

### 8. TestDataValidation (4 tests)
Tests input and output data validation.

**Tests:**
- `test_url_list_validation` - URL list validation
- `test_result_structure_validation` - Result structure validation
- `test_metadata_validation` - Metadata field validation
- `test_pattern_count_consistency` - Pattern count consistency

**Key Assertions:**
- All URLs valid before processing
- Result structure meets requirements
- All required metadata fields present
- Counts consistent across data structures

## Running Tests

### Quick Start

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/test_bug_finder.py -v

# Run with coverage
pytest tests/test_bug_finder.py --cov=. --cov-report=html
```

### Run Specific Test Classes

```bash
# Pattern matching tests only
pytest tests/test_bug_finder.py::TestPatternMatching -v

# Configuration tests only
pytest tests/test_bug_finder.py::TestConfigurationHandling -v

# Export format tests only
pytest tests/test_bug_finder.py::TestExportFormats -v

# Integration tests only
pytest tests/test_bug_finder.py::TestIntegration -v

# Async tests only
pytest tests/test_bug_finder.py::TestAsyncIntegration -v
```

### Run Specific Tests

```bash
# Single test
pytest tests/test_bug_finder.py::TestPatternMatching::test_basic_wordpress_pattern -v

# Pattern matching specific tests
pytest tests/test_bug_finder.py::TestPatternMatching::test_multi_field_pattern -v
```

### Advanced Test Running

```bash
# Run with output capture disabled (see print statements)
pytest tests/test_bug_finder.py -v -s

# Run with detailed error information
pytest tests/test_bug_finder.py -v --tb=long

# Run tests in parallel (requires pytest-xdist)
pytest tests/test_bug_finder.py -v -n auto

# Run only tests matching a pattern
pytest tests/test_bug_finder.py -v -k "pattern"

# Run with markers (if defined)
pytest tests/test_bug_finder.py -v -m "not network"

# Generate JUnit XML report
pytest tests/test_bug_finder.py --junit-xml=test-results.xml

# Generate HTML report (requires pytest-html)
pytest tests/test_bug_finder.py --html=report.html --self-contained-html
```

## Fixtures Reference

### Pytest Fixtures (from conftest.py)

**HTML Fixtures:**
- `sample_html_with_wordpress_embed` - Single WordPress bug
- `sample_html_without_bug` - Clean HTML
- `sample_html_multiple_bugs` - Multiple bugs
- `sample_html_various_quotes` - Unicode quote variations

**Mock Responses:**
- `mock_crawler_response_with_bug` - AsyncMock with WordPress bug
- `mock_crawler_response_without_bug` - AsyncMock clean response
- `mock_crawler_response_failure` - AsyncMock network failure

**Test Data:**
- `sample_patterns` - Dictionary of test patterns
- `sample_config` - Sample configuration
- `sample_scan_results` - List of scan results
- `sample_scan_metadata` - Scan metadata

**Mocks:**
- `mock_async_crawler` - Mocked AsyncWebCrawler
- `mock_site_scanner` - Mocked SiteScanner
- `mock_pattern_generator` - Mocked PatternGenerator

**Directories:**
- `temp_results_dir` - Temporary results directory
- `temp_config_file` - Temporary config file
- `temp_html_fixtures` - Directory with fixture HTML files

**Error Fixtures:**
- `network_error` - ConnectionError instance
- `timeout_error` - TimeoutError instance
- `invalid_url_error` - ValueError instance

## Test Statistics

```
Total Test Classes:      8
Total Test Functions:    60+
Pattern Matching:        11 tests
Configuration:           9 tests
Export Formats:          8 tests
Incremental Output:      6 tests
Error Handling:         12 tests
Async Integration:       4 tests
Integration Tests:       4 tests
Data Validation:         4 tests

Code Coverage Target:    80%+
Network-Free:           100% (all mocked)
```

## Continuous Integration

### GitHub Actions Workflow

The `.github/workflows/test.yml` file defines CI/CD pipeline that:

1. **Runs on:** Linux (ubuntu-latest)
2. **Python Version:** 3.11
3. **Steps:**
   - Install dependencies from requirements.txt
   - Install pytest, pytest-asyncio, pytest-cov
   - Run all tests with coverage
   - Run async tests separately
   - Run integration tests separately
   - Generate coverage reports
   - Upload to Codecov
   - Archive test results

### Running Locally (Like CI)

```bash
# Run exactly as CI does
pytest tests/test_bug_finder.py -v --tb=short --cov=. --cov-report=term-missing
```

## Coverage Report

Generate and view coverage:

```bash
# Terminal report
pytest tests/test_bug_finder.py --cov=. --cov-report=term-missing

# HTML report
pytest tests/test_bug_finder.py --cov=. --cov-report=html
open htmlcov/index.html

# Coverage badge (requires coverage-badge)
coverage-badge -o coverage.svg -f
```

## Common Issues and Solutions

### Issue: Async tests fail with "no running event loop"

**Solution:** Ensure `pytest-asyncio` is installed and tests are marked with `@pytest.mark.asyncio`

```bash
pip install pytest-asyncio
```

### Issue: Mock fixtures not working

**Solution:** Verify fixture names are spelled correctly and `conftest.py` is in the tests directory.

### Issue: Tests timeout

**Solution:** Add timeout to pytest configuration or specific tests:

```bash
pytest tests/test_bug_finder.py --timeout=300
```

### Issue: "fixture not found" error

**Solution:** Ensure conftest.py is in:
- `/tests/conftest.py` (recommended)
- In the same directory as tests

### Issue: Import errors in tests

**Solution:** Ensure the project root is in PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
pytest tests/test_bug_finder.py -v
```

## Best Practices for Test Development

1. **One assertion per test** - Tests should verify one thing
2. **Descriptive names** - Test names should describe what is being tested
3. **Use fixtures** - Leverage fixtures for setup/teardown
4. **Mock external APIs** - Don't make real network calls
5. **Test error cases** - Include negative tests
6. **Keep tests fast** - Aim for < 100ms per test
7. **Avoid dependencies** - Tests should not depend on each other
8. **Document complex tests** - Add docstrings explaining test purpose

## Adding New Tests

### Template for New Test Class

```python
class TestNewFeature:
    """Test description."""

    def test_basic_functionality(self, fixture_name):
        """Test basic functionality."""
        # Arrange
        input_data = fixture_name

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_value

    @pytest.mark.asyncio
    async def test_async_functionality(self):
        """Test async functionality."""
        result = await async_function()
        assert result is not None
```

## Debugging Tests

### Print Debugging

```bash
# Run with print output visible
pytest tests/test_bug_finder.py::TestClass::test_name -v -s
```

### PDB Debugging

```python
def test_something():
    result = function()
    import pdb; pdb.set_trace()  # Debug here
    assert result == expected
```

Then run with:
```bash
pytest tests/test_bug_finder.py::test_something -v -s
```

### Verbose Output

```bash
pytest tests/test_bug_finder.py -vv --tb=long
```

## Performance Testing

### Run with timing info

```bash
pytest tests/test_bug_finder.py -v --durations=10
```

This shows the 10 slowest tests.

## Test Maintenance

### Update fixtures when requirements change

1. Edit `conftest.py` with new fixture
2. Add tests for new fixture
3. Run `pytest --collect-only` to verify discovery
4. Update this documentation

### Archive old tests

Keep removed tests in comments or separate branches for reference.

### Review coverage regularly

```bash
# Quick coverage summary
coverage report -m
```

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/how-to/fixtures.html)
- [Pytest Async](https://pytest-asyncio.readthedocs.io/)
- [Mock Testing](https://docs.python.org/3/library/unittest.mock.html)
- [Python Testing Best Practices](https://realpython.com/python-testing/)

## Support

For test-related questions or issues:

1. Check this README
2. Review existing tests for examples
3. Check conftest.py for available fixtures
4. Run `pytest --collect-only` to see all tests
5. Use `pytest -v` for detailed output

---

**Last Updated:** December 11, 2024
**Test Suite Version:** 1.0
**Compatibility:** Python 3.11+
