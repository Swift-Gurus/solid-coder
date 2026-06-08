"""
solid-description: Aggregates code review violations across principles into a structured severity verdict.
solid-category: service
solid-tags: [pipeline, service]
"""

import json
from pathlib import Path
from typing import Protocol


class ReviewResultsCollecting(Protocol):
    def collect(self, output_root: str) -> dict: ...


class ReviewResultsCollector:
    """Aggregates per-principle review outputs and returns a structured severity verdict.

    Reads every rules/*/review-output.json under output_root, counts SEVERE/MINOR violations
    per principle, and returns verdict (ALL_COMPLIANT | MINOR_ONLY | HAS_SEVERE) with a
    summary table and the list of minor violations.
    """

    def collect(self, output_root: str) -> dict:
        rules_dir = Path(output_root) / "rules"
        if not rules_dir.is_dir():
            return {"error": f"No rules/ directory found in {output_root}. Have reviews completed?"}

        table = []
        minor_violations = []
        all_compliant = True

        for principle_dir in sorted(rules_dir.iterdir()):
            review_path = principle_dir / "review-output.json"
            if not review_path.exists():
                continue
            try:
                data = json.loads(review_path.read_text(encoding="utf-8"))
            except Exception as exc:
                table.append({
                    "principle": principle_dir.name,
                    "severity": "ERROR",
                    "violations": 0,
                    "path": str(review_path),
                    "error": str(exc),
                })
                continue

            severe = minor = 0
            for file_entry in data.get("files", []):
                for unit in file_entry.get("units", []):
                    for violation in unit.get("violations", []):
                        sev = violation.get("severity", "COMPLIANT")
                        if sev == "SEVERE":
                            severe += 1
                            all_compliant = False
                        elif sev == "MINOR":
                            minor += 1
                            minor_violations.append(violation)
                            all_compliant = False

            worst = "SEVERE" if severe else ("MINOR" if minor else "COMPLIANT")
            table.append({
                "principle": principle_dir.name,
                "severity": worst,
                "violations": severe + minor,
                "severe": severe,
                "minor": minor,
                "path": str(review_path),
            })

        if not table:
            return {"verdict": "ALL_COMPLIANT", "summary": [], "minor_violations": []}

        has_severe = any(r["severity"] == "SEVERE" for r in table)
        verdict = "ALL_COMPLIANT" if all_compliant else ("HAS_SEVERE" if has_severe else "MINOR_ONLY")
        return {
            "verdict": verdict,
            "summary": table,
            "minor_violations": minor_violations,
            "total_severe": sum(r.get("severe", 0) for r in table),
            "total_minor": sum(r.get("minor", 0) for r in table),
        }