import asyncio
import json
import pytest
from unittest.mock import MagicMock
from src.analyzer.runner import TestRunner
from src.analyzer.test_plugin import TestResult, SiteSnapshot

class MockPlugin:
    name = "mock-plugin"
    description = "mock"
    async def analyze(self, snapshot, **kwargs):
        return TestResult(
            plugin_name=self.name, 
            status="pass", 
            summary=f"mocked {snapshot.timestamp}"
        )

class ErrorPlugin:
    name = "error-plugin"
    description = "error"
    async def analyze(self, snapshot, **kwargs):
        raise ValueError("oops")

class TimeoutPlugin:
    name = "timeout-plugin"
    description = "timeout"
    async def analyze(self, snapshot, **kwargs):
        await asyncio.sleep(0.5)
        return TestResult(plugin_name=self.name, status="pass", summary="ok")

@pytest.mark.asyncio
async def test_runner_success(tmp_path, monkeypatch):
    # Setup workspace
    base_dir = tmp_path
    projects_dir = base_dir / "projects"
    projects_dir.mkdir()
    proj_dir = projects_dir / "test-proj"
    proj_dir.mkdir()
    
    # Metadata
    (proj_dir / "metadata.json").write_text(json.dumps({
        "url": "http://example.com", 
        "slug": "test-proj",
        "created_at": "2025-01-01T00:00:00Z"
    }))
    (proj_dir / "issues.json").write_text("[]")
    (proj_dir / "snapshots").mkdir()
    (proj_dir / "test-results").mkdir()
    
    # Snapshot
    ts = "2025-01-01T00-00-00Z"
    snap_dir = proj_dir / "snapshots" / ts
    snap_dir.mkdir()
    (snap_dir / "sitemap.json").write_text(json.dumps({"root": "http://example.com"}))
    (snap_dir / "summary.json").write_text(json.dumps({}))
    (snap_dir / "pages").mkdir()
    
    # Mock load_plugins
    monkeypatch.setattr("src.analyzer.runner.load_plugins", lambda: [MockPlugin()])
    
    runner = TestRunner(base_dir)
    results = await runner.run("test-proj")
    
    assert len(results) == 1
    assert results[0].plugin_name == "mock-plugin"
    assert results[0].summary == f"mocked {ts}"


@pytest.mark.asyncio
async def test_runner_handles_exception(tmp_path, monkeypatch):
    # Setup workspace (copy-paste setup or fixture, keep simple for now)
    base_dir = tmp_path
    projects_dir = base_dir / "projects"
    projects_dir.mkdir()
    proj_dir = projects_dir / "test-proj"
    proj_dir.mkdir()
    (proj_dir / "metadata.json").write_text(json.dumps({"url": "x", "slug": "test-proj"}))
    (proj_dir / "issues.json").write_text("[]")
    (proj_dir / "snapshots").mkdir()
    (proj_dir / "test-results").mkdir()
    
    ts = "2025-01-01T00-00-00Z"
    snap_dir = proj_dir / "snapshots" / ts
    snap_dir.mkdir()
    (snap_dir / "sitemap.json").write_text('{}')
    (snap_dir / "summary.json").write_text('{}')
    
    monkeypatch.setattr("src.analyzer.runner.load_plugins", lambda: [ErrorPlugin()])
    
    runner = TestRunner(base_dir)
    results = await runner.run("test-proj")
    
    assert len(results) == 1
    assert results[0].plugin_name == "error-plugin"
    assert results[0].status == "error"
    assert "oops" in results[0].summary
    assert "traceback" in results[0].details


@pytest.mark.asyncio
async def test_runner_filters_tests(tmp_path, monkeypatch):
    # Basic setup
    base_dir = tmp_path
    projects_dir = base_dir / "projects"
    projects_dir.mkdir()
    proj_dir = projects_dir / "test-proj"
    proj_dir.mkdir()
    (proj_dir / "metadata.json").write_text(json.dumps({"url": "x", "slug": "test-proj"}))
    (proj_dir / "issues.json").write_text("[]")
    (proj_dir / "snapshots").mkdir()
    (proj_dir / "test-results").mkdir()
    
    snap_dir = proj_dir / "snapshots" / "2025-01-01T00-00-00Z"
    snap_dir.mkdir()
    (snap_dir / "sitemap.json").write_text('{}')
    (snap_dir / "summary.json").write_text('{}')

    # Two plugins
    monkeypatch.setattr("src.analyzer.runner.load_plugins", lambda: [MockPlugin(), ErrorPlugin()])
    
    runner = TestRunner(base_dir)
    # request only mock-plugin
    results = await runner.run("test-proj", test_names=["mock-plugin"])
    
    assert len(results) == 1
    assert results[0].plugin_name == "mock-plugin"


@pytest.mark.asyncio
async def test_runner_no_snapshot_error(tmp_path):
    base_dir = tmp_path
    projects_dir = base_dir / "projects"
    projects_dir.mkdir()
    proj_dir = projects_dir / "test-proj"
    proj_dir.mkdir()
    (proj_dir / "metadata.json").write_text(json.dumps({"url": "x", "slug": "test-proj"}))
    (proj_dir / "issues.json").write_text("[]")
    (proj_dir / "snapshots").mkdir()
    (proj_dir / "test-results").mkdir()
    
    runner = TestRunner(base_dir)
    with pytest.raises(ValueError, match="No snapshots found"):
        await runner.run("test-proj")


@pytest.mark.asyncio
async def test_runner_saves_results(tmp_path, monkeypatch):
    # Setup workspace
    base_dir = tmp_path
    projects_dir = base_dir / "projects"
    projects_dir.mkdir()
    proj_dir = projects_dir / "test-proj"
    proj_dir.mkdir()
    
    (proj_dir / "metadata.json").write_text(json.dumps({"url": "x", "slug": "test-proj"}))
    (proj_dir / "issues.json").write_text("[]")
    (proj_dir / "snapshots").mkdir()
    (proj_dir / "test-results").mkdir()
    
    snap_dir = proj_dir / "snapshots" / "2025-01-01T00-00-00Z"
    snap_dir.mkdir()
    (snap_dir / "sitemap.json").write_text('{}')
    (snap_dir / "summary.json").write_text('{}')
    (snap_dir / "pages").mkdir()
    
    monkeypatch.setattr("src.analyzer.runner.load_plugins", lambda: [MockPlugin()])
    
    runner = TestRunner(base_dir)
    await runner.run("test-proj", save=True)
    
    results_dir = proj_dir / "test-results"
    files = [f for f in results_dir.iterdir() if f.name != ".gitkeep"]
    
    assert len(files) == 1
    assert files[0].name.startswith("results_")
    assert files[0].name.endswith(".json")
    
    content = json.loads(files[0].read_text())
    assert len(content) == 1
    assert content[0]["plugin_name"] == "mock-plugin"


class ConfigPlugin:
    name = "config-plugin"
    description = "config"
    async def analyze(self, snapshot, **kwargs):
        return TestResult(
            plugin_name=self.name,
            status="pass",
            summary=f"config: {kwargs.get('foo')}"
        )


@pytest.mark.asyncio
async def test_runner_passes_config(tmp_path, monkeypatch):
    # Setup workspace
    base_dir = tmp_path
    projects_dir = base_dir / "projects"
    projects_dir.mkdir()
    proj_dir = projects_dir / "test-proj"
    proj_dir.mkdir()
    (proj_dir / "metadata.json").write_text(json.dumps({"url": "x", "slug": "test-proj"}))
    (proj_dir / "issues.json").write_text("[]")
    (proj_dir / "snapshots").mkdir()
    (proj_dir / "test-results").mkdir()
    
    snap_dir = proj_dir / "snapshots" / "2025-01-01T00-00-00Z"
    snap_dir.mkdir()
    (snap_dir / "sitemap.json").write_text('{}')
    (snap_dir / "summary.json").write_text('{}')
    (snap_dir / "pages").mkdir()

    monkeypatch.setattr("src.analyzer.runner.load_plugins", lambda: [ConfigPlugin()])
    
    runner = TestRunner(base_dir)
    config = {"config-plugin": {"foo": "bar"}}
    results = await runner.run("test-proj", config=config)
    
    assert len(results) == 1
    assert results[0].summary == "config: bar"

@pytest.mark.asyncio
async def test_runner_timeout(tmp_path, monkeypatch):
    base_dir = tmp_path
    projects_dir = base_dir / "projects"
    projects_dir.mkdir()
    proj_dir = projects_dir / "test-proj"
    proj_dir.mkdir()
    (proj_dir / "metadata.json").write_text(json.dumps({"url": "x", "slug": "test-proj"}))
    (proj_dir / "issues.json").write_text("[]")
    (proj_dir / "snapshots").mkdir()
    (proj_dir / "test-results").mkdir()
    
    snap_dir = proj_dir / "snapshots" / "2025-01-01T00-00-00Z"
    snap_dir.mkdir()
    (snap_dir / "sitemap.json").write_text('{}')
    (snap_dir / "summary.json").write_text('{}')
    
    monkeypatch.setattr("src.analyzer.runner.load_plugins", lambda: [TimeoutPlugin()])
    
    runner = TestRunner(base_dir)
    # Set short timeout
    results = await runner.run("test-proj", timeout_seconds=0.1)
    
    assert len(results) == 1
    assert results[0].status == "error"
    assert "timed out" in results[0].summary