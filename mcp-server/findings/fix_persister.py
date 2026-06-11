"""
solid-description: Persists and retrieves fix suggestions for code violations.
solid-category: service
solid-tags: [utility, service]
"""

import json
import re
from pathlib import Path
from typing import Protocol


def violation_key(rule_id: str, file_path: str, unit_name: str) -> str:
    """Stable identifier for a (rule_id, file, unit) triple."""
    safe_path = re.sub(r'[^\w.-]', '_', file_path)
    safe_unit = re.sub(r'[^\w.-]', '_', unit_name)
    return f"{rule_id}__{safe_path}__{safe_unit}"


class FixPersisting(Protocol):
    def persist(self, output_dir: str, fixes: list) -> dict: ...
    def load_all(self, output_dir: str) -> dict: ...


class FixPersister:
    """Writes fix suggestions to the fixes/ subdirectory and reads them back."""

    def persist(self, output_dir: str, fixes: list) -> dict:
        fixes_dir = Path(output_dir) / "fixes"
        fixes_dir.mkdir(parents=True, exist_ok=True)
        for fix in fixes:
            try:
                key = violation_key(fix["rule_id"], fix["file_path"], fix["unit_name"])
            except KeyError as exc:
                return {"error": f"Fix entry missing required field: {exc}. Required: rule_id, file_path, unit_name, suggested_fix"}
            (fixes_dir / f"{key}.json").write_text(json.dumps(fix), encoding="utf-8")
        return {}

    def load_all(self, output_dir: str) -> dict:
        fixes_by_key: dict = {}
        fixes_dir = Path(output_dir) / "fixes"
        for fp in fixes_dir.glob("*.json"):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                key = violation_key(data["rule_id"], data["file_path"], data["unit_name"])
                fixes_by_key[key] = data
            except (json.JSONDecodeError, OSError, KeyError):
                pass
        return fixes_by_key
