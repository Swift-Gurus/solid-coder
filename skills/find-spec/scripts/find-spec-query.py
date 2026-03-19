#!/usr/bin/env python3
"""Discover and query spec files in .claude/specs/.

Subcommands:
    scan   [--type <type>] [--status <status>] [--no-parent] [--parent <SPEC-NNN>] [--specs-root <path>]
               Scan all spec files, output as JSON array.
               --type      Filter to specs of this type only (e.g. epic, feature)
               --status    Filter by status; comma-separated for multiple (e.g. draft, ready, draft,ready)
               --no-parent Filter to specs with no parent (root-level only)
               --parent    Filter to direct children of this spec number

    children <SPEC-NNN> [--specs-root <path>]
               Direct children of a spec (one level).

    ancestors <SPEC-NNN> [--specs-root <path>]
               All ancestor specs from root down to the given spec (inclusive),
               ordered root → leaf.

    next-number [--specs-root <path>]
               Next available SPEC number (zero-padded to 3 digits).
               Returns {"next": "SPEC-NNN"}.

Exit codes:
    0 — success
    1 — error (spec not found, etc.)
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Frontmatter parsing
# ---------------------------------------------------------------------------

def extract_frontmatter_text(content: str) -> Optional[str]:
    if not content.startswith("---"):
        return None
    end = content.find("---", 3)
    if end == -1:
        return None
    return content[3:end].strip()


def parse_frontmatter(content: str) -> Dict[str, Any]:
    yaml_text = extract_frontmatter_text(content)
    if not yaml_text:
        return {}
    result: Dict[str, Any] = {}
    current_key: Optional[str] = None
    current_list: Optional[List[str]] = None

    for line in yaml_text.splitlines():
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


# ---------------------------------------------------------------------------
# Spec discovery
# ---------------------------------------------------------------------------

def find_specs_root(given: Optional[str]) -> Path:
    if given:
        return Path(given).resolve()
    cwd = Path.cwd()
    for candidate in [cwd, *cwd.parents]:
        specs = candidate / ".claude" / "specs"
        if specs.is_dir():
            return specs
    return cwd / ".claude" / "specs"


def load_all_specs(specs_root: Path) -> List[Dict[str, Any]]:
    specs = []
    for md_file in sorted(specs_root.rglob("Spec.md")):
        content = md_file.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        if not fm.get("number"):
            continue
        specs.append({
            "number": fm.get("number"),
            "feature": fm.get("feature"),
            "type": fm.get("type"),
            "status": fm.get("status", "draft"),
            "parent": fm.get("parent"),
            "blocked_by": fm.get("blocked-by") or [],
            "blocking": fm.get("blocking") or [],
            "path": str(md_file),
        })
    return specs


def build_hierarchy(specs: List[Dict[str, Any]]) -> None:
    by_number = {s["number"]: s for s in specs}
    for s in specs:
        s["children"] = []
    for s in specs:
        parent_num = s.get("parent")
        if parent_num and parent_num in by_number:
            by_number[parent_num]["children"].append(s["number"])


def find_spec(specs: List[Dict[str, Any]], number: str) -> Optional[Dict[str, Any]]:
    for s in specs:
        if s["number"] == number:
            return s
    return None


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_scan(
    specs_root: Path,
    filter_type: Optional[str] = None,
    filter_status: Optional[str] = None,
    no_parent: bool = False,
    filter_parent: Optional[str] = None,
) -> None:
    specs = load_all_specs(specs_root)
    build_hierarchy(specs)
    if filter_type:
        specs = [s for s in specs if s.get("type") == filter_type]
    if filter_status:
        allowed = {s.strip() for s in filter_status.split(",")}
        specs = [s for s in specs if s.get("status") in allowed]
    if no_parent:
        specs = [s for s in specs if not s.get("parent")]
    if filter_parent:
        specs = [s for s in specs if s.get("parent") == filter_parent]
    print(json.dumps(specs, indent=2))


def cmd_children(specs_root: Path, number: str) -> None:
    specs = load_all_specs(specs_root)
    build_hierarchy(specs)
    spec = find_spec(specs, number)
    if not spec:
        print(json.dumps({"error": "not_found", "message": f"{number} not found"}))
        sys.exit(1)
    children = [s for s in specs if s["number"] in spec.get("children", [])]
    print(json.dumps(children, indent=2))


def cmd_ancestors(specs_root: Path, number: str) -> None:
    specs = load_all_specs(specs_root)
    spec = find_spec(specs, number)
    if not spec:
        print(json.dumps({"error": "not_found", "message": f"{number} not found"}))
        sys.exit(1)
    chain = []
    current = spec
    while current:
        chain.append(current)
        parent_num = current.get("parent")
        current = find_spec(specs, parent_num) if parent_num else None
    chain.reverse()
    print(json.dumps(chain, indent=2))


def cmd_next_number(specs_root: Path) -> None:
    specs = load_all_specs(specs_root)
    highest = 0
    for s in specs:
        num = s.get("number", "")
        m = re.match(r"SPEC-(\d+)", str(num))
        if m:
            highest = max(highest, int(m.group(1)))
    print(json.dumps({"next": f"SPEC-{highest + 1:03d}"}))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = sys.argv[1:]

    specs_root_override: Optional[str] = None
    if "--specs-root" in args:
        idx = args.index("--specs-root")
        if idx + 1 < len(args):
            specs_root_override = args[idx + 1]
            args = args[:idx] + args[idx + 2:]

    if not args:
        print(__doc__, file=sys.stderr)
        sys.exit(1)

    specs_root = find_specs_root(specs_root_override)

    subcommand = args[0]
    if subcommand == "scan":
        scan_args = args[1:]
        filter_type = filter_status = filter_parent = None
        no_parent = False
        if "--type" in scan_args:
            i = scan_args.index("--type")
            filter_type = scan_args[i + 1] if i + 1 < len(scan_args) else None
        if "--status" in scan_args:
            i = scan_args.index("--status")
            filter_status = scan_args[i + 1] if i + 1 < len(scan_args) else None
        if "--no-parent" in scan_args:
            no_parent = True
        if "--parent" in scan_args:
            i = scan_args.index("--parent")
            filter_parent = scan_args[i + 1] if i + 1 < len(scan_args) else None
        cmd_scan(specs_root, filter_type, filter_status, no_parent, filter_parent)
    elif subcommand == "children":
        if len(args) < 2:
            print("Usage: spec-query.py children <SPEC-NNN>", file=sys.stderr)
            sys.exit(1)
        cmd_children(specs_root, args[1])
    elif subcommand == "ancestors":
        if len(args) < 2:
            print("Usage: spec-query.py ancestors <SPEC-NNN>", file=sys.stderr)
            sys.exit(1)
        cmd_ancestors(specs_root, args[1])
    elif subcommand == "next-number":
        cmd_next_number(specs_root)
    else:
        print(f"Error: unknown subcommand '{subcommand}'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
