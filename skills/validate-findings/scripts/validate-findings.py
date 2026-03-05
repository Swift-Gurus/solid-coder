#!/usr/bin/env python3
"""
Validate and reorganize SOLID review findings by file.

Filters findings to only those overlapping changed ranges,
then groups findings + suggestions by file path.

Usage:
    python3 validate-findings.py <output-root> [plugin-root]

    When plugin-root is provided, JSON inputs are validated against their
    schemas before processing. When omitted, validation is skipped.

Input:
    <output-root>/prepare/review-input.json
    <output-root>/rules/*/review-output.json
    <output-root>/rules/*/fix.json

Output:
    <output-root>/by-file/<filename>.output.json
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timezone

try:
    import jsonschema
except ImportError:
    jsonschema = None


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def validate_json(data, schema_path):
    """Validate data against a JSON schema. Raises SystemExit on failure."""
    if jsonschema is None:
        print("Warning: jsonschema not installed, skipping validation", file=sys.stderr)
        return
    schema = load_json(schema_path)
    try:
        jsonschema.validate(instance=data, schema=schema)
    except jsonschema.ValidationError as e:
        print(f"Schema validation failed for {schema_path}:\n  {e.message}", file=sys.stderr)
        sys.exit(1)


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def ranges_overlap(finding, changed_ranges):
    """Check if finding's line range overlaps any changed range."""
    f_start = finding.get("line_start")
    f_end = finding.get("line_end")
    if f_start is None or f_end is None:
        return True  # no line info = keep it
    for r in changed_ranges:
        if f_start <= r["end"] and f_end >= r["start"]:
            return True
    return False


def worst_severity(findings):
    """Return worst severity from a list of findings."""
    order = {"COMPLIANT": 0, "MINOR": 1, "SEVERE": 2}
    if not findings:
        return "COMPLIANT"
    worst = max(findings, key=lambda f: order.get(f.get("severity", "COMPLIANT"), 0))
    return worst.get("severity", "COMPLIANT")


def main():
    if len(sys.argv) < 2 or len(sys.argv) > 3:
        print(f"Usage: {sys.argv[0]} <output-root> [plugin-root]", file=sys.stderr)
        sys.exit(1)

    output_root = Path(sys.argv[1])
    plugin_root = Path(sys.argv[2]) if len(sys.argv) == 3 else None

    # Phase 1: Load data
    review_input_path = output_root / "prepare" / "review-input.json"
    if not review_input_path.exists():
        print(f"Error: {review_input_path} not found", file=sys.stderr)
        sys.exit(1)

    review_input = load_json(review_input_path)
    if plugin_root:
        validate_json(review_input, plugin_root / "skills" / "prepare-review-input" / "output.schema.json")
    source_type = review_input.get("source_type", "branch")
    skip_filtering = source_type in ("folder", "file", "buffer")

    # Build lookup: file_path -> changed_ranges
    changed_lookup = {}
    for file_entry in review_input.get("files") or []:
        fp = file_entry["file_path"]
        changed_lookup[fp] = file_entry.get("changed_ranges")

    # Discover review outputs and fix outputs
    rules_dir = output_root / "rules"
    if not rules_dir.exists():
        print(f"Error: {rules_dir} not found", file=sys.stderr)
        sys.exit(1)

    principles = []
    for principle_dir in sorted(rules_dir.iterdir()):
        if not principle_dir.is_dir():
            continue
        review_path = principle_dir / "review-output.json"
        fix_path = principle_dir / "fix.json"
        if not review_path.exists():
            continue
        review_data = load_json(review_path)
        fix_data = load_json(fix_path) if fix_path.exists() else None
        if plugin_root:
            principle_name_upper = principle_dir.name.upper()
            review_schema = plugin_root / "references" / principle_name_upper / "review" / "output.schema.json"
            if review_schema.exists():
                validate_json(review_data, review_schema)
            if fix_data:
                fix_schema = plugin_root / "references" / principle_name_upper / "fix" / "output.schema.json"
                if fix_schema.exists():
                    validate_json(fix_data, fix_schema)
        entry = {
            "review": review_data,
            "fix": fix_data,
        }
        principles.append(entry)

    # Phase 2 & 3: Filter and reorganize by file
    # Structure: file_path -> [{ agent, principle, findings, suggestions }]
    by_file = {}
    total_findings = 0
    total_rejected = 0

    for entry in principles:
        review = entry["review"]
        fix = entry["fix"]

        agent = review.get("agent", "")
        principle_name = review.get("principle", "")
        timestamp = review.get("timestamp", datetime.now(timezone.utc).isoformat())

        # Build suggestion lookup from fix.json: finding_id -> [suggestions]
        suggestions_by_finding = {}
        all_suggestions = []
        if fix and "suggestions" in fix:
            all_suggestions = fix["suggestions"]
            for s in all_suggestions:
                for addr in s.get("addresses", []):
                    suggestions_by_finding.setdefault(addr, []).append(s)

        # Process each file in review output
        for file_entry in review.get("files", []):
            file_path = file_entry.get("file", "")

            # Support both unit-based (new) and flat (legacy) review output
            units = file_entry.get("units")
            if units is not None:
                # New per-unit structure: files[].units[].findings
                for unit in units:
                    findings = unit.get("findings", [])
                    unit_name = unit.get("unit_name", "")
                    unit_kind = unit.get("unit_kind", "")

                    passing = _filter_findings(
                        findings, file_path, changed_lookup, skip_filtering
                    )
                    total_findings += len(findings)
                    total_rejected += len(findings) - len(passing)

                    if not passing:
                        continue

                    passing_ids = {f["id"] for f in passing}
                    matched_suggestions = _match_suggestions(passing, suggestions_by_finding)
                    severity = worst_severity(passing)

                    if severity == "COMPLIANT":
                        continue

                    by_file.setdefault(file_path, {"timestamp": timestamp, "principles": []})
                    by_file[file_path]["principles"].append({
                        "agent": agent,
                        "principle": principle_name,
                        "severity": severity,
                        "unit_name": unit_name,
                        "unit_kind": unit_kind,
                        "findings": passing,
                        "suggestions": matched_suggestions,
                    })
            else:
                # Legacy flat structure: files[].findings
                findings = file_entry.get("findings", [])

                passing = _filter_findings(
                    findings, file_path, changed_lookup, skip_filtering
                )
                total_findings += len(findings)
                total_rejected += len(findings) - len(passing)

                if not passing:
                    continue

                matched_suggestions = _match_suggestions(passing, suggestions_by_finding)
                severity = worst_severity(passing)

                if severity == "COMPLIANT":
                    continue

                by_file.setdefault(file_path, {"timestamp": timestamp, "principles": []})
                by_file[file_path]["principles"].append({
                    "agent": agent,
                    "principle": principle_name,
                    "severity": severity,
                    "findings": passing,
                    "suggestions": matched_suggestions,
                })

    # Phase 4: Write outputs
    by_file_dir = output_root / "by-file"
    total_passed = total_findings - total_rejected

    for file_path, data in sorted(by_file.items()):
        filename = os.path.basename(file_path)
        output = {
            "file": file_path,
            "timestamp": data["timestamp"],
            "principles": data["principles"],
        }
        out_path = by_file_dir / f"{filename}.output.json"
        write_json(str(out_path), output)

    print(f"{total_findings} findings → {total_passed} validated, {total_rejected} rejected")
    print(f"Output: {by_file_dir}")


def _filter_findings(findings, file_path, changed_lookup, skip_filtering):
    """Filter findings based on changed ranges."""
    passing = []
    for finding in findings:
        if skip_filtering:
            passing.append(finding)
            continue

        cr = changed_lookup.get(file_path)
        if cr is None or cr is True:
            # null or true = entire file is new
            passing.append(finding)
            continue

        if isinstance(cr, list) and ranges_overlap(finding, cr):
            passing.append(finding)

    return passing


def _match_suggestions(passing, suggestions_by_finding):
    """Collect suggestions that address at least one passing finding."""
    seen_suggestion_ids = set()
    matched = []
    for f in passing:
        for s in suggestions_by_finding.get(f["id"], []):
            if s["id"] not in seen_suggestion_ids:
                seen_suggestion_ids.add(s["id"])
                matched.append(s)
    return matched


if __name__ == "__main__":
    main()
