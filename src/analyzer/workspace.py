"""Workspace manager for handling project directories and metadata.

Provides functionality to:
- Generate filesystem-safe slugs from URLs
- Create new project workspaces with proper directory structure
- Load existing workspaces and validate their structure
- Manage project metadata (URL, timestamps, crawl history)
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from pydantic import BaseModel, Field


class ProjectMetadata(BaseModel):
    """Schema for project metadata.json file.

    Attributes:
        url: Original website URL
        slug: Filesystem-safe slug derived from URL
        created_at: ISO 8601 timestamp when workspace was created
        last_crawl: ISO 8601 timestamp of last successful crawl (nullable)
        last_test: Name of last test executed (nullable)
    """

    model_config = {"frozen": True}

    url: str
    slug: str
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    last_crawl: Optional[str] = None
    last_test: Optional[str] = None


def slugify_url(url: str) -> str:
    """Convert a URL to a filesystem-safe slug.

    Converts URLs like:
    - https://example.com → example-com
    - https://blog.example.com/path → blog-example-com
    - https://example.com:8080 → example-com-8080

    Process:
    1. Parse URL to extract domain
    2. Remove protocol and trailing slashes
    3. Convert to lowercase
    4. Replace dots with hyphens
    5. Replace colons with hyphens (for ports)
    6. Remove any remaining special characters

    Args:
        url: URL string to convert

    Returns:
        Filesystem-safe slug string

    Raises:
        ValueError: If URL is empty or contains only invalid characters
    """
    if not url:
        raise ValueError(
            "URL cannot be empty. "
            "Please provide a valid URL, for example: https://example.com"
        )

    # Parse the URL to extract domain and port
    parsed = urlparse(url)

    # Get the network location (domain + optional port)
    netloc = parsed.netloc

    if not netloc:
        raise ValueError(
            f"Invalid URL: {url}. "
            "URL must include a protocol (http:// or https://) and a domain name. "
            "Examples: https://example.com or https://blog.example.com"
        )

    # Convert to lowercase
    slug = netloc.lower()

    # Replace dots with hyphens
    slug = slug.replace(".", "-")

    # Replace colons with hyphens (for ports)
    slug = slug.replace(":", "-")

    # Remove any remaining special characters (only allow alphanumeric and hyphens)
    slug = re.sub(r"[^a-z0-9\-]", "", slug)

    # Remove leading/trailing hyphens
    slug = slug.strip("-")

    # Remove consecutive hyphens
    slug = re.sub(r"-+", "-", slug)

    if not slug:
        raise ValueError(
            f"URL resulted in empty slug: {url}. "
            "The URL must contain valid domain characters (letters, numbers, dots). "
            "Please check that the URL is properly formatted."
        )

    return slug


class Workspace:
    """Manages project workspace for a website being analyzed.

    A workspace includes:
    - metadata.json: Project metadata (URL, timestamps)
    - issues.json: Aggregated issues found by tests
    - snapshots/: Timestamped site crawl snapshots
    - test-results/: Results from each test execution

    Attributes:
        project_dir: Path to the project directory
        metadata: ProjectMetadata instance
    """

    def __init__(self, project_dir: Path, metadata: ProjectMetadata) -> None:
        """Initialize workspace with project directory and metadata.

        Args:
            project_dir: Path to project root directory
            metadata: ProjectMetadata instance
        """
        self.project_dir = project_dir
        self.metadata = metadata

    @classmethod
    def create(cls, url: str, base_dir: Path) -> "Workspace":
        """Create a new workspace for a website.

        Creates the directory structure:
        - projects/<slug>/
          ├── metadata.json
          ├── issues.json
          ├── snapshots/ (.gitkeep)
          └── test-results/ (.gitkeep)

        Args:
            url: Website URL to create workspace for
            base_dir: Base directory where projects/ folder exists

        Returns:
            Workspace instance for the new project

        Raises:
            ValueError: If URL is invalid or workspace already exists
        """
        # Generate slug from URL
        slug = slugify_url(url)

        # Construct project directory path
        project_dir = base_dir / "projects" / slug

        # Check if workspace already exists
        if project_dir.exists():
            raise ValueError(
                f"Workspace already exists for {slug} at {project_dir}. "
                "To use this project, run: "
                f"python -m src.analyzer.cli crawl site {slug}. "
                "Or, to start fresh, delete the existing project directory first."
            )

        # Create directory structure
        project_dir.mkdir(parents=True, exist_ok=False)

        snapshots_dir = project_dir / "snapshots"
        snapshots_dir.mkdir(exist_ok=False)
        (snapshots_dir / ".gitkeep").touch()

        test_results_dir = project_dir / "test-results"
        test_results_dir.mkdir(exist_ok=False)
        (test_results_dir / ".gitkeep").touch()

        # Create metadata
        metadata = ProjectMetadata(
            url=url,
            slug=slug,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

        # Create workspace instance and save metadata
        workspace = cls(project_dir, metadata)
        workspace.save_metadata()

        # Create empty issues.json
        issues_path = project_dir / "issues.json"
        issues_path.write_text(json.dumps([], indent=2))

        return workspace

    @classmethod
    def load(cls, slug: str, base_dir: Path) -> "Workspace":
        """Load an existing workspace by slug.

        Args:
            slug: Project slug (directory name)
            base_dir: Base directory where projects/ folder exists

        Returns:
            Workspace instance for the existing project

        Raises:
            ValueError: If workspace doesn't exist or is invalid
        """
        project_dir = base_dir / "projects" / slug

        # Validate directory exists
        if not project_dir.exists():
            raise ValueError(
                f"Workspace not found for slug: {slug}. "
                f"Expected location: {project_dir}. "
                "To create a new project, run: "
                "python -m src.analyzer.cli project new <URL>. "
                "To list existing projects, run: "
                "python -m src.analyzer.cli project list"
            )

        if not project_dir.is_dir():
            raise ValueError(
                f"Project path is not a directory: {project_dir}. "
                "The project location exists but is a file instead of a directory. "
                "This is likely a filesystem error. Please remove the file and recreate the project."
            )

        # Load and validate metadata
        metadata_path = project_dir / "metadata.json"
        if not metadata_path.exists():
            raise ValueError(
                f"metadata.json not found in workspace: {project_dir}. "
                "The project directory exists but is missing required metadata. "
                "This workspace may be corrupted. "
                "To fix, either delete and recreate the project, or manually create metadata.json "
                "with the required fields: url, slug, created_at"
            )

        try:
            metadata_data = json.loads(metadata_path.read_text())
            metadata = ProjectMetadata(**metadata_data)
        except json.JSONDecodeError as e:
            raise ValueError(
                f"Invalid JSON in metadata.json: {e}. "
                f"File location: {metadata_path}. "
                "The metadata file contains malformed JSON. "
                "To fix, either manually correct the JSON syntax, or delete and recreate the project."
            )
        except Exception as e:
            raise ValueError(
                f"Failed to parse metadata: {e}. "
                f"File location: {metadata_path}. "
                "The metadata file is missing required fields (url, slug, created_at) "
                "or contains invalid values. "
                "To fix, check the file contents against the ProjectMetadata schema, "
                "or delete and recreate the project."
            )

        # Validate workspace structure
        required_dirs = ["snapshots", "test-results"]
        for dir_name in required_dirs:
            dir_path = project_dir / dir_name
            if not dir_path.is_dir():
                raise ValueError(
                    f"Missing required directory: {dir_name} in {project_dir}. "
                    "The project workspace is incomplete. "
                    f"To fix, manually create the directory: mkdir -p {dir_path}, "
                    "or delete and recreate the project."
                )

        # Validate issues.json exists
        issues_path = project_dir / "issues.json"
        if not issues_path.exists():
            raise ValueError(
                f"issues.json not found in workspace: {project_dir}. "
                "The project is missing the issues tracking file. "
                f"To fix, manually create the file: echo '[]' > {issues_path}, "
                "or delete and recreate the project."
            )

        return cls(project_dir, metadata)

    def save_metadata(self) -> None:
        """Persist metadata to metadata.json file.

        Writes the current metadata instance to JSON format.
        File is created/overwritten at projects/<slug>/metadata.json
        """
        metadata_path = self.project_dir / "metadata.json"
        metadata_json = self.metadata.model_dump_json(indent=2)
        metadata_path.write_text(metadata_json)

    def get_snapshots_dir(self) -> Path:
        """Get the snapshots directory for this workspace.

        Returns:
            Path to snapshots/ directory
        """
        return self.project_dir / "snapshots"

    def get_test_results_dir(self) -> Path:
        """Get the test-results directory for this workspace.

        Returns:
            Path to test-results/ directory
        """
        return self.project_dir / "test-results"

    def get_issues_path(self) -> Path:
        """Get the issues.json file path for this workspace.

        Returns:
            Path to issues.json file
        """
        return self.project_dir / "issues.json"


class SnapshotManager:
    """Manages timestamped snapshot directories within a workspace.

    A snapshot is a timestamped directory within the workspace's snapshots/
    folder that contains page snapshots (HTML, markdown, metadata) from a
    single crawl operation.

    Snapshot directory structure:
    - projects/<slug>/snapshots/
      ├── 2025-12-02T14-30-45-123456Z/
      │   ├── pages/
      │   ├── sitemap.json
      │   └── summary.json
      └── 2025-12-02T15-45-30-654321Z/
          └── ...
    """

    def __init__(self, snapshots_dir: Path) -> None:
        """Initialize snapshot manager for a workspace's snapshots directory.

        Args:
            snapshots_dir: Path to the workspace's snapshots/ directory
        """
        self.snapshots_dir = snapshots_dir

    @staticmethod
    def create_timestamp() -> str:
        """Generate a filesystem-safe ISO timestamp for snapshot naming.

        Returns timestamp in format: YYYY-MM-DDTHH-MM-SS.ffffffZ
        where colons are replaced with hyphens for filesystem compatibility.

        Returns:
            Timestamp string suitable for directory naming
        """
        now = datetime.utcnow()
        # Format: 2025-12-02T14:30:45.123456 -> 2025-12-02T14-30-45.123456Z
        iso_timestamp = now.isoformat()
        # Replace colons in time portion with hyphens
        # Format: YYYY-MM-DDTHH:MM:SS.ffffff -> YYYY-MM-DDTHH-MM-SS.ffffffZ
        timestamp = iso_timestamp.replace(":", "-")
        # Add Z suffix to indicate UTC timezone
        if not timestamp.endswith("Z"):
            timestamp = timestamp + "Z"
        return timestamp

    def create_snapshot_dir(self) -> Path:
        """Create a new timestamped snapshot directory.

        Creates a directory with format: YYYY-MM-DDTHH-MM-SS.ffffffZ

        Returns:
            Path to the newly created snapshot directory

        Raises:
            OSError: If directory creation fails
        """
        timestamp = self.create_timestamp()
        snapshot_dir = self.snapshots_dir / timestamp

        # Create the snapshot directory
        snapshot_dir.mkdir(parents=True, exist_ok=False)
        (snapshot_dir / "pages").mkdir(parents=True, exist_ok=False)

        return snapshot_dir

    def list_snapshots(self) -> list[Path]:
        """List all snapshot directories in reverse chronological order.

        Returns:
            List of Path objects for snapshot directories, most recent first
        """
        if not self.snapshots_dir.exists():
            return []

        # Find all directories that match timestamp pattern
        snapshots = []
        for item in self.snapshots_dir.iterdir():
            if item.is_dir() and item.name != ".gitkeep":
                snapshots.append(item)

        # Sort by name (ISO format) in reverse (most recent first)
        snapshots.sort(reverse=True)
        return snapshots

    def get_latest_snapshot(self) -> Optional[Path]:
        """Get the most recent snapshot directory.

        Returns:
            Path to the most recent snapshot, or None if no snapshots exist
        """
        snapshots = self.list_snapshots()
        return snapshots[0] if snapshots else None

    def validate_snapshot_timestamp(self, timestamp: str) -> bool:
        """Validate that a string is a properly formatted snapshot timestamp.

        Valid format: YYYY-MM-DDTHH-MM-SS.ffffffZ
        Example: 2025-12-02T14-30-45.123456Z

        Args:
            timestamp: Timestamp string to validate

        Returns:
            True if timestamp is valid, False otherwise
        """
        # Pattern for ISO-like timestamp with hyphens instead of colons in time
        pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}-\d{2}-\d{2}\.\d{6}Z$"
        return bool(re.match(pattern, timestamp))
