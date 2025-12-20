"""Issue tracking models and management.

Defines the Issue schema and provides issue aggregation functionality to
extract issues from test results.
"""

from __future__ import annotations

import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.analyzer.test_plugin import TestResult


class IssuePriority(str, Enum):
    """Priority levels for issues."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class IssueStatus(str, Enum):
    """Lifecycle states for issues."""

    OPEN = "open"
    INVESTIGATING = "investigating"
    FIXED = "fixed"
    VERIFIED = "verified"


class StatusTransition(BaseModel):
    """Records a status change event."""

    from_status: str
    to_status: str
    timestamp: str
    reason: str


class Issue(BaseModel):
    """Represents a tracked issue found during testing.

    Attributes:
        id: Unique identifier (format: ISSUE-001, ISSUE-002, etc.)
        test_name: Name of the test plugin that discovered this issue
        priority: Issue priority level
        status: Current status in the issue lifecycle
        title: Human-readable summary of the issue
        affected_urls: List of URLs where this issue was found
        created_at: ISO 8601 timestamp when issue was first detected
        updated_at: ISO 8601 timestamp of last status change
        resolved_at: ISO 8601 timestamp when issue was resolved (nullable)
        details: Additional structured data about the issue
        status_history: Log of status transitions
    """

    id: str
    test_name: str
    priority: IssuePriority
    status: IssueStatus
    title: str
    affected_urls: List[str] = Field(default_factory=list)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    resolved_at: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    status_history: List[StatusTransition] = Field(default_factory=list)
    first_detected_at: Optional[str] = None
    last_seen_at: Optional[str] = None
    detection_count: int = 1


# Valid status transitions (state machine)
VALID_TRANSITIONS: Dict[str, List[str]] = {
    "open": ["investigating", "fixed"],
    "investigating": ["fixed", "open"],
    "fixed": ["verified", "open"],
    "verified": ["open"],
}


def transition_status(
    issue: Issue,
    new_status: IssueStatus,
    reason: str
) -> Issue:
    """Validate and apply a status transition.

    Raises:
        ValueError: If transition is invalid
    """
    current = issue.status.value
    target = new_status.value

    if target not in VALID_TRANSITIONS.get(current, []):
        valid = VALID_TRANSITIONS.get(current, [])
        raise ValueError(
            f"Invalid transition: {current} -> {target}. "
            f"Valid transitions: {valid}"
        )

    now = datetime.utcnow().isoformat() + "Z"
    history_entry = StatusTransition(
        from_status=current,
        to_status=target,
        timestamp=now,
        reason=reason
    )

    updates = {
        "status": new_status,
        "updated_at": now,
        "status_history": issue.status_history + [history_entry]
    }

    if new_status in (IssueStatus.FIXED, IssueStatus.VERIFIED):
        updates["resolved_at"] = now

    return issue.model_copy(update=updates)


class IssueManager:
    """Manages issue persistence and ID generation for a workspace."""

    def __init__(self, issues_path: Path):
        """Initialize issue manager.

        Args:
            issues_path: Path to the workspace's issues.json file
        """
        self.issues_path = issues_path

    def load_issues(self) -> List[Issue]:
        """Load all issues from issues.json.

        Returns:
            List of Issue objects

        Raises:
            ValueError: If issues.json is invalid JSON or contains invalid Issue data
        """
        if not self.issues_path.exists():
            return []

        try:
            data = json.loads(self.issues_path.read_text(encoding="utf-8"))
            if not data:  # Empty array
                return []
            return [Issue(**issue_data) for issue_data in data]
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in issues.json: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse issues: {e}")

    def save_issues(self, issues: List[Issue]) -> None:
        """Save issues to issues.json.

        Args:
            issues: List of Issue objects to persist
        """
        data = [issue.model_dump() for issue in issues]
        self.issues_path.write_text(
            json.dumps(data, indent=2),
            encoding="utf-8"
        )

    def generate_next_id(self) -> str:
        """Generate the next sequential issue ID.

        Reads existing issues to find the highest ID number and increments.
        Format: ISSUE-001, ISSUE-002, etc.

        Returns:
            Next available issue ID
        """
        issues = self.load_issues()

        if not issues:
            return "ISSUE-001"

        # Extract numeric part from all IDs
        max_num = 0
        for issue in issues:
            # ID format: ISSUE-NNN
            if issue.id.startswith("ISSUE-"):
                try:
                    num = int(issue.id.split("-")[1])
                    max_num = max(max_num, num)
                except (IndexError, ValueError):
                    # Skip malformed IDs
                    continue

        # Generate next ID with zero-padded 3 digits
        next_num = max_num + 1
        return f"ISSUE-{next_num:03d}"

    def add_issue(self, issue: Issue) -> None:
        """Add a new issue to the store."""
        issues = self.load_issues()
        issues.append(issue)
        self.save_issues(issues)

    def update_issue(self, issue: Issue) -> None:
        """Update an existing issue by ID."""
        issues = self.load_issues()
        for i, existing in enumerate(issues):
            if existing.id == issue.id:
                issues[i] = issue
                break
        self.save_issues(issues)

    def filter_issues(
        self,
        test_name: Optional[str] = None,
        priority: Optional[IssuePriority] = None,
        status: Optional[IssueStatus] = None
    ) -> List[Issue]:
        """Filter issues by criteria."""
        issues = self.load_issues()

        if test_name:
            issues = [i for i in issues if i.test_name == test_name]
        if priority:
            issues = [i for i in issues if i.priority == priority]
        if status:
            issues = [i for i in issues if i.status == status]

        return issues


class IssueAggregator:
    """Extracts issues from test results.

    Converts TestResult objects into Issue objects for persistent tracking.
    """

    def __init__(self, issue_manager: IssueManager):
        """Initialize aggregator with an issue manager.

        Args:
            issue_manager: IssueManager for ID generation and persistence
        """
        self.issue_manager = issue_manager

    def extract_issues(
        self,
        test_results: List[TestResult],
        priority_map: Optional[Dict[str, IssuePriority]] = None
    ) -> List[Issue]:
        """Extract issues from test results.

        Creates Issue objects from TestResults with status "fail" or "warning".

        Args:
            test_results: List of TestResult objects from test runner
            priority_map: Optional mapping of test_name to default priority.
                         If not provided, uses "medium" for fails, "low" for warnings.

        Returns:
            List of newly created Issue objects
        """
        priority_map = priority_map or {}
        issues = []

        for result in test_results:
            # Skip passed or error results (errors aren't tracked as issues)
            if result.status not in ("fail", "warning"):
                continue

            # Determine priority based on test type
            if result.plugin_name in priority_map:
                priority = priority_map[result.plugin_name]
            else:
                priority = self._assign_priority(result)

            # Extract affected URLs from result details
            affected_urls = self._extract_urls_from_result(result)

            now = datetime.utcnow().isoformat() + "Z"
            issue_id = self.issue_manager.generate_next_id()
            issue = Issue(
                id=issue_id,
                test_name=result.plugin_name,
                priority=priority,
                status=IssueStatus.OPEN,
                title=result.summary,
                affected_urls=affected_urls,
                details=result.details,
                first_detected_at=now,
                last_seen_at=now,
            )
            issues.append(issue)

        return issues

    def _assign_priority(self, result: TestResult) -> IssuePriority:
        """Auto-assign priority based on test type and severity."""
        test_name = result.plugin_name.lower()

        # Security issues are always critical
        if "security" in test_name:
            return IssuePriority.CRITICAL

        # Migration issues are high (breaking changes)
        if "migration" in test_name:
            return IssuePriority.HIGH

        # SEO based on affected count
        if "seo" in test_name:
            affected = len(self._extract_urls_from_result(result))
            if affected >= 10:
                return IssuePriority.HIGH
            return IssuePriority.MEDIUM

        # LLM optimization suggestions
        if "llm" in test_name:
            return IssuePriority.MEDIUM

        # Default
        return IssuePriority.MEDIUM if result.status == "fail" else IssuePriority.LOW

    def _extract_urls_from_result(self, result: TestResult) -> List[str]:
        """Extract affected URLs from a TestResult's details.

        Looks for common patterns in result.details:
        - details["affected_urls"] (list)
        - details["url"] (string)
        - details["findings"] (list of dicts with "url" key)
        - details["pages"] (list of dicts with "url" key)

        Args:
            result: TestResult to extract URLs from

        Returns:
            List of unique URLs found in the result
        """
        urls = set()
        details = result.details

        # Pattern 1: Direct affected_urls list
        if "affected_urls" in details:
            if isinstance(details["affected_urls"], list):
                urls.update(str(url) for url in details["affected_urls"])

        # Pattern 2: Single URL field
        if "url" in details:
            urls.add(str(details["url"]))

        # Pattern 3: Findings with URLs
        if "findings" in details:
            if isinstance(details["findings"], list):
                for finding in details["findings"]:
                    if isinstance(finding, dict) and "url" in finding:
                        urls.add(str(finding["url"]))

        # Pattern 4: Pages with URLs
        if "pages" in details:
            if isinstance(details["pages"], list):
                for page in details["pages"]:
                    if isinstance(page, dict) and "url" in page:
                        urls.add(str(page["url"]))

        return sorted(list(urls))


def find_duplicate(
    new_issue: Issue,
    existing_issues: List[Issue]
) -> Optional[Issue]:
    """Find a duplicate of the new issue in the existing list.

    Matches based on: test_name + affected_urls + similar title.

    Returns:
        The matching existing issue, or None if this is new.
    """
    for existing in existing_issues:
        # Must be same test
        if existing.test_name != new_issue.test_name:
            continue

        # Check URL overlap
        existing_urls = set(existing.affected_urls)
        new_urls = set(new_issue.affected_urls)

        if existing_urls & new_urls:  # Any overlap
            # Check title similarity (simple approach)
            if _title_similarity(existing.title, new_issue.title) > 0.8:
                return existing

    return None


def _title_similarity(a: str, b: str) -> float:
    """Calculate simple title similarity (0-1)."""
    a_words = set(a.lower().split())
    b_words = set(b.lower().split())

    if not a_words or not b_words:
        return 0.0

    intersection = len(a_words & b_words)
    union = len(a_words | b_words)

    return intersection / union if union > 0 else 0.0


def detect_resolutions(
    existing_issues: List[Issue],
    new_results: List[TestResult]
) -> List[Issue]:
    """Find issues that may have been resolved.

    Compares existing open issues against new test results.
    If an issue's conditions no longer exist, flag it as potentially resolved.

    Returns:
        List of issues that may be resolved.
    """
    potentially_resolved = []

    # Build lookup of new result URLs by test
    result_urls_by_test: Dict[str, set] = {}
    for result in new_results:
        if result.plugin_name not in result_urls_by_test:
            result_urls_by_test[result.plugin_name] = set()

        # Extract URLs from this result's details
        details = result.details
        if "affected_urls" in details:
            result_urls_by_test[result.plugin_name].update(details["affected_urls"])
        if "findings" in details:
            for f in details.get("findings", []):
                if isinstance(f, dict) and "url" in f:
                    result_urls_by_test[result.plugin_name].add(f["url"])

    for issue in existing_issues:
        # Only check open/investigating issues
        if issue.status not in (IssueStatus.OPEN, IssueStatus.INVESTIGATING):
            continue

        # Get new URLs for this test
        new_urls = result_urls_by_test.get(issue.test_name, set())

        # If none of the issue's URLs appear in new results, maybe resolved
        if not any(url in new_urls for url in issue.affected_urls):
            potentially_resolved.append(issue)

    return potentially_resolved
