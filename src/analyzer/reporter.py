"""Test result reporter.

Aggregates and formats test results for display or storage.
"""

from typing import Any, Dict, List

from src.analyzer.test_plugin import TestResult


class Reporter:
    """Aggregates and formats test results."""

    @staticmethod
    def generate_summary(results: List[TestResult]) -> Dict[str, Any]:
        """Generate a summary dictionary from a list of test results.

        Args:
            results: List of TestResult objects.

        Returns:
            Dictionary containing statistics and serialized results.
        """
        total = len(results)
        passed = sum(1 for r in results if r.status == "pass")
        failed = sum(1 for r in results if r.status == "fail")
        errors = sum(1 for r in results if r.status == "error")
        warnings = sum(1 for r in results if r.status == "warning")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "warnings": warnings,
            "results": [r.model_dump() for r in results],
        }
