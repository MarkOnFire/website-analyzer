#!/usr/bin/env python3.11
"""
Root Cause Analyzer for Bug Finder

Analyzes bug patterns detected in web pages and generates likely root causes.
Focuses on identifying:
- WordPress embed code issues (migrated content from old CMS)
- CSS styling conflicts
- JavaScript errors
- Accessibility problems

This module uses pattern matching and heuristics to classify bugs and provide
contextual explanations about their origins.
"""

import re
from typing import Dict, Any, Optional, List
from enum import Enum


class BugType(Enum):
    """Enumeration of bug types that can be detected."""
    WORDPRESS_EMBED = "wordpress_embed"
    CSS_STYLING = "css_styling"
    JAVASCRIPT_ERROR = "javascript_error"
    ACCESSIBILITY = "accessibility"
    UNKNOWN = "unknown"


class RootCauseAnalyzer:
    """
    Analyzes bug text and generates likely root causes.

    This class examines bug patterns found in web pages and provides structured
    analysis including bug classification, root cause hypothesis, and confidence
    assessment. The primary focus is on WordPress embed codes and migration-related
    issues.

    Example:
        >>> analyzer = RootCauseAnalyzer()
        >>> bug_text = '[[{"fid":"1101026″,"view_mode":"full_width"...}]]'
        >>> result = analyzer.analyze_wordpress_embeds(bug_text, "https://example.com/page")
        >>> print(result['root_cause'])
        'Content migrated from old CMS with WordPress shortcodes...'
    """

    def __init__(self):
        """Initialize the analyzer with pattern definitions."""
        self.wordpress_embed_pattern = re.compile(
            r'\[\[.+?"fid"\s*:\s*"[^"]+".+?\]\]',
            re.DOTALL | re.IGNORECASE
        )
        self.view_mode_pattern = re.compile(
            r'"view_mode"\s*:\s*"([^"]+)"'
        )
        self.field_pattern = re.compile(
            r'"field_[^"]+"\s*:'
        )
        self.shortcode_pattern = re.compile(
            r'\[(?!\/)[a-z_-]+(?:\s+[^\]]*?)?\]'
        )
        self.css_error_keywords = [
            'undefined', 'color', 'font', 'margin', 'padding', 'border',
            'display', 'position', 'overflow', 'z-index', 'opacity'
        ]
        self.js_error_keywords = [
            'error', 'undefined', 'null', 'cannot read', 'is not a function',
            'reference error', 'type error', 'syntax error'
        ]

    def classify_bug_type(self, bug_text: str) -> str:
        """
        Classify the type of bug based on text content.

        Examines the bug text to determine its category:
        - wordpress_embed: Contains [[...]] structures with fid fields
        - css_styling: Contains CSS property references and style errors
        - javascript_error: Contains JS error messages
        - accessibility: Contains ARIA or alt text issues
        - unknown: Cannot be classified

        Args:
            bug_text: The bug text to classify

        Returns:
            String representing the bug type from BugType enum
        """
        if not bug_text or not isinstance(bug_text, str):
            return BugType.UNKNOWN.value

        bug_text_lower = bug_text.lower()

        # Check for WordPress embeds (primary pattern)
        if self.wordpress_embed_pattern.search(bug_text):
            if '"fid"' in bug_text or "'fid'" in bug_text:
                return BugType.WORDPRESS_EMBED.value

        # Check for CSS styling issues
        if any(keyword in bug_text_lower for keyword in self.css_error_keywords):
            if 'style' in bug_text_lower or 'css' in bug_text_lower:
                return BugType.CSS_STYLING.value

        # Check for JavaScript errors
        if any(keyword in bug_text_lower for keyword in self.js_error_keywords):
            return BugType.JAVASCRIPT_ERROR.value

        # Check for accessibility issues
        if any(keyword in bug_text_lower for keyword in ['aria', 'alt text', 'role=']):
            return BugType.ACCESSIBILITY.value

        return BugType.UNKNOWN.value

    def analyze_wordpress_embeds(
        self,
        bug_text: str,
        url: str
    ) -> Dict[str, Any]:
        """
        Analyze WordPress embed code issues.

        Detects WordPress embed patterns (typically from Drupal/CMS migrations)
        and provides context about:
        - Migration era (pre-2023 content)
        - Shortcode patterns
        - Theme compatibility issues
        - View modes and field types

        Args:
            bug_text: Text containing potential WordPress embed code
            url: URL where the bug was found (for context)

        Returns:
            Dictionary with keys:
            - bug_type: 'wordpress_embed'
            - root_cause: Plain-English explanation
            - migration_era: 'pre-2023' or 'unknown'
            - confidence: 'low', 'medium', or 'high'
            - indicators: List of detected patterns
            - view_modes: List of detected view modes
        """
        indicators = []
        view_modes = []

        if not bug_text or not isinstance(bug_text, str):
            return {
                "bug_type": "wordpress_embed",
                "root_cause": "Invalid bug text provided",
                "migration_era": "unknown",
                "confidence": "low",
                "indicators": [],
                "view_modes": []
            }

        # Check for double-bracket syntax
        if '[[' in bug_text and ']]' in bug_text:
            indicators.append("double-bracket syntax [[...]]")

        # Check for fid field (Drupal media field ID)
        if '"fid"' in bug_text or "'fid'" in bug_text:
            indicators.append("fid field (Drupal media identifier)")

        # Check for view_mode field
        view_mode_matches = self.view_mode_pattern.findall(bug_text)
        if view_mode_matches:
            view_modes = list(set(view_mode_matches))  # Remove duplicates
            indicators.append("view_mode field")

        # Check for field array syntax
        field_matches = self.field_pattern.findall(bug_text)
        if field_matches:
            indicators.append(f"field array syntax ({len(field_matches)} fields)")

        # Check for type field
        if '"type"' in bug_text:
            indicators.append("type field")

        # Check for encoded data (common in migrations)
        if '%' in bug_text and any(c in bug_text for c in ['%3C', '%20', '%2F']):
            indicators.append("URL-encoded field data")

        # Determine confidence based on indicators found
        confidence = "low"
        if len(indicators) >= 3:
            confidence = "high"
        elif len(indicators) >= 2:
            confidence = "medium"

        # Build root cause explanation
        root_cause = (
            "Content migrated from old CMS (likely Drupal 7) with WordPress "
            "shortcodes containing media references. The current theme does not "
            "process these [[{...}]] structures, causing them to render as raw text. "
            f"Detected view modes: {', '.join(view_modes) if view_modes else 'unknown'}. "
            "This typically occurs when pages are migrated without converting embedded "
            "media references to the new platform's format."
        )

        return {
            "bug_type": BugType.WORDPRESS_EMBED.value,
            "root_cause": root_cause,
            "migration_era": "pre-2023",
            "confidence": confidence,
            "indicators": indicators,
            "view_modes": view_modes
        }

    def analyze_css_issues(
        self,
        bug_text: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Analyze CSS styling conflict issues.

        Detects CSS-related problems such as:
        - Missing style definitions
        - CSS override conflicts
        - Specificity problems
        - Missing theme files

        Args:
            bug_text: Text describing or containing the CSS issue
            context: Optional context dict with page info, selectors, etc.

        Returns:
            Dictionary with keys:
            - bug_type: 'css_styling'
            - root_cause: Plain-English explanation
            - confidence: 'low', 'medium', or 'high'
            - affected_properties: List of CSS properties mentioned
            - indicators: List of detected patterns
        """
        indicators = []
        affected_properties = []

        if not bug_text or not isinstance(bug_text, str):
            return {
                "bug_type": "css_styling",
                "root_cause": "Invalid bug text provided",
                "confidence": "low",
                "affected_properties": [],
                "indicators": []
            }

        bug_text_lower = bug_text.lower()

        # Detect CSS property mentions
        for prop in self.css_error_keywords:
            if prop in bug_text_lower:
                affected_properties.append(prop)

        # Check for specific error patterns
        if 'undefined' in bug_text_lower:
            indicators.append("undefined style or property")
        if 'override' in bug_text_lower:
            indicators.append("CSS override conflict")
        if 'specificity' in bug_text_lower:
            indicators.append("selector specificity issue")
        if 'missing' in bug_text_lower or 'not found' in bug_text_lower:
            indicators.append("missing stylesheet or definition")
        if '!important' in bug_text:
            indicators.append("!important flag usage detected")

        confidence = "low"
        if len(indicators) >= 2:
            confidence = "medium"
        if len(indicators) >= 3:
            confidence = "high"

        root_cause = (
            "CSS styling conflict detected. This typically results from theme updates, "
            "missing stylesheet files, or CSS specificity issues. "
        )

        if affected_properties:
            root_cause += (
                f"Affected CSS properties: {', '.join(set(affected_properties))}. "
            )

        if indicators:
            root_cause += (
                f"Issues detected: {', '.join(indicators)}. "
            )

        root_cause += (
            "Verify that all theme stylesheet files are present and correctly linked. "
            "Check for CSS specificity conflicts in custom CSS or child theme files."
        )

        return {
            "bug_type": BugType.CSS_STYLING.value,
            "root_cause": root_cause,
            "confidence": confidence,
            "affected_properties": list(set(affected_properties)),
            "indicators": indicators
        }

    def generate_hypothesis(
        self,
        bug_type: str,
        bug_text: str,
        url: str
    ) -> str:
        """
        Generate a plain-English hypothesis about the bug's root cause.

        Creates a human-readable explanation of why the bug likely occurred,
        tailored to the bug type.

        Args:
            bug_type: Type of bug (from BugType enum or classification)
            bug_text: The bug text to analyze
            url: URL where bug was found

        Returns:
            Plain-English explanation of likely root cause
        """
        if not bug_type or not isinstance(bug_text, str):
            return "Unable to generate hypothesis: invalid input"

        if bug_type == BugType.WORDPRESS_EMBED.value:
            return (
                "This page contains content that was migrated from an older content "
                "management system (likely Drupal 7 or WordPress with custom plugins). "
                "The embedded media references use a shortcode syntax [[{...}]] that "
                "is no longer processed by the current theme or platform. The code that "
                "handled these shortcodes was either lost during migration or is "
                "incompatible with the current WordPress version. To fix this, the "
                "embedded media should be re-inserted using WordPress's native media "
                "blocks or the appropriate plugin for handling this content format."
            )

        elif bug_type == BugType.CSS_STYLING.value:
            return (
                "This page is experiencing CSS styling conflicts. The issue could be "
                "caused by: (1) missing or broken stylesheet files after a theme update; "
                "(2) CSS specificity conflicts between theme styles and custom CSS; "
                "(3) deprecated CSS properties no longer supported by modern browsers; "
                "or (4) child theme overrides conflicting with parent theme styles. "
                "Check the browser's developer tools to identify which CSS rules are "
                "being applied and verify that all stylesheets are loading correctly."
            )

        elif bug_type == BugType.JAVASCRIPT_ERROR.value:
            return (
                "This page contains a JavaScript error that's preventing proper rendering "
                "or functionality. The error could stem from: (1) deprecated JavaScript "
                "libraries no longer compatible with modern browsers; (2) missing plugin "
                "files or conflicts between multiple plugins; (3) inline scripts referencing "
                "removed or renamed functions; or (4) third-party script errors. Check the "
                "browser console for specific error messages to identify the problematic code."
            )

        elif bug_type == BugType.ACCESSIBILITY.value:
            return (
                "This page has accessibility issues that may prevent some users from "
                "accessing content. Common causes include: (1) missing alt text for images; "
                "(2) improper ARIA labels or roles; (3) insufficient color contrast; "
                "(4) keyboard navigation problems; or (5) missing semantic HTML structure. "
                "Review the page with accessibility testing tools to identify specific "
                "violations and ensure compliance with WCAG guidelines."
            )

        else:
            return (
                "Unable to determine the specific root cause of this bug. The issue may be "
                "caused by theme conflicts, plugin incompatibilities, server-side rendering "
                "errors, or data corruption. Manual inspection of the page source code and "
                "browser console output is recommended for further diagnosis."
            )

    def analyze(self, bug_text: str, url: str = "") -> Dict[str, Any]:
        """
        Comprehensive analysis of a bug.

        Automatically detects bug type and generates full analysis including
        classification, root cause, and confidence assessment.

        Args:
            bug_text: The bug text to analyze
            url: URL where the bug was found (optional, for context)

        Returns:
            Dictionary containing:
            - bug_type: Classification of the bug
            - root_cause: Detailed explanation
            - confidence: Confidence level (low/medium/high)
            - hypothesis: Plain-English summary
            - All additional fields from specific analyzers
        """
        if not bug_text or not isinstance(bug_text, str):
            return {
                "bug_type": BugType.UNKNOWN.value,
                "root_cause": "Invalid bug text provided",
                "confidence": "low",
                "hypothesis": "Unable to analyze invalid input"
            }

        # Classify the bug
        bug_type = self.classify_bug_type(bug_text)

        # Route to appropriate analyzer
        if bug_type == BugType.WORDPRESS_EMBED.value:
            analysis = self.analyze_wordpress_embeds(bug_text, url)
        elif bug_type == BugType.CSS_STYLING.value:
            analysis = self.analyze_css_issues(bug_text)
        else:
            # Generic analysis for unknown types
            analysis = {
                "bug_type": bug_type,
                "root_cause": self.generate_hypothesis(bug_type, bug_text, url),
                "confidence": "low"
            }

        # Add hypothesis to all analyses
        analysis["hypothesis"] = self.generate_hypothesis(bug_type, bug_text, url)

        return analysis


# Example usage and testing
if __name__ == "__main__":
    # Initialize analyzer
    analyzer = RootCauseAnalyzer()

    # Example: WordPress embed bug (from WPR.org)
    wordpress_bug = '''[[{"fid":"1101026″,"view_mode":"full_width","fields":{"format":"full_width","alignment":"","field_image_caption[und][0][value]":"%3Cp%3ETom%20and%20Jerry%20milkglass%20set%20%3Cem%3E%3Ca%20href%3D%22https%3A%2F%2Fwww.flickr.com%2Fphotos%2Fjohnnyvintage%2F%22%3EJonnie%20Andersen%3C%2Fa%3E%20(CC%20BY-NC-ND%202.0)%3C%2Fem%3E%3C%2Fp%3E%0A","field_image_caption[und][0][format]":"full_html"},"type":"media"}]]'''

    print("=" * 80)
    print("BUG FINDER ROOT CAUSE ANALYZER - EXAMPLE USAGE")
    print("=" * 80)
    print()

    # Test 1: WordPress embed analysis
    print("TEST 1: WordPress Embed Bug Analysis")
    print("-" * 80)
    result = analyzer.analyze(wordpress_bug, "https://www.wpr.org/example")
    print(f"Bug Type: {result['bug_type']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Migration Era: {result.get('migration_era', 'N/A')}")
    print()
    print("Indicators Found:")
    for indicator in result.get('indicators', []):
        print(f"  • {indicator}")
    print()
    print(f"View Modes: {', '.join(result.get('view_modes', []))}")
    print()
    print("Root Cause Analysis:")
    print(result['root_cause'])
    print()
    print("Plain-English Hypothesis:")
    print(result['hypothesis'])
    print()

    # Test 2: CSS bug analysis
    print("=" * 80)
    print("TEST 2: CSS Styling Bug Analysis")
    print("-" * 80)
    css_bug = "undefined color style for .header-nav element, missing CSS override for theme"
    result2 = analyzer.analyze(css_bug, "https://example.com/page")
    print(f"Bug Type: {result2['bug_type']}")
    print(f"Confidence: {result2['confidence']}")
    print()
    print("Affected Properties:")
    for prop in result2.get('affected_properties', []):
        print(f"  • {prop}")
    print()
    print("Root Cause Analysis:")
    print(result2['root_cause'])
    print()

    # Test 3: JavaScript error analysis
    print("=" * 80)
    print("TEST 3: JavaScript Error Analysis")
    print("-" * 80)
    js_bug = "Uncaught TypeError: jQuery is not defined, reference error in plugin.js"
    result3 = analyzer.analyze(js_bug, "https://example.com/page")
    print(f"Bug Type: {result3['bug_type']}")
    print(f"Confidence: {result3['confidence']}")
    print()
    print("Plain-English Hypothesis:")
    print(result3['hypothesis'])
    print()

    # Test 4: Unknown bug
    print("=" * 80)
    print("TEST 4: Unknown Bug Analysis")
    print("-" * 80)
    unknown_bug = "Some random text that doesn't match any pattern"
    result4 = analyzer.analyze(unknown_bug, "https://example.com/page")
    print(f"Bug Type: {result4['bug_type']}")
    print(f"Confidence: {result4['confidence']}")
    print()
    print("Root Cause Analysis:")
    print(result4['root_cause'])
