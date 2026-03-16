#!/usr/bin/env python3
"""Search codebase for files with solid-frontmatter matching synonym keywords.

Usage:
    python3 search-codebase.py --sources <dir> --synonyms '<json-array-string>'

Output (stdout): JSON object with matches and summary.
Exit codes: 0 = success, 1 = error.
"""

import argparse
import json
import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", ".build", "build", "DerivedData", "Pods", "node_modules"}


def strip_comment_prefix(line):
    """Strip common comment prefixes from a line, returning the inner text."""
    stripped = line.strip()
    for prefix in ("///", "/**", "//", "/*", "*", "#"):
        if stripped.startswith(prefix):
            return stripped[len(prefix):].strip()
    return stripped


def extract_all_frontmatter_blocks(lines):
    """Extract all solid-frontmatter blocks from a file's lines.

    Scans the entire file for lines containing solid-category and
    solid-description fields. Groups consecutive fields into blocks.
    Returns a list of dicts with 'category' and 'description' keys.
    """
    blocks = []
    current = {}

    for line in lines:
        inner = strip_comment_prefix(line)
        lower = inner.lower()

        if lower.startswith("solid-category:"):
            if "category" in current:
                blocks.append(current)
                current = {}
            current["category"] = inner[len("solid-category:"):].strip()
        elif lower.startswith("solid-description:"):
            current["description"] = inner[len("solid-description:"):].strip()
            blocks.append(current)
            current = {}

    if current:
        blocks.append(current)

    return blocks


def scan_file(filepath, synonyms_set):
    """Scan a file for all solid-frontmatter blocks and check against synonyms.

    Returns (has_frontmatter, match_dict_or_none).
    match_dict has {path, matched_terms[]} if any synonym matches.
    """
    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False, None

    blocks = extract_all_frontmatter_blocks(lines)

    if not blocks:
        return False, None

    words = set()
    for block in blocks:
        cat = block.get("category")
        desc = block.get("description")
        if cat:
            words.add(cat.lower())
        if desc:
            for w in re.split(r"\W+", desc.lower()):
                if w:
                    words.add(w)

    matched_terms = sorted(w for w in words if w in synonyms_set)

    if matched_terms:
        return True, {
            "path": str(filepath),
            "matched_terms": matched_terms,
        }

    return True, None


def main():
    parser = argparse.ArgumentParser(description="Search codebase for solid-frontmatter matches")
    parser.add_argument("--sources", default=".", help="Root directory to search (default: .)")
    parser.add_argument("--synonyms", required=True, help="JSON array string of synonym keywords")
    args = parser.parse_args()

    sources = Path(args.sources)
    if not sources.is_dir():
        print(f"Error: sources path not found: {args.sources}", file=sys.stderr)
        sys.exit(1)

    try:
        synonyms = json.loads(args.synonyms)
        if not isinstance(synonyms, list):
            raise ValueError("synonyms must be a JSON array")
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Error: invalid synonyms JSON: {e}", file=sys.stderr)
        sys.exit(1)

    synonyms_set = {s.lower() for s in synonyms if isinstance(s, str)}

    # Glob all files, skip hidden/build directories
    all_files = [
        f for f in sources.rglob("*")
        if f.is_file() and not any(part in SKIP_DIRS for part in f.parts)
    ]

    matches = []
    files_with_frontmatter = 0

    for filepath in all_files:
        has_fm, match = scan_file(filepath, synonyms_set)
        if has_fm:
            files_with_frontmatter += 1
        if match:
            matches.append(match)

    result = {
        "matches": matches,
        "summary": {
            "total_files_scanned": len(all_files),
            "files_with_frontmatter": files_with_frontmatter,
            "files_matched": len(matches),
        },
    }

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
