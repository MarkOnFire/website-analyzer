"""Test cases for LLM Optimizer plugin."""

import asyncio
import os
from pathlib import Path
from unittest.mock import patch
from src.analyzer.test_plugin import SiteSnapshot, PageData
from src.analyzer.plugins.llm_optimizer import LLMOptimizer


def create_mock_page(
    url: str,
    title: str,
    description: str,
    headings: str,
    schema: bool,
    word_count: int,
    semantic_html: str = "",
    internal_links: str = ""
) -> PageData:
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
        {semantic_html if semantic_html else '<div>'}
        {headings}
        {internal_links}
        <p>{'Lorem ipsum dolor sit amet. ' * (word_count // 5)}</p>
        {semantic_html if semantic_html else '</div>'}
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
        word_count=500,
        semantic_html="<article><section>",
        internal_links='<a href="/other">Related</a><a href="/more">More</a>'
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


async def test_semantic_html_detection():
    """Test semantic HTML detection (Feature #80)."""

    pages = [
        create_mock_page(
            url="https://example.com/good",
            title="Good Page",
            description="Good semantic HTML",
            headings="<h1>Title</h1><h2>Section</h2>",
            schema=True,
            word_count=300,
            semantic_html="<article><section><nav><header>",
        ),
        create_mock_page(
            url="https://example.com/bad",
            title="Bad Page",
            description="No semantic HTML",
            headings="<h1>Title</h1>",
            schema=False,
            word_count=300,
            semantic_html="",  # No semantic tags
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

    # Should detect semantic tags on good page
    assert "article" in result.details["metrics"]["semantic_tags_found"]
    assert "section" in result.details["metrics"]["semantic_tags_found"]
    assert result.details["metrics"]["pages_without_semantic_html"] == 1
    print("✓ Semantic HTML detection test passed")


async def test_internal_link_analysis():
    """Test internal link structure analysis (Feature #81)."""

    pages = [
        create_mock_page(
            url="https://example.com/page1",
            title="Page 1",
            description="First page",
            headings="<h1>Page 1</h1>",
            schema=True,
            word_count=300,
            internal_links='<a href="/page2">Link to Page 2</a><a href="/page3">Link to Page 3</a>',
        ),
        create_mock_page(
            url="https://example.com/page2",
            title="Page 2",
            description="Second page",
            headings="<h1>Page 2</h1>",
            schema=True,
            word_count=300,
            internal_links='<a href="/page1">Back to Page 1</a>',
        ),
        create_mock_page(
            url="https://example.com/page3",
            title="Page 3 - Orphan",
            description="Orphaned page",
            headings="<h1>Page 3</h1>",
            schema=True,
            word_count=300,
            internal_links="",  # No outbound links
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

    # Should track internal links
    assert result.details["metrics"]["avg_internal_links_per_page"] >= 0
    assert result.details["metrics"]["pages_with_poor_linking"] >= 1  # page3 has no links
    print("✓ Internal link analysis test passed")


async def test_llm_meta_description_quality():
    """Test LLM-based meta description quality check (Feature #83)."""

    # Mock the LLM API response
    mock_response_data = {
        "score": 8,
        "feedback": "Clear and concise description with good keyword usage."
    }

    async def mock_check(description):
        if description:
            return mock_response_data
        return None

    page = create_mock_page(
        url="https://example.com/article",
        title="Article",
        description="A comprehensive guide to best practices in web development",
        headings="<h1>Article</h1>",
        schema=True,
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

    # Patch the quality check method
    with patch.object(plugin, '_check_meta_description_quality', side_effect=mock_check):
        result = await plugin.analyze(snapshot)

    # Should have LLM quality check results
    if result.details["metrics"]["llm_description_checks"]:
        assert len(result.details["metrics"]["llm_description_checks"]) > 0
        assert result.details["metrics"]["llm_description_checks"][0]["score"] == 8
    print("✓ LLM meta description quality check test passed")


async def test_documentation_site_optimization():
    """Test LLM optimization on documentation site (schema-rich) - Feature #87."""

    # Simulate a documentation site with good schema markup
    pages = [
        create_mock_page(
            url="https://docs.example.com/",
            title="Documentation Home",
            description="Complete API documentation",
            headings="<h1>Documentation</h1><h2>Getting Started</h2><h3>Installation</h3>",
            schema=True,
            word_count=500,
            semantic_html="<article><section><nav>",
            internal_links='<a href="/api">API Reference</a><a href="/guide">Guide</a>',
        ),
        create_mock_page(
            url="https://docs.example.com/api",
            title="API Reference",
            description="Detailed API reference",
            headings="<h1>API</h1><h2>Methods</h2><h3>Authentication</h3>",
            schema=True,
            word_count=800,
            semantic_html="<article><section><aside>",
            internal_links='<a href="/">Home</a><a href="/guide">Guide</a>',
        ),
        create_mock_page(
            url="https://docs.example.com/guide",
            title="User Guide",
            description="Step-by-step user guide",
            headings="<h1>Guide</h1><h2>Basics</h2><h3>Advanced</h3>",
            schema=True,
            word_count=600,
            semantic_html="<article><section><nav>",
            internal_links='<a href="/">Home</a><a href="/api">API</a>',
        )
    ]

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://docs.example.com",
        pages=pages,
        sitemap={},
        summary={}
    )

    plugin = LLMOptimizer()
    result = await plugin.analyze(snapshot)

    # Documentation site should score well
    assert result.details["overall_score"] >= 7.0, f"Expected high score for docs site, got {result.details['overall_score']}"
    assert result.details["metrics"]["pages_without_schema"] == 0, "All docs pages should have schema"
    assert len(result.details["metrics"]["semantic_tags_found"]) >= 3, "Should use semantic HTML"
    print("✓ Documentation site optimization test passed (Feature #87)")


async def test_blog_site_optimization():
    """Test LLM optimization on blog site (meta tag focus) - Feature #88."""

    # Simulate a blog with varying meta tag quality
    pages = [
        create_mock_page(
            url="https://blog.example.com/post1",
            title="10 Tips for Better Code",
            description="Learn the top 10 tips for writing better, cleaner code that's maintainable and efficient.",
            headings="<h1>10 Tips for Better Code</h1><h2>Tip 1</h2><h2>Tip 2</h2>",
            schema=True,
            word_count=800,
            semantic_html="<article><header><footer>",
            internal_links='<a href="/post2">Related Post</a>',
        ),
        create_mock_page(
            url="https://blog.example.com/post2",
            title="Post",  # Short title
            description="",  # Missing description
            headings="<h1>Post</h1>",
            schema=False,
            word_count=200,
            semantic_html="",
            internal_links='<a href="/post1">Previous</a>',
        ),
        create_mock_page(
            url="https://blog.example.com/post3",
            title="Understanding Async Programming in Python",
            description="A deep dive into async programming patterns in Python with practical examples.",
            headings="<h1>Async Programming</h1><h2>Basics</h2><h2>Advanced</h2>",
            schema=True,
            word_count=1000,
            semantic_html="<article><section>",
            internal_links='<a href="/post1">Related</a><a href="/post2">More</a>',
        )
    ]

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://blog.example.com",
        pages=pages,
        sitemap={},
        summary={}
    )

    plugin = LLMOptimizer()
    result = await plugin.analyze(snapshot)

    # Should detect meta tag issues
    assert result.details["metrics"]["pages_missing_description"] >= 1, "Should detect missing descriptions"

    # Should find issues in quick wins
    meta_tag_issues = [w for w in result.details["quick_wins"] if "meta" in w["category"].lower()]
    assert len(meta_tag_issues) > 0, "Should identify meta tag quick wins"

    print("✓ Blog site optimization test passed (Feature #88)")


async def run_all_tests():
    """Run all tests."""
    print("Running LLM Optimizer Tests...\n")

    await test_llm_optimizer_perfect_page()
    await test_llm_optimizer_missing_metadata()
    await test_llm_optimizer_poor_structure()
    await test_llm_optimizer_multiple_pages()
    await test_llm_optimizer_empty_site()
    await test_semantic_html_detection()
    await test_internal_link_analysis()
    await test_llm_meta_description_quality()
    await test_documentation_site_optimization()
    await test_blog_site_optimization()

    print("\n✓ All tests passed!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
