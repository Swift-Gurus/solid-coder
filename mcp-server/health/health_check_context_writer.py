"""
solid-description: Writes health-check context and registration for the MCP scoring system.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from typing import Callable, Optional

from hook_utils import solid_coder_project_dir
from health_check_context_writing import HealthCheckContextWriting
from code_unit_extractor import CodeUnitExtractor, CodeUnitExtracting
from findings.json_file_writer import JsonFileWriter, JsonFileWriting


class HealthCheckContextWriter(HealthCheckContextWriting):
    """Writes hook-input.json and the active-health-check pointer before the LLM runs.

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
        extractor: Optional[CodeUnitExtracting] = None,
        writer: Optional[JsonFileWriting] = None,
    ) -> None:
        self._project_dir_fn: Callable = project_dir_fn or solid_coder_project_dir
        self._extractor: CodeUnitExtracting = extractor or CodeUnitExtractor()
        self._writer: JsonFileWriting = writer or JsonFileWriter()

    def write(self, output_dir: str, file_path: str, language: str, content: str = "") -> None:
        health_dir = Path(output_dir)
        health_dir.mkdir(parents=True, exist_ok=True)
        hook_input = {
            "file_path": file_path,
            "language": language,
            "output_dir": output_dir,
            "expected_units": self._extractor.extract(content, language) if content else [],
        }
        self._writer.write(str(health_dir / "hook-input.json"), hook_input)
        project_dir = self._project_dir_fn()
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "active-health-check").write_text(
            health_dir.name, encoding="utf-8"
        )
