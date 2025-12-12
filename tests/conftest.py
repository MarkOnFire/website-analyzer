#!/usr/bin/env python3.11
"""
Pytest configuration and shared fixtures for bug finder tests.

Provides:
- Mock Crawl4AI responses
- Sample HTML fixtures
- Configuration fixtures
- Temporary directories
"""

import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime


@pytest.fixture
def sample_html_with_wordpress_embed():
    """Sample HTML containing WordPress embed bug."""
    return """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <div class="article">
            <h1>Article Title</h1>
            <p>Some content here.</p>
            <p>[[{"fid":"1101026″,"view_mode":"full_width","fields":{"format":"full_width","alignment":""},"type":"media"}]]</p>
            <p>More content after the bug.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_without_bug():
    """Sample HTML without any WordPress embed bugs."""
    return """
    <html>
    <head><title>Clean Page</title></head>
    <body>
        <div class="article">
            <h1>Normal Article</h1>
            <p>This page has no embedded bugs.</p>
            <p>Just regular content.</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_multiple_bugs():
    """Sample HTML containing multiple WordPress embed bugs."""
    return """
    <html>
    <head><title>Multiple Bugs Page</title></head>
    <body>
        <div class="article">
            <h1>Article with Multiple Bugs</h1>
            <p>[[{"fid":"1101026″,"view_mode":"full_width"}]]</p>
            <p>Some content.</p>
            <p>[[{"fid":"1101027″,"view_mode":"full_width","fields":{"format":"full_width"},"type":"media"}]]</p>
            <p>More content.</p>
            <p>"fid":"1101028″ "view_mode":"preview"</p>
        </div>
    </body>
    </html>
    """


@pytest.fixture
def sample_html_various_quotes():
    """Sample HTML with various Unicode quote characters."""
    return """
    <html>
    <body>
        <div>
            Regular quotes: ["fid":"1234", "view_mode":"full"]
            Curly quotes: "fid":"5678", "view_mode":"preview"
            Single quotes: 'fid':'9999', 'view_mode':'full'
            Mixed: ["fid":'1111', "view_mode":'normal']
        </div>
    </body>
    </html>
    """


@pytest.fixture
def mock_crawler_response_with_bug():
    """Mock Crawl4AI response with WordPress embed bug."""
    response = AsyncMock()
    response.html = """
    <html>
    <body>
        <p>[[{"fid":"1101026″,"view_mode":"full_width","type":"media"}]]</p>
    </body>
    </html>
    """
    response.success = True
    response.metadata = {
        'url': 'https://example.com/page1',
        'title': 'Example Page',
    }
    return response


@pytest.fixture
def mock_crawler_response_without_bug():
    """Mock Crawl4AI response without bugs."""
    response = AsyncMock()
    response.html = """
    <html>
    <body>
        <p>Normal content without any bugs.</p>
    </body>
    </html>
    """
    response.success = True
    response.metadata = {
        'url': 'https://example.com/clean',
        'title': 'Clean Page',
    }
    return response


@pytest.fixture
def mock_crawler_response_failure():
    """Mock Crawl4AI response with network failure."""
    response = AsyncMock()
    response.html = None
    response.success = False
    response.error_message = "Connection timeout"
    return response


@pytest.fixture
def sample_patterns():
    """Sample bug patterns for testing."""
    return {
        'opening_structure': r'\[\[\s*\{',
        'opening_with_field': r'\[\[\s*\{\s*["\'\u2018\u2019\u201C\u201D\u2033\u2034]fid["\'\u2018\u2019\u201C\u201D\u2033\u2034]',
        'multi_field': r'["\'\u2018\u2019\u201C\u201D\u2033\u2034]fid["\'\u2018\u2019\u201C\u201D\u2033\u2034][^}]{0,500}["\'\u2018\u2019\u201C\u201D\u2033\u2034]view_mode["\'\u2018\u2019\u201C\u201D\u2033\u2034]',
        'type_field': r'["\'\u2018\u2019\u201C\u201D\u2033\u2034]type["\'\u2018\u2019\u201C\u201D\u2033\u2034]\s*:\s*["\'\u2018\u2019\u201C\u201D\u2033\u2034]media["\'\u2018\u2019\u201C\u201D\u2033\u2034]',
    }


@pytest.fixture
def sample_config():
    """Sample configuration for bug finder."""
    return {
        "name": "Test Bug Finder",
        "start_url": "https://example.com",
        "max_pages": 10,
        "max_depth": 3,
        "timeout_seconds": 30,
        "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "patterns": {
            "wordpress_embed": {
                "enabled": True,
                "patterns": {
                    "multi_field": r'"fid".*"view_mode"',
                }
            }
        },
        "export": {
            "formats": ["json", "html", "csv"],
            "incremental": True,
            "output_dir": "./results"
        }
    }


@pytest.fixture
def sample_scan_results():
    """Sample scan results matching output format."""
    return [
        {
            'url': 'https://example.com/page1',
            'total_matches': 3,
            'patterns': {
                'multi_field': 2,
                'opening_with_field': 1,
            }
        },
        {
            'url': 'https://example.com/page2',
            'total_matches': 5,
            'patterns': {
                'multi_field': 3,
                'field_fid': 2,
            }
        },
        {
            'url': 'https://example.com/page3',
            'total_matches': 1,
            'patterns': {
                'opening_structure': 1,
            }
        },
    ]


@pytest.fixture
def sample_scan_metadata():
    """Sample metadata for scan results."""
    return {
        'scan_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'site_scanned': 'https://example.com',
        'example_url': 'https://archive.org/web/.../example-with-bug',
        'pages_scanned': 100,
        'total_bugs': 9,
        'scan_duration_seconds': 45.2,
    }


@pytest.fixture
def temp_results_dir(tmp_path):
    """Create a temporary directory for test results."""
    results_dir = tmp_path / "results"
    results_dir.mkdir()
    return results_dir


@pytest.fixture
def temp_config_file(tmp_path, sample_config):
    """Create a temporary config file."""
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(sample_config, indent=2))
    return config_path


@pytest.fixture
def temp_html_fixtures(tmp_path, sample_html_with_wordpress_embed, sample_html_without_bug, sample_html_multiple_bugs):
    """Create temporary HTML fixture files."""
    fixtures_dir = tmp_path / "fixtures"
    fixtures_dir.mkdir()

    (fixtures_dir / "with_bug.html").write_text(sample_html_with_wordpress_embed)
    (fixtures_dir / "without_bug.html").write_text(sample_html_without_bug)
    (fixtures_dir / "multiple_bugs.html").write_text(sample_html_multiple_bugs)

    return fixtures_dir


@pytest.fixture
def mock_async_crawler():
    """Mock AsyncWebCrawler for testing without network access."""
    with patch('bug_finder_cli.AsyncWebCrawler') as mock:
        crawler_instance = AsyncMock()
        mock.return_value.__aenter__.return_value = crawler_instance
        yield crawler_instance


@pytest.fixture
def mock_site_scanner():
    """Mock SiteScanner for testing."""
    with patch('bug_finder_cli.SiteScanner') as mock:
        scanner = AsyncMock()
        scanner.scan = AsyncMock(return_value=[
            {
                'url': 'https://example.com/page1',
                'total_matches': 3,
                'patterns': {'multi_field': 2}
            }
        ])
        mock.return_value = scanner
        yield scanner


@pytest.fixture
def mock_pattern_generator():
    """Mock PatternGenerator for testing."""
    with patch('bug_finder_cli.PatternGenerator') as mock:
        generator = MagicMock()
        generator.analyze = MagicMock(return_value=MagicMock(
            patterns={
                'multi_field': r'"fid".*"view_mode"',
                'opening_with_field': r'\[\[\s*\{\s*"fid"'
            },
            confidence='high',
            key_fields=['fid', 'view_mode', 'type']
        ))
        mock.return_value = generator
        yield generator


@pytest.fixture
def network_error():
    """Network error for testing error handling."""
    return ConnectionError("Failed to establish connection")


@pytest.fixture
def timeout_error():
    """Timeout error for testing timeout handling."""
    return TimeoutError("Request timed out after 30 seconds")


@pytest.fixture
def invalid_url_error():
    """Invalid URL error for testing."""
    return ValueError("Invalid URL format")
