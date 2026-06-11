"""
solid-description: Extracts SEVERE violations from review output files.
solid-category: service
solid-tags: [utility, service]
"""

import json
from pathlib import Path
from typing import Callable, Optional, Protocol


FileGlobCallable = Callable[[str, str], list]
JsonReadCallable = Callable[[str], Optional[dict]]


def _default_glob(directory: str, pattern: str) -> list:
    return sorted(str(p) for p in Path(directory).glob(pattern))


def _default_read_json(path: str) -> Optional[dict]:
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


class ViolationReading(Protocol):
    def read_violations(self, output_dir: str) -> list: ...


class ViolationReader:
    """Reads SEVERE violations from output files using injected file-access callables."""

    def __init__(
        self,
        glob_fn: FileGlobCallable = _default_glob,
        read_json_fn: JsonReadCallable = _default_read_json,
    ) -> None:
        self._glob = glob_fn
        self._read_json = read_json_fn

    def read_violations(self, output_dir: str) -> list:
        violations = []
        for path in self._glob(output_dir, "*/review-output.json"):
            doc = self._read_json(path)
            if not doc:
                continue
            for file_obj in doc.get("files", []):
                file_path = file_obj.get("file_path", "?")
                for unit in file_obj.get("units", []):
                    unit_name = unit.get("unit_name", "?")
                    for violation in unit.get("violations", []):
                        if violation.get("severity") == "SEVERE":
                            violations.append({
                                "rule_id": violation.get("rule_id", ""),
                                "file_path": file_path,
                                "unit_name": unit_name,
                            })
        return violations
