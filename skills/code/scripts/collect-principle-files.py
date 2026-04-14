#!/usr/bin/env python3
"""Collect all loadable file paths for a set of active principles.

Takes active_principles JSON (from discover-principles output) and returns
a flat JSON array of file paths to load. Reuses parse-frontmatter.py for
frontmatter parsing and path resolution.

For each principle, collects:
  1. rule.md (the principle's rule file)
  2. files_to_load from parse-frontmatter (examples, design patterns, code/)
  3. fix/instructions.md (if it exists)

Usage:
    echo '<active_principles_json>' | python3 collect-principle-files.py
    python3 collect-principle-files.py --json '<active_principles_json>'
    python3 collect-principle-files.py --file path/to/discover-output.json

Output (stdout): JSON object with a single "files_to_load" array of absolute file paths.

Exit codes:
    0 — success
    1 — error
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import List


SCRIPT_DIR = Path(__file__).resolve().parent
PARSE_FRONTMATTER = (
    SCRIPT_DIR.parent.parent / "parse-frontmatter" / "scripts" / "parse-frontmatter.py"
)


def parse_frontmatter(rule_path: str) -> dict:
    """Run parse-frontmatter.py on a rule.md and return parsed JSON."""
    result = subprocess.run(
        [sys.executable, str(PARSE_FRONTMATTER), rule_path],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(
            f"Warning: parse-frontmatter failed for {rule_path}: {result.stderr.strip()}",
            file=sys.stderr,
        )
        return {}
    return json.loads(result.stdout)


def collect_files(active_principles: list) -> List[str]:
    """Collect all file paths to load for the given active principles."""
    files: List[str] = []
    seen: set = set()

    def add(path: str) -> None:
        resolved = str(Path(path).resolve())
        if resolved not in seen and Path(resolved).is_file():
            seen.add(resolved)
            files.append(resolved)

    for principle in active_principles:
        rule_path = principle.get("rule_path")
        folder = principle.get("folder")

        if not rule_path or not folder:
            continue

        # 1. rule.md itself
        add(rule_path)

        # 2. files_to_load from parse-frontmatter
        parsed = parse_frontmatter(rule_path)
        for path in parsed.get("files_to_load", []):
            add(path)

        # 3. fix/instructions.md
        fix_instructions = Path(folder) / "fix" / "instructions.md"
        add(str(fix_instructions))

    return files


def load_active_principles(args: list) -> list:
    """Parse active_principles from CLI args or stdin."""
    raw = None

    if "--file" in args:
        idx = args.index("--file")
        if idx + 1 >= len(args):
            print("Error: --file requires a path argument", file=sys.stderr)
            sys.exit(1)
        file_path = Path(args[idx + 1])
        if not file_path.is_file():
            print(f"Error: {file_path} not found", file=sys.stderr)
            sys.exit(1)
        raw = file_path.read_text(encoding="utf-8")
    elif "--json" in args:
        idx = args.index("--json")
        if idx + 1 >= len(args):
            print("Error: --json requires a JSON string argument", file=sys.stderr)
            sys.exit(1)
        raw = args[idx + 1]
    elif not sys.stdin.isatty():
        raw = sys.stdin.read()
    else:
        print(
            "Usage: python3 collect-principle-files.py --json '<json>' | --file <path> | stdin",
            file=sys.stderr,
        )
        sys.exit(1)

    data = json.loads(raw)

    # Accept either the full discover-principles output or just the array
    if isinstance(data, dict) and "active_principles" in data:
        return data["active_principles"]
    if isinstance(data, list):
        return data
    print("Error: expected a JSON array or object with active_principles", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    active_principles = load_active_principles(sys.argv[1:])
    files = collect_files(active_principles)
    print(json.dumps({"files_to_load": files}, indent=2))


if __name__ == "__main__":
    main()
