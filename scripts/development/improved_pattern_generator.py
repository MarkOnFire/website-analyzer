#!/usr/bin/env python3.11
"""
Pattern Generator: Creates flexible regex patterns from bug examples.

Handles:
- Unicode quote variations (" ' ' " ″ ‴)
- Whitespace variations
- Structural matching vs exact content
- Optional fields
"""

import re
from typing import List, Dict

class PatternGenerator:
    """Generates flexible regex patterns from bug examples."""

    # Common quote characters (regular, curly, primes)
    QUOTE_CHARS = r'["\'"″‴]'

    # Common whitespace
    WHITESPACE = r'\s*'

    @staticmethod
    def analyze_example(example: str) -> Dict[str, str]:
        """
        Analyze a bug example and generate multiple flexible patterns.

        Args:
            example: The bug text example from user

        Returns:
            Dict of pattern_name -> regex_pattern
        """
        patterns = {}

        # Pattern 1: Opening structure - most lenient
        # Matches [[ followed by { and fid field
        patterns["opening_structure"] = (
            r'\[\[' +  # Double opening brackets
            PatternGenerator.WHITESPACE +
            r'\{' +  # Opening brace
            PatternGenerator.WHITESPACE +
            PatternGenerator.QUOTE_CHARS + r'fid' + PatternGenerator.QUOTE_CHARS +
            PatternGenerator.WHITESPACE + r':' + PatternGenerator.WHITESPACE +
            PatternGenerator.QUOTE_CHARS  # Start of fid value
        )

        # Pattern 2: Core structure - fid + view_mode
        patterns["fid_with_viewmode"] = (
            r'\[\[' +
            r'\{' +
            PatternGenerator.QUOTE_CHARS + r'fid' + PatternGenerator.QUOTE_CHARS +
            r'\s*:\s*' +
            PatternGenerator.QUOTE_CHARS + r'[0-9]+' + PatternGenerator.QUOTE_CHARS +
            r'[^}]{0,200}' +  # Allow up to 200 chars before view_mode
            PatternGenerator.QUOTE_CHARS + r'view_mode' + PatternGenerator.QUOTE_CHARS
        )

        # Pattern 3: Media type indicator
        patterns["media_type"] = (
            PatternGenerator.QUOTE_CHARS + r'type' + PatternGenerator.QUOTE_CHARS +
            r'\s*:\s*' +
            PatternGenerator.QUOTE_CHARS + r'media' + PatternGenerator.QUOTE_CHARS
        )

        # Pattern 4: Field deltas structure
        patterns["field_deltas"] = (
            PatternGenerator.QUOTE_CHARS + r'field_deltas' + PatternGenerator.QUOTE_CHARS +
            r'\s*:\s*\{'
        )

        # Pattern 5: Complete WordPress embed pattern
        # More permissive - looks for the overall structure
        patterns["complete_embed"] = (
            r'\[\[' +
            r'\{' +
            PatternGenerator.QUOTE_CHARS + r'fid' + PatternGenerator.QUOTE_CHARS +
            r'[^\]]{50,}' +  # At least 50 chars of content
            PatternGenerator.QUOTE_CHARS + r'type' + PatternGenerator.QUOTE_CHARS +
            r'\s*:\s*' +
            PatternGenerator.QUOTE_CHARS + r'media' + PatternGenerator.QUOTE_CHARS +
            r'[^\]]*' +
            r'\]\]'
        )

        # Pattern 6: Closing structure with data-delta
        patterns["closing_with_delta"] = (
            PatternGenerator.QUOTE_CHARS + r'data-delta' + PatternGenerator.QUOTE_CHARS +
            r'\s*:\s*' +
            PatternGenerator.QUOTE_CHARS + r'[0-9]+' + PatternGenerator.QUOTE_CHARS +
            r'[^}]*\}\}\]\]'
        )

        return patterns

    @staticmethod
    def test_patterns(html: str, patterns: Dict[str, str]) -> Dict[str, List]:
        """Test all patterns against HTML and return matches."""
        results = {}
        for name, pattern in patterns.items():
            matches = list(re.finditer(pattern, html, re.IGNORECASE | re.DOTALL))
            if matches:
                results[name] = matches
        return results

    @staticmethod
    def get_recommended_patterns() -> Dict[str, str]:
        """
        Get the recommended pattern set for WordPress embed bugs.
        These are pre-generated and optimized.
        """
        return {
            # Catches the opening [[ with fid field (very broad)
            "wordpress_embed_opening": (
                r'\[\[\s*\{\s*["\'"″‴]fid["\'"″‴]\s*:\s*["\'"″‴]'
            ),

            # Catches fid with numeric value
            "wordpress_fid_numeric": (
                r'\[\[\s*\{\s*["\'"″‴]fid["\'"″‴]\s*:\s*["\'"″‴][0-9]+'
            ),

            # Catches the type:media field
            "wordpress_media_type": (
                r'["\'"″‴]type["\'"″‴]\s*:\s*["\'"″‴]media["\'"″‴]'
            ),

            # Catches field_deltas structure
            "wordpress_field_deltas": (
                r'["\'"″‴]field_deltas["\'"″‴]\s*:\s*\{'
            ),

            # Catches complete structure (more strict)
            "wordpress_complete": (
                r'\[\[\s*\{["\'"″‴]fid["\'"″‴][^]]{100,}["\'"″‴]type["\'"″‴]\s*:\s*["\'"″‴]media["\'"″‴][^]]*\]\]'
            ),
        }


def main():
    """Demo: Show pattern generation from example."""
    print("WordPress Embed Bug - Pattern Generator")
    print("=" * 60)

    # Example from test-project-bug-hunter.md
    example = '''[[{"fid":"1101026″,"view_mode":"full_width"...}}]]'''

    print(f"\nInput example:\n{example}\n")

    generator = PatternGenerator()
    patterns = generator.analyze_example(example)

    print("Generated Patterns:")
    print("-" * 60)
    for name, pattern in patterns.items():
        print(f"\n{name}:")
        print(f"  {pattern}")

    print("\n\nRecommended Production Patterns:")
    print("-" * 60)
    recommended = generator.get_recommended_patterns()
    for name, pattern in recommended.items():
        print(f"\n{name}:")
        print(f"  {pattern}")


if __name__ == "__main__":
    main()
