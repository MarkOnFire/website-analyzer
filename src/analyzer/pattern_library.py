#!/usr/bin/env python3.11
"""
Pattern Library Management System

Provides functionality to:
1. Discover and list available patterns
2. Load patterns from JSON files
3. Create new patterns from templates
4. Validate pattern structure
5. Test patterns against URLs
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class Pattern:
    """Represents a bug pattern definition."""
    name: str
    description: str
    patterns: List[str]  # List of regex patterns
    severity: str  # low, medium, high, critical
    examples: List[str]  # Examples where this pattern appears
    tags: Optional[List[str]] = None
    author: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pattern":
        """Create from dictionary."""
        # Handle missing optional fields
        data.setdefault("tags", None)
        data.setdefault("author", None)
        data.setdefault("created_at", None)
        data.setdefault("updated_at", None)
        data.setdefault("notes", None)
        return cls(**data)

    def validate(self) -> tuple[bool, List[str]]:
        """Validate pattern structure. Returns (is_valid, error_messages)."""
        errors = []

        if not self.name or not isinstance(self.name, str):
            errors.append("Pattern 'name' must be a non-empty string")

        if not self.description or not isinstance(self.description, str):
            errors.append("Pattern 'description' must be a non-empty string")

        if not self.patterns or not isinstance(self.patterns, list):
            errors.append("Pattern 'patterns' must be a non-empty list")
        else:
            # Validate each regex pattern
            for i, pattern in enumerate(self.patterns):
                if not isinstance(pattern, str):
                    errors.append(f"Pattern {i}: regex must be a string")
                else:
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        errors.append(f"Pattern {i}: invalid regex '{pattern}' - {e}")

        if self.severity not in ["low", "medium", "high", "critical"]:
            errors.append(
                f"Severity must be one of: low, medium, high, critical (got '{self.severity}')"
            )

        if not isinstance(self.examples, list):
            errors.append("Pattern 'examples' must be a list")
        elif len(self.examples) == 0:
            errors.append("Pattern must have at least one example")

        if self.tags is not None and not isinstance(self.tags, list):
            errors.append("Pattern 'tags' must be a list if provided")

        return len(errors) == 0, errors


class PatternLibrary:
    """Manages pattern definitions and operations."""

    def __init__(self, patterns_dir: Path = None):
        """Initialize pattern library with a patterns directory."""
        if patterns_dir is None:
            # Default to patterns directory in repository root
            patterns_dir = Path(__file__).parent.parent.parent / "patterns"

        self.patterns_dir = Path(patterns_dir)
        self.patterns_dir.mkdir(parents=True, exist_ok=True)

    def list_patterns(self) -> List[Dict[str, Any]]:
        """List all available patterns with metadata."""
        patterns = []

        for pattern_file in self.patterns_dir.glob("*.json"):
            try:
                pattern_data = self.load_pattern_file(pattern_file)
                patterns.append({
                    "filename": pattern_file.name,
                    "name": pattern_data.name,
                    "description": pattern_data.description,
                    "severity": pattern_data.severity,
                    "patterns_count": len(pattern_data.patterns),
                    "tags": pattern_data.tags or [],
                    "author": pattern_data.author,
                    "created_at": pattern_data.created_at,
                    "updated_at": pattern_data.updated_at,
                })
            except Exception as e:
                patterns.append({
                    "filename": pattern_file.name,
                    "error": str(e),
                })

        return patterns

    def load_pattern_file(self, file_path: Path) -> Pattern:
        """Load a pattern from a JSON file."""
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pattern = Pattern.from_dict(data)
        is_valid, errors = pattern.validate()

        if not is_valid:
            raise ValueError(
                f"Invalid pattern in {file_path.name}:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return pattern

    def load_pattern_by_name(self, pattern_name: str) -> Optional[Pattern]:
        """Load a pattern by its name."""
        for pattern_file in self.patterns_dir.glob("*.json"):
            try:
                pattern = self.load_pattern_file(pattern_file)
                if pattern.name == pattern_name:
                    return pattern
            except Exception:
                continue

        return None

    def load_pattern_by_file(self, filename: str) -> Optional[Pattern]:
        """Load a pattern by its filename."""
        pattern_file = self.patterns_dir / filename
        if pattern_file.exists():
            return self.load_pattern_file(pattern_file)
        return None

    def load_all_patterns(self) -> List[Pattern]:
        """Load all patterns from the library."""
        patterns = []
        for pattern_file in self.patterns_dir.glob("*.json"):
            try:
                patterns.append(self.load_pattern_file(pattern_file))
            except Exception:
                continue
        return patterns

    def save_pattern(self, pattern: Pattern, filename: str = None) -> Path:
        """Save a pattern to a JSON file."""
        is_valid, errors = pattern.validate()
        if not is_valid:
            raise ValueError(
                "Cannot save invalid pattern:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        if filename is None:
            # Generate filename from pattern name
            filename = f"{pattern.name.lower().replace(' ', '_')}.json"

        file_path = self.patterns_dir / filename

        # Update timestamps
        now = datetime.now().isoformat()
        if pattern.created_at is None:
            pattern.created_at = now
        pattern.updated_at = now

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(pattern.to_dict(), f, indent=2, ensure_ascii=False)

        return file_path

    def create_pattern_from_template(
        self,
        name: str,
        description: str,
        regex_patterns: List[str],
        severity: str = "medium",
        examples: List[str] = None,
        tags: List[str] = None,
        author: str = None,
        notes: str = None,
    ) -> Pattern:
        """Create a new pattern from provided data."""
        if examples is None:
            examples = []

        if tags is None:
            tags = []

        pattern = Pattern(
            name=name,
            description=description,
            patterns=regex_patterns,
            severity=severity,
            examples=examples or [""],
            tags=tags,
            author=author,
            notes=notes,
        )

        is_valid, errors = pattern.validate()
        if not is_valid:
            raise ValueError(
                "Invalid pattern data:\n" + "\n".join(f"  - {e}" for e in errors)
            )

        return pattern

    def delete_pattern(self, filename: str) -> bool:
        """Delete a pattern file."""
        pattern_file = self.patterns_dir / filename
        if pattern_file.exists():
            pattern_file.unlink()
            return True
        return False

    def get_pattern_template(self) -> Dict[str, Any]:
        """Get a template for creating new patterns."""
        return {
            "name": "pattern_name",
            "description": "Brief description of what this pattern detects",
            "patterns": [
                "regex_pattern_1",
                "regex_pattern_2",
            ],
            "severity": "medium",
            "examples": [
                "Example HTML or text where pattern appears",
            ],
            "tags": ["optional", "tags"],
            "author": "Your Name",
            "notes": "Optional notes about the pattern",
        }

    def test_pattern_on_content(self, pattern: Pattern, content: str) -> Dict[str, Any]:
        """Test a pattern against content and return matches."""
        matches_by_pattern = {}

        for regex in pattern.patterns:
            try:
                compiled_regex = re.compile(regex, re.IGNORECASE | re.DOTALL)
                matches = compiled_regex.findall(content)

                if matches:
                    matches_by_pattern[regex] = {
                        "count": len(matches),
                        "matches": matches[:5],  # Show first 5 matches
                    }
            except re.error as e:
                matches_by_pattern[regex] = {
                    "error": str(e),
                }

        total_matches = sum(
            m["count"] for m in matches_by_pattern.values() if "count" in m
        )

        return {
            "pattern_name": pattern.name,
            "total_matches": total_matches,
            "matches_by_pattern": matches_by_pattern,
            "content_length": len(content),
        }

    def test_pattern_on_url(self, pattern: Pattern, url: str) -> Dict[str, Any]:
        """
        Test a pattern against a URL by fetching and analyzing the content.

        This requires crawl4ai to be available.
        """
        try:
            from crawl4ai import AsyncWebCrawler
            import asyncio

            async def _fetch_and_test():
                async with AsyncWebCrawler() as crawler:
                    result = await crawler.arun(url)
                    if not result.html:
                        return {"error": "Failed to fetch URL"}

                    test_result = self.test_pattern_on_content(pattern, result.html)
                    test_result["url"] = url
                    test_result["html_length"] = len(result.html)
                    return test_result

            # Try to run async function
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            return loop.run_until_complete(_fetch_and_test())

        except ImportError:
            return {"error": "crawl4ai not installed. Cannot fetch URL."}
        except Exception as e:
            return {"error": str(e)}
