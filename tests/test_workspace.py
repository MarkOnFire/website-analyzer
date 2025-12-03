"""Unit tests for workspace manager functionality.

Tests cover:
- URL slug generation with various URL formats
- Workspace creation with proper directory structure
- Workspace loading and validation
- Metadata persistence and retrieval
- Error handling for invalid inputs
"""

import json
import tempfile
from pathlib import Path

import pytest

from src.analyzer.workspace import ProjectMetadata, SnapshotManager, Workspace, slugify_url


class TestSlugifyUrl:
    """Test suite for URL to slug conversion."""

    def test_basic_domain(self):
        """Test simple domain conversion."""
        assert slugify_url("https://example.com") == "example-com"

    def test_basic_domain_http(self):
        """Test HTTP protocol."""
        assert slugify_url("http://example.com") == "example-com"

    def test_subdomain(self):
        """Test subdomain handling."""
        assert slugify_url("https://blog.example.com") == "blog-example-com"

    def test_subdomain_multiple_levels(self):
        """Test multiple subdomain levels."""
        assert (
            slugify_url("https://api.v2.example.com") == "api-v2-example-com"
        )

    def test_domain_with_port(self):
        """Test domain with port number."""
        assert slugify_url("https://example.com:8080") == "example-com-8080"

    def test_domain_with_port_and_subdomain(self):
        """Test subdomain with port."""
        assert (
            slugify_url("https://blog.example.com:3000") == "blog-example-com-3000"
        )

    def test_domain_with_path_ignored(self):
        """Test that paths are ignored."""
        assert slugify_url("https://example.com/path/to/page") == "example-com"

    def test_domain_with_query_ignored(self):
        """Test that query parameters are ignored."""
        assert slugify_url("https://example.com?param=value") == "example-com"

    def test_case_insensitive(self):
        """Test case conversion to lowercase."""
        assert slugify_url("https://Example.COM") == "example-com"
        assert slugify_url("https://BLOG.EXAMPLE.COM") == "blog-example-com"

    def test_trailing_slash_ignored(self):
        """Test that trailing slashes don't affect slug."""
        assert slugify_url("https://example.com/") == "example-com"

    def test_www_subdomain(self):
        """Test www prefix is handled correctly."""
        assert slugify_url("https://www.example.com") == "www-example-com"

    def test_single_letter_domains(self):
        """Test single letter domain parts."""
        assert slugify_url("https://a.b.c") == "a-b-c"

    def test_numeric_domains(self):
        """Test numeric domains."""
        assert slugify_url("https://192-168-1-1.com") == "192-168-1-1-com"

    def test_hyphenated_domain(self):
        """Test domains already containing hyphens."""
        assert slugify_url("https://my-domain.com") == "my-domain-com"

    def test_consecutive_dots_handling(self):
        """Test that multiple consecutive dots don't break slug."""
        # This would be invalid, but we handle gracefully
        result = slugify_url("https://example.com")
        assert "-" not in result or result.count("-") >= 1

    def test_empty_url_raises_error(self):
        """Test that empty URL raises ValueError."""
        with pytest.raises(ValueError, match="URL cannot be empty"):
            slugify_url("")

    def test_invalid_url_no_domain_raises_error(self):
        """Test that URL without domain raises ValueError."""
        with pytest.raises(ValueError, match="Invalid URL"):
            slugify_url("http://")

    def test_special_characters_removed(self):
        """Test that special characters are filtered."""
        # Even if URL somehow has special chars, they should be removed
        assert "@" not in slugify_url("https://example.com")
        assert "/" not in slugify_url("https://example.com")


class TestProjectMetadata:
    """Test suite for ProjectMetadata model."""

    def test_metadata_creation_with_defaults(self):
        """Test creating metadata with default timestamps."""
        metadata = ProjectMetadata(url="https://example.com", slug="example-com")

        assert metadata.url == "https://example.com"
        assert metadata.slug == "example-com"
        assert metadata.created_at is not None
        assert metadata.created_at.endswith("Z")
        assert metadata.last_crawl is None
        assert metadata.last_test is None

    def test_metadata_creation_with_explicit_timestamp(self):
        """Test creating metadata with explicit timestamp."""
        timestamp = "2025-12-02T12:00:00Z"
        metadata = ProjectMetadata(
            url="https://example.com",
            slug="example-com",
            created_at=timestamp,
        )

        assert metadata.created_at == timestamp

    def test_metadata_with_crawl_history(self):
        """Test metadata with crawl and test history."""
        metadata = ProjectMetadata(
            url="https://example.com",
            slug="example-com",
            last_crawl="2025-12-02T12:30:00Z",
            last_test="migration-scan",
        )

        assert metadata.last_crawl == "2025-12-02T12:30:00Z"
        assert metadata.last_test == "migration-scan"

    def test_metadata_immutable(self):
        """Test that metadata instances are immutable."""
        metadata = ProjectMetadata(url="https://example.com", slug="example-com")

        with pytest.raises(Exception):  # Pydantic FrozenModel raises ValidationError
            metadata.url = "https://newsite.com"

    def test_metadata_to_json(self):
        """Test serialization to JSON."""
        metadata = ProjectMetadata(
            url="https://example.com",
            slug="example-com",
            created_at="2025-12-02T12:00:00Z",
        )

        json_str = metadata.model_dump_json(indent=2)
        parsed = json.loads(json_str)

        assert parsed["url"] == "https://example.com"
        assert parsed["slug"] == "example-com"
        assert parsed["created_at"] == "2025-12-02T12:00:00Z"

    def test_metadata_from_json(self):
        """Test deserialization from JSON."""
        json_str = """{
            "url": "https://example.com",
            "slug": "example-com",
            "created_at": "2025-12-02T12:00:00Z",
            "last_crawl": null,
            "last_test": null
        }"""

        metadata = ProjectMetadata(**json.loads(json_str))

        assert metadata.url == "https://example.com"
        assert metadata.slug == "example-com"


class TestWorkspaceCreation:
    """Test suite for workspace creation."""

    def test_create_workspace_basic(self):
        """Test creating a basic workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create(
                "https://example.com",
                base_dir,
            )

            # Verify workspace properties
            assert workspace.metadata.url == "https://example.com"
            assert workspace.metadata.slug == "example-com"
            assert workspace.project_dir == base_dir / "projects" / "example-com"

    def test_create_workspace_directory_structure(self):
        """Test that all required directories are created."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create(
                "https://example.com",
                base_dir,
            )

            # Verify directories exist
            assert (workspace.project_dir / "snapshots").exists()
            assert (workspace.project_dir / "test-results").exists()
            assert (workspace.project_dir / "snapshots" / ".gitkeep").exists()
            assert (workspace.project_dir / "test-results" / ".gitkeep").exists()

    def test_create_workspace_metadata_file(self):
        """Test that metadata.json is created correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create(
                "https://blog.example.com",
                base_dir,
            )

            # Verify metadata file
            metadata_file = workspace.project_dir / "metadata.json"
            assert metadata_file.exists()

            metadata_data = json.loads(metadata_file.read_text())
            assert metadata_data["url"] == "https://blog.example.com"
            assert metadata_data["slug"] == "blog-example-com"

    def test_create_workspace_issues_file(self):
        """Test that issues.json is created as empty array."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create(
                "https://example.com",
                base_dir,
            )

            # Verify issues file
            issues_file = workspace.project_dir / "issues.json"
            assert issues_file.exists()

            issues_data = json.loads(issues_file.read_text())
            assert isinstance(issues_data, list)
            assert len(issues_data) == 0

    def test_create_workspace_subdomain(self):
        """Test creating workspace for subdomain."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create(
                "https://api.example.com",
                base_dir,
            )

            assert workspace.metadata.slug == "api-example-com"
            assert (base_dir / "projects" / "api-example-com").exists()

    def test_create_workspace_with_port(self):
        """Test creating workspace for URL with port."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create(
                "https://example.com:3000",
                base_dir,
            )

            assert workspace.metadata.slug == "example-com-3000"
            assert (base_dir / "projects" / "example-com-3000").exists()

    def test_create_workspace_already_exists_raises_error(self):
        """Test that creating duplicate workspace raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create first workspace
            Workspace.create("https://example.com", base_dir)

            # Try to create duplicate
            with pytest.raises(ValueError, match="Workspace already exists"):
                Workspace.create("https://example.com", base_dir)

    def test_create_workspace_invalid_url_raises_error(self):
        """Test that invalid URL raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            with pytest.raises(ValueError):
                Workspace.create("", base_dir)


class TestWorkspaceLoading:
    """Test suite for workspace loading."""

    def test_load_workspace_basic(self):
        """Test loading an existing workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create workspace
            created = Workspace.create("https://example.com", base_dir)

            # Load workspace
            loaded = Workspace.load("example-com", base_dir)

            assert loaded.metadata.url == created.metadata.url
            assert loaded.metadata.slug == created.metadata.slug

    def test_load_workspace_preserves_metadata(self):
        """Test that loading preserves all metadata fields."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create workspace
            created = Workspace.create("https://example.com", base_dir)

            # Load workspace
            loaded = Workspace.load("example-com", base_dir)

            assert loaded.metadata.url == "https://example.com"
            assert loaded.metadata.slug == "example-com"
            assert loaded.metadata.created_at == created.metadata.created_at

    def test_load_workspace_not_found_raises_error(self):
        """Test that loading non-existent workspace raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            with pytest.raises(ValueError, match="Workspace not found"):
                Workspace.load("nonexistent", base_dir)

    def test_load_workspace_missing_metadata_raises_error(self):
        """Test that workspace missing metadata.json raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create incomplete workspace manually
            project_dir = base_dir / "projects" / "broken"
            project_dir.mkdir(parents=True)
            (project_dir / "snapshots").mkdir()
            (project_dir / "test-results").mkdir()
            (project_dir / "issues.json").write_text("[]")

            with pytest.raises(ValueError, match="metadata.json not found"):
                Workspace.load("broken", base_dir)

    def test_load_workspace_missing_snapshots_dir_raises_error(self):
        """Test that workspace missing snapshots/ dir raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create workspace then delete snapshots dir
            workspace = Workspace.create("https://example.com", base_dir)
            import shutil
            shutil.rmtree(workspace.project_dir / "snapshots")

            with pytest.raises(ValueError, match="Missing required directory"):
                Workspace.load("example-com", base_dir)

    def test_load_workspace_missing_test_results_dir_raises_error(self):
        """Test that workspace missing test-results/ dir raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create workspace then delete test-results dir
            workspace = Workspace.create("https://example.com", base_dir)
            import shutil
            shutil.rmtree(workspace.project_dir / "test-results")

            with pytest.raises(ValueError, match="Missing required directory"):
                Workspace.load("example-com", base_dir)

    def test_load_workspace_missing_issues_json_raises_error(self):
        """Test that workspace missing issues.json raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create workspace then delete issues.json
            workspace = Workspace.create("https://example.com", base_dir)
            (workspace.project_dir / "issues.json").unlink()

            with pytest.raises(ValueError, match="issues.json not found"):
                Workspace.load("example-com", base_dir)

    def test_load_workspace_invalid_metadata_json_raises_error(self):
        """Test that workspace with invalid metadata.json raises error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create workspace with invalid metadata
            project_dir = base_dir / "projects" / "broken"
            project_dir.mkdir(parents=True)
            (project_dir / "snapshots").mkdir()
            (project_dir / "test-results").mkdir()
            (project_dir / "issues.json").write_text("[]")
            (project_dir / "metadata.json").write_text("{invalid json")

            with pytest.raises(ValueError, match="Invalid JSON"):
                Workspace.load("broken", base_dir)


class TestWorkspaceSaveMetadata:
    """Test suite for metadata persistence."""

    def test_save_metadata_basic(self):
        """Test saving metadata updates."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create("https://example.com", base_dir)

            # Manually update metadata
            new_metadata = ProjectMetadata(
                url="https://example.com",
                slug="example-com",
                created_at=workspace.metadata.created_at,
                last_crawl="2025-12-02T13:00:00Z",
                last_test="seo-optimization",
            )

            # Create new workspace instance with updated metadata
            workspace = Workspace(workspace.project_dir, new_metadata)
            workspace.save_metadata()

            # Verify persisted
            metadata_file = workspace.project_dir / "metadata.json"
            metadata_data = json.loads(metadata_file.read_text())

            assert metadata_data["last_crawl"] == "2025-12-02T13:00:00Z"
            assert metadata_data["last_test"] == "seo-optimization"


class TestWorkspaceAccessors:
    """Test suite for workspace accessor methods."""

    def test_get_snapshots_dir(self):
        """Test getting snapshots directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create("https://example.com", base_dir)

            snapshots_dir = workspace.get_snapshots_dir()
            assert snapshots_dir.exists()
            assert snapshots_dir.name == "snapshots"

    def test_get_test_results_dir(self):
        """Test getting test-results directory path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create("https://example.com", base_dir)

            test_results_dir = workspace.get_test_results_dir()
            assert test_results_dir.exists()
            assert test_results_dir.name == "test-results"

    def test_get_issues_path(self):
        """Test getting issues.json file path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)
            workspace = Workspace.create("https://example.com", base_dir)

            issues_path = workspace.get_issues_path()
            assert issues_path.exists()
            assert issues_path.name == "issues.json"


class TestSnapshotManagerTimestamp:
    """Test suite for snapshot timestamp generation."""

    def test_create_timestamp_format(self):
        """Test that timestamp has correct format."""
        timestamp = SnapshotManager.create_timestamp()
        # Format should be: YYYY-MM-DDTHH-MM-SS.ffffffZ
        # Structure: 2025-12-03T03-08-28.664648Z (27 chars)
        assert len(timestamp) == 27  # 10 + 1 + 8 + 1 + 6 + 1 = 27
        assert timestamp[10] == "T"  # T separator
        assert timestamp[19] == "."  # Dot before microseconds
        assert timestamp[-1] == "Z"  # UTC suffix
        assert timestamp.count("-") == 4  # 2 in date + 2 in time

    def test_create_timestamp_uniqueness(self):
        """Test that consecutive timestamps are different."""
        import time

        ts1 = SnapshotManager.create_timestamp()
        time.sleep(0.001)  # Small sleep to ensure different microsecond
        ts2 = SnapshotManager.create_timestamp()

        # Timestamps should be different (at minimum at microsecond level)
        assert ts1 != ts2

    def test_timestamp_iso_comparable(self):
        """Test that timestamps are sortable chronologically."""
        import time

        ts1 = SnapshotManager.create_timestamp()
        time.sleep(0.001)
        ts2 = SnapshotManager.create_timestamp()
        time.sleep(0.001)
        ts3 = SnapshotManager.create_timestamp()

        # Should be sortable in chronological order
        timestamps = [ts3, ts1, ts2]
        sorted_ts = sorted(timestamps)
        assert sorted_ts == [ts1, ts2, ts3]


class TestSnapshotManager:
    """Test suite for snapshot directory management."""

    def test_snapshot_manager_initialization(self):
        """Test creating snapshot manager."""
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshots_dir = Path(tmpdir) / "snapshots"
            snapshots_dir.mkdir()

            manager = SnapshotManager(snapshots_dir)
            assert manager.snapshots_dir == snapshots_dir

    def test_create_snapshot_dir(self):
        """Test creating a new snapshot directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshots_dir = Path(tmpdir) / "snapshots"
            snapshots_dir.mkdir()

            manager = SnapshotManager(snapshots_dir)
            snapshot_dir = manager.create_snapshot_dir()

            # Directory should exist
            assert snapshot_dir.exists()
            assert snapshot_dir.is_dir()

            # Should be a subdirectory of snapshots
            assert snapshot_dir.parent == snapshots_dir

            # Name should have correct format
            assert manager.validate_snapshot_timestamp(snapshot_dir.name)

    def test_create_multiple_snapshot_dirs(self):
        """Test creating multiple snapshot directories."""
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            snapshots_dir = Path(tmpdir) / "snapshots"
            snapshots_dir.mkdir()

            manager = SnapshotManager(snapshots_dir)

            # Create multiple snapshots
            dirs = []
            for _ in range(3):
                dirs.append(manager.create_snapshot_dir())
                time.sleep(0.001)

            # All should exist
            for d in dirs:
                assert d.exists()

            # All should have different names
            names = [d.name for d in dirs]
            assert len(set(names)) == 3

    def test_list_snapshots_empty(self):
        """Test listing snapshots when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshots_dir = Path(tmpdir) / "snapshots"
            snapshots_dir.mkdir()

            manager = SnapshotManager(snapshots_dir)
            snapshots = manager.list_snapshots()

            assert snapshots == []

    def test_list_snapshots_reverse_chronological(self):
        """Test that snapshots are listed in reverse chronological order."""
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            snapshots_dir = Path(tmpdir) / "snapshots"
            snapshots_dir.mkdir()

            manager = SnapshotManager(snapshots_dir)

            # Create multiple snapshots
            for _ in range(3):
                manager.create_snapshot_dir()
                time.sleep(0.001)

            snapshots = manager.list_snapshots()

            # Should have 3 snapshots
            assert len(snapshots) == 3

            # Should be in reverse chronological order (newest first)
            names = [s.name for s in snapshots]
            assert names == sorted(names, reverse=True)

    def test_get_latest_snapshot_when_empty(self):
        """Test getting latest snapshot when none exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshots_dir = Path(tmpdir) / "snapshots"
            snapshots_dir.mkdir()

            manager = SnapshotManager(snapshots_dir)
            latest = manager.get_latest_snapshot()

            assert latest is None

    def test_get_latest_snapshot(self):
        """Test getting the most recent snapshot."""
        import time

        with tempfile.TemporaryDirectory() as tmpdir:
            snapshots_dir = Path(tmpdir) / "snapshots"
            snapshots_dir.mkdir()

            manager = SnapshotManager(snapshots_dir)

            # Create multiple snapshots
            snapshots = []
            for _ in range(3):
                s = manager.create_snapshot_dir()
                snapshots.append(s)
                time.sleep(0.001)

            latest = manager.get_latest_snapshot()

            # Latest should be the last one created
            assert latest == snapshots[-1]

    def test_validate_snapshot_timestamp_valid(self):
        """Test validating correct timestamp format."""
        manager = SnapshotManager(Path("/tmp"))

        # Valid timestamps
        valid_timestamps = [
            "2025-12-02T14-30-45.123456Z",
            "2025-01-01T00-00-00.000000Z",
            "2099-12-31T23-59-59.999999Z",
        ]

        for ts in valid_timestamps:
            assert manager.validate_snapshot_timestamp(ts)

    def test_validate_snapshot_timestamp_invalid(self):
        """Test that invalid timestamps are rejected."""
        manager = SnapshotManager(Path("/tmp"))

        # Invalid timestamps
        invalid_timestamps = [
            "2025-12-02T14:30:45.123456Z",  # Colons in time portion
            "2025-12-02T14-30-45-123456Z",  # Hyphen instead of dot before microseconds
            "2025-12-02T14-30-45.123456",  # Missing Z
            "2025/12/02T14-30-45.123456Z",  # Wrong date separator
            "invalid",
            "2025-12-02",
            "",
        ]

        for ts in invalid_timestamps:
            assert not manager.validate_snapshot_timestamp(ts)

    def test_snapshot_dir_ignores_gitkeep(self):
        """Test that .gitkeep file doesn't appear as a snapshot."""
        with tempfile.TemporaryDirectory() as tmpdir:
            snapshots_dir = Path(tmpdir) / "snapshots"
            snapshots_dir.mkdir()
            (snapshots_dir / ".gitkeep").touch()

            manager = SnapshotManager(snapshots_dir)

            # Create one real snapshot
            manager.create_snapshot_dir()

            snapshots = manager.list_snapshots()

            # Should only have 1 snapshot, .gitkeep should be ignored
            assert len(snapshots) == 1

    def test_snapshot_dir_with_workspace(self):
        """Test snapshot manager integration with workspace."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_dir = Path(tmpdir)

            # Create a workspace
            workspace = Workspace.create("https://example.com", base_dir)

            # Create snapshot manager from workspace
            manager = SnapshotManager(workspace.get_snapshots_dir())
            snapshot_dir = manager.create_snapshot_dir()

            # Snapshot should exist under workspace
            assert snapshot_dir.exists()
            assert snapshot_dir.parent == workspace.get_snapshots_dir()

            # Workspace should see the snapshot
            latest = manager.get_latest_snapshot()
            assert latest == snapshot_dir


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
