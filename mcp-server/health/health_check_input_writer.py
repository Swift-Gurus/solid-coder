import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from code_unit_extractor import CodeUnitExtracting
from findings.json_file_writer import JsonFileWriting
from health.dry_search_completion_clearing import DrySearchCompletionClearing
from llama.directory_creator import DirectoryCreating


"""
solid-name: HealthCheckInputWriter
solid-category: service
solid-description: Starts a health-input generation with extracted code units and source metadata.
"""
class HealthCheckInputWriter:
    """Boundary adapter: writes hook-input.json — file_path, language, output_dir, and expected_units."""

    def __init__(
        self,
        extractor: CodeUnitExtracting,
        writer: JsonFileWriting,
        dir_creator: DirectoryCreating,
        completion: DrySearchCompletionClearing,
    ) -> None:
        self._extractor = extractor
        self._writer = writer
        self._dir_creator = dir_creator
        self._completion = completion

    def write(self, output_dir: str, file_path: str, language: str, content: str) -> None:
        health_dir = Path(output_dir)
        self._completion.clear(output_dir)
        self._dir_creator.create(health_dir)
        hook_input = {
            "file_path": file_path,
            "language": language,
            "output_dir": output_dir,
            "expected_units": self._extractor.extract(content, language) if content else [],
        }
        self._writer.write(str(health_dir / "hook-input.json"), hook_input)
