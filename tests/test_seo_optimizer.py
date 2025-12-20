"""Test cases for SEO Optimizer plugin."""

import asyncio
from pathlib import Path
from src.analyzer.test_plugin import SiteSnapshot, PageData
from src.analyzer.plugins.seo_optimizer import SeoOptimizer


def create_mock_page(
    url: str,
    title: str,
    description: str,
    h1_count: int,
    headings: str,
    images_with_alt: int,
    images_without_alt: int,
    word_count: int,
    internal_links: int = 2
) -> PageData:
    """Create a mock PageData for testing."""

    # Build image tags
    img_tags = []
    for i in range(images_with_alt):
        img_tags.append(f'<img src="image{i}.jpg" alt="Image {i}">')
    for i in range(images_without_alt):
        img_tags.append(f'<img src="noalt{i}.jpg">')

    # Build internal links
    link_tags = []
    for i in range(internal_links):
        link_tags.append(f'<a href="/page{i}">Link {i}</a>')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        {f'<meta name="description" content="{description}">' if description else ''}
        <meta name="viewport" content="width=device-width, initial-scale=1">
    </head>
    <body>
        {headings}
        {''.join(img_tags)}
        <p>{'Lorem ipsum dolor sit amet consectetur adipiscing elit. ' * (word_count // 7)}</p>
        {''.join(link_tags)}
    </body>
    </html>
    """

    # Create temporary directory structure
    temp_dir = Path(f"/tmp/test_seo_{url.replace('/', '_').replace(':', '_')}")
    temp_dir.mkdir(parents=True, exist_ok=True)

    (temp_dir / "raw.html").write_text(html)
    (temp_dir / "cleaned.html").write_text(html)
    (temp_dir / "content.md").write_text("# Test Content\n\n" + "Lorem ipsum. " * word_count)
    (temp_dir / "metadata.json").write_text('{}')

    return PageData(
        url=url,
        status_code=200,
        timestamp="2025-01-01T00:00:00Z",
        title=title if title else None,
        directory=temp_dir
    )


async def test_seo_optimizer_perfect_page():
    """Test analyzer with perfectly optimized page."""

    page = create_mock_page(
        url="https://example.com/article",
        title="SEO Optimized Article Title - 50 Characters",
        description="This is a well-optimized meta description that provides clear value and is within the recommended 120-160 character range for search engines.",
        h1_count=1,
        headings="<h1>Main Article Title</h1><h2>Section One</h2><h3>Subsection</h3><h2>Section Two</h2>",
        images_with_alt=3,
        images_without_alt=0,
        word_count=400,
        internal_links=5
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={"pages": ["https://example.com/article"]},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.status == "pass", f"Expected pass but got {result.status}"
    assert result.details["overall_score"] >= 7.0, f"Expected score >= 7, got {result.details['overall_score']}"
    assert len(result.details["critical_issues"]) == 0, "Expected no critical issues for perfect page"
    print("✓ Perfect page test passed")


async def test_seo_optimizer_missing_metadata():
    """Test analyzer with missing title and meta description."""

    page = create_mock_page(
        url="https://example.com/bad",
        title="",  # Missing title
        description="",  # Missing description
        h1_count=0,  # No H1
        headings="<h2>Section</h2>",
        images_with_alt=0,
        images_without_alt=2,
        word_count=100,
        internal_links=0
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.status == "fail", f"Expected fail but got {result.status}"
    assert len(result.details["critical_issues"]) > 0, "Expected critical issues for missing title"

    # Check that missing title was detected
    title_issue_found = any(
        "title" in issue["issue"].lower()
        for issue in result.details["critical_issues"]
    )
    assert title_issue_found, "Expected missing title to be detected"

    # Check that missing H1 was detected
    h1_issue_found = any(
        "h1" in issue["issue"].lower()
        for issue in result.details["critical_issues"]
    )
    assert h1_issue_found, "Expected missing H1 to be detected"
    print("✓ Missing metadata test passed")


async def test_seo_optimizer_suboptimal_metadata():
    """Test analyzer with suboptimal metadata (too short/long)."""

    page = create_mock_page(
        url="https://example.com/suboptimal",
        title="Short",  # Too short (< 30 chars)
        description="Short description.",  # Too short (< 120 chars)
        h1_count=1,
        headings="<h1>Title</h1><h2>Section</h2>",
        images_with_alt=1,
        images_without_alt=0,
        word_count=250,
        internal_links=2
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.status in ["warning", "fail"], "Expected warning or fail for suboptimal metadata"
    assert len(result.details["warnings"]) > 0, "Expected warnings for short metadata"

    # Check that short title was detected
    short_title_found = any(
        "short title" in w["issue"].lower()
        for w in result.details["warnings"]
    )
    assert short_title_found, "Expected short title to be detected"
    print("✓ Suboptimal metadata test passed")


async def test_seo_optimizer_duplicate_titles():
    """Test analyzer with duplicate title tags."""

    pages = [
        create_mock_page(
            url="https://example.com/page1",
            title="Same Title for All Pages",
            description="First page description.",
            h1_count=1,
            headings="<h1>Page 1</h1>",
            images_with_alt=1,
            images_without_alt=0,
            word_count=300,
            internal_links=2
        ),
        create_mock_page(
            url="https://example.com/page2",
            title="Same Title for All Pages",  # Duplicate
            description="Second page description.",
            h1_count=1,
            headings="<h1>Page 2</h1>",
            images_with_alt=1,
            images_without_alt=0,
            word_count=300,
            internal_links=2
        ),
        create_mock_page(
            url="https://example.com/page3",
            title="Same Title for All Pages",  # Duplicate
            description="Third page description.",
            h1_count=1,
            headings="<h1>Page 3</h1>",
            images_with_alt=1,
            images_without_alt=0,
            word_count=300,
            internal_links=2
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

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.status in ["fail", "warning"], "Expected fail or warning for duplicate titles"

    # Check that duplicate titles were detected
    duplicate_title_found = any(
        "duplicate title" in issue["issue"].lower()
        for issue in result.details["critical_issues"]
    )
    assert duplicate_title_found, "Expected duplicate titles to be detected"
    print("✓ Duplicate titles test passed")


async def test_seo_optimizer_image_alt_text():
    """Test analyzer with missing image alt text."""

    page = create_mock_page(
        url="https://example.com/images",
        title="Page with Images - Good SEO Title Here",
        description="Testing image alt text detection for SEO optimization purposes.",
        h1_count=1,
        headings="<h1>Images</h1>",
        images_with_alt=2,
        images_without_alt=5,  # Missing alt text
        word_count=300,
        internal_links=3
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.status in ["warning", "fail"], "Expected warning or fail for missing alt text"

    # Check that missing alt text was detected
    alt_text_issue_found = any(
        "alt text" in w["issue"].lower()
        for w in result.details["warnings"]
    )
    assert alt_text_issue_found, "Expected missing alt text to be detected"
    print("✓ Image alt text test passed")


async def test_seo_optimizer_thin_content():
    """Test analyzer with thin content pages."""

    page = create_mock_page(
        url="https://example.com/thin",
        title="Thin Content Page - Needs More Words",
        description="This page has very little content and should be flagged.",
        h1_count=1,
        headings="<h1>Thin Content</h1>",
        images_with_alt=1,
        images_without_alt=0,
        word_count=50,  # Too few words
        internal_links=1
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    assert result.status in ["warning", "fail"], "Expected warning or fail for thin content"

    # Check that thin content was detected
    thin_content_found = any(
        "word" in w["issue"].lower() or "content" in w["issue"].lower()
        for w in result.details["warnings"]
    )
    assert thin_content_found, "Expected thin content to be detected"
    print("✓ Thin content test passed")


async def test_seo_optimizer_keyword_targeting():
    """Test analyzer with keyword targeting."""

    page = create_mock_page(
        url="https://example.com/keywords",
        title="SEO Optimization Guide - Best Practices",
        description="Learn SEO optimization techniques and best practices.",
        h1_count=1,
        headings="<h1>SEO Optimization</h1><h2>Keywords</h2>",
        images_with_alt=1,
        images_without_alt=0,
        word_count=400,
        internal_links=3
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot, target_keywords="SEO optimization, best practices")

    assert result.details["target_keywords"] == ["SEO optimization", "best practices"]

    # Should have opportunities if keywords aren't well distributed
    assert "opportunities" in result.details
    print("✓ Keyword targeting test passed")


async def test_seo_optimizer_internal_linking():
    """Test analyzer with poor internal linking."""

    page = create_mock_page(
        url="https://example.com/isolated",
        title="Isolated Page with No Links - SEO Issue",
        description="This page has no internal links and is isolated.",
        h1_count=1,
        headings="<h1>Isolated</h1>",
        images_with_alt=1,
        images_without_alt=0,
        word_count=300,
        internal_links=0  # No internal links
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    # Check that lack of internal links was detected
    internal_link_issue = any(
        "internal link" in opp["issue"].lower()
        for opp in result.details["opportunities"]
    )
    assert internal_link_issue, "Expected internal linking issue to be detected"
    print("✓ Internal linking test passed")


async def test_seo_optimizer_overall_score():
    """Test overall score calculation."""

    page = create_mock_page(
        url="https://example.com/score",
        title="Good SEO Page with Decent Optimization",
        description="This page has good SEO fundamentals but could be improved.",
        h1_count=1,
        headings="<h1>Title</h1><h2>Section</h2>",
        images_with_alt=2,
        images_without_alt=1,  # One issue
        word_count=350,
        internal_links=3
    )

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page],
        sitemap={"pages": ["https://example.com/score"]},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    assert "overall_score" in result.details
    assert 0 <= result.details["overall_score"] <= 10
    assert isinstance(result.details["overall_score"], float)
    print("✓ Overall score test passed")


async def test_seo_optimizer_categorization():
    """Test issue categorization (critical/warnings/opportunities)."""

    pages = [
        create_mock_page(
            url="https://example.com/critical",
            title="",  # Missing - critical
            description="",
            h1_count=0,  # Missing - critical
            headings="<h2>Section</h2>",
            images_with_alt=0,
            images_without_alt=3,  # Warning
            word_count=150,  # Warning
            internal_links=0
        ),
        create_mock_page(
            url="https://example.com/good",
            title="Good Page Title with Decent Length Here",
            description="Good meta description with sufficient length.",
            h1_count=1,
            headings="<h1>Good</h1><h2>Section</h2>",
            images_with_alt=2,
            images_without_alt=0,
            word_count=400,
            internal_links=3
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

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    assert "critical_issues" in result.details
    assert "warnings" in result.details
    assert "opportunities" in result.details

    # Should have critical issues from first page
    assert len(result.details["critical_issues"]) > 0

    print("✓ Categorization test passed")


async def run_all_tests():
    """Run all tests."""
    print("Running SEO Optimizer Tests...\n")

    await test_seo_optimizer_perfect_page()
    await test_seo_optimizer_missing_metadata()
    await test_seo_optimizer_suboptimal_metadata()
    await test_seo_optimizer_duplicate_titles()
    await test_seo_optimizer_image_alt_text()
    await test_seo_optimizer_thin_content()
    await test_seo_optimizer_keyword_targeting()
    await test_seo_optimizer_internal_linking()
    await test_seo_optimizer_overall_score()
    await test_seo_optimizer_categorization()

    print("\n✓ All SEO optimizer tests passed!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
