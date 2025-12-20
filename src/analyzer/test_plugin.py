"""TestPlugin protocol definition.

Defines the core interface for analysis plugins used by the test runner.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel, Field


class PageData(BaseModel):
    """Represents a single crawled page's data.

    Provides access to metadata and content artifacts (HTML, markdown).
    """

    url: str
    status_code: int
    timestamp: str
    title: Optional[str] = None
    links: List[str] = Field(default_factory=list)
    headers: Optional[Dict[str, str]] = None
    directory: Path

    def get_content(self) -> str:
        """Read raw HTML content."""
        return (self.directory / "raw.html").read_text(encoding="utf-8")

    def get_cleaned_html(self) -> str:
        """Read cleaned HTML content."""
        return (self.directory / "cleaned.html").read_text(encoding="utf-8")

    def get_markdown(self) -> str:
        """Read markdown content."""
        return (self.directory / "content.md").read_text(encoding="utf-8")


class SiteSnapshot(BaseModel):
    """Represents a full website snapshot.

    Contains metadata, sitemap, crawl summary, and list of all crawled pages.
    """

    snapshot_dir: Path
    timestamp: str
    root_url: str
    pages: List[PageData]
    sitemap: Dict[str, Any]
    summary: Dict[str, Any]

    @classmethod
    def load(cls, snapshot_dir: Path) -> "SiteSnapshot":
        """Load a snapshot from a directory.

        Args:
            snapshot_dir: Path to the timestamped snapshot directory.

        Returns:
            Loaded SiteSnapshot instance.

        Raises:
            ValueError: If required files (sitemap.json, summary.json) are missing.
        """
        if not snapshot_dir.exists():
            raise ValueError(
                f"Snapshot directory not found: {snapshot_dir}. "
                "The snapshot directory does not exist. "
                "This may indicate the snapshot was deleted or the path is incorrect. "
                "To create a new snapshot, recrawl the project."
            )

        # Load sitemap
        sitemap_path = snapshot_dir / "sitemap.json"
        if not sitemap_path.exists():
            raise ValueError(
                f"sitemap.json not found in {snapshot_dir}. "
                "The snapshot is incomplete. This usually means the crawl was interrupted "
                "or failed before completing. "
                "To fix, recrawl the project to create a complete snapshot."
            )
        sitemap = json.loads(sitemap_path.read_text(encoding="utf-8"))

        # Load summary
        summary_path = snapshot_dir / "summary.json"
        if not summary_path.exists():
            # Allow missing summary for older snapshots, use default
            summary = {}
        else:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))

        # Load pages
        pages_dir = snapshot_dir / "pages"
        pages: List[PageData] = []
        if pages_dir.exists():
            for page_dir in pages_dir.iterdir():
                if not page_dir.is_dir():
                    continue
                
                metadata_path = page_dir / "metadata.json"
                if not metadata_path.exists():
                    continue
                
                try:
                    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
                    pages.append(
                        PageData(
                            url=meta["url"],
                            status_code=meta.get("status_code", 0),
                            timestamp=meta["timestamp"],
                            title=meta.get("title"),
                            links=meta.get("links", []),
                            headers=meta.get("headers"),
                            directory=page_dir,
                        )
                    )
                except Exception:
                    # Skip malformed pages
                    continue

        return cls(
            snapshot_dir=snapshot_dir,
            timestamp=snapshot_dir.name,
            root_url=sitemap.get("root", ""),
            pages=pages,
            sitemap=sitemap,
            summary=summary,
        )


class TestResult(BaseModel):
    """Result of a test plugin execution.

    Attributes:
        plugin_name: Name of the plugin that generated this result.
        timestamp: Execution timestamp (UTC ISO 8601).
        status: Outcome (pass, fail, warning, error).
        summary: Human-readable summary of findings.
        details: Structured data regarding findings (flexible schema).
    """

    plugin_name: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    status: str
    summary: str
    details: Dict[str, Any] = Field(default_factory=dict)


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

    async def analyze(self, snapshot: SiteSnapshot, **kwargs) -> TestResult:
        ...
