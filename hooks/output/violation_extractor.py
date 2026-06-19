"""
solid-description: Reads scored review-output.json files and merges any submitted fixes into violations.
solid-category: service
solid-tags: [hook, llm]
"""

import re
from typing import Optional, Protocol

from path_file_system_reader import FileSystemReading, PathFileSystemReader


class ViolationExtracting(Protocol):
    def extract(self, output_dir: str) -> list: ...


class ViolationExtractor:
    """Reads scored review-output.json files and merges any submitted fixes.

    Single responsibility: data extraction. No filesystem cleanup — that is
    the caller's concern.
    """

    def __init__(self, fs: Optional[FileSystemReading] = None) -> None:
        self._fs: FileSystemReading = fs or PathFileSystemReader()

    def _violation_key(self, rule_id: str, file_path: str, unit_name: str) -> str:
        safe_path = re.sub(r'[^\w.-]', '_', file_path)
        safe_unit = re.sub(r'[^\w.-]', '_', unit_name)
        return f"{rule_id}__{safe_path}__{safe_unit}"

    def extract(self, output_dir: str) -> list:
        import json
        output_files = self._fs.glob(output_dir, "*/review-output.json")
        violations = []
        for f in output_files:
            doc = json.loads(self._fs.read_text(f))
            for file_obj in doc.get("files", []):
                file_path = file_obj.get("file_path", "?")
                for unit in file_obj.get("units", []):
                    unit_name = unit.get("unit_name", "?")
                    for v in unit.get("violations", []):
                        if v.get("severity") == "SEVERE":
                            rule_id = v.get("rule_id", "")
                            principle = rule_id.split("-")[0] if "-" in rule_id else rule_id
                            violations.append({
                                "principle": principle,
                                "metric_id": rule_id,
                                "file_path": file_path,
                                "unit_name": unit_name,
                                "issue": f"{rule_id}: {file_path}, unit {unit_name} — SEVERE violation",
                                "fix": f"Call mcp__docs__load_fix_for_violation({rule_id}) for guidance.",
                            })
        fixes = self._read_fixes(output_dir)
        for v in violations:
            key = self._violation_key(v["metric_id"], v["file_path"], v["unit_name"])
            if key in fixes:
                v["fix"] = fixes[key].get("suggested_fix", v["fix"])
        return violations

    def _read_fixes(self, output_dir: str) -> dict:
        import json
        fixes: dict = {}
        fixes_dir = self._fs.subpath(output_dir, "fixes")
        if not self._fs.is_dir(fixes_dir):
            return fixes
        for fp in self._fs.glob(fixes_dir, "*.json"):
            try:
                data = json.loads(self._fs.read_text(fp))
                key = self._violation_key(
                    data.get("rule_id", data.get("metric_id", "")),
                    data["file_path"],
                    data["unit_name"],
                )
                fixes[key] = data
            except Exception:
                pass
        return fixes
