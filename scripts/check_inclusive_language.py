#!/usr/bin/env python3
"""
Inclusive Language Checker
Scans code for potentially non-inclusive terminology and suggests alternatives.
"""

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Terms to avoid and their alternatives
TERM_MAPPINGS = {
    r"\bwhitelist\b": "allowlist",
    r"\bblacklist\b": "denylist/blocklist",
    r"\bmaster\s+(?:database|server|node)\b": "primary",
    r"\bslave\s+(?:database|server|node)\b": "replica/secondary",
    r"\bgrandfathered\b": "legacy status",
    r"\bman-hours\b": "person-hours/work-hours",
    r"\bman-days\b": "person-days/work-days",
    r"\bsanity\s+check\b": "confidence check/verification",
    r"\bdummy\s+(?:data|value|variable)\b": "placeholder/sample",
}

# Patterns to exclude (legitimate uses)
EXCLUDE_PATTERNS = [
    r'(?:main|master)\s*[\'"]?\s*(?:branch)?',  # Git branches
    r"Task\s+Master",  # Proper names
    r"Scrum\s+Master",  # Official titles
    r"\.git/",  # Git internals
    r"node_modules/",  # Dependencies
    r"venv/",  # Virtual environments
    r"#\s*inclusive-language:\s*ignore",  # Explicit ignore comments
]


def should_skip_file(path: Path) -> bool:
    """Check if file should be skipped."""
    # Skip binary and lock files
    if path.suffix in [
        ".pyc",
        ".lock",
        ".jpg",
        ".png",
        ".gif",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".eot",
    ]:
        return True

    # Skip dependency directories
    skip_dirs = [".git", "node_modules", "venv",
                 "__pycache__", ".venv", "dist", "build"]
    return any(skip_dir in path.parts for skip_dir in skip_dirs)


def is_excluded_line(line: str) -> bool:
    """Check if line matches exclusion patterns."""
    return any(re.search(pattern, line, re.IGNORECASE) for pattern in EXCLUDE_PATTERNS)


def check_file(file_path: Path) -> List[Tuple[int, str, str]]:
    """
    Check a file for non-inclusive language.

    Returns:
        List of (line_number, matched_term, suggestion) tuples
    """
    issues = []

    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except (OSError, UnicodeDecodeError) as e:
        print(f"Warning: Could not read {file_path}: {e}", file=sys.stderr)
        return issues

    for line_num, line in enumerate(content.splitlines(), 1):
        # Skip excluded lines
        if is_excluded_line(line):
            continue

        # Check for non-inclusive terms
        for pattern, suggestion in TERM_MAPPINGS.items():
            matches = re.finditer(pattern, line, re.IGNORECASE)
            for match in matches:
                issues.append((line_num, match.group(), suggestion))

    return issues


def main():
    """Main entry point."""
    # Set UTF-8 encoding for Windows compatibility
    if sys.platform == "win32":
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

    if len(sys.argv) < 2:
        print("Usage: check_inclusive_language.py <file1> <file2> ...")
        sys.exit(1)

    all_issues: Dict[str, List[Tuple[int, str, str]]] = {}

    for file_arg in sys.argv[1:]:
        file_path = Path(file_arg)

        if not file_path.exists():
            continue

        if should_skip_file(file_path):
            continue

        issues = check_file(file_path)
        if issues:
            all_issues[str(file_path)] = issues

    if all_issues:
        print("\n⚠️  Non-inclusive language detected:\n")

        for file_path, issues in sorted(all_issues.items()):
            print(f"  {file_path}:")
            for line_num, term, suggestion in issues:
                print(
                    f"    Line {line_num}: '{term}' → consider '{suggestion}'")

        print("\nℹ️  These are suggestions for more inclusive terminology.")
        print("If a usage is legitimate, you can:")
        print("  1. Add '# inclusive-language: ignore' comment on the line")
        print("  2. Add the pattern to EXCLUDE_PATTERNS in the checker script")
        print("")

        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
