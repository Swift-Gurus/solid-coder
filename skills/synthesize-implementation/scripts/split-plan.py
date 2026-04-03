#!/usr/bin/env python3
"""Split implementation-plan.json into dependency-level chunks.

Usage:
    python3 split-plan.py <plan.json> --output-dir <dir>

Each chunk file uses the same schema as implementation-plan.json but contains
only the plan_items for that dependency level. Files are numbered so the code
agent processes them in order:

    01-level-0.json   (items with no dependencies)
    02-level-1.json   (items depending on level 0)
    ...

Shared fields (spec_summary, matched_tags, acceptance_criteria) are copied
into every chunk so each file is self-contained.
"""

import argparse
import json
import os
import sys
from collections import defaultdict


def compute_levels(items):
    """Assign a dependency level to each plan item.

    Level 0 = no dependencies.
    Level N = max(level of each dependency) + 1.
    """
    id_to_item = {item["id"]: item for item in items}
    levels = {}

    def resolve(item_id):
        if item_id in levels:
            return levels[item_id]
        item = id_to_item.get(item_id)
        if item is None:
            return 0
        deps = item.get("depends_on", [])
        if not deps:
            levels[item_id] = 0
            return 0
        level = max(resolve(dep) for dep in deps) + 1
        levels[item_id] = level
        return level

    for item in items:
        resolve(item["id"])

    return levels


def split(plan, output_dir):
    items = plan.get("plan_items", [])
    if not items:
        print("No plan items to split.", file=sys.stderr)
        sys.exit(0)

    levels = compute_levels(items)

    # Group items by level
    groups = defaultdict(list)
    for item in items:
        groups[levels[item["id"]]].append(item)

    # Shared fields copied into every chunk
    shared = {
        "spec_summary": plan.get("spec_summary", ""),
        "matched_tags": plan.get("matched_tags", []),
        "acceptance_criteria": plan.get("acceptance_criteria", []),
    }

    os.makedirs(output_dir, exist_ok=True)

    for level_num in sorted(groups.keys()):
        group_items = groups[level_num]
        filename = f"{level_num + 1:02d}-plan.json"
        filepath = os.path.join(output_dir, filename)

        chunk = {
            **shared,
            "plan_items": group_items,
        }

        with open(filepath, "w") as f:
            json.dump(chunk, f, indent=2)

        component_names = [item.get("component", "?") for item in group_items]
        has_design_refs = any(
            item.get("design_references")
            for item in group_items
        )

        print(f"  {filename}: {len(group_items)} items [{', '.join(component_names)}]"
              + (" (has design refs)" if has_design_refs else ""))

    print(f"\n{len(groups)} chunks written to {output_dir}/")


def main():
    parser = argparse.ArgumentParser(
        description="Split implementation-plan.json into dependency-level chunks."
    )
    parser.add_argument("plan", help="Path to implementation-plan.json")
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory to write chunk files into"
    )
    args = parser.parse_args()

    with open(args.plan) as f:
        plan = json.load(f)

    split(plan, args.output_dir)


if __name__ == "__main__":
    main()
