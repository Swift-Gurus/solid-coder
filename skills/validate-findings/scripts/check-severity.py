#!/usr/bin/env python3
"""
Check if review findings contain any SEVERE violations.

Reads rules/*/review-output.json (raw review outputs per principle) and reports
whether the pipeline should continue to validation/synthesis or stop early.

Usage:
    python3 check-severity.py <output-root>

Output (stdout):
    Line 1: "MINOR_ONLY" or "HAS_SEVERE"
    Line 2: summary, e.g. "4 findings: 0 severe, 4 minor across 3 principles"

Exit codes:
    0 — check completed (read stdout for verdict)
    1 — error (missing directory, no valid JSON, etc.)
"""

import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <output-root>", file=sys.stderr)
        sys.exit(1)

    rules_dir = Path(sys.argv[1]) / "rules"
    if not rules_dir.is_dir():
        print(f"Error: {rules_dir} not found", file=sys.stderr)
        sys.exit(1)

    severe_count = 0
    minor_count = 0
    principles_count = 0

    for principle_dir in sorted(rules_dir.iterdir()):
        review_path = principle_dir / "review-output.json"
        if not review_path.exists():
            continue
        principles_count += 1
        with open(review_path) as f:
            data = json.load(f)
        for file_entry in data.get("files", []):
            for unit in file_entry.get("units", []):
                for finding in unit.get("findings", []):
                    sev = finding.get("severity", "COMPLIANT")
                    if sev == "SEVERE":
                        severe_count += 1
                    elif sev == "MINOR":
                        minor_count += 1

    total = severe_count + minor_count
    verdict = "HAS_SEVERE" if severe_count > 0 else "MINOR_ONLY"

    print(verdict)
    print(f"{total} findings: {severe_count} severe, {minor_count} minor across {principles_count} principles")


if __name__ == "__main__":
    main()
