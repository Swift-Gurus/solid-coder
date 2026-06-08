#!/usr/bin/env python3
"""
Validate and reorganize SOLID review violations by file.

Filters units to only those overlapping changed ranges,
then groups violations + suggestions by file path.

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


def unit_in_changed_range(unit, changed_ranges):
    """Return True if the unit's line range overlaps any changed range, or if no range info."""
    line_start = unit.get("line_start")
    line_end = unit.get("line_end")
    if line_start is None or line_end is None:
        return True  # no line info — keep the unit
    for r in changed_ranges:
        if line_start <= r["end"] and line_end >= r["start"]:
            return True
    return False


def worst_severity(violations):
    """Return worst severity from a list of violations."""
    order = {"COMPLIANT": 0, "MINOR": 1, "SEVERE": 2}
    if not violations:
        return "COMPLIANT"
    worst = max(violations, key=lambda v: order.get(v.get("severity", "COMPLIANT"), 0))
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
    source_type = review_input.get("source_type", "changes")
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
            # Validate against the unified review-output schema
            unified_schema = plugin_root / "references" / "review-output.schema.json"
            if unified_schema.exists():
                validate_json(review_data, unified_schema)
            if fix_data:
                # Fix schema remains per-principle
                refs_root = plugin_root / "references"
                for candidate in refs_root.rglob("*/"):
                    if candidate.name.lower() == principle_dir.name.lower() and (candidate / "rule.md").exists():
                        fix_schema = candidate / "fix" / "output.schema.json"
                        if fix_schema.exists():
                            validate_json(fix_data, fix_schema)
                        break
        principles.append({"review": review_data, "fix": fix_data})

    # Phase 2 & 3: Filter and reorganize by file
    # Structure: file_path -> {timestamp, principles: [...]}
    by_file = {}
    total_violations = 0
    total_rejected = 0

    for entry in principles:
        review = entry["review"]
        fix = entry["fix"]

        timestamp = review.get("timestamp", datetime.now(timezone.utc).isoformat())

        # Build suggestion lookup from fix.json: rule_id -> [suggestions]
        suggestions_by_rule = {}
        if fix and "suggestions" in fix:
            for s in fix["suggestions"]:
                for addr in s.get("addresses", []):
                    suggestions_by_rule.setdefault(addr, []).append(s)

        # Process each file in review output
        for file_entry in review.get("files", []):
            file_path = file_entry.get("file_path", "")

            # New per-unit structure: files[].units[].violations
            units = file_entry.get("units")
            if units is not None:
                for unit in units:
                    violations = unit.get("violations", [])
                    unit_name = unit.get("unit_name", "")
                    unit_kind = unit.get("unit_kind", "")

                    # Filter: check unit-level line range
                    unit_passes = _unit_passes_filter(
                        unit, file_path, changed_lookup, skip_filtering
                    )
                    total_violations += len(violations)
                    if not unit_passes:
                        total_rejected += len(violations)
                        continue

                    if not violations:
                        continue

                    matched_suggestions = _match_suggestions(violations, suggestions_by_rule)
                    severity = worst_severity(violations)

                    if severity == "COMPLIANT":
                        continue

                    by_file.setdefault(file_path, {"timestamp": timestamp, "principles": []})
                    by_file[file_path]["principles"].append({
                        "principle": _infer_principle(review, violations),
                        "severity": severity,
                        "unit_name": unit_name,
                        "unit_kind": unit_kind,
                        "violations": violations,
                        "suggestions": matched_suggestions,
                    })
            else:
                # Legacy flat structure: files[].findings (backward compatibility)
                findings = file_entry.get("findings", [])
                passing = _filter_findings_legacy(
                    findings, file_path, changed_lookup, skip_filtering
                )
                total_violations += len(findings)
                total_rejected += len(findings) - len(passing)
                if not passing:
                    continue
                severity = worst_severity(passing)
                if severity == "COMPLIANT":
                    continue
                by_file.setdefault(file_path, {"timestamp": timestamp, "principles": []})
                by_file[file_path]["principles"].append({
                    "principle": review.get("principle", review.get("agent", "")),
                    "severity": severity,
                    "violations": passing,
                    "suggestions": [],
                })

    # Phase 4: Write outputs
    by_file_dir = output_root / "by-file"
    total_passed = total_violations - total_rejected

    for file_path, data in sorted(by_file.items()):
        filename = os.path.basename(file_path)
        output = {
            "file_path": file_path,
            "timestamp": data["timestamp"],
            "principles": data["principles"],
        }
        out_path = by_file_dir / f"{filename}.output.json"
        write_json(str(out_path), output)

    print(f"{total_violations} violations → {total_passed} validated, {total_rejected} rejected")
    print(f"Output: {by_file_dir}")


def _infer_principle(review: dict, violations: list) -> str:
    """Infer a display principle name from the review doc or the first violation's rule_id."""
    if violations:
        rule_id = violations[0].get("rule_id", "")
        if "-" in rule_id:
            return rule_id.split("-")[0]
    return review.get("principle", review.get("agent", ""))


def _unit_passes_filter(unit, file_path, changed_lookup, skip_filtering):
    """Return True if this unit should be included based on changed-range filtering.

    Three cases for a file in the lookup:
      - null changed_ranges → entire file is new, keep all units
      - list changed_ranges → check unit line range against each changed range
      - file not in lookup → file not in review-input, reject unit
    """
    if skip_filtering:
        return True

    if file_path not in changed_lookup:
        return False  # file not in review-input — reject (guards against hallucination)

    cr = changed_lookup[file_path]
    if cr is None or cr is True:
        return True  # null or true = entire file is new, keep all

    if isinstance(cr, list):
        return unit_in_changed_range(unit, cr)

    return False


def _filter_findings_legacy(findings, file_path, changed_lookup, skip_filtering):
    """Legacy per-finding filter for backward compatibility with old flat review-output files."""
    passing = []
    for finding in findings:
        if skip_filtering:
            passing.append(finding)
            continue
        cr = changed_lookup.get(file_path)
        if cr is None or cr is True:
            passing.append(finding)
            continue
        if isinstance(cr, list):
            # For old findings, check line_start/line_end on the finding itself
            f_start = finding.get("line_start")
            f_end = finding.get("line_end")
            if f_start is None or f_end is None:
                passing.append(finding)
                continue
            for r in cr:
                if f_start <= r["end"] and f_end >= r["start"]:
                    passing.append(finding)
                    break
    return passing


def _match_suggestions(violations, suggestions_by_rule):
    """Collect suggestions that address at least one violation's rule_id."""
    seen_ids = set()
    matched = []
    for v in violations:
        rule_id = v.get("rule_id", "")
        for s in suggestions_by_rule.get(rule_id, []):
            sid = s.get("id", id(s))
            if sid not in seen_ids:
                seen_ids.add(sid)
                matched.append(s)
    return matched


if __name__ == "__main__":
    main()
