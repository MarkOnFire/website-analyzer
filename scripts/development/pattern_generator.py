#!/usr/bin/env python3.11
"""
Intelligent Pattern Generator for Visual Bug Detection

Takes user-provided bug examples and generates flexible regex patterns
that can catch variations in encoding, formatting, and structure.
"""

import re
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class BugAnalysis:
    """Analysis results for a bug example."""
    original_text: str
    unicode_chars: List[Tuple[str, str]]  # (char, description)
    structural_markers: List[str]
    key_fields: List[str]
    patterns: Dict[str, str]
    confidence: str  # "high", "medium", "low"


class PatternGenerator:
    """
    Generates flexible regex patterns from bug examples.

    Key features:
    - Detects Unicode character variations (quotes, dashes, spaces)
    - Identifies structural markers (brackets, braces, delimiters)
    - Extracts key fields that define the bug
    - Creates multiple pattern variants (strict to lenient)
    - Validates patterns against the original example
    """

    # All quote-like characters we should match
    QUOTE_CHARS = {
        '"': 'U+0022 (ASCII double quote)',
        "'": 'U+0027 (ASCII single quote)',
        ''': 'U+2018 (left single quote)',
        ''': 'U+2019 (right single quote)',
        '"': 'U+201C (left double quote)',
        '"': 'U+201D (right double quote)',
        '″': 'U+2033 (double prime)',
        '‴': 'U+2034 (triple prime)',
    }

    # Regex pattern that matches any quote character
    QUOTE_PATTERN = r'["\'\u2018\u2019\u201C\u201D\u2033\u2034]'

    # Common structural markers in bugs
    STRUCTURAL_MARKERS = {
        '[[': 'double opening brackets',
        ']]': 'double closing brackets',
        '{{': 'double opening braces',
        '}}': 'double closing braces',
        '{': 'opening brace',
        '}': 'closing brace',
        '[': 'opening bracket',
        ']': 'closing bracket',
    }

    def analyze(self, bug_example: str, description: str = "") -> BugAnalysis:
        """
        Analyze a bug example and generate patterns.

        Args:
            bug_example: The actual bug text from the page
            description: Optional human description of what makes this a bug

        Returns:
            BugAnalysis with patterns and metadata
        """
        # 1. Analyze Unicode characters
        unicode_chars = self._find_unicode_chars(bug_example)

        # 2. Identify structural markers
        structural_markers = self._find_structural_markers(bug_example)

        # 3. Extract key fields (JSON-like structures)
        key_fields = self._extract_key_fields(bug_example)

        # 4. Generate patterns
        patterns = self._generate_patterns(bug_example, structural_markers, key_fields)

        # 5. Validate patterns
        confidence = self._validate_patterns(bug_example, patterns)

        return BugAnalysis(
            original_text=bug_example,
            unicode_chars=unicode_chars,
            structural_markers=structural_markers,
            key_fields=key_fields,
            patterns=patterns,
            confidence=confidence
        )

    def _find_unicode_chars(self, text: str) -> List[Tuple[str, str]]:
        """Find non-ASCII characters that might need special handling."""
        unicode_chars = []
        for char in text:
            if ord(char) > 127:  # Non-ASCII
                desc = self.QUOTE_CHARS.get(char, f'U+{ord(char):04X}')
                unicode_chars.append((char, desc))
        return unicode_chars

    def _find_structural_markers(self, text: str) -> List[str]:
        """Identify structural markers that define the bug pattern."""
        markers = []
        for marker, desc in self.STRUCTURAL_MARKERS.items():
            if marker in text:
                markers.append(marker)
        return markers

    def _extract_key_fields(self, text: str) -> List[str]:
        """
        Extract JSON-like field names that are key to identifying the bug.
        Returns fields in order of first appearance (early fields are more important).
        """
        # Look for "fieldname": or 'fieldname': patterns
        field_pattern = self.QUOTE_PATTERN + r'([a-zA-Z_][a-zA-Z0-9_]*)' + self.QUOTE_PATTERN + r'\s*:'
        fields = re.findall(field_pattern, text)

        # Keep order of first appearance, remove duplicates
        seen = set()
        ordered_fields = []
        for field in fields:
            if field not in seen:
                seen.add(field)
                ordered_fields.append(field)

        return ordered_fields

    def _generate_patterns(
        self,
        example: str,
        structural_markers: List[str],
        key_fields: List[str]
    ) -> Dict[str, str]:
        """
        Generate multiple regex patterns with varying strictness.

        Returns dict of pattern_name -> regex_string
        """
        patterns = {}

        # Pattern 1: VERY LENIENT - Just opening structure
        if '[[' in structural_markers and '{' in structural_markers:
            patterns['opening_structure'] = r'\[\[\s*\{'

        # Pattern 2: Opening with first field
        if key_fields and '[[' in structural_markers:
            first_field = key_fields[0] if key_fields else 'fid'
            patterns['opening_with_field'] = (
                r'\[\[\s*\{\s*' + self.QUOTE_PATTERN +
                re.escape(first_field) + self.QUOTE_PATTERN
            )

        # Pattern 3: Key field combinations
        if len(key_fields) >= 2:
            # Match presence of multiple key fields (order-independent)
            field1, field2 = key_fields[0], key_fields[1]
            patterns['multi_field'] = (
                self.QUOTE_PATTERN + re.escape(field1) + self.QUOTE_PATTERN +
                r'[^}]{0,500}' +  # Allow content between fields
                self.QUOTE_PATTERN + re.escape(field2) + self.QUOTE_PATTERN
            )

        # Pattern 4: Specific field values (if we can identify them)
        type_match = re.search(
            self.QUOTE_PATTERN + r'type' + self.QUOTE_PATTERN +
            r'\s*:\s*' +
            self.QUOTE_PATTERN + r'(\w+)' + self.QUOTE_PATTERN,
            example
        )
        if type_match:
            type_value = type_match.group(1)
            patterns['type_field'] = (
                self.QUOTE_PATTERN + r'type' + self.QUOTE_PATTERN +
                r'\s*:\s*' +
                self.QUOTE_PATTERN + re.escape(type_value) + self.QUOTE_PATTERN
            )

        # Pattern 5: Complete structure (strict)
        if '[[' in structural_markers and ']]' in structural_markers and key_fields:
            # Build pattern that requires opening, some content, and closing
            min_length = max(100, len(example) // 10)  # At least 100 chars or 10% of example
            patterns['complete_structure'] = (
                r'\[\[' +
                r'[^\]]{' + str(min_length) + r',}' +  # Substantial content
                r'\]\]'
            )

        # Pattern 6: Field-specific patterns for each key field
        for field in key_fields[:3]:  # Top 3 most important fields
            patterns[f'field_{field}'] = (
                self.QUOTE_PATTERN + re.escape(field) + self.QUOTE_PATTERN +
                r'\s*:\s*' + self.QUOTE_PATTERN
            )

        return patterns

    def _validate_patterns(self, example: str, patterns: Dict[str, str]) -> str:
        """
        Validate that patterns match the original example.

        Returns confidence level: "high", "medium", or "low"
        """
        matches = 0
        for pattern in patterns.values():
            if re.search(pattern, example, re.IGNORECASE | re.DOTALL):
                matches += 1

        match_rate = matches / len(patterns) if patterns else 0

        if match_rate >= 0.8:
            return "high"
        elif match_rate >= 0.5:
            return "medium"
        else:
            return "low"

    def generate_scanner_code(self, analysis: BugAnalysis, variable_name: str = "PATTERNS") -> str:
        """
        Generate Python code for the patterns that can be copied into scanner.

        Args:
            analysis: The BugAnalysis result
            variable_name: Name for the patterns dict

        Returns:
            Python code as a string
        """
        code = f"# Generated patterns for bug detection\n"
        code += f"# Confidence: {analysis.confidence}\n"
        code += f"# Key fields detected: {', '.join(analysis.key_fields)}\n\n"

        if analysis.unicode_chars:
            code += "# Unicode characters found in example:\n"
            for char, desc in analysis.unicode_chars[:5]:
                code += f"#   '{char}' - {desc}\n"
            code += "\n"

        code += f"QUOTE_PATTERN = r'{self.QUOTE_PATTERN}'\n\n"
        code += f"{variable_name} = {{\n"

        for name, pattern in analysis.patterns.items():
            # Pretty-print the pattern
            code += f"    '{name}': (\n"
            code += f"        r'{pattern}'\n"
            code += f"    ),\n"

        code += "}\n"

        return code


def main():
    """Demo: Generate patterns from the WordPress embed bug example."""
    print("=" * 70)
    print("Pattern Generator - WordPress Embed Bug Example")
    print("=" * 70)

    # Real bug example from test-project-bug-hunter.md
    bug_example = '''[[{"fid":"1101026″,"view_mode":"full_width","fields":{"format":"full_width","alignment":"","field_image_caption[und][0][value]":"%3Cp%3ETom%20and%20Jerry%20milkglass%20set%20%3Cem%3E%3Ca%20href%3D%22https%3A%2F%2Fwww.flickr.com%2Fphotos%2Fjohnnyvintage%2F%22%3EJonnie%20Andersen%3C%2Fa%3E%20(CC%20BY-NC-ND%202.0)%3C%2Fem%3E%3C%2Fp%3E%0A","field_image_caption[und][0][format]":"full_html","field_file_image_alt_text[und][0][value]":"Tom and Jerry milkglass set","field_file_image_title_text[und][0][value]":"Tom and Jerry milkglass set"},"type":"media","field_deltas":{"2":{"format":"full_width","alignment":"","field_image_caption[und][0][value]":"%3Cp%3ETom%20and%20Jerry%20milkglass%20set%20%3Cem%3E%3Ca%20href%3D%22https%3A%2F%2Fwww.flickr.com%2Fphotos%2Fjohnnyvintage%2F%22%3EJonnie%20Andersen%3C%2Fa%3E%20(CC%20BY-NC-ND%202.0)%3C%2Fem%3E%3C%2Fp%3E%0A","field_image_caption[und][0][format]":"full_html","field_file_image_alt_text[und][0][value]":"Tom and Jerry milkglass set","field_file_image_title_text[und][0][value]":"Tom and Jerry milkglass set"}},"link_text":false,"attributes":{"alt":"Tom and Jerry milkglass set","title":"Tom and Jerry milkglass set","class":"media-element file-full-width","data-delta":"2″}}]]'''

    description = "WordPress embed code that appears as visible text instead of rendering as an image"

    # Generate patterns
    generator = PatternGenerator()
    analysis = generator.analyze(bug_example, description)

    print(f"\n📝 Original bug text ({len(bug_example)} chars)")
    print(f"   {bug_example[:100]}...\n")

    print(f"🔍 Analysis Results")
    print(f"   Confidence: {analysis.confidence}")
    print(f"   Unicode chars found: {len(analysis.unicode_chars)}")
    print(f"   Structural markers: {', '.join(analysis.structural_markers)}")
    print(f"   Key fields: {', '.join(analysis.key_fields[:5])}{'...' if len(analysis.key_fields) > 5 else ''}")
    print(f"   Patterns generated: {len(analysis.patterns)}")

    if analysis.unicode_chars:
        print("\n📌 Special characters detected:")
        for char, desc in analysis.unicode_chars[:5]:
            print(f"   '{char}' - {desc}")

    print("\n✅ Generated Patterns:")
    print("-" * 70)
    for name, pattern in analysis.patterns.items():
        # Test the pattern
        match = re.search(pattern, bug_example, re.IGNORECASE | re.DOTALL)
        status = "✅" if match else "❌"
        print(f"{status} {name}")
        print(f"   {pattern[:80]}{'...' if len(pattern) > 80 else ''}")

    print("\n" + "=" * 70)
    print("Generated Scanner Code:")
    print("=" * 70)
    print(generator.generate_scanner_code(analysis))


if __name__ == "__main__":
    main()
