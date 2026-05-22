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
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from lib.codebase_searcher import search_raw  # noqa: E402


def _parse_args():
    parser = argparse.ArgumentParser(description="Search codebase for solid-frontmatter matches")
    parser.add_argument("--sources", default=".", help="Root directory to search (default: .)")
    parser.add_argument("--synonyms", default=None, help="JSON array string of synonym keywords")
    parser.add_argument("--spec", action="append", default=[], metavar="SPEC-NNN",
                        help="Spec number (repeatable)")
    parser.add_argument("--min-matches", type=int, default=1, metavar="N",
                        help="Minimum synonym terms that must match (default: 1)")
    return parser.parse_args()


def _build_params(args):
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
    return synonyms_set, spec_numbers


def main():
    args = _parse_args()

    if not args.synonyms and not args.spec:
        print("Error: at least one of --synonyms or --spec is required", file=sys.stderr)
        sys.exit(1)

    sources = Path(args.sources)
    if not sources.is_dir():
        print(f"Error: sources path not found: {args.sources}", file=sys.stderr)
        sys.exit(1)

    synonyms_set, spec_numbers = _build_params(args)
    result = search_raw(
        sources_dir=str(sources),
        tags=list(synonyms_set),
        spec_numbers=list(spec_numbers),
        min_matches=args.min_matches,
    )
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
