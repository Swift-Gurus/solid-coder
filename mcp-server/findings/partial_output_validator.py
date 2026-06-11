"""
solid-description: Validates partial review output submissions against schema requirements.
solid-category: service
solid-tags: [utility, service]
"""

import copy
import json
from pathlib import Path
from typing import Optional, Protocol

try:
    import jsonschema as _jsonschema
    _JSONSCHEMA_AVAILABLE = True
except ImportError:
    _jsonschema = None  # type: ignore[assignment]
    _JSONSCHEMA_AVAILABLE = False

from rules.principal_folder_resolver import resolve as _resolve_folder_fn


class PartialOutputValidating(Protocol):
    def validate_output(self, partial_output: dict) -> Optional[dict]: ...


class PartialOutputValidator:
    """Two-pass validation for partial_output submissions.

    Pass 1: validates overall structure against references/review-output.schema.json.
    Pass 2: validates each principle's metrics slice against its review/output.schema.json.
    No-ops when jsonschema is unavailable.
    """

    def __init__(self, refs_root: Path) -> None:
        self._refs_root = refs_root

    def validate_output(self, partial_output: dict) -> Optional[dict]:
        if not _JSONSCHEMA_AVAILABLE:
            return None

        unified_path = self._refs_root / "review-output.schema.json"
        if unified_path.exists():
            schema = copy.deepcopy(json.loads(unified_path.read_text(encoding="utf-8")))
            try:
                unit_items = (
                    schema["properties"]["files"]["items"]
                    ["properties"]["units"]["items"]
                )
                unit_items["required"] = [
                    f for f in unit_items.get("required", []) if f != "violations"
                ]
            except (KeyError, TypeError):
                pass
            try:
                _jsonschema.validate(partial_output, schema)
            except _jsonschema.ValidationError as exc:
                vpath = list(exc.absolute_path)
                file_path, unit_name = "?", "?"
                if len(vpath) >= 2 and vpath[0] == "files":
                    try:
                        fidx = vpath[1]
                        files_list = partial_output.get("files", [])
                        file_path = files_list[fidx].get("file_path", "?")
                        if len(vpath) >= 4 and vpath[2] == "units":
                            uidx = vpath[3]
                            unit_name = files_list[fidx].get("units", [])[uidx].get("unit_name", "?")
                    except (IndexError, AttributeError):
                        pass
                return {
                    "error": (
                        f"{file_path}, unit {unit_name}: {exc.message}. "
                        f"Use the <submission-metrics-example> format from load_detection_rules output."
                    )
                }

        for file_obj in partial_output.get("files", []):
            for unit in file_obj.get("units", []):
                _file_path = file_obj.get("file_path", "?")
                _unit_name = unit.get("unit_name", "?")
                for principle_name, principle_metrics in unit.get("metrics", {}).items():
                    try:
                        principle_folder = _resolve_folder_fn(principle_name, self._refs_root)
                    except (ValueError, FileNotFoundError):
                        continue
                    schema_path = principle_folder / "review" / "output.schema.json"
                    if not schema_path.exists():
                        continue
                    try:
                        principle_schema = json.loads(schema_path.read_text(encoding="utf-8"))
                        _jsonschema.validate(principle_metrics, principle_schema)
                    except _jsonschema.ValidationError as exc:
                        return {
                            "error": (
                                f"{_file_path}, unit {_unit_name}, principle {principle_name}: "
                                f"{exc.message}. "
                                f"Use the <submission-metrics-example> format from load_detection_rules output."
                            )
                        }
                    except Exception:
                        continue

        return None
