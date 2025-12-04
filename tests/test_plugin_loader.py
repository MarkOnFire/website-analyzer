import sys
from pathlib import Path
from typing import Any

from src.analyzer.plugin_loader import load_plugins
from src.analyzer.test_plugin import TestResult


def test_load_plugins_finds_valid_plugin(tmp_path: Path, monkeypatch):
    # Create a temporary package for plugins
    pkg_dir = tmp_path / "test_plugins_pkg"
    pkg_dir.mkdir()
    (pkg_dir / "__init__.py").touch()

    # Valid plugin
    (pkg_dir / "valid_plugin.py").write_text(
        """
from typing import Any
from src.analyzer.test_plugin import SiteSnapshot, TestResult

class ValidPlugin:
    name = "valid"
    description = "valid desc"

    async def analyze(self, snapshot: SiteSnapshot, **kwargs: Any) -> TestResult:
        return TestResult(plugin_name=self.name, status="pass", summary="ok")
""",
        encoding="utf-8",
    )

    # Invalid plugin (missing name)
    (pkg_dir / "invalid_plugin.py").write_text(
        """
from typing import Any
from src.analyzer.test_plugin import SiteSnapshot, TestResult

class InvalidPlugin:
    description = "missing name"

    async def analyze(self, snapshot: SiteSnapshot, **kwargs: Any) -> TestResult:
        return TestResult(plugin_name="unknown", status="pass", summary="ok")
""",
        encoding="utf-8",
    )

    # Add tmp_path to sys.path so we can import the package
    monkeypatch.syspath_prepend(str(tmp_path))

    plugins = load_plugins("test_plugins_pkg")

    assert len(plugins) == 1
    assert plugins[0].name == "valid"
    assert plugins[0].description == "valid desc"


def test_load_plugins_returns_empty_for_missing_pkg():
    plugins = load_plugins("non_existent_package")
    assert plugins == []
