"""
solid-description: Enables the MCP server to independently resolve file paths and output configuration.
solid-category: service
solid-tags: [hook, utility]
"""

import json
from pathlib import Path
from typing import Callable, Optional

from hook_utils import solid_coder_project_dir
from health_check_context_writing import HealthCheckContextWriting  # noqa: F401


class HealthCheckContextWriter:
    """Writes hook-input.json and the active-health-check pointer before the LLM runs.

    hook-input.json  — authoritative file_path, language, output_dir for the MCP scorer.
    active-health-check — pointer from project dir to the current health-<uuid>/ dir name,
                          so the MCP server can find hook-input.json without the model's help.
    """

    def __init__(self, project_dir_fn: Optional[Callable] = None) -> None:
        self._project_dir_fn: Callable = project_dir_fn or solid_coder_project_dir

    def write(self, output_dir: str, file_path: str, language: str) -> None:
        health_dir = Path(output_dir)
        health_dir.mkdir(parents=True, exist_ok=True)
        hook_input = {
            "file_path": file_path,
            "language": language,
            "output_dir": output_dir,
        }
        (health_dir / "hook-input.json").write_text(
            json.dumps(hook_input), encoding="utf-8"
        )
        project_dir = self._project_dir_fn()
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "active-health-check").write_text(
            health_dir.name, encoding="utf-8"
        )
