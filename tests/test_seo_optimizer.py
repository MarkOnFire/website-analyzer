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

    # Build internal links (link to self or fragment links to avoid broken link detection)
    link_tags = []
    for i in range(internal_links):
        link_tags.append(f'<a href="#{i}">Link {i}</a>')

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

    # Should have warnings even if status is pass
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


async def test_seo_optimizer_broken_links():
    """Test broken internal link detection."""

    pages = [
        create_mock_page(
            url="https://example.com/page1",
            title="Page 1 - Good Page Title",
            description="This page has links to other pages.",
            h1_count=1,
            headings="<h1>Page 1</h1>",
            images_with_alt=1,
            images_without_alt=0,
            word_count=300,
            internal_links=2
        ),
        create_mock_page(
            url="https://example.com/page2",
            title="Page 2 - Good Page Title",
            description="This page exists.",
            h1_count=1,
            headings="<h1>Page 2</h1>",
            images_with_alt=1,
            images_without_alt=0,
            word_count=300,
            internal_links=2
        )
    ]

    # Add broken link to page1
    temp_dir = pages[0].directory
    html_content = (temp_dir / "raw.html").read_text()
    # Add a link to non-existent page
    html_content = html_content.replace("</body>", '<a href="/broken-page">Broken Link</a></body>')
    (temp_dir / "raw.html").write_text(html_content)
    (temp_dir / "cleaned.html").write_text(html_content)

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

    # Check that broken link was detected
    broken_link_issue = any(
        "broken internal link" in issue["issue"].lower()
        for issue in result.details["critical_issues"]
    )
    assert broken_link_issue, "Expected broken internal link to be detected"
    print("✓ Broken links test passed")


async def test_seo_optimizer_redirect_chains():
    """Test redirect chain detection."""

    # Create a page with redirect status code
    page = create_mock_page(
        url="https://example.com/old-page",
        title="Old Page - Redirects",
        description="This page redirects.",
        h1_count=1,
        headings="<h1>Old Page</h1>",
        images_with_alt=1,
        images_without_alt=0,
        word_count=300,
        internal_links=1
    )

    # Modify the page to have redirect status
    page.status_code = 301

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

    # Check that redirect was detected
    redirect_issue = any(
        "redirect" in w["issue"].lower()
        for w in result.details["warnings"]
    )
    assert redirect_issue, "Expected redirect chain to be detected"
    print("✓ Redirect chains test passed")


async def test_seo_optimizer_mobile_responsiveness():
    """Test mobile responsiveness indicators (viewport meta tag)."""

    # Page without viewport
    page_no_viewport = create_mock_page(
        url="https://example.com/no-viewport",
        title="No Viewport - Bad for Mobile",
        description="This page has no viewport meta tag.",
        h1_count=1,
        headings="<h1>No Viewport</h1>",
        images_with_alt=1,
        images_without_alt=0,
        word_count=300,
        internal_links=1
    )

    # Remove viewport from HTML
    temp_dir = page_no_viewport.directory
    html_content = (temp_dir / "raw.html").read_text()
    html_content = html_content.replace('<meta name="viewport" content="width=device-width, initial-scale=1">', '')
    (temp_dir / "raw.html").write_text(html_content)
    (temp_dir / "cleaned.html").write_text(html_content)

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://example.com",
        pages=[page_no_viewport],
        sitemap={},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    # Check that missing viewport was detected
    viewport_issue = any(
        "viewport" in issue["issue"].lower()
        for issue in result.details["critical_issues"]
    )
    assert viewport_issue, "Expected missing viewport to be detected"
    print("✓ Mobile responsiveness test passed")


async def test_seo_optimizer_page_performance():
    """Test page load performance metrics."""

    # Create a page with large HTML content
    page = create_mock_page(
        url="https://example.com/large",
        title="Large Page - Performance Issue",
        description="This page has very large HTML.",
        h1_count=1,
        headings="<h1>Large Page</h1>",
        images_with_alt=1,
        images_without_alt=0,
        word_count=300,
        internal_links=1
    )

    # Make the HTML very large (>1MB)
    temp_dir = page.directory
    html_content = (temp_dir / "raw.html").read_text()
    # Add lots of content to exceed 1MB
    large_content = html_content + ("<p>Large content padding. " * 50000)
    (temp_dir / "raw.html").write_text(large_content)
    (temp_dir / "cleaned.html").write_text(large_content)

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

    # Check that large page was detected
    perf_issue = any(
        "large" in w["issue"].lower() and "html size" in w["issue"].lower()
        for w in result.details["warnings"]
    )
    assert perf_issue, "Expected large page to be detected"
    print("✓ Page performance test passed")


async def test_seo_optimizer_ecommerce_site():
    """Test SEO optimization on e-commerce site."""

    # E-commerce sites need: product schema, proper titles, good images with alt text
    pages = [
        # Homepage
        create_mock_page(
            url="https://shop.example.com/",
            title="Example Shop - Buy Quality Products Online",
            description="Shop the best selection of quality products. Free shipping on orders over $50. 30-day returns.",
            h1_count=1,
            headings="<h1>Welcome to Example Shop</h1><h2>Featured Products</h2><h2>Shop by Category</h2>",
            images_with_alt=5,
            images_without_alt=0,
            word_count=400,
            internal_links=10
        ),
        # Product page
        create_mock_page(
            url="https://shop.example.com/products/widget",
            title="Premium Widget - $29.99 - Example Shop",
            description="High-quality premium widget. Durable construction, lifetime warranty. Order today for free shipping!",
            h1_count=1,
            headings="<h1>Premium Widget</h1><h2>Product Details</h2><h2>Customer Reviews</h2><h2>Related Products</h2>",
            images_with_alt=4,
            images_without_alt=0,
            word_count=500,
            internal_links=8
        ),
        # Category page
        create_mock_page(
            url="https://shop.example.com/category/widgets",
            title="Widgets - Shop All Widget Products - Example Shop",
            description="Browse our complete selection of widgets. Compare features, prices, and customer reviews.",
            h1_count=1,
            headings="<h1>All Widgets</h1><h2>Filter by Price</h2>",
            images_with_alt=12,
            images_without_alt=0,
            word_count=350,
            internal_links=15
        ),
    ]

    # Add product schema to product page
    product_page_dir = pages[1].directory
    html = (product_page_dir / "raw.html").read_text()
    schema = '''<script type="application/ld+json">
    {
      "@context": "https://schema.org/",
      "@type": "Product",
      "name": "Premium Widget",
      "offers": {
        "@type": "Offer",
        "price": "29.99",
        "priceCurrency": "USD"
      }
    }
    </script>'''
    html = html.replace("</head>", schema + "</head>")
    (product_page_dir / "raw.html").write_text(html)
    (product_page_dir / "cleaned.html").write_text(html)

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://shop.example.com",
        pages=pages,
        sitemap={"pages": [p.url for p in pages]},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    # E-commerce should have good overall score
    assert result.details["overall_score"] >= 7.0, f"Expected score >= 7 for e-commerce, got {result.details['overall_score']}"

    # E-commerce should have no critical issues
    assert len(result.details["critical_issues"]) == 0, "Well-optimized e-commerce should have no critical issues"

    print("✓ E-commerce site test passed")


async def test_seo_optimizer_blog_site():
    """Test SEO optimization on blog/content site."""

    # Blog sites need: good meta descriptions, proper heading hierarchy, internal linking
    pages = [
        # Homepage
        create_mock_page(
            url="https://blog.example.com/",
            title="Example Blog - Insights on Technology and Innovation",
            description="Read the latest articles on technology, innovation, and industry trends. Updated weekly with expert insights.",
            h1_count=1,
            headings="<h1>Example Blog</h1><h2>Latest Posts</h2><h2>Popular Categories</h2>",
            images_with_alt=3,
            images_without_alt=0,
            word_count=450,
            internal_links=12
        ),
        # Blog post 1
        create_mock_page(
            url="https://blog.example.com/2025/01/seo-best-practices",
            title="SEO Best Practices for 2025: Complete Guide",
            description="Learn the latest SEO best practices for 2025. From technical optimization to content strategy, this guide covers everything.",
            h1_count=1,
            headings="<h1>SEO Best Practices for 2025</h1><h2>Introduction</h2><h3>Why SEO Matters</h3><h2>Technical SEO</h2><h3>Page Speed</h3><h3>Mobile Optimization</h3><h2>Content Strategy</h2><h3>Keyword Research</h3>",
            images_with_alt=5,
            images_without_alt=0,
            word_count=1200,
            internal_links=8
        ),
        # Blog post 2
        create_mock_page(
            url="https://blog.example.com/2025/01/content-marketing-trends",
            title="Top Content Marketing Trends to Watch in 2025",
            description="Discover the content marketing trends that will shape 2025. Expert analysis and actionable insights for marketers.",
            h1_count=1,
            headings="<h1>Top Content Marketing Trends</h1><h2>Trend 1: AI-Powered Content</h2><h2>Trend 2: Video Content</h2><h2>Trend 3: Personalization</h2><h2>Conclusion</h2>",
            images_with_alt=4,
            images_without_alt=0,
            word_count=900,
            internal_links=6
        ),
        # Category page
        create_mock_page(
            url="https://blog.example.com/category/seo",
            title="SEO Articles - Example Blog",
            description="Browse all SEO articles. Learn about search engine optimization from industry experts.",
            h1_count=1,
            headings="<h1>SEO Articles</h1><h2>Recent Posts</h2>",
            images_with_alt=2,
            images_without_alt=0,
            word_count=300,
            internal_links=10
        ),
    ]

    # Add article schema to blog posts
    for page in pages[1:3]:  # Add to blog posts
        page_dir = page.directory
        html = (page_dir / "raw.html").read_text()
        schema = '''<script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "Article",
          "headline": "Article Headline",
          "author": {
            "@type": "Person",
            "name": "John Doe"
          },
          "datePublished": "2025-01-01"
        }
        </script>'''
        html = html.replace("</head>", schema + "</head>")
        (page_dir / "raw.html").write_text(html)
        (page_dir / "cleaned.html").write_text(html)

    snapshot = SiteSnapshot(
        snapshot_dir=Path("/tmp"),
        timestamp="2025-01-01T00:00:00Z",
        root_url="https://blog.example.com",
        pages=pages,
        sitemap={"pages": [p.url for p in pages]},
        summary={}
    )

    plugin = SeoOptimizer()
    result = await plugin.analyze(snapshot)

    # Blog should have good overall score
    assert result.details["overall_score"] >= 7.0, f"Expected score >= 7 for blog, got {result.details['overall_score']}"

    # Blog should have no critical issues
    assert len(result.details["critical_issues"]) == 0, "Well-optimized blog should have no critical issues"

    print("✓ Blog site test passed")


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
    await test_seo_optimizer_broken_links()
    await test_seo_optimizer_redirect_chains()
    await test_seo_optimizer_mobile_responsiveness()
    await test_seo_optimizer_page_performance()
    await test_seo_optimizer_ecommerce_site()
    await test_seo_optimizer_blog_site()

    print("\n✓ All SEO optimizer tests passed!")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
