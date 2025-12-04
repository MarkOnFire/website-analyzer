"""TestPlugin protocol definition.

Defines the core interface for analysis plugins used by the test runner.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class TestPlugin(Protocol):
    """Protocol for analysis plugins.

    Each plugin must declare:
    - name: human-readable name of the plugin
    - description: short summary of what the plugin checks
    - analyze(snapshot, **kwargs): async entrypoint returning a TestResult
    """

    name: str
    description: str

    async def analyze(self, snapshot, **kwargs):
        ...
