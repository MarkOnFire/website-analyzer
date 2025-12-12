#!/usr/bin/env python3.11
"""
Fix Generator - Generates actionable code fixes for detected CMS bugs.

Provides template-based fix generation for common WordPress bugs:
- Malformed embed codes (JSON in visible text)
- CSS rendering issues
- Legacy code patterns

Each fix includes:
- Multiple implementation approaches (database, code, manual)
- Syntax highlighting hints
- Realistic effort estimates
- Pros/cons analysis for informed decision-making
"""

from typing import Dict, List, Any
from dataclasses import dataclass
import re


@dataclass
class FixOption:
    """Represents a single fix approach."""
    name: str
    description: str
    code: str
    language: str  # sql, php, css, markdown
    effort_hours: str  # e.g., "2-4", "15 minutes"
    pros: List[str]
    cons: List[str]

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "name": self.name,
            "description": self.description,
            "code": self.code,
            "language": self.language,
            "effort_hours": self.effort_hours,
            "pros": self.pros,
            "cons": self.cons
        }


class FixGenerator:
    """
    Generates code fixes for detected bugs.

    Supports:
    - WordPress embed code fixes (database, PHP filter, manual)
    - CSS rendering fixes
    - Effort estimation
    - Priority assignment based on impact
    """

    def __init__(self):
        """Initialize fix generator with templates."""
        self.wordpress_embed_pattern = re.compile(
            r'\[\[.*?"fid".*?\]\]',
            re.DOTALL | re.IGNORECASE
        )
        self.css_issues = {
            'footer_bullets': {
                'selector': 'footer ul, footer ol',
                'properties': {'list-style': 'none', 'margin-left': '0', 'padding-left': '0'},
                'description': 'Remove bullet points from footer navigation'
            }
        }

    def generate_wordpress_embed_fix(self, bug_pattern: str) -> dict:
        """
        Generate WordPress embed code fix options.

        Args:
            bug_pattern: The detected embed code pattern (e.g., [[{"fid":"..."...}]])

        Returns:
            Dictionary with multiple fix options and recommendation
        """
        # Extract fid (file ID) from the pattern for use in fixes
        fid_match = re.search(r'"fid"\s*:\s*"([^"]+)"', bug_pattern)
        fid = fid_match.group(1) if fid_match else "FILE_ID"

        # Extract view_mode if present
        view_mode_match = re.search(r'"view_mode"\s*:\s*"([^"]+)"', bug_pattern)
        view_mode = view_mode_match.group(1) if view_mode_match else "full_width"

        # Option 1: Database Migration (SQL)
        option1 = FixOption(
            name="Database Migration (SQL)",
            description="Find and replace malformed embed codes with proper WordPress shortcodes",
            code="""-- Find pages with malformed embed codes
SELECT ID, post_title, post_content
FROM wp_posts
WHERE post_content LIKE '%[[{"fid"%'
AND post_type = 'post'
LIMIT 100;

-- Replace embed codes with proper media shortcodes
UPDATE wp_posts
SET post_content = REGEXP_REPLACE(
    post_content,
    '\\\\[\\\\[\\{"fid"\\s*:\\s*"([^"]+)"[^\\]]*\\}\\]\\]',
    '[media id="$1" class=""" + view_mode + """]'
)
WHERE post_content LIKE '%[[{"fid"%'
AND post_type = 'post';

-- Verify the changes
SELECT ID, post_title, post_content
FROM wp_posts
WHERE post_content LIKE '%[media id=%'
LIMIT 20;

-- IMPORTANT: Backup before running!
-- mysqldump -u root -p wordpress > backup.sql""",
            language="sql",
            effort_hours="2-4",
            pros=[
                "Permanent fix affecting all pages at once",
                "No user-facing code needed",
                "Complete fix in one operation"
            ],
            cons=[
                "Requires direct database access",
                "Must backup database first",
                "Requires WordPress knowledge",
                "Risk of data loss if regex is wrong"
            ]
        )

        # Option 2: PHP Filter (Code-based)
        php_code = """// Add to your theme's functions.php or a custom plugin
// This will fix embed codes without modifying the database

add_filter('the_content', 'fix_legacy_embed_codes', 20);

function fix_legacy_embed_codes($content) {
    // Match malformed embed patterns: [[{"fid":"...", ...}]]
    $pattern = '/\\\\[\\\\[\\{[^\\]]*"fid"\\s*:\\s*"([^"]+)"[^\\]]*\\}\\\\]/';

    // Replace with proper WordPress media shortcode
    $replacement = '[media id="$1" class=\"""" + view_mode + """\"]';

    $fixed_content = preg_replace($pattern, $replacement, $content);

    // Log how many fixes were applied
    if ($fixed_content !== $content) {
        error_log('Fixed ' . substr_count($content, '[[') . ' embed codes on ' . get_the_title());
    }

    return $fixed_content;
}

// Optional: Filter by post type to avoid unexpected changes
function fix_legacy_embed_codes($content) {
    if (is_singular('post')) {  // Only fix on blog posts
        $pattern = '/\\\\[\\\\[\\{[^\\]]*"fid"\\s*:\\s*"([^"]+)"[^\\]]*\\}\\\\]/';
        $replacement = '[media id="$1" class=\"""" + view_mode + """\"]';
        return preg_replace($pattern, $replacement, $content);
    }
    return $content;
}"""

        option2 = FixOption(
            name="PHP Content Filter",
            description="Use a WordPress filter to fix embeds on-the-fly without database changes",
            code=php_code,
            language="php",
            effort_hours="1-2",
            pros=[
                "No database changes needed",
                "Can be disabled by removing the filter",
                "Easy to test and debug",
                "Reversible - just remove the code"
            ],
            cons=[
                "Runs on every page load (minor performance impact)",
                "Only fixes display, not actual data",
                "Doesn't work if cache is enabled",
                "Requires access to theme/plugin files"
            ]
        )

        # Option 3: Manual Fix Instructions
        option3 = FixOption(
            name="Manual Fix (Step-by-Step)",
            description="Edit affected posts manually to replace embed codes",
            code="""STEPS TO FIX MANUALLY:

1. Identify Affected Pages:
   - Look for pages displaying raw JSON/embed code as text
   - Common on media-heavy content (articles, galleries)

2. For Each Affected Page:

   a) Open the post in WordPress Editor
   b) Switch to "Text" (HTML) view
   c) Find the malformed code: [[{"fid":"...", "view_mode":"...", ...}]]
   d) Delete the malformed code
   e) Re-add the image/media using the Media button:
      - Click "Add Media"
      - Select the image (search by ID if needed)
      - Set any caption/alignment
      - Click "Insert into post"
   f) Save/Update the post

3. Verify:
   - Check the page on the frontend
   - Ensure image displays correctly
   - Verify no text shows the raw code

4. Bulk Tools (Optional):
   - Use "Find & Replace" plugin to find all instances
   - https://wordpress.org/plugins/better-find-replace/
   - Test on staging first!

ESTIMATED TIME:
- Per page: 5-10 minutes (depending on number of embeds)
- 10 pages: 1-2 hours
- 50+ pages: Consider database or PHP approach""",
            language="markdown",
            effort_hours="5 minutes - 2 hours (per 10 pages)",
            pros=[
                "No coding required",
                "Full control and verification",
                "Can inspect each page individually",
                "Zero risk of unintended changes"
            ],
            cons=[
                "Very time-consuming for many pages",
                "Requires manual WordPress access",
                "Not scalable for large sites",
                "Human error risk (missing pages)"
            ]
        )

        return {
            "bug_type": "wordpress_malformed_embed",
            "affected_code_sample": bug_pattern[:100] + "...",
            "options": [
                option1.to_dict(),
                option2.to_dict(),
                option3.to_dict()
            ],
            "recommended": 1,  # PHP filter as default (reversible, low-risk)
            "severity": "high",
            "notes": [
                f"File ID detected: {fid}",
                f"View mode: {view_mode}",
                "This is a rendering bug where embed metadata is shown as text",
                "Usually caused by plugin conflicts or database corruption"
            ]
        }

    def generate_css_fix(
        self,
        selector: str,
        property_name: str,
        context: dict
    ) -> dict:
        """
        Generate CSS override fix.

        Args:
            selector: CSS selector (e.g., "footer ul")
            property_name: CSS property to fix (e.g., "list-style")
            context: Additional context including bug_type, description, etc.

        Returns:
            Dictionary with CSS fix
        """
        bug_type = context.get('bug_type', 'unknown')
        description = context.get('description', 'CSS rendering issue')
        issue_count = context.get('issue_count', 1)

        # Determine appropriate CSS value based on property
        css_value_map = {
            'list-style': 'none',
            'display': 'none',
            'visibility': 'hidden',
            'margin': '0',
            'padding': '0',
            'border': 'none',
            'color': 'inherit',
            'background': 'transparent',
            'text-decoration': 'none'
        }

        css_value = css_value_map.get(property_name, 'auto')

        # Build CSS code with proper specificity
        css_code = f"""/* Fix for: {description} */

/* Option 1: Simple override (add to custom CSS) */
{selector} {{
    {property_name}: {css_value} !important;
}}

/* Option 2: More specific selector (if conflicts) */
.main {selector} {{
    {property_name}: {css_value} !important;
}}

/* Option 3: Minimal fix (if specificity is overkill) */
{selector} {{
    {property_name}: {css_value};
}}"""

        fix_notes = []
        if issue_count == 1:
            fix_notes.append(f"This fixes the single affected element: {selector}")
        else:
            fix_notes.append(f"This fixes {issue_count} pages with the issue")

        fix_notes.extend([
            "Use !important if the original rule is hard to override",
            "Test on different screen sizes",
            "Check that no child elements need adjustment"
        ])

        return {
            "bug_type": "css_rendering_issue",
            "issue": description,
            "affected_elements": issue_count,
            "selector": selector,
            "property": property_name,
            "value": css_value,
            "options": [
                {
                    "name": "CSS Override (Custom CSS)",
                    "description": f"Add CSS rule to hide or reset the {property_name} property",
                    "code": css_code,
                    "language": "css",
                    "effort_hours": "15 minutes",
                    "pros": [
                        "No code/database changes needed",
                        "Can be added via theme customizer",
                        "Immediately visible and testable",
                        "Easy to remove or modify"
                    ],
                    "cons": [
                        "Only fixes display, not underlying cause",
                        "May need !important (fragile)",
                        "Doesn't scale to semantic fixes"
                    ]
                }
            ],
            "recommended": 0,
            "root_cause_suggestions": [
                "Check parent element styling",
                "Review theme CSS conflicts",
                "Verify plugin compatibility",
                "Inspect element in browser DevTools"
            ],
            "notes": fix_notes
        }

    def estimate_effort(self, fix_option: dict) -> str:
        """
        Estimate implementation effort for a fix option.

        Args:
            fix_option: A fix option dictionary from generate_*_fix methods

        Returns:
            Effort estimate string (e.g., "2-4 hours", "15 minutes")
        """
        effort = fix_option.get('effort_hours', 'unknown')

        # Parse and return with context
        return effort

    def assign_priority(self, bug_type: str, page_count: int) -> str:
        """
        Assign priority level based on bug type and impact.

        Args:
            bug_type: Type of bug (e.g., "wordpress_malformed_embed", "css_issue")
            page_count: Number of pages affected

        Returns:
            Priority level: "critical", "high", "medium", or "low"
        """
        # High impact bugs
        critical_types = {
            'wordpress_malformed_embed',
            'missing_page_content',
            'broken_navigation',
            'security_issue'
        }

        high_types = {
            'css_rendering_issue',
            'missing_images',
            'broken_links',
            'performance_issue'
        }

        # Determine base priority from bug type
        if bug_type in critical_types:
            base_priority = 3  # critical
        elif bug_type in high_types:
            base_priority = 2  # high
        else:
            base_priority = 1  # medium/low

        # Adjust by impact (number of pages)
        impact_multiplier = min(page_count / 10, 2)  # Up to 2x multiplier

        adjusted_priority = base_priority + impact_multiplier

        if adjusted_priority >= 2.5 or page_count > 100:
            return "critical"
        elif adjusted_priority >= 2.0 or page_count > 50:
            return "high"
        elif adjusted_priority >= 1.5 or page_count > 10:
            return "medium"
        else:
            return "low"

    def generate_fix_report(
        self,
        bug_type: str,
        bug_pattern: str,
        page_count: int,
        affected_pages: List[str] = None
    ) -> dict:
        """
        Generate a comprehensive fix report for a detected bug.

        Args:
            bug_type: Type of bug ("wordpress_embed", "css_issue", etc.)
            bug_pattern: The detected bug pattern
            page_count: Number of affected pages
            affected_pages: List of affected page URLs (optional)

        Returns:
            Complete fix report with priority, options, and recommendations
        """
        # Generate fixes based on bug type
        if 'wordpress' in bug_type.lower() or 'embed' in bug_type.lower():
            fix_options = self.generate_wordpress_embed_fix(bug_pattern)
        elif 'css' in bug_type.lower():
            fix_options = self.generate_css_fix('footer ul', 'list-style', {
                'bug_type': bug_type,
                'description': 'CSS rendering issue detected',
                'issue_count': page_count
            })
        else:
            fix_options = self._generate_generic_fix(bug_type)

        # Assign priority
        priority = self.assign_priority(bug_type, page_count)

        # Estimate total effort
        recommended_option = fix_options['options'][fix_options['recommended']]
        effort = self.estimate_effort(recommended_option)

        return {
            "summary": {
                "bug_type": bug_type,
                "pages_affected": page_count,
                "priority": priority,
                "estimated_effort": effort
            },
            "affected_pages": affected_pages or [],
            "fixes": fix_options,
            "next_steps": [
                f"1. Review the {len(fix_options['options'])} fix options above",
                f"2. Choose based on your comfort level and resources",
                f"3. Test on staging environment first",
                f"4. Monitor pages after applying fix",
                f"5. Update your deployment checklist"
            ]
        }

    def _generate_generic_fix(self, bug_type: str) -> dict:
        """Generate a generic fix template for unknown bug types."""
        return {
            "bug_type": bug_type,
            "options": [
                {
                    "name": "Investigation Required",
                    "description": f"Unknown bug type: {bug_type}. Manual investigation needed.",
                    "code": f"# TODO: Investigate {bug_type}\n# Check browser console for errors\n# Compare with working pages",
                    "language": "markdown",
                    "effort_hours": "1-2",
                    "pros": ["Ensures correct fix is applied"],
                    "cons": ["Requires manual work"]
                }
            ],
            "recommended": 0
        }


# Example usage and demonstration
if __name__ == "__main__":
    generator = FixGenerator()

    # Example 1: WordPress embed bug
    print("=" * 70)
    print("EXAMPLE 1: WordPress Embed Code Bug")
    print("=" * 70)
    print()

    embed_bug = '''[[{"fid":"1101026″,"view_mode":"full_width","fields":{"format":"full_width","alignment":"","field_image_caption[und][0][value]":"%3Cp%3ETom%20and%20Jerry%20milkglass%20set%3C%2Fp%3E"}}]]'''

    result = generator.generate_wordpress_embed_fix(embed_bug)

    print(f"Bug Type: {result['bug_type']}")
    print(f"Severity: {result['severity']}")
    print(f"Pages Found: {len(result['options'])} fix options")
    print()

    for i, option in enumerate(result['options'], 1):
        print(f"\nOption {i}: {option['name']}")
        print(f"  Effort: {option['effort_hours']}")
        print(f"  Language: {option['language']}")
        print(f"  Pros:")
        for pro in option['pros'][:2]:
            print(f"    - {pro}")
        print(f"  Cons:")
        for con in option['cons'][:2]:
            print(f"    - {con}")

    recommended_idx = result['recommended']
    print(f"\nRecommended: Option {recommended_idx + 1} ({result['options'][recommended_idx]['name']})")

    # Example 2: CSS issue fix
    print("\n" + "=" * 70)
    print("EXAMPLE 2: CSS Rendering Issue")
    print("=" * 70)
    print()

    css_context = {
        'bug_type': 'css_rendering_issue',
        'description': 'Footer navigation showing unwanted bullet points',
        'issue_count': 5
    }

    css_result = generator.generate_css_fix('footer ul', 'list-style', css_context)

    print(f"Issue: {css_result['issue']}")
    print(f"Affected Elements: {css_result['affected_elements']}")
    print(f"Selector: {css_result['selector']}")
    print()
    print("CSS Fix Code:")
    print(css_result['options'][0]['code'][:300])
    print("...\n")

    # Example 3: Priority assignment
    print("=" * 70)
    print("EXAMPLE 3: Priority Assignment")
    print("=" * 70)
    print()

    test_cases = [
        ("wordpress_malformed_embed", 1),
        ("wordpress_malformed_embed", 50),
        ("css_rendering_issue", 5),
        ("missing_images", 200),
    ]

    for bug_type, count in test_cases:
        priority = generator.assign_priority(bug_type, count)
        print(f"{bug_type:30} ({count:3} pages) -> Priority: {priority}")

    print()
