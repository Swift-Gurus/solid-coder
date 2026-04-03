#!/usr/bin/env python3
"""
Synthesize-fixes Phase 1: Load Context

Globs by-file/*.output.json, parses all findings, and outputs a summary JSON
with file paths, active principle IDs, severity counts, and all-compliant flag.

Usage:
    python3 load-context.py <output-root>

Output (JSON to stdout):
{
    "all_compliant": false,
    "files": [
        {
            "file_path": "/path/to/Source.swift",
            "output_json": "/path/to/by-file/Source.swift.output.json",
            "principles": [
                {
                    "agent": "srp",
                    "principle": "Single Responsibility",
                    "severity": "SEVERE",
                    "finding_count": 2,
                    "finding_ids": ["srp-001", "srp-002"],
                    "has_suggestions": true
                }
            ]
        }
    ],
    "active_principles": ["srp", "ocp", "swiftui"],
    "summary": {
        "total_files": 3,
        "files_with_findings": 2,
        "total_findings": 5,
        "severe_count": 3,
        "minor_count": 2,
        "principles_with_findings": 3
    }
}
"""

import json
import glob
import os
import sys


def load_context(output_root):
    pattern = os.path.join(output_root, "by-file", "*.output.json")
    output_files = sorted(glob.glob(pattern))

    if not output_files:
        return {
            "all_compliant": True,
            "files": [],
            "active_principles": [],
            "summary": {
                "total_files": 0,
                "files_with_findings": 0,
                "total_findings": 0,
                "severe_count": 0,
                "minor_count": 0,
                "principles_with_findings": 0,
            },
        }

    files = []
    active_principles = set()
    total_findings = 0
    severe_count = 0
    minor_count = 0
    files_with_findings = 0

    for output_file in output_files:
        try:
            with open(output_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            print(f"ERROR: Failed to parse {output_file}: {e}", file=sys.stderr)
            sys.exit(1)

        file_path = data.get("file_path", "")
        principles_data = data.get("principles", [])

        file_principles = []
        file_has_findings = False

        for p in principles_data:
            agent = p.get("agent", "")
            principle = p.get("principle", "")
            severity = p.get("severity", "COMPLIANT")
            findings = p.get("findings", [])
            suggestions = p.get("suggestions", [])

            finding_ids = [fd.get("id", "") for fd in findings]
            finding_count = len(findings)

            if severity != "COMPLIANT" and finding_count > 0:
                active_principles.add(agent)
                file_has_findings = True
                total_findings += finding_count

                for fd in findings:
                    sev = fd.get("severity", "")
                    if sev == "SEVERE":
                        severe_count += 1
                    elif sev == "MINOR":
                        minor_count += 1

            file_principles.append(
                {
                    "agent": agent,
                    "principle": principle,
                    "severity": severity,
                    "finding_count": finding_count,
                    "finding_ids": finding_ids,
                    "has_suggestions": len(suggestions) > 0,
                }
            )

        if file_has_findings:
            files_with_findings += 1

        files.append(
            {
                "file_path": file_path,
                "output_json": output_file,
                "principles": file_principles,
            }
        )

    active_list = sorted(active_principles)

    return {
        "all_compliant": len(active_list) == 0,
        "files": files,
        "active_principles": active_list,
        "summary": {
            "total_files": len(files),
            "files_with_findings": files_with_findings,
            "total_findings": total_findings,
            "severe_count": severe_count,
            "minor_count": minor_count,
            "principles_with_findings": len(active_list),
        },
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: load-context.py <output-root>", file=sys.stderr)
        sys.exit(1)

    output_root = sys.argv[1]

    if not os.path.isdir(output_root):
        print(f"ERROR: Output root not found: {output_root}", file=sys.stderr)
        sys.exit(1)

    result = load_context(output_root)
    json.dump(result, sys.stdout, indent=2)
    print()


if __name__ == "__main__":
    main()
