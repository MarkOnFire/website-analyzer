import re
from typing import Any, Dict, List

from pydantic import BaseModel

from src.analyzer.test_plugin import SiteSnapshot, TestResult, TestPlugin, PageData


class MigrationFinding(BaseModel):
    """Represents a single migration-related finding."""
    url: str
    match: str
    start: int
    end: int
    page_slug: str
    context: str
    line_number: int
    pattern_name: str # New field to indicate which pattern matched
    suggestion: Optional[str] = None # New field for suggested fix/replacement


class MigrationScanner(TestPlugin):
    """
    A plugin for scanning website content for migration-related patterns using regex.
    """
    name: str = "migration-scanner"
    description: str = "Scans for deprecated patterns or migration artifacts."

    _SUGGESTIONS: Dict[str, str] = {
        "jquery_live_event": "jQuery .live() is deprecated. Consider using .on() instead. For example, replace `$(selector).live('event', handler)` with `$(document).on('event', selector, handler)`.",
        "deprecated_api_call": "This API call is deprecated. Refer to the project's migration guide or official documentation for alternatives.",
        "old_js_syntax": "This JavaScript syntax might be outdated. Consider updating to modern ES6+ syntax for better maintainability and performance.",
        "http_link": "Consider updating HTTP links to HTTPS for improved security and SEO.",
        # Add more common patterns and suggestions here
    }

    @staticmethod
    def _extract_context(text: str, start_char: int, end_char: int, lines_before: int = 10, lines_after: int = 10) -> Dict[str, Any]:
        """Extracts lines of text around a given character range and determines the line number of the match.
        
        Returns:
            A dictionary containing "context_text" and "line_number" (1-based).
        """
        lines = text.splitlines(keepends=True) # Keepends to preserve original line structure
        
        # Calculate line number for start_char (start of the match)
        char_count = 0
        original_start_line_idx = 0

        for i, line in enumerate(lines):
            if char_count + len(line) > start_char:
                original_start_line_idx = i
                break
            char_count += len(line)
        
        # The line number of the *start* of the match within the original document (1-based)
        original_line_number = original_start_line_idx + 1 

        context_start_line = max(0, original_start_line_idx - lines_before)
        context_end_line = min(len(lines), original_start_line_idx + lines_after + 1) # +1 to include the last line of context

        return {
            "context_text": "".join(lines[context_start_line:context_end_line]),
            "line_number": original_line_number
        }


    async def analyze(self, snapshot: SiteSnapshot, **kwargs: Any) -> TestResult:
        """
        Analyzes the site snapshot for migration-related issues based on a regex pattern.
        
        Args:
            snapshot: The SiteSnapshot object containing the website data.
            **kwargs: Configuration parameters, expects 'patterns' (Dict[str, str]) and 'case_sensitive' (bool).

        Returns:
            A TestResult indicating the outcome of the analysis.
        """
        pattern_config = kwargs.get("patterns") # Expect a dict of named patterns
        if not pattern_config:
            return TestResult(
                plugin_name=self.name,
                status="warning",
                summary="No patterns provided for migration scan.",
                details={"message": "Specify patterns using --config 'migration-scanner:{\"patterns\":{\"name\":\"regex\"}}'"}
            )

        case_sensitive = kwargs.get("case_sensitive", False) # Default to case-insensitive
        re_flags = 0
        if not case_sensitive:
            re_flags |= re.IGNORECASE

        compiled_patterns: Dict[str, re.Pattern] = {}
        for name, pattern_str in pattern_config.items():
            try:
                compiled_patterns[name] = re.compile(pattern_str, flags=re_flags) # Pass flags here
            except re.error as e:
                return TestResult(
                    plugin_name=self.name,
                    status="error",
                    summary=f"Invalid regex pattern for '{name}': {e}",
                    details={"pattern_name": name, "pattern": pattern_str, "error": str(e)}
                )

        findings: List[MigrationFinding] = [] # Use MigrationFinding objects

        for page in snapshot.pages:
            content = page.get_content() # Using raw HTML content for comprehensive scanning
            for pattern_name, pattern in compiled_patterns.items():
                matches = list(pattern.finditer(content))
                
                if matches:
                    for match in matches:
                        context_info = self._extract_context(content, match.start(), match.end(), lines_before=10, lines_after=10)
                        
                        suggestion = self._SUGGESTIONS.get(pattern_name) # Get suggestion using pattern_name

                        findings.append(MigrationFinding( # Create MigrationFinding object
                            url=page.url,
                            match=match.group(0),
                            start=match.start(),
                            end=match.end(),
                            page_slug=page.directory.name,
                            context=context_info["context_text"],
                            line_number=context_info["line_number"],
                            pattern_name=pattern_name,
                            suggestion=suggestion # Add suggestion here
                        ))
        
        if findings:
            summary = (f"Found {len(findings)} migration-related patterns "
                       f"across {len(set(f.url for f in findings))} unique pages.") 
            status = "fail"
        else:
            summary = "No migration-related patterns found."
            status = "pass"

        return TestResult(
            plugin_name=self.name,
            status=status,
            summary=summary,
            details={"findings": [f.model_dump() for f in findings], "patterns": pattern_config, "case_sensitive": case_sensitive}
        )
