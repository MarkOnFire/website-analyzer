"""Test cases for LLM Optimizer plugin."""

import asyncio
from pathlib import Path
from src.analyzer.test_plugin import SiteSnapshot, PageData
from src.analyzer.plugins.llm_optimizer import LLMOptimizer


def create_mock_page(url: str, title: str, description: str, headings: str, schema: bool, word_count: int) -> PageData:
    """Create a mock PageData for testing."""

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        {f'<meta name="description" content="{description}">' if description else ''}
        {f'<script type="application/ld+json">{{"@type":"Article"}}</script>' if schema else ''}
    </head>
    <body>
        {headings}
        <p>{'Lorem ipsum dolor sit amet. ' * (word_count // 5)}</p>
    </body>
    </html>
    """

    # Create temporary directory structure
    temp_dir = Path(f"/tmp/test_page_{url.replace('/', '_')}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    (temp_dir / "raw.html").write_text(html)
    (temp_dir / "cleaned.html").write_text(html)
    (temp_dir / "content.md").write_text("# Test Content")
    (temp_dir / "metadata.json").write_text('{}')

    return PageData(
        url=url,
        status_code=200,
        timestamp="2025-01-01T00:00:00Z",
        title=title if title else None,
        directory=temp_dir
    )


async def test_llm_optimizer_perfect_page():
    """Test analyzer with perfectly optimized page."""

    page = create_mock_page(
        url="https://example.com/article",
        title="Article Title - Best Practices Guide",
        description="Complete guide to best practices with actionable tips and examples.",
        headings="<h1>Main Title</h1><h2>Section 1</h2><h3>Subsection</h3><h2>Section 2</h2>",
        schema=True,
        word_count=500
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={},
        summary={}
    )

    plugin = LLMOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.status == "pass", f"Expected pass but got {result.status}"
    assert result.details["overall_score"] >= 7.0, f"Expected score >= 7, got {result.details['overall_score']}"
    assert len(result.details["quick_wins"]) == 0, "Expected no quick wins for perfect page"
    print("✓ Perfect page test passed")


async def test_llm_optimizer_missing_metadata():
    """Test analyzer with missing metadata."""

    page = create_mock_page(
        url="https://example.com/missing",
        title="",  # Missing title
        description="",  # Missing description
        headings="<h1>Title Only</h1>",
        schema=False,  # No schema
        word_count=300
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={},
        summary={}
    )

    plugin = LLMOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.status == "fail", f"Expected fail but got {result.status}"
    assert len(result.details["quick_wins"]) > 0, "Expected quick wins for missing metadata"

    # Check that missing metadata was detected
    meta_tags_found = any(
        "meta-tags" in w["category"].lower()
        for w in result.details["quick_wins"]
    )
    assert meta_tags_found, "Expected missing metadata to be detected"
    print("✓ Missing metadata test passed")


async def test_llm_optimizer_poor_structure():
    """Test analyzer with poor content structure."""

    page = create_mock_page(
        url="https://example.com/poor",
        title="Article",
        description="Article description",
        headings="<h1>Title</h1><p>No subheadings</p>",  # No H2 or H3
        schema=False,
        word_count=150  # Thin content
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={},
        summary={}
    )

    plugin = LLMOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.status in ["fail", "warning"], "Expected fail or warning for poor structure"

    # Check that structural issues were detected
    recommendations = result.details["strategic_recommendations"]
    structural_found = any(
        "heading" in r["finding"].lower() or "content" in r["finding"].lower()
        for r in recommendations
    )
    assert structural_found, "Expected structural issues to be detected"
    print("✓ Poor structure test passed")


async def test_llm_optimizer_multiple_pages():
    """Test analyzer with multiple pages."""

    pages = [
        create_mock_page(
            url="https://example.com/1",
            title="Page One Title",
            description="First page description",
            headings="<h1>One</h1><h2>Section</h2>",
            schema=True,
            word_count=400
        ),
        create_mock_page(
            url="https://example.com/2",
            title="Page Two Title",
            description="",  # Missing
            headings="<h1>Two</h1>",  # Poor hierarchy
            schema=False,
            word_count=100
        ),
        create_mock_page(
            url="https://example.com/3",
            title="",  # Missing
            description="Third page description",
            headings="<h1>Three</h1><h2>One</h2><h2>Two</h2>",
            schema=True,
            word_count=350
        )
    ]

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=pages,
        sitemap={},
        summary={}
    )

    plugin = LLMOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.details["pages_analyzed"] == 3, "Should analyze all 3 pages"
    assert result.details["metrics"]["pages_missing_description"] == 1
    assert result.details["metrics"]["pages_missing_title"] == 1
    assert result.details["metrics"]["pages_without_schema"] == 1

    # Score should reflect multiple issues
    score = result.details["overall_score"]
    assert score < 10.0, "Score should be less than perfect"
    print("✓ Multiple pages test passed")


async def test_llm_optimizer_empty_site():
    """Test analyzer with no pages."""

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[],
        sitemap={},
        summary={}
    )

    plugin = LLMOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.details["pages_analyzed"] == 0
    print("✓ Empty site test passed")


async def run_all_tests():
    """Run all tests."""
    print("Running LLM Optimizer Tests...\n")

    await test_llm_optimizer_perfect_page()
    await test_llm_optimizer_missing_metadata()
    await test_llm_optimizer_poor_structure()
    await test_llm_optimizer_multiple_pages()
    await test_llm_optimizer_empty_site()

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
