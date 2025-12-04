from src.analyzer.reporter import Reporter
from src.analyzer.test_plugin import TestResult


def test_reporter_summary():
    results = [
        TestResult(plugin_name="p1", status="pass", summary="ok"),
        TestResult(plugin_name="p2", status="fail", summary="bad"),
        TestResult(plugin_name="p3", status="error", summary="oops"),
    ]
    
    summary = Reporter.generate_summary(results)
    
    assert summary["total"] == 3
    assert summary["passed"] == 1
    assert summary["failed"] == 1
    assert summary["errors"] == 1
    assert summary["warnings"] == 0
    assert len(summary["results"]) == 3
    assert summary["results"][0]["plugin_name"] == "p1"
