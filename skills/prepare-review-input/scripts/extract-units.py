#!/usr/bin/env python3
"""Extract Swift top-level units from the files listed in a review-input.json
and annotate each with has_changes based on `changed_ranges` overlap.

Updates review-input.json in place:
- Fills each `files[].units` array with {name, kind, line_start, line_end, has_changes}
- Recomputes summary.total_units and summary.changed_units

For buffer mode: parses `buffer.input` and writes units into `buffer.units`.

Usage:
    python3 extract-units.py <review-input.json>
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple


UNIT_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"^\s*(?:public\s+|internal\s+|private\s+|fileprivate\s+|open\s+)?(?:final\s+)?class\s+(\w+)"), "class"),
    (re.compile(r"^\s*(?:public\s+|internal\s+|private\s+|fileprivate\s+|open\s+)?(?:final\s+)?struct\s+(\w+)"), "struct"),
    (re.compile(r"^\s*(?:public\s+|internal\s+|private\s+|fileprivate\s+|open\s+)?enum\s+(\w+)"), "enum"),
    (re.compile(r"^\s*(?:public\s+|internal\s+|private\s+|fileprivate\s+|open\s+)?protocol\s+(\w+)"), "protocol"),
    (re.compile(r"^\s*(?:public\s+|internal\s+|private\s+|fileprivate\s+|open\s+)?extension\s+(\w+)"), "extension"),
]


def extract_units(source: str) -> List[dict]:
    """Scan Swift source text → list of units with line_start/line_end."""
    lines = source.splitlines()
    raw: List[dict] = []
    for i, line in enumerate(lines, start=1):
        for pattern, kind in UNIT_PATTERNS:
            m = pattern.match(line)
            if m:
                raw.append({"name": m.group(1), "kind": kind, "line_start": i})
                break

    raw.sort(key=lambda u: u["line_start"])
    total = len(lines)
    units: List[dict] = []
    for idx, u in enumerate(raw):
        line_end = raw[idx + 1]["line_start"] - 1 if idx + 1 < len(raw) else total
        units.append({
            "name": u["name"],
            "kind": u["kind"],
            "line_start": u["line_start"],
            "line_end": line_end,
        })
    return units


def overlaps(unit_start: int, unit_end: int, ranges: Optional[list]) -> bool:
    """True if unit line range overlaps any changed range. None/empty ranges = whole-file."""
    if not ranges:
        return True
    for r in ranges:
        if r["start"] <= unit_end and r["end"] >= unit_start:
            return True
    return False


def read_file(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def process_files(file_entries: list) -> Tuple[int, int]:
    """Mutate each file entry's units[] in place. Returns (total_units, changed_units)."""
    total_units = 0
    changed_units = 0
    for entry in file_entries:
        fp = entry.get("file_path")
        if not fp:
            continue
        source = read_file(Path(fp))
        if source is None:
            entry["units"] = []
            continue
        units = extract_units(source)
        changed_ranges = entry.get("changed_ranges")
        for u in units:
            u["has_changes"] = overlaps(u["line_start"], u["line_end"], changed_ranges)
        entry["units"] = units
        total_units += len(units)
        changed_units += sum(1 for u in units if u["has_changes"])
    return total_units, changed_units


def process_buffer(buffer_entry: dict) -> int:
    source = buffer_entry.get("input", "")
    units = extract_units(source)
    # Buffer units don't get has_changes (there's no diff to compare against)
    buffer_entry["units"] = [
        {"name": u["name"], "kind": u["kind"], "line_start": u["line_start"], "line_end": u["line_end"]}
        for u in units
    ]
    return len(units)


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract Swift units + compute has_changes for review-input.json")
    parser.add_argument("review_input", help="Path to review-input.json (updated in place)")
    args = parser.parse_args()

    path = Path(args.review_input)
    if not path.exists():
        print(f"Error: {path} not found", file=sys.stderr)
        return 1

    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"Error parsing {path}: {e}", file=sys.stderr)
        return 1

    source_type = data.get("source_type")
    total_units = 0
    changed_units = 0

    if source_type == "buffer":
        buffer_entry = data.get("buffer") or {}
        total_units = process_buffer(buffer_entry)
        changed_units = total_units  # whole-buffer review
        data["buffer"] = buffer_entry
    else:
        files = data.get("files") or []
        total_units, changed_units = process_files(files)
        data["files"] = files

    summary = data.setdefault("summary", {})
    summary["total_units"] = total_units
    summary["changed_units"] = changed_units
    if "total_files" not in summary:
        summary["total_files"] = len(data.get("files") or [])

    path.write_text(json.dumps(data, indent=2) + "\n")
    print(f"units: {total_units}, changed: {changed_units}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
