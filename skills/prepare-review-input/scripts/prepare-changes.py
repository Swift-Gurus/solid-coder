#!/usr/bin/env python3
"""Collect working-tree changes (staged + unstaged + untracked) and output
structured JSON with per-file changed line ranges.

Output conforms to output.schema.json (source_type="changes").
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

DIFF_FILE_RE = re.compile(r"^diff --git a/(.*) b/(.*)$")
HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
IMPORT_RE = re.compile(r"^\s*import\s+(\w+)", re.MULTILINE)


def run_git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0 and result.stderr:
        print(f"git {' '.join(args)}: {result.stderr.strip()}", file=sys.stderr)
    return result.stdout


def parse_diff(diff_text: str) -> Dict[str, list]:
    """Parse unified diff → {file_path: [{start, end}, ...]}."""
    files: Dict[str, List[int]] = {}
    current_file: Optional[str] = None
    line_no = 0

    for raw_line in diff_text.splitlines():
        m_file = DIFF_FILE_RE.match(raw_line)
        if m_file:
            # Coalesce previous file
            if current_file and current_file in files:
                files[current_file] = _coalesce(files[current_file])
            current_file = m_file.group(2)
            files.setdefault(current_file, [])
            continue

        m_hunk = HUNK_RE.match(raw_line)
        if m_hunk:
            line_no = int(m_hunk.group(1))
            continue

        if current_file is None:
            continue

        if raw_line.startswith("+++") or raw_line.startswith("---"):
            continue

        if raw_line.startswith("+"):
            files[current_file].append(line_no)
            line_no += 1
        elif raw_line.startswith("-"):
            pass  # deletion — don't increment
        else:
            line_no += 1

    # Coalesce last file
    if current_file and current_file in files:
        files[current_file] = _coalesce(files[current_file])

    # Convert raw changed-line lists to range dicts
    return {fp: ranges for fp, ranges in files.items()}


def _coalesce(lines: List[int]) -> List[dict]:
    """Turn sorted line numbers into [{start, end}, ...]."""
    if not lines:
        return []
    lines.sort()
    ranges: list[dict] = []
    start = lines[0]
    end = lines[0]
    for ln in lines[1:]:
        if ln == end + 1:
            end = ln
        else:
            ranges.append({"start": start, "end": end})
            start = end = ln
    ranges.append({"start": start, "end": end})
    return ranges


def untracked_files() -> List[str]:
    out = run_git("ls-files", "--others", "--exclude-standard")
    return [f for f in out.splitlines() if f.strip()]


def file_line_count(path: str) -> int:
    try:
        return sum(1 for _ in Path(path).open(encoding="utf-8", errors="replace"))
    except OSError:
        return 0


def extract_imports(file_paths: List[str]) -> List[str]:
    """Extract unique import module names from a list of files."""
    imports: set = set()
    for fp in file_paths:
        try:
            content = Path(fp).read_text(encoding="utf-8", errors="replace")
            for m in IMPORT_RE.finditer(content):
                imports.add(m.group(1))
        except OSError:
            continue
    return sorted(imports)


def build_output(output_path: Optional[str]) -> None:
    # 1. Collect diffs
    staged = run_git("diff", "--staged")
    unstaged = run_git("diff")

    staged_ranges = parse_diff(staged)
    unstaged_ranges = parse_diff(unstaged)

    # Merge: unstaged wins for overlapping files
    merged: Dict[str, list] = {**staged_ranges}
    for fp, ranges in unstaged_ranges.items():
        if fp in merged:
            all_lines: List[int] = []
            for r in merged[fp]:
                all_lines.extend(range(r["start"], r["end"] + 1))
            for r in ranges:
                all_lines.extend(range(r["start"], r["end"] + 1))
            merged[fp] = _coalesce(all_lines)
        else:
            merged[fp] = ranges

    # 2. Untracked files — entire file is changed
    for uf in untracked_files():
        if uf not in merged:
            count = file_line_count(uf)
            if count > 0:
                merged[uf] = [{"start": 1, "end": count}]

    # 3. Build files array
    files = []
    for fp in sorted(merged):
        files.append({
            "file_path": fp,
            "changed_ranges": merged[fp] if merged[fp] else None,
            "units": [],
        })

    # 4. Extract imports from all files
    all_file_paths = [fp for fp in sorted(merged)]
    detected_imports = extract_imports(all_file_paths)

    branch = run_git("branch", "--show-current").strip() or None

    output = {
        "source_type": "changes",
        "metadata": {
            "branch": branch,
            "base_branch": None,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        "files": files if files else None,
        "buffer": None,
        "detected_imports": detected_imports,
        "matched_tags": [],
        "summary": {
            "total_files": len(files),
            "total_units": 0,
            "changed_units": 0,
        },
    }

    text = json.dumps(output, indent=2)

    if output_path:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(text + "\n")
        print(f"Written to {output_path}", file=sys.stderr)
    else:
        print(text)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect working-tree changes into structured JSON."
    )
    parser.add_argument(
        "--output", "-o",
        help="Write JSON to file instead of stdout",
    )
    args = parser.parse_args()
    build_output(args.output)


if __name__ == "__main__":
    main()
