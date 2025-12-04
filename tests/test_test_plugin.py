from typing import Any

import pytest

from src.analyzer.test_plugin import TestPlugin


pytestmark = pytest.mark.filterwarnings(
    "ignore:cannot collect test class 'TestPlugin':pytest.PytestCollectionWarning"
)


class DummySnapshot:
    """Minimal snapshot stub."""

    def __init__(self, url: str):
        self.url = url


class GoodPlugin:
    name = "good"
    description = "does something"

    async def analyze(self, snapshot: DummySnapshot, **kwargs: Any) -> str:
        return f"analyzed {snapshot.url}"


class MissingNamePlugin:
    description = "no name"

    async def analyze(self, snapshot: DummySnapshot, **kwargs: Any) -> str:
        return "ok"


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
async def test_analyze_signature_works():
    plugin: TestPlugin = GoodPlugin()
    snapshot = DummySnapshot("https://example.com")
    result = await plugin.analyze(snapshot)
    assert result == "analyzed https://example.com"
