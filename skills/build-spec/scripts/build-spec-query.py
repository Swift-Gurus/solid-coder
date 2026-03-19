#!/usr/bin/env python3
"""Build and update spec files.

Subcommands:
    types
               Return the list of valid spec types as JSON.

    statuses
               Return the list of valid spec statuses as JSON.

    resolve-path <type> <SPEC-NNN> <slug> [--parent <SPEC-NNN>] [--specs-root <path>]
               Return the output file path for a new spec.
               Path rules:
                 - Root epic (no parent) → .claude/specs/SPEC-N-slug/SPEC-N-slug.md
                 - Child epic            → {parent-folder}/SPEC-N-slug/SPEC-N-slug.md
                 - feature               → {parent-folder}/features/SPEC-N-slug.md
                 - subtask               → {parent-folder}/features/subtasks/SPEC-N-slug.md
                 - bug                   → {parent-folder}/features/bugs/SPEC-N-slug.md

    update-status <SPEC-NNN> <new-status> [--specs-root <path>]
               Write new status to spec file, then propagate up the hierarchy.
               Propagation rules:
                 - All siblings ready  → parent becomes ready
                 - All siblings done   → parent becomes done
               Returns {"modified": [<paths>]}.

Exit codes:
    0 — success
    1 — error (invalid status, spec not found, blocked by draft children, etc.)
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

VALID_STATUSES = ["draft", "ready", "in-progress", "done"]
VALID_TYPES = ["bug", "feature", "epic", "subtask"]
STATUS_RANK = {"draft": 0, "ready": 1, "in-progress": 2, "done": 3}


# ---------------------------------------------------------------------------
# Frontmatter parsing / writing
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


def write_status(file_path: Path, new_status: str) -> None:
    content = file_path.read_text(encoding="utf-8")
    updated = re.sub(
        r"^(status:\s*).*$",
        lambda m: f"{m.group(1)}{new_status}",
        content, count=1, flags=re.MULTILINE,
    )
    if updated == content:
        updated = re.sub(
            r"^(number:\s*.+)$",
            lambda m: f"{m.group(1)}\nstatus: {new_status}",
            content, count=1, flags=re.MULTILINE,
        )
    file_path.write_text(updated, encoding="utf-8")


# ---------------------------------------------------------------------------
# Spec discovery (minimal — only what resolve-path and update-status need)
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
    for md_file in sorted(specs_root.rglob("*.md")):
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
            "children": [],
            "path": str(md_file),
        })
    return specs


def build_hierarchy(specs: List[Dict[str, Any]]) -> None:
    by_number = {s["number"]: s for s in specs}
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

def cmd_types() -> None:
    print(json.dumps(VALID_TYPES))


def cmd_statuses() -> None:
    print(json.dumps(VALID_STATUSES))


def cmd_resolve_path(
    specs_root: Path,
    spec_type: str,
    number: str,
    slug: str,
    parent_number: Optional[str],
) -> None:
    if spec_type not in VALID_TYPES:
        print(json.dumps({"error": "invalid_type", "message": f"'{spec_type}' must be one of: {', '.join(VALID_TYPES)}"}))
        sys.exit(1)

    filename = f"{number}-{slug}.md"

    if spec_type == "epic" and not parent_number:
        path = specs_root / f"{number}-{slug}" / filename
    else:
        if not parent_number:
            print(json.dumps({"error": "missing_parent", "message": f"--parent is required for type '{spec_type}'"}))
            sys.exit(1)
        specs = load_all_specs(specs_root)
        parent = find_spec(specs, parent_number)
        if not parent:
            print(json.dumps({"error": "not_found", "message": f"parent {parent_number} not found"}))
            sys.exit(1)
        parent_folder = Path(parent["path"]).parent
        if spec_type == "epic":
            path = parent_folder / f"{number}-{slug}" / filename
        elif spec_type == "feature":
            path = parent_folder / "features" / filename
        elif spec_type == "subtask":
            path = parent_folder / "features" / "subtasks" / filename
        elif spec_type == "bug":
            path = parent_folder / "features" / "bugs" / filename

    print(json.dumps({"path": str(path)}))


def cmd_update_status(specs_root: Path, number: str, new_status: str) -> None:
    if new_status not in set(VALID_STATUSES):
        print(json.dumps({"error": "invalid_status", "message": f"'{new_status}' must be one of: {', '.join(VALID_STATUSES)}"}))
        sys.exit(1)

    specs = load_all_specs(specs_root)
    build_hierarchy(specs)
    spec = find_spec(specs, number)
    if not spec:
        print(json.dumps({"error": "not_found", "message": f"{number} not found"}))
        sys.exit(1)

    draft_children = [
        find_spec(specs, n) for n in spec.get("children", [])
        if (s := find_spec(specs, n)) and s["status"] == "draft"
    ]
    draft_children = [c for c in draft_children if c]
    if draft_children and STATUS_RANK.get(new_status, 0) > STATUS_RANK["draft"]:
        print(json.dumps({
            "error": "blocked_by_draft_children",
            "message": f"Cannot set {number} to '{new_status}': {len(draft_children)} child spec(s) are still draft.",
            "draft_children": [{"number": c["number"], "feature": c["feature"], "path": c["path"]} for c in draft_children],
        }))
        sys.exit(1)

    modified = []
    write_status(Path(spec["path"]), new_status)
    spec["status"] = new_status
    modified.append(spec["path"])

    current = spec
    while current.get("parent"):
        parent = find_spec(specs, current["parent"])
        if not parent:
            break
        siblings = [s for n in parent.get("children", []) if (s := find_spec(specs, n))]
        sibling_statuses = {s["status"] for s in siblings}
        if sibling_statuses and all(s == "done" for s in sibling_statuses):
            if parent["status"] != "done":
                write_status(Path(parent["path"]), "done")
                parent["status"] = "done"
                modified.append(parent["path"])
        elif sibling_statuses and all(s in ("ready", "done") for s in sibling_statuses):
            if parent["status"] == "draft":
                write_status(Path(parent["path"]), "ready")
                parent["status"] = "ready"
                modified.append(parent["path"])
        else:
            break
        current = parent

    print(json.dumps({"modified": modified}, indent=2))


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
    if subcommand == "types":
        cmd_types()
    elif subcommand == "statuses":
        cmd_statuses()
    elif subcommand == "resolve-path":
        if len(args) < 4:
            print("Usage: spec-query.py resolve-path <type> <SPEC-NNN> <slug> [--parent <SPEC-NNN>]", file=sys.stderr)
            sys.exit(1)
        parent_num: Optional[str] = None
        remaining = args[1:]
        if "--parent" in remaining:
            i = remaining.index("--parent")
            if i + 1 < len(remaining):
                parent_num = remaining[i + 1]
                remaining = remaining[:i] + remaining[i + 2:]
        cmd_resolve_path(specs_root, remaining[0], remaining[1], remaining[2], parent_num)
    elif subcommand == "update-status":
        if len(args) < 3:
            print("Usage: spec-query.py update-status <SPEC-NNN> <new-status>", file=sys.stderr)
            sys.exit(1)
        cmd_update_status(specs_root, args[1], args[2])
    else:
        print(f"Error: unknown subcommand '{subcommand}'", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
