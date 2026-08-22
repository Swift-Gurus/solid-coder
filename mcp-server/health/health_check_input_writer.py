import sys
from pathlib import Path
from typing import Optional
_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from code_unit_extractor import CodeUnitExtracting
from findings.json_file_writer import JsonFileWriting
from health.dry_search_completion_clearing import DrySearchCompletionClearing
from health_check_input_document import HealthCheckInputDocument
from llama.directory_creator import DirectoryCreating
from patch_review_context import PatchReviewContext
from proposed_source_document import ProposedSourceDocument


"""
solid-name: HealthCheckInputWriter
solid-category: service
solid-description: Persists authoritative prospective source context and expected review coverage for an isolated health check.
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

    def write(
        self,
        output_dir: str,
        file_path: str,
        language: str,
        content: str,
        patch_context: Optional[PatchReviewContext] = None,
    ) -> None:
        health_dir = Path(output_dir)
        self._completion.clear(output_dir)
        self._dir_creator.create(health_dir)
        proposed_files = (
            [
                ProposedSourceDocument(
                    file_path=simulation.file_path,
                    content=simulation.content,
                )
                for simulation in patch_context.proposed_files
            ]
            if patch_context is not None
            else [ProposedSourceDocument(file_path=file_path, content=content)]
        )
        document = HealthCheckInputDocument(
            file_path=file_path,
            language=language,
            output_dir=output_dir,
            expected_units=(
                self._extractor.extract(content, language) if content else []
            ),
            proposed_files=proposed_files,
        )
        self._writer.write(
            str(health_dir / "hook-input.json"),
            document.model_dump(mode="json"),
        )
