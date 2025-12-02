"""Workspace manager for handling project directories and metadata.

Provides functionality to:
- Generate filesystem-safe slugs from URLs
- Create new project workspaces with proper directory structure
- Load existing workspaces and validate their structure
- Manage project metadata (URL, timestamps, crawl history)
"""

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
        raise ValueError("URL cannot be empty")

    # Parse the URL to extract domain and port
    parsed = urlparse(url)

    # Get the network location (domain + optional port)
    netloc = parsed.netloc

    if not netloc:
        raise ValueError(f"Invalid URL: {url}")

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
        raise ValueError(f"URL resulted in empty slug: {url}")

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
                f"Workspace already exists for {slug} at {project_dir}"
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
            raise ValueError(f"Workspace not found for slug: {slug}")

        if not project_dir.is_dir():
            raise ValueError(f"Project path is not a directory: {project_dir}")

        # Load and validate metadata
        metadata_path = project_dir / "metadata.json"
        if not metadata_path.exists():
            raise ValueError(f"metadata.json not found in workspace: {project_dir}")

        try:
            metadata_data = json.loads(metadata_path.read_text())
            metadata = ProjectMetadata(**metadata_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in metadata.json: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse metadata: {e}")

        # Validate workspace structure
        required_dirs = ["snapshots", "test-results"]
        for dir_name in required_dirs:
            dir_path = project_dir / dir_name
            if not dir_path.is_dir():
                raise ValueError(
                    f"Missing required directory: {dir_name} in {project_dir}"
                )

        # Validate issues.json exists
        issues_path = project_dir / "issues.json"
        if not issues_path.exists():
            raise ValueError(f"issues.json not found in workspace: {project_dir}")

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
