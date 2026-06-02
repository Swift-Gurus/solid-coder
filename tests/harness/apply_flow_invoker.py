"""solid-name: ApplyFlowInvoker
solid-category: service
solid-spec: [SPEC-014]
solid-description: Runs a principle review against a source file and returns the resulting findings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from interfaces import (  # noqa: E402
    ClaudeRunning,
    FlowInvoking,
    McpConfigBuilding,
    ReviewArtifactHandling,
    ReviewSessionExecuting,
)
from models import ModelProfile, OutputPaths  # noqa: E402

_SKILL_PATH = "skills/apply-principle-review/SKILL.md"
_ALLOWED_TOOLS = (
    "Read,"
    "mcp__plugin_solid-coder_docs__load_rules,"
    "mcp__plugin_solid-coder_docs__load_pattern,"
    "mcp__plugin_solid-coder_pipeline__search_codebase"
)


class ReviewArtifactHandler(ReviewArtifactHandling):
    def build_input(self, fixture_path: Path, log_dir: Path) -> Path:
        unit = {
            "name": fixture_path.stem,
            "kind": "file",
            "line_start": 1,
            "line_end": sum(1 for _ in fixture_path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)),
            "has_changes": True,
            "changed_ranges": None,
        }
        review_input = {
            "files": [
                {
                    "file_path": str(fixture_path),
                    "units": [unit],
                    "changed_ranges": None,
                }
            ]
        }
        review_input_path = log_dir / "review-input.json"
        review_input_path.write_text(json.dumps(review_input, indent=2), encoding="utf-8")
        return review_input_path

    def write_reasoning(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")

    def read_findings(self, path: Path) -> list[dict]:
        if not path.exists():
            raise RuntimeError(f"review-output.json not produced: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Malformed review-output.json at {path}: {exc}") from exc
        return data.get("findings", [])


class ClaudeReviewSessionRunner(ReviewSessionExecuting):
    def __init__(
        self,
        project_root: Path,
        claude_runner: ClaudeRunning,
        mcp_config_builder: McpConfigBuilding,
    ) -> None:
        self._project_root = project_root
        self._claude_runner = claude_runner
        self._mcp_config_builder = mcp_config_builder

    def execute(
        self,
        principle_folder: Path,
        review_input_path: Path,
        output_path: Path,
        timeout: int,
    ) -> str | None:
        skill_path = self._project_root / _SKILL_PATH
        prompt = (
            f"Follow the skill at {skill_path}. "
            f"Arguments: {principle_folder} {review_input_path} {output_path}"
        )
        return self._claude_runner.run_bare(
            prompt=prompt,
            allowed_tools=_ALLOWED_TOOLS,
            mcp_config=self._mcp_config_builder.build(self._project_root),
            timeout=timeout,
            session_id="",
        )


class ApplyFlowInvoker(FlowInvoking):
    def __init__(
        self,
        principle_folder: Path,
        artifact_handler: ReviewArtifactHandling,
        session_runner: ReviewSessionExecuting,
    ) -> None:
        self._principle_folder = principle_folder
        self._artifact_handler = artifact_handler
        self._session_runner = session_runner

    def invoke(
        self,
        fixture_path: Path,
        output_paths: OutputPaths,
        model_profile: ModelProfile,
        timeout: int,
    ) -> list[dict]:
        output_paths.log_dir.mkdir(parents=True, exist_ok=True)
        review_input_path = self._artifact_handler.build_input(fixture_path, output_paths.log_dir)
        result = self._session_runner.execute(
            self._principle_folder, review_input_path, output_paths.review_output_path, timeout
        )
        if result is None:
            raise RuntimeError(f"Claude session failed for fixture: {fixture_path}")
        self._artifact_handler.write_reasoning(output_paths.reasoning_path, result)
        return self._artifact_handler.read_findings(output_paths.review_output_path)
