"""
solid-description: Verifies that submitted fixes provide coverage for all identified code violations.
solid-category: service
solid-tags: [utility, service]
"""

from typing import Protocol

from findings.fix_persister import violation_key
from findings.violation_reader import ViolationReading


class FixCompletenessValidating(Protocol):
    def validate_completeness(self, output_dir: str, fix_keys: set) -> dict: ...
    def violations_with_fixes(self, output_dir: str, fixes_by_key: dict) -> list: ...


class FixCompletenessValidator:
    """Checks that submitted fixes cover all severe violations and assembles the final result."""

    def __init__(self, reader: ViolationReading) -> None:
        self._reader = reader

    def validate_completeness(self, output_dir: str, fix_keys: set) -> dict:
        all_violations = self._reader.read_violations(output_dir)
        violation_keys = {
            violation_key(v["rule_id"], v["file_path"], v["unit_name"])
            for v in all_violations
        }
        missing_keys = violation_keys - fix_keys
        if missing_keys:
            missing_ids = [
                v["rule_id"] for v in all_violations
                if violation_key(v["rule_id"], v["file_path"], v["unit_name"]) in missing_keys
            ]
            return {
                "error": (
                    f"Missing fixes for {len(missing_keys)} violation(s): {missing_ids}. "
                    "Include an entry for every violation in the fixes array."
                ),
            }
        return {}

    def violations_with_fixes(self, output_dir: str, fixes_by_key: dict) -> list:
        all_violations = self._reader.read_violations(output_dir)
        return [
            {**v, "suggested_fix": fixes_by_key.get(
                violation_key(v["rule_id"], v["file_path"], v["unit_name"]), {}
            ).get("suggested_fix", "")}
            for v in all_violations
        ]
