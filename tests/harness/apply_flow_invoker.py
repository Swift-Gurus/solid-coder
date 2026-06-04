"""solid-name: ApplyFlowInvoker
solid-category: service
solid-spec: [SPEC-014]
solid-description: Runs a principle review against a source file and returns the resulting findings.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from interfaces import (  # noqa: E402
    ClaudeRunning,
    FindingsReading,
    FlowInvoking,
    McpConfigBuilding,
    ReasoningWriting,
    ReviewArtifactHandling,
    ReviewInputBuilding,
    ReviewSessionExecuting,
)
from models import ModelProfile, OutputPaths  # noqa: E402

_SKILL_PATH = "skills/apply-principle-review/SKILL.md"
_ALLOWED_TOOLS = (
    "Read,"
    "mcp__docs__load_rules,"
    "mcp__docs__load_detection_rules,"
    "mcp__docs__load_fix_for_violation,"
    "mcp__pipeline__submit_findings,"
    "mcp__pipeline__search_codebase"
)


def _strip_frontmatter(content: str) -> str:
    """Strip YAML frontmatter delimited by --- lines."""
    if not content.startswith("---"):
        return content
    end = content.find("\n---", 3)
    if end == -1:
        return content
    return content[end + 4:].lstrip("\n")


def _build_skill_prompt(
    project_root: Path,
    principle_folder: Path,
    review_input_path: Path,
    output_dir: Path,
    parent_session_id: str,
) -> str:
    """Return the fully resolved skill prompt ready for claude -p --bare.

    Reads the SKILL.md, strips frontmatter, substitutes ${CLAUDE_PLUGIN_ROOT},
    $ARGUMENTS, and plugin-prefixed MCP tool names so the bare session can call
    the correct tool names (mcp__docs__* / mcp__pipeline__*).
    """
    skill_path = project_root / _SKILL_PATH
    raw = skill_path.read_text(encoding="utf-8")
    skill_content = _strip_frontmatter(raw)

    plugin_root = str(project_root)
    principle_name = principle_folder.name

    skill_content = skill_content.replace("${CLAUDE_PLUGIN_ROOT}", plugin_root)
    skill_content = skill_content.replace("$ARGUMENTS[0]", principle_name)
    skill_content = skill_content.replace("$ARGUMENTS[1]", str(output_dir))
    # Strip inline fallback description left after $ARGUMENTS[1] substitution.
    # The skill line reads: "- OUTPUT_PATH: <path> - output root if not provided use ..."
    # Without stripping the agent appends the description text to the path.
    skill_content = re.sub(
        r'(- OUTPUT_PATH:\s+' + re.escape(str(output_dir)) + r')\s*-.*',
        r'\1',
        skill_content,
    )
    # Remap plugin-prefixed tool names to bare-session names
    skill_content = skill_content.replace("mcp__plugin_solid-coder_docs__", "mcp__docs__")
    skill_content = skill_content.replace("mcp__plugin_solid-coder_pipeline__", "mcp__pipeline__")

    header = f"# spawned-by: {parent_session_id}\n\n" if parent_session_id else ""
    return (
        f"{header}"
        f"{skill_content}\n\n"
        f"Code files (review-input): {review_input_path}"
    )


_SWIFT_TYPE_RE = re.compile(
    r'^\s*(public\s+|internal\s+|private\s+|open\s+|final\s+)*'
    r'(class|struct|protocol|enum|extension)\s+(\w+)',
    re.MULTILINE,
)
_VALID_KINDS = {"class", "struct", "protocol", "enum", "extension"}


def _parse_swift_units(content: str) -> list[dict]:
    """Extract top-level Swift type declarations as unit dicts."""
    lines = content.splitlines()
    total = len(lines)
    units = []
    for m in _SWIFT_TYPE_RE.finditer(content):
        kind = m.group(2)
        name = m.group(3)
        line_start = content[:m.start()].count("\n") + 1
        units.append({
            "name": name,
            "kind": kind,
            "line_start": line_start,
            "line_end": total,
            "has_changes": True,
            "changed_ranges": None,
        })
    return units


class ReviewInputBuilder(ReviewInputBuilding):
    def build_input(self, fixture_path: Path, log_dir: Path) -> Path:
        content = fixture_path.read_text(encoding="utf-8", errors="replace")
        line_count = len(content.splitlines())
        units = _parse_swift_units(content)
        if not units:
            # Fallback: treat the whole file as a single class-kind unit
            units = [{
                "name": fixture_path.stem,
                "kind": "class",
                "line_start": 1,
                "line_end": line_count,
                "has_changes": True,
                "changed_ranges": None,
            }]

        from datetime import datetime, timezone
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        review_input = {
            "source_type": "file",
            "metadata": {"timestamp": timestamp, "branch": None, "base_branch": None},
            "summary": {
                "total_files": 1,
                "total_units": len(units),
                "changed_units": len(units),
            },
            "files": [
                {
                    "file_path": str(fixture_path),
                    "units": units,
                    "changed_ranges": None,
                }
            ],
        }
        review_input_path = log_dir / "review-input.json"
        review_input_path.write_text(json.dumps(review_input, indent=2), encoding="utf-8")
        return review_input_path


class ReasoningWriter(ReasoningWriting):
    def write_reasoning(self, path: Path, content: str) -> None:
        path.write_text(content, encoding="utf-8")


class FindingsReader(FindingsReading):
    def read_findings(self, path: Path) -> list[dict]:
        if not path.exists():
            raise RuntimeError(f"review-output.json not produced: {path}")
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Malformed review-output.json at {path}: {exc}") from exc
        # Top-level findings array (validate-findings format)
        if "findings" in data:
            return data["findings"]
        # Nested files[].units[].findings[] (submit_findings / scored review format)
        findings = []
        for file_entry in data.get("files", []):
            for unit in file_entry.get("units", []):
                unit_name = unit.get("unit_name", "")
                for finding in unit.get("findings", []):
                    f = dict(finding)
                    if "unit_name" not in f:
                        f["unit_name"] = unit_name
                    findings.append(f)
        return findings


class ReviewArtifactHandler(ReviewArtifactHandling):
    """Facade — delegates to protocol-typed input builder, reasoning writer, and findings reader."""

    def __init__(
        self,
        input_builder: ReviewInputBuilding,
        reasoning_writer: ReasoningWriting,
        findings_reader: FindingsReading,
    ) -> None:
        self._input_builder = input_builder
        self._reasoning_writer = reasoning_writer
        self._findings_reader = findings_reader

    def build_input(self, fixture_path: Path, log_dir: Path) -> Path:
        return self._input_builder.build_input(fixture_path, log_dir)

    def write_reasoning(self, path: Path, content: str) -> None:
        return self._reasoning_writer.write_reasoning(path, content)

    def read_findings(self, path: Path) -> list[dict]:
        return self._findings_reader.read_findings(path)


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
        output_dir: Path,
        timeout: int,
    ) -> str | None:
        parent_session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        prompt = _build_skill_prompt(
            self._project_root,
            principle_folder,
            review_input_path,
            output_dir,
            parent_session_id,
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
        # Use a fixture-scoped output dir to avoid collisions when multiple fixtures
        # in the same principle share the same log_dir timestamp.
        fixture_output_dir = output_paths.log_dir / fixture_path.stem
        fixture_output_dir.mkdir(parents=True, exist_ok=True)
        review_input_path = self._artifact_handler.build_input(fixture_path, output_paths.log_dir)
        # Skill writes to {fixture_output_dir}/{NAME}/review-output.json
        result = self._session_runner.execute(
            self._principle_folder, review_input_path, fixture_output_dir, timeout
        )
        if result is not None:
            self._artifact_handler.write_reasoning(output_paths.reasoning_path, result)
        # The skill may write review-output.json at {fixture_output_dir}/{NAME}/review-output.json
        # (when Phase 1.1 creates the subfolder) or directly at {fixture_output_dir}/review-output.json
        # (when the agent skips subfolder creation). Search both locations.
        # Non-zero exit code from the bare session does not mean the skill failed —
        # the file may still have been written successfully.
        candidates = [
            fixture_output_dir / self._principle_folder.name / "review-output.json",
            fixture_output_dir / "review-output.json",
        ]
        actual_output = next((p for p in candidates if p.exists()), None)
        if actual_output is None:
            raise RuntimeError(f"Claude session failed for fixture: {fixture_path}")
        return self._artifact_handler.read_findings(actual_output)
