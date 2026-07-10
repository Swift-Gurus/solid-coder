"""
solid-description: Prepares health check configuration and maintains tracking of the active health check.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from typing import Callable, Optional

from hook_utils import solid_coder_project_dir
from health_check_context_writing import HealthCheckContextWriting
from code_unit_extractor import CodeUnitExtractor, CodeUnitExtracting
from findings.json_file_writer import JsonFileWriter, JsonFileWriting
from json_serializer import JsonSerializer
from llama.directory_creator import PathDirectoryCreator, DirectoryCreating
from health_check_input_writing import HealthCheckInputWriting
from health_check_input_writer import HealthCheckInputWriter
from active_health_check_pointer_storing import ActiveHealthCheckPointerStoring
from active_health_check_pointer_store import ActiveHealthCheckPointerStore


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
        project_dir_fn: Optional[Callable] = None,
        input_writer: Optional[HealthCheckInputWriting] = None,
        pointer_store: Optional[ActiveHealthCheckPointerStoring] = None,
    ) -> None:
        self._project_dir_fn: Callable = project_dir_fn or solid_coder_project_dir
        self._input_writer: HealthCheckInputWriting = input_writer or HealthCheckInputWriter(
            extractor=CodeUnitExtractor(),
            writer=JsonFileWriter(JsonSerializer()),
            dir_creator=PathDirectoryCreator(),
        )
        self._pointer_store: ActiveHealthCheckPointerStoring = pointer_store or ActiveHealthCheckPointerStore()

    def write(self, output_dir: str, file_path: str, language: str, content: str = "") -> None:
        self._input_writer.write(output_dir, file_path, language, content)
        self._pointer_store.write(self._project_dir_fn(), Path(output_dir).name)

    def clear(self) -> None:
        self._pointer_store.clear(self._project_dir_fn())
