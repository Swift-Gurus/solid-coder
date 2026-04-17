#!/usr/bin/env python3
"""Discover principles from references directory and optionally filter by tags.

Mode 1 — Discovery (no --matched-tags):
    Returns all principles with their tags, plus all unique candidate tags.

Mode 2 — Filter (with --matched-tags):
    Returns only active principles (no tags = always active, has tags = active
    only if any tag intersects with matched-tags).

Mode 3 — Profile filter (with --profile <name>):
    Also filters out principles that don't support the requested profile.
    A principle's `profile:` frontmatter is a list of supported profiles
    (e.g. `profile: [code]`). Missing field → principle is available in all
    profiles (backward compatible).

Usage:
    python3 discover-principles.py --refs-root <path>
    python3 discover-principles.py --refs-root <path> --matched-tags swiftui,combine
    python3 discover-principles.py --refs-root <path> --review-input path/to/review-input.json
    python3 discover-principles.py --refs-root <path> --glob "*/rule.md"
    python3 discover-principles.py --refs-root <path> --profile review

Output (stdout): JSON object with active_principles, skipped_principles,
    and all_candidate_tags.

Exit codes:
    0 — success
    1 — error
"""

import argparse
import json
import sys
from glob import glob
from pathlib import Path
from typing import Any, Dict, List, Optional


def parse_yaml_simple(text: str) -> Dict[str, Any]:
    """Minimal YAML parser for flat frontmatter with optional lists."""
    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: Optional[List[str]] = None

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if stripped.startswith("- ") and current_key is not None:
            if current_list is None:
                current_list = []
            current_list.append(stripped[2:].strip())
            continue

        if current_key is not None and current_list is not None:
            result[current_key] = current_list
            current_list = None
            current_key = None

        if ":" in stripped:
            colon_idx = stripped.index(":")
            key = stripped[:colon_idx].strip()
            value = stripped[colon_idx + 1:].strip()

            if value:
                if value.startswith("[") and value.endswith("]"):
                    inner = value[1:-1].strip()
                    result[key] = [item.strip() for item in inner.split(",")] if inner else []
                elif value.lower() in ("true", "yes"):
                    result[key] = True
                elif value.lower() in ("false", "no"):
                    result[key] = False
                else:
                    try:
                        result[key] = int(value)
                    except ValueError:
                        result[key] = value
                current_key = None
                current_list = None
            else:
                current_key = key
                current_list = None

    if current_key is not None and current_list is not None:
        result[current_key] = current_list
    elif current_key is not None:
        result[current_key] = None

    return result


def extract_frontmatter(content: str) -> Optional[str]:
    """Extract YAML frontmatter between --- delimiters."""
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    return content[3:end].strip()


def discover(refs_root: Path, pattern: str) -> List[Dict[str, Any]]:
    """Find all rule.md files and parse their frontmatter."""
    principles = []
    search = str(refs_root / pattern)

    for rule_path in sorted(glob(search, recursive=True)):
        rule_file = Path(rule_path)
        if not rule_file.is_file():
            continue

        content = rule_file.read_text(encoding="utf-8")
        yaml_text = extract_frontmatter(content)
        if yaml_text is None:
            continue

        data = parse_yaml_simple(yaml_text)
        folder = rule_file.parent

        # Normalize tags to list of lowercase strings
        raw_tags = data.get("tags")
        tags = None
        if raw_tags is not None:
            if isinstance(raw_tags, str):
                tags = [raw_tags.lower()]
            elif isinstance(raw_tags, list):
                tags = [t.lower() for t in raw_tags]

        # Normalize profile to list of lowercase strings. Missing = available everywhere.
        raw_profile = data.get("profile")
        profile = None
        if raw_profile is not None:
            if isinstance(raw_profile, str):
                profile = [raw_profile.lower()]
            elif isinstance(raw_profile, list):
                profile = [p.lower() for p in raw_profile]

        principles.append({
            "name": data.get("name", folder.name),
            "displayName": data.get("displayName", data.get("name", folder.name)),
            "folder": str(folder.resolve()),
            "rule_path": str(rule_file.resolve()),
            "tags": tags,
            "profile": profile,
        })

    return principles


def filter_principles(
    principles: List[Dict[str, Any]],
    matched_tags: Optional[List[str]],
    profile: Optional[str] = None,
) -> tuple:
    """Split principles into active and skipped based on matched tags and profile.

    Profile filtering (when `profile` is provided):
        - principles with no `profile:` field → included (available everywhere)
        - principles with `profile: [x, y, ...]` → included only if `profile` is in the list
    """
    active = []
    skipped = []

    matched_set = set(t.lower() for t in matched_tags) if matched_tags else set()
    profile_key = profile.lower() if profile else None

    for p in principles:
        # Profile filter first — skip principles that don't support the requested profile.
        profiles = p.get("profile")
        if profile_key is not None and profiles is not None and profile_key not in profiles:
            skipped.append({
                **p,
                "reason": f"profile '{profile_key}' not in supported profiles {profiles}",
            })
            continue

        tags = p["tags"]
        if tags is None:
            active.append(p)
        elif matched_tags is None:
            active.append(p)
        elif set(tags) & matched_set:
            active.append(p)
        else:
            skipped.append({
                **p,
                "reason": "no matching tags",
            })

    return active, skipped



# --- Public API ---


def discover_and_filter(
    refs_root: str,
    glob_pattern: str = "**/rule.md",
    matched_tags: Optional[List[str]] = None,
    profile: Optional[str] = None,
) -> Dict[str, Any]:
    """Discover principles and optionally filter by tags and/or profile.

    Returns dict with active_principles, skipped_principles, all_candidate_tags.
    """
    root = Path(refs_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"{root} is not a directory")

    principles = discover(root, glob_pattern)

    all_candidate_tags = set()
    for p in principles:
        if p["tags"]:
            all_candidate_tags.update(p["tags"])

    active, skipped = filter_principles(principles, matched_tags, profile)

    return {
        "all_candidate_tags": sorted(all_candidate_tags),
        "active_principles": active,
        "skipped_principles": skipped,
    }


# --- CLI entry point ---


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Discover and filter principles by tags."
    )
    parser.add_argument(
        "--refs-root", required=True,
        help="Path to references directory",
    )
    parser.add_argument(
        "--matched-tags",
        help="Comma-separated list of matched tags to filter by",
    )
    parser.add_argument(
        "--review-input",
        help="Path to review-input.json — reads matched_tags from it (alternative to --matched-tags)",
    )
    parser.add_argument(
        "--glob", default="**/rule.md",
        help="Glob pattern for finding rule.md files (default: **/rule.md)",
    )
    parser.add_argument(
        "--profile",
        help="Filter to principles supporting this profile (e.g. 'review', 'code'). "
             "Principles with no `profile:` field are always included.",
    )
    args = parser.parse_args()

    refs_root = Path(args.refs_root).resolve()
    if not refs_root.is_dir():
        print(f"Error: {refs_root} is not a directory", file=sys.stderr)
        sys.exit(1)

    matched_tags = None
    if args.review_input:
        ri_path = Path(args.review_input)
        if not ri_path.is_file():
            print(f"Error: {ri_path} not found", file=sys.stderr)
            sys.exit(1)
        ri_data = json.loads(ri_path.read_text(encoding="utf-8"))
        tags_from_json = ri_data.get("matched_tags")
        if tags_from_json is not None:
            matched_tags = tags_from_json
    elif args.matched_tags:
        matched_tags = [t.strip() for t in args.matched_tags.split(",") if t.strip()]

    principles = discover(refs_root, args.glob)

    # Collect all unique candidate tags across all principles
    all_candidate_tags = set()
    for p in principles:
        if p["tags"]:
            all_candidate_tags.update(p["tags"])

    active, skipped = filter_principles(principles, matched_tags, args.profile)

    output = {
        "all_candidate_tags": sorted(all_candidate_tags),
        "active_principles": active,
        "skipped_principles": skipped,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
