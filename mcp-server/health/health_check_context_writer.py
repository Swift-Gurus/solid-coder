"""Coordinates health-check context and active-check tracking."""

import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from typing import Callable

from health_check_context_writing import HealthCheckContextWriting
from health_check_input_writing import HealthCheckInputWriting
from active_health_check_pointer_storing import ActiveHealthCheckPointerStoring


"""
solid-name: HealthCheckContextWriter
solid-category: service
solid-description: Coordinates health-check context persistence and active-check lifecycle tracking.
"""
class HealthCheckContextWriter(HealthCheckContextWriting):
    """Facade: coordinates hook-input.json writing and active-health-check pointer lifecycle.

    hook-input.json  — authoritative file_path, language, output_dir, and expected_units
                       for the MCP scorer. expected_units are extracted from the file
                       content so submit_batch_findings can detect silent principle skips
                       without re-reading the (potentially deleted) source file.
    active-health-check — pointer from project dir to the current health-<uuid>/ dir name,
                          so the MCP server can find hook-input.json without the model's help.
    """

    def __init__(
        self,
        project_dir_fn: Callable,
        input_writer: HealthCheckInputWriting,
        pointer_store: ActiveHealthCheckPointerStoring,
    ) -> None:
        self._project_dir_fn = project_dir_fn
        self._input_writer = input_writer
        self._pointer_store = pointer_store

    def write(self, output_dir: str, file_path: str, language: str, content: str = "") -> None:
        self._input_writer.write(output_dir, file_path, language, content)
        self._pointer_store.write(self._project_dir_fn(), Path(output_dir).name)

    def clear(self) -> None:
        self._pointer_store.clear(self._project_dir_fn())
