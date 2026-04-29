#!/usr/bin/env python3
"""Split implementation-plan.json into semantically grouped chunk files.

Usage:
    python3 split-plan.py <plan.json> --output-dir <dir> [--arch <arch.json>]

When --arch is provided, items are classified by component category and
test_cases type, then split into groups:

    01-foundations.json      models, enums, typealiases (no behavior, no tests)
    02-implementations.json  level-0 services, VMs, views
    03-implementations.json  level-1 implementations (depend on level 0), etc.
    0N-tests.json            unit and integration test items
    0M-ui-tests.json         UI test items

Without --arch, all items are treated as implementations and split by
dependency level only (backward-compatible, files named xx-implementations.json).

Shared fields (spec_summary, matched_tags, acceptance_criteria) are copied
into every chunk so each file is self-contained.
"""

import argparse
import json
import os
import sys
from collections import defaultdict


FOUNDATION_CATEGORIES = frozenset({"model", "enum", "typealias"})

_GROUP_ORDER = ["foundation", "implementation", "test", "ui_test"]
_VALID_GROUPS = frozenset(_GROUP_ORDER)
_GROUP_LABELS = {
    "foundation": "foundations",
    "implementation": "implementations",
    "test": "tests",
    "ui_test": "ui-tests",
}
DEFAULT_GROUP = "implementation"


def load_category_lookup(arch_path):
    """Build {component_name: category} from arch.json. Returns {} on any failure."""
    if not arch_path:
        return {}
    try:
        with open(arch_path) as f:
            arch = json.load(f)
        return {
            comp["name"]: comp.get("category", "")
            for comp in arch.get("components", [])
            if "name" in comp
        }
    except (OSError, json.JSONDecodeError, KeyError):
        return {}


def classify_item(item, category_lookup):
    """Return the chunk group for a plan item."""
    test_cases = item.get("test_cases") or []
    if any(tc.get("type") == "ui" for tc in test_cases):
        return "ui_test"
    if test_cases:
        return "test"
    category = category_lookup.get(item.get("component", ""), "").lower()
    if category in FOUNDATION_CATEGORIES:
        return "foundation"
    return DEFAULT_GROUP


def compute_impl_levels(impl_items):
    """Assign dependency levels to implementation items, ignoring cross-group deps.

    Dependencies on foundation, test, or ui_test items are treated as pre-done
    (they run in earlier/later chunks) and do not contribute to level inflation.

    Level 0 = no implementation-to-implementation dependencies.
    Level N = max(level of impl deps) + 1.
    """
    impl_ids = {item["id"] for item in impl_items}
    id_to_item = {item["id"]: item for item in impl_items}
    levels = {}

    def resolve(item_id):
        if item_id in levels:
            return levels[item_id]
        if item_id not in impl_ids:
            return -1  # pre-done in another chunk — does not count
        item = id_to_item[item_id]
        impl_deps = [d for d in item.get("depends_on", []) if d in impl_ids]
        if not impl_deps:
            levels[item_id] = 0
            return 0
        level = max(resolve(dep) for dep in impl_deps) + 1
        levels[item_id] = level
        return level

    for item in impl_items:
        resolve(item["id"])

    return levels


def split(plan, output_dir, arch_path=None):
    items = plan.get("plan_items", [])
    if not items:
        print("No plan items to split.", file=sys.stderr)
        sys.exit(0)

    category_lookup = load_category_lookup(arch_path)

    buckets = defaultdict(list)
    for item in items:
        buckets[classify_item(item, category_lookup)].append(item)

    chunks = []

    if buckets["foundation"]:
        chunks.append((_GROUP_LABELS["foundation"], buckets["foundation"]))

    if buckets["implementation"]:
        impl_levels = compute_impl_levels(buckets["implementation"])
        impl_by_level = defaultdict(list)
        for item in buckets["implementation"]:
            impl_by_level[impl_levels[item["id"]]].append(item)
        for level in sorted(impl_by_level.keys()):
            chunks.append((_GROUP_LABELS["implementation"], impl_by_level[level]))

    if buckets["test"]:
        chunks.append((_GROUP_LABELS["test"], buckets["test"]))

    if buckets["ui_test"]:
        chunks.append((_GROUP_LABELS["ui_test"], buckets["ui_test"]))

    shared = {
        "spec_summary": plan.get("spec_summary", ""),
        "matched_tags": plan.get("matched_tags", []),
        "acceptance_criteria": plan.get("acceptance_criteria", []),
    }

    os.makedirs(output_dir, exist_ok=True)

    for idx, (label, group_items) in enumerate(chunks, 1):
        filename = f"{idx:02d}-{label}.json"
        filepath = os.path.join(output_dir, filename)

        with open(filepath, "w") as f:
            json.dump({**shared, "plan_items": group_items}, f, indent=2)

        component_names = [item.get("component", "?") for item in group_items]
        has_design_refs = any(item.get("design_references") for item in group_items)

        print(
            f"  {filename}: {len(group_items)} items [{', '.join(component_names)}]"
            + (" (has design refs)" if has_design_refs else "")
        )

    print(f"\n{len(chunks)} chunks written to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Split implementation-plan.json into semantically grouped chunks."
    )
    parser.add_argument("plan", help="Path to implementation-plan.json")
    parser.add_argument("--output-dir", required=True, help="Directory to write chunk files")
    parser.add_argument(
        "--arch", default=None,
        help="Path to arch.json. Used to classify items by component category.",
    )
    args = parser.parse_args()

    with open(args.plan) as f:
        plan = json.load(f)

    split(plan, args.output_dir, arch_path=args.arch)


if __name__ == "__main__":
    main()
