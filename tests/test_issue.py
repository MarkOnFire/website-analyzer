"""Tests for issue tracking module."""

import json
import pytest
from pathlib import Path

from src.analyzer.issue import (
    Issue,
    IssueManager,
    IssueAggregator,
    IssuePriority,
    IssueStatus,
    StatusTransition,
    transition_status,
    find_duplicate,
    detect_resolutions,
    VALID_TRANSITIONS,
)
from src.analyzer.test_plugin import TestResult


class TestIssue:
    """Tests for Issue model."""

    def test_create_issue(self):
        """Test creating a basic issue."""
        issue = Issue(
            id="ISSUE-001",
            test_name="migration-scanner",
            priority=IssuePriority.HIGH,
            status=IssueStatus.OPEN,
            title="Found deprecated jQuery patterns",
            affected_urls=["https://example.com/page1", "https://example.com/page2"],
        )

        assert issue.id == "ISSUE-001"
        assert issue.test_name == "migration-scanner"
        assert issue.priority == IssuePriority.HIGH
        assert issue.status == IssueStatus.OPEN
        assert len(issue.affected_urls) == 2

    def test_issue_defaults(self):
        """Test issue default values."""
        issue = Issue(
            id="ISSUE-001",
            test_name="test",
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.OPEN,
            title="Test issue",
        )

        assert issue.affected_urls == []
        assert issue.details == {}
        assert issue.resolved_at is None
        assert issue.status_history == []
        assert issue.created_at.endswith("Z")

    def test_issue_serialization(self):
        """Test issue JSON serialization."""
        issue = Issue(
            id="ISSUE-001",
            test_name="test",
            priority=IssuePriority.CRITICAL,
            status=IssueStatus.INVESTIGATING,
            title="Critical issue",
            details={"key": "value"},
        )

        data = issue.model_dump()
        assert data["id"] == "ISSUE-001"
        assert data["priority"] == "critical"
        assert data["status"] == "investigating"
        assert data["details"]["key"] == "value"


class TestStatusTransitions:
    """Tests for status transition state machine."""

    def test_valid_transition_open_to_investigating(self):
        """Test valid transition from open to investigating."""
        issue = Issue(
            id="ISSUE-001",
            test_name="test",
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.OPEN,
            title="Test issue",
        )

        updated = transition_status(issue, IssueStatus.INVESTIGATING, "Started investigation")

        assert updated.status == IssueStatus.INVESTIGATING
        assert len(updated.status_history) == 1
        assert updated.status_history[0].from_status == "open"
        assert updated.status_history[0].to_status == "investigating"
        assert updated.status_history[0].reason == "Started investigation"

    def test_valid_transition_investigating_to_fixed(self):
        """Test valid transition from investigating to fixed."""
        issue = Issue(
            id="ISSUE-001",
            test_name="test",
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.INVESTIGATING,
            title="Test issue",
        )

        updated = transition_status(issue, IssueStatus.FIXED, "Applied fix")

        assert updated.status == IssueStatus.FIXED
        assert updated.resolved_at is not None

    def test_valid_transition_fixed_to_verified(self):
        """Test valid transition from fixed to verified."""
        issue = Issue(
            id="ISSUE-001",
            test_name="test",
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.FIXED,
            title="Test issue",
        )

        updated = transition_status(issue, IssueStatus.VERIFIED, "Verified in production")

        assert updated.status == IssueStatus.VERIFIED

    def test_invalid_transition_open_to_verified(self):
        """Test invalid transition raises error."""
        issue = Issue(
            id="ISSUE-001",
            test_name="test",
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.OPEN,
            title="Test issue",
        )

        with pytest.raises(ValueError, match="Invalid transition"):
            transition_status(issue, IssueStatus.VERIFIED, "Skip steps")

    def test_reopen_from_fixed(self):
        """Test reopening an issue from fixed status."""
        issue = Issue(
            id="ISSUE-001",
            test_name="test",
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.FIXED,
            title="Test issue",
        )

        updated = transition_status(issue, IssueStatus.OPEN, "Regression detected")

        assert updated.status == IssueStatus.OPEN


class TestIssueManager:
    """Tests for IssueManager."""

    def test_load_empty_issues(self, tmp_path: Path):
        """Test loading from empty issues.json."""
        issues_path = tmp_path / "issues.json"
        issues_path.write_text("[]")

        manager = IssueManager(issues_path)
        issues = manager.load_issues()

        assert issues == []

    def test_load_nonexistent_file(self, tmp_path: Path):
        """Test loading when file doesn't exist."""
        issues_path = tmp_path / "issues.json"

        manager = IssueManager(issues_path)
        issues = manager.load_issues()

        assert issues == []

    def test_save_and_load_issues(self, tmp_path: Path):
        """Test saving and reloading issues."""
        issues_path = tmp_path / "issues.json"

        manager = IssueManager(issues_path)

        issue = Issue(
            id="ISSUE-001",
            test_name="test",
            priority=IssuePriority.HIGH,
            status=IssueStatus.OPEN,
            title="Test issue",
            affected_urls=["https://example.com"],
        )

        manager.save_issues([issue])

        # Reload
        loaded = manager.load_issues()
        assert len(loaded) == 1
        assert loaded[0].id == "ISSUE-001"
        assert loaded[0].priority == IssuePriority.HIGH

    def test_generate_next_id_empty(self, tmp_path: Path):
        """Test ID generation with no existing issues."""
        issues_path = tmp_path / "issues.json"
        issues_path.write_text("[]")

        manager = IssueManager(issues_path)
        next_id = manager.generate_next_id()

        assert next_id == "ISSUE-001"

    def test_generate_next_id_sequential(self, tmp_path: Path):
        """Test sequential ID generation."""
        issues_path = tmp_path / "issues.json"

        manager = IssueManager(issues_path)

        # Create issues with IDs 1, 2, 3
        issues = [
            Issue(id="ISSUE-001", test_name="test", priority=IssuePriority.LOW,
                  status=IssueStatus.OPEN, title="Issue 1"),
            Issue(id="ISSUE-002", test_name="test", priority=IssuePriority.LOW,
                  status=IssueStatus.OPEN, title="Issue 2"),
            Issue(id="ISSUE-003", test_name="test", priority=IssuePriority.LOW,
                  status=IssueStatus.OPEN, title="Issue 3"),
        ]
        manager.save_issues(issues)

        next_id = manager.generate_next_id()
        assert next_id == "ISSUE-004"

    def test_filter_by_status(self, tmp_path: Path):
        """Test filtering issues by status."""
        issues_path = tmp_path / "issues.json"

        manager = IssueManager(issues_path)

        issues = [
            Issue(id="ISSUE-001", test_name="test", priority=IssuePriority.LOW,
                  status=IssueStatus.OPEN, title="Open 1"),
            Issue(id="ISSUE-002", test_name="test", priority=IssuePriority.LOW,
                  status=IssueStatus.FIXED, title="Fixed 1"),
            Issue(id="ISSUE-003", test_name="test", priority=IssuePriority.LOW,
                  status=IssueStatus.OPEN, title="Open 2"),
        ]
        manager.save_issues(issues)

        open_issues = manager.filter_issues(status=IssueStatus.OPEN)
        assert len(open_issues) == 2

        fixed_issues = manager.filter_issues(status=IssueStatus.FIXED)
        assert len(fixed_issues) == 1

    def test_filter_by_priority(self, tmp_path: Path):
        """Test filtering issues by priority."""
        issues_path = tmp_path / "issues.json"

        manager = IssueManager(issues_path)

        issues = [
            Issue(id="ISSUE-001", test_name="test", priority=IssuePriority.CRITICAL,
                  status=IssueStatus.OPEN, title="Critical 1"),
            Issue(id="ISSUE-002", test_name="test", priority=IssuePriority.LOW,
                  status=IssueStatus.OPEN, title="Low 1"),
        ]
        manager.save_issues(issues)

        critical = manager.filter_issues(priority=IssuePriority.CRITICAL)
        assert len(critical) == 1
        assert critical[0].id == "ISSUE-001"


class TestIssueAggregator:
    """Tests for IssueAggregator."""

    def test_extract_from_failed_result(self, tmp_path: Path):
        """Test extracting issues from failed test result."""
        issues_path = tmp_path / "issues.json"
        issues_path.write_text("[]")

        manager = IssueManager(issues_path)
        aggregator = IssueAggregator(manager)

        result = TestResult(
            plugin_name="migration-scanner",
            status="fail",
            summary="Found deprecated patterns",
            details={
                "affected_urls": ["https://example.com/page1", "https://example.com/page2"]
            }
        )

        issues = aggregator.extract_issues([result])

        assert len(issues) == 1
        assert issues[0].test_name == "migration-scanner"
        assert issues[0].priority == IssuePriority.HIGH  # migration = high
        assert len(issues[0].affected_urls) == 2

    def test_skip_passed_results(self, tmp_path: Path):
        """Test that passed results don't create issues."""
        issues_path = tmp_path / "issues.json"
        issues_path.write_text("[]")

        manager = IssueManager(issues_path)
        aggregator = IssueAggregator(manager)

        result = TestResult(
            plugin_name="seo-optimizer",
            status="pass",
            summary="All SEO checks passed",
            details={}
        )

        issues = aggregator.extract_issues([result])

        assert len(issues) == 0

    def test_security_priority_is_critical(self, tmp_path: Path):
        """Test that security issues get critical priority."""
        issues_path = tmp_path / "issues.json"
        issues_path.write_text("[]")

        manager = IssueManager(issues_path)
        aggregator = IssueAggregator(manager)

        result = TestResult(
            plugin_name="security-audit",
            status="fail",
            summary="Found vulnerabilities",
            details={"affected_urls": ["https://example.com"]}
        )

        issues = aggregator.extract_issues([result])

        assert issues[0].priority == IssuePriority.CRITICAL


class TestDeduplication:
    """Tests for issue deduplication."""

    def test_find_duplicate_by_url(self):
        """Test finding duplicate by overlapping URLs."""
        existing = Issue(
            id="ISSUE-001",
            test_name="migration-scanner",
            priority=IssuePriority.HIGH,
            status=IssueStatus.OPEN,
            title="Found jQuery issues",
            affected_urls=["https://example.com/page1", "https://example.com/page2"],
        )

        new_issue = Issue(
            id="ISSUE-002",
            test_name="migration-scanner",
            priority=IssuePriority.HIGH,
            status=IssueStatus.OPEN,
            title="Found jQuery issues",
            affected_urls=["https://example.com/page2", "https://example.com/page3"],
        )

        duplicate = find_duplicate(new_issue, [existing])

        assert duplicate is not None
        assert duplicate.id == "ISSUE-001"

    def test_no_duplicate_different_test(self):
        """Test that different tests don't match as duplicates."""
        existing = Issue(
            id="ISSUE-001",
            test_name="migration-scanner",
            priority=IssuePriority.HIGH,
            status=IssueStatus.OPEN,
            title="Found jQuery issues",
            affected_urls=["https://example.com/page1"],
        )

        new_issue = Issue(
            id="ISSUE-002",
            test_name="seo-optimizer",
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.OPEN,
            title="Found jQuery issues",
            affected_urls=["https://example.com/page1"],
        )

        duplicate = find_duplicate(new_issue, [existing])

        assert duplicate is None


class TestResolutionDetection:
    """Tests for automatic resolution detection."""

    def test_detect_resolved_issue(self):
        """Test detecting a resolved issue."""
        existing = Issue(
            id="ISSUE-001",
            test_name="seo-optimizer",
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.OPEN,
            title="Missing meta descriptions",
            affected_urls=["https://example.com/page1"],
        )

        # New results don't include the affected URL
        new_result = TestResult(
            plugin_name="seo-optimizer",
            status="pass",
            summary="All pages have meta descriptions",
            details={"affected_urls": []}
        )

        resolved = detect_resolutions([existing], [new_result])

        assert len(resolved) == 1
        assert resolved[0].id == "ISSUE-001"

    def test_issue_still_exists(self):
        """Test that still-existing issues aren't marked resolved."""
        existing = Issue(
            id="ISSUE-001",
            test_name="seo-optimizer",
            priority=IssuePriority.MEDIUM,
            status=IssueStatus.OPEN,
            title="Missing meta descriptions",
            affected_urls=["https://example.com/page1"],
        )

        # New results still include the affected URL
        new_result = TestResult(
            plugin_name="seo-optimizer",
            status="fail",
            summary="Still missing meta descriptions",
            details={"affected_urls": ["https://example.com/page1"]}
        )

        resolved = detect_resolutions([existing], [new_result])

        assert len(resolved) == 0
