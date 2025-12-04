import json
from pathlib import Path
from typing import Any

import pytest

from src.analyzer.test_plugin import PageData, SiteSnapshot, TestPlugin, TestResult


pytestmark = pytest.mark.filterwarnings(
    "ignore:cannot collect test class 'TestPlugin':pytest.PytestCollectionWarning"
)


class DummySnapshot:
    """Minimal snapshot stub."""
    pass


class GoodPlugin:
    name = "good"
    description = "does something"

    async def analyze(self, snapshot: Any, **kwargs: Any) -> TestResult:
        return TestResult(
            plugin_name=self.name,
            status="pass",
            summary="all good",
            details={"foo": "bar"}
        )


class MissingNamePlugin:
    description = "no name"

    async def analyze(self, snapshot: Any, **kwargs: Any) -> TestResult:
        return TestResult(plugin_name="unknown", status="fail", summary="bad")


class MissingAnalyzePlugin:
    name = "missing"
    description = "no analyze"


def test_good_plugin_is_runtime_checkable():
    plugin: TestPlugin = GoodPlugin()
    assert isinstance(plugin, TestPlugin)


def test_missing_name_fails_runtime_check():
    plugin = MissingNamePlugin()
    assert not isinstance(plugin, TestPlugin)


def test_missing_analyze_fails_runtime_check():
    plugin = MissingAnalyzePlugin()
    assert not isinstance(plugin, TestPlugin)


@pytest.mark.asyncio
async def test_analyze_returns_test_result():
    plugin: TestPlugin = GoodPlugin()
    snapshot = DummySnapshot()
    result = await plugin.analyze(snapshot)
    
    assert isinstance(result, TestResult)
    assert result.plugin_name == "good"
    assert result.status == "pass"
    assert result.summary == "all good"
    assert result.details == {"foo": "bar"}
    assert result.timestamp.endswith("Z")


def test_page_data_methods(tmp_path: Path):
    page_dir = tmp_path / "page"
    page_dir.mkdir()
    (page_dir / "raw.html").write_text("<h1>raw</h1>", encoding="utf-8")
    (page_dir / "cleaned.html").write_text("<h1>cleaned</h1>", encoding="utf-8")
    (page_dir / "content.md").write_text("# content", encoding="utf-8")

    pd = PageData(
        url="http://example.com",
        status_code=200,
        timestamp="2025-01-01T00:00:00Z",
        directory=page_dir,
    )

    assert pd.get_content() == "<h1>raw</h1>"
    assert pd.get_cleaned_html() == "<h1>cleaned</h1>"
    assert pd.get_markdown() == "# content"


def test_site_snapshot_load_valid(tmp_path: Path):
    snapshot_dir = tmp_path / "snapshot"
    snapshot_dir.mkdir()
    
    # Create sitemap
    sitemap = {"root": "http://example.com", "pages": ["http://example.com"]}
    (snapshot_dir / "sitemap.json").write_text(json.dumps(sitemap), encoding="utf-8")
    
    # Create summary
    summary = {"total_pages": 1, "errors": []}
    (snapshot_dir / "summary.json").write_text(json.dumps(summary), encoding="utf-8")
    
    # Create pages
    pages_dir = snapshot_dir / "pages"
    pages_dir.mkdir()
    
    page1_dir = pages_dir / "example-com"
    page1_dir.mkdir()
    
    meta = {
        "url": "http://example.com",
        "status_code": 200,
        "timestamp": "2025-01-01T00:00:00Z",
        "title": "Example",
        "links": [],
        "headers": {"Content-Type": "text/html"}
    }
    (page1_dir / "metadata.json").write_text(json.dumps(meta), encoding="utf-8")
    (page1_dir / "raw.html").touch()
    (page1_dir / "cleaned.html").touch()
    (page1_dir / "content.md").touch()

    # Load snapshot
    snapshot = SiteSnapshot.load(snapshot_dir)
    
    assert snapshot.root_url == "http://example.com"
    assert snapshot.timestamp == "snapshot"
    assert len(snapshot.pages) == 1
    assert snapshot.pages[0].url == "http://example.com"
    assert snapshot.pages[0].title == "Example"
    assert snapshot.sitemap == sitemap
    assert snapshot.summary == summary


def test_site_snapshot_load_missing_dir(tmp_path: Path):
    with pytest.raises(ValueError, match="Snapshot directory not found"):
        SiteSnapshot.load(tmp_path / "missing")


def test_site_snapshot_load_missing_sitemap(tmp_path: Path):
    snapshot_dir = tmp_path / "snapshot"
    snapshot_dir.mkdir()
    
    with pytest.raises(ValueError, match="sitemap.json not found"):
        SiteSnapshot.load(snapshot_dir)


def test_site_snapshot_load_malformed_page(tmp_path: Path):
    snapshot_dir = tmp_path / "snapshot"
    snapshot_dir.mkdir()
    
    (snapshot_dir / "sitemap.json").write_text("{}", encoding="utf-8")
    (snapshot_dir / "summary.json").write_text("{}", encoding="utf-8")
    
    pages_dir = snapshot_dir / "pages"
    pages_dir.mkdir()
    
    # Bad page (missing metadata)
    (pages_dir / "bad-page").mkdir()
    
    # Malformed metadata page
    (pages_dir / "malformed").mkdir()
    (pages_dir / "malformed" / "metadata.json").write_text("{invalid-json", encoding="utf-8")

    snapshot = SiteSnapshot.load(snapshot_dir)
    assert len(snapshot.pages) == 0
