#!/usr/bin/env python3
"""Load one or more reference files, stripping YAML frontmatter.

Accepts file paths and/or directories. Directories are expanded to all files
within them. Each file is output with a header showing its path, followed by
the body content (everything after the frontmatter block).

Usage:
    python3 load-reference.py <path> [<path> ...]

Output (stdout):
    For each file:
        === <absolute-path> ===
        <body without frontmatter>

Exit codes:
    0 — success
    1 — error (no arguments, no files found)
"""

import sys
from pathlib import Path
from typing import List


def strip_frontmatter(content: str) -> str:
    """Remove YAML frontmatter from content, return the body."""
    if not content.startswith("---"):
        return content
    end = content.find("---", 3)
    if end == -1:
        return content
    # Skip past the closing --- and any immediate newline
    body_start = end + 3
    if body_start < len(content) and content[body_start] == "\n":
        body_start += 1
    return content[body_start:]


def collect_files(paths: List[str]) -> List[Path]:
    """Expand paths — directories become their children, files pass through."""
    files: List[Path] = []
    for p in paths:
        pp = Path(p)
        if pp.is_dir():
            files.extend(sorted(f for f in pp.iterdir() if f.is_file()))
        elif pp.is_file():
            files.append(pp)
        else:
            print(f"Warning: {p} not found, skipping", file=sys.stderr)
    return files



# --- Public API ---


def load(file_paths: List[str]) -> List[dict]:
    """Load reference files, stripping frontmatter.

    Returns list of {path: str, content: str} dicts.
    Skips missing files with a warning to stderr.
    """
    files = collect_files(file_paths)
    results = []
    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        body = strip_frontmatter(content)
        results.append({
            "path": str(f.resolve()),
            "content": body,
        })
    return results


# --- CLI entry point ---


def main() -> None:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <path> [<path> ...]", file=sys.stderr)
        sys.exit(1)

    files = collect_files(sys.argv[1:])

    if not files:
        print("Error: no files found", file=sys.stderr)
        sys.exit(1)

    for f in files:
        content = f.read_text(encoding="utf-8", errors="replace")
        body = strip_frontmatter(content)
        print(f"=== {f.resolve()} ===")
        print(body)


if __name__ == "__main__":
    main()
