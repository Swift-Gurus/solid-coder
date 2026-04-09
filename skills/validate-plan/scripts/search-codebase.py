#!/usr/bin/env python3
"""Search codebase for files with solid-frontmatter matching synonym keywords or spec numbers.

Usage:
    # Synonym search (validate-plan)
    python3 search-codebase.py --sources <dir> --synonyms '<json-array-string>'

    # Spec search (plan skill — find types already built for a spec)
    python3 search-codebase.py --sources <dir> --spec SPEC-015 --spec SPEC-016

    # Both (combined results)
    python3 search-codebase.py --sources <dir> --synonyms '["fetch","repo"]' --spec SPEC-015

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


def parse_spec_list(value):
    """Parse solid-spec value into a set of spec numbers.

    Handles formats:
      [SPEC-015]
      [SPEC-015, SPEC-016]
      SPEC-015
    Returns a set of uppercase spec number strings.
    """
    value = value.strip()
    # Strip surrounding brackets if present
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    parts = re.split(r"[,\s]+", value)
    return {p.strip().upper() for p in parts if p.strip()}


def extract_all_frontmatter_blocks(lines):
    """Extract all solid-frontmatter blocks from a file's lines.

    Scans the entire file for lines containing solid-category, solid-description,
    and solid-spec fields. Groups consecutive fields into blocks.
    Returns a list of dicts with 'category', 'description', and 'specs' keys.
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
        elif lower.startswith("solid-spec:"):
            raw = inner[len("solid-spec:"):].strip()
            current["specs"] = parse_spec_list(raw)

    if current:
        blocks.append(current)

    return blocks


def scan_file(filepath, synonyms_set, spec_numbers):
    """Scan a file for solid-frontmatter blocks and check against synonyms and/or spec numbers.

    Returns (has_frontmatter, match_dict_or_none).
    match_dict has {path, matched_terms[], matched_specs[]} if any match found.
    """
    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return False, None

    blocks = extract_all_frontmatter_blocks(lines)

    if not blocks:
        return False, None

    # Synonym matching
    matched_terms = []
    if synonyms_set:
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

    # Spec matching
    matched_specs = []
    if spec_numbers:
        file_specs = set()
        for block in blocks:
            file_specs.update(block.get("specs", set()))
        matched_specs = sorted(file_specs & spec_numbers)

    if matched_terms or matched_specs:
        result = {"path": str(filepath)}
        if matched_terms:
            result["matched_terms"] = matched_terms
        if matched_specs:
            result["matched_specs"] = matched_specs
        return True, result

    return True, None


def main():
    parser = argparse.ArgumentParser(description="Search codebase for solid-frontmatter matches")
    parser.add_argument("--sources", default=".", help="Root directory to search (default: .)")
    parser.add_argument("--synonyms", default=None, help="JSON array string of synonym keywords")
    parser.add_argument("--spec", action="append", default=[], metavar="SPEC-NNN",
                        help="Spec number to search for (repeatable: --spec SPEC-015 --spec SPEC-016)")
    args = parser.parse_args()

    if not args.synonyms and not args.spec:
        print("Error: at least one of --synonyms or --spec is required", file=sys.stderr)
        sys.exit(1)

    sources = Path(args.sources)
    if not sources.is_dir():
        print(f"Error: sources path not found: {args.sources}", file=sys.stderr)
        sys.exit(1)

    synonyms_set = set()
    if args.synonyms:
        try:
            synonyms = json.loads(args.synonyms)
            if not isinstance(synonyms, list):
                raise ValueError("synonyms must be a JSON array")
            synonyms_set = {s.lower() for s in synonyms if isinstance(s, str)}
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error: invalid synonyms JSON: {e}", file=sys.stderr)
            sys.exit(1)

    spec_numbers = {s.strip().upper() for s in args.spec if s.strip()}

    # Glob all files, skip hidden/build directories
    all_files = [
        f for f in sources.rglob("*")
        if f.is_file() and not any(part in SKIP_DIRS for part in f.parts)
    ]

    matches = []
    files_with_frontmatter = 0

    for filepath in all_files:
        has_fm, match = scan_file(filepath, synonyms_set, spec_numbers)
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
