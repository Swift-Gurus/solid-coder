"""
solid-description: Checks source files for code health violations and reports findings.
solid-category: service
solid-tags: [hook, llm]
"""

import sys
from pathlib import Path
from typing import Callable, Optional, Protocol

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import Logging, PLUGIN_ROOT, run_claude_bare
from prompt_builder import BasePromptBuilder, PromptReading
from hook_callable import CallableAdapting
from hc_rule_loader import RulesLoading
from hc_tag_detector import TagDetecting
from hc_violation_parser import ViolationParsing

ClaudeCallable = Callable[..., Optional[str]]


class ClaudeRunning(Protocol):
    def run(self, prompt: str, timeout: int) -> Optional[str]: ...


class ClaudeRunner(CallableAdapting):
    """Adapts a ClaudeCallable to the ClaudeRunning protocol, owning MCP config and tool list."""

    def __init__(
        self,
        mcp_config: str,
        allowed_tools: str,
        model: str = "",
        fn: ClaudeCallable = run_claude_bare,
    ) -> None:
        super().__init__(fn)
        self._mcp_config = mcp_config
        self._allowed_tools = allowed_tools
        self._model = model

    def run(self, prompt: str, timeout: int) -> Optional[str]:
        return self._fn(
            prompt,
            mcp_config=self._mcp_config,
            allowed_tools=self._allowed_tools,
            model=self._model,
            timeout=timeout,
        )


# ── Principles loading ────────────────────────────────────────────

class PrinciplesLoading(Protocol):
    def load(self, content: str, path: str) -> Optional[list]: ...


class PrinciplesLoader:
    """Detects active tags from content and fetches matching detection rules."""

    def __init__(self, rules: RulesLoading, tags: TagDetecting) -> None:
        self._rules = rules
        self._tags = tags

    def load(self, content: str, path: str) -> Optional[list]:
        candidate_tags = self._rules.get_candidate_tags()
        matched_tags = self._tags.detect(content, candidate_tags)
        detection_data = self._rules.load_detection_rules(matched_tags)
        if not detection_data:
            return None
        return detection_data.get("principles", [])


# ── Prompt building ─────────────────────────────────────────────

class PromptBuilding(Protocol):
    def build(
        self,
        principles: list,
        content: str,
        path: str,
        parent_session_id: str,
    ) -> str: ...


_PROMPTS_DIR = PLUGIN_ROOT / "mcp-server" / "prompts" / "health-check"

# Principles that only apply to specific unit kinds.
# Drives the correct unit_kind in the submit_batch example so the LLM
# does not submit non-applicable unit types (e.g. class units for ISP).
_HC_UNIT_KINDS: dict = {
    "isp": "protocol",
}

# Override the schema-minimum (0) with a COMPLIANT representative value
# for principles where submitting 0 would trigger a false SEVERE band.
# ISP min_coverage: the schema expects integer percentage (0-100) but LLMs
# sometimes submit fractions (1 = 1.0 = 100%). Show 100 to teach the scale.
_HC_COMPLIANT_METRICS: dict = {
    "isp": {"width": 1, "min_coverage": 100, "cohesion_groups": 1},
}


class HealthPromptBuilder(BasePromptBuilder):
    """Assembles the LLM health-check prompt from detection rules and file content."""

    def __init__(
        self,
        reader: Optional[PromptReading] = None,
        shared_reader: Optional[PromptReading] = None,
    ) -> None:
        super().__init__(reader=reader, shared_reader=shared_reader, prompts_dir=_PROMPTS_DIR)

    def build(
        self,
        principles: list,
        content: str,
        path: str,
        parent_session_id: str,
        output_dir: str = "",
    ) -> str:
        import json as _json
        detection_instructions = "\n\n---\n\n".join(
            p["content"] for p in principles if p.get("content")
        )
        batch_example = self._make_batch_example(principles, output_dir)
        workflow = (
            self._read("workflow.md")
            .replace("{file_path}", path)
            .replace("{output_dir}", output_dir)
            .replace("{submit_batch_example}", batch_example)
        )
        return self._header(parent_session_id) + (
            self._read("preamble.md")
            + "\n\n<detection-instructions>\n"
            + detection_instructions
            + "\n</detection-instructions>"
            + "\n\n<code-to-review>\n"
            + content
            + "\n</code-to-review>"
            + "\n\n"
            + workflow
            + "\n\n"
            + self._read("output-format.md")
            + "\n\n"
            + self._read_shared("constraints.md")
        )

    def _make_batch_example(self, principles: list, output_dir: str) -> str:
        """Generate a complete submit_batch_findings JSON example from active principles."""
        import json as _json
        submissions = {}
        for p in principles:
            agent = p.get("name", "")
            principle_name = p.get("principle_name", agent.upper())
            metrics_example = p.get("metrics_example", {})
            if not agent:
                continue
            unit_kind = _HC_UNIT_KINDS.get(agent, "class")
            unit_name = "MyProtocol" if unit_kind == "protocol" else "ClassName"
            metrics = _HC_COMPLIANT_METRICS.get(agent, metrics_example)
            unit = {"unit_name": unit_name, "unit_kind": unit_kind, "metrics": metrics}
            if p.get("findings_required") and p.get("findings_example"):
                unit["findings"] = [p["findings_example"]]
            submissions[agent] = {
                "agent": agent,
                "principle": principle_name,
                "timestamp": "2026-06-05T10:00:00Z",
                "files": [{"file_path": "/path/to/ReviewedFile.swift", "units": [unit]}],
            }
        example = {
            "output_dir": output_dir or "/path/to/gate/session",
            "submissions": submissions,
        }
        return _json.dumps(example, indent=2)


# ── LLM execution ─────────────────────────────────────────────────────────────

class LLMExecuting(Protocol):
    def execute(self, prompt: str, path: str) -> Optional[str]: ...


class LLMExecutor:
    """Invokes the LLM session and returns the raw result. Logs and re-raises on exception."""

    def __init__(self, runner: ClaudeRunning, logger: Logging, timeout: int = 300) -> None:
        self._runner = runner
        self._logger = logger
        self._timeout = timeout

    def execute(self, prompt: str, path: str) -> Optional[str]:
        try:
            return self._runner.run(prompt, timeout=self._timeout)
        except Exception as exc:
            self._logger.log(f"HEALTH_ERR {Path(path).name}: {type(exc).__name__}: {exc}")
            raise


# ── Output handling ─────────────────────────────────────────────────────────────

class OutputReading(Protocol):
    def read_violations(self, output_dir: str, path: str) -> list: ...


class FileOutputReader:
    """Reads scored JSON files written by submit_batch_findings, extracts SEVERE violations.

    Only SEVERE findings are returned — consistent with the original gate behaviour.
    Merges any fix suggestions submitted via submit_fix into the violations.
    Cleans up the output directory after reading so reports do not accumulate.
    """

    def __init__(self, _path_cls=None, _rmtree_fn=None) -> None:
        import shutil as _shutil
        self._path_cls = _path_cls if _path_cls is not None else Path
        self._rmtree_fn = _rmtree_fn if _rmtree_fn is not None else _shutil.rmtree

    def read_violations(self, output_dir: str, path: str) -> list:
        import json
        dir_path = self._path_cls(output_dir)
        try:
            output_files = list(dir_path.glob("*/review-output.json"))
            if not output_files:
                raise RuntimeError(
                    f"LLM did not call submit_batch_findings — no output files in {output_dir}"
                )
            violations = self._extract_severe(output_files)
            fixes = self._read_fixes(output_dir)
            for v in violations:
                key = self._violation_key(v["metric_id"], v["file_path"], v["unit_name"])
                if key in fixes:
                    v["fix"] = fixes[key].get("suggested_fix", v["fix"])
            return violations
        finally:
            self._rmtree_fn(output_dir, ignore_errors=True)

    @staticmethod
    def _violation_key(metric_id: str, file_path: str, unit_name: str) -> str:
        import re as _re
        safe_path = _re.sub(r'[^\w.-]', '_', file_path)
        safe_unit = _re.sub(r'[^\w.-]', '_', unit_name)
        return f"{metric_id}__{safe_path}__{safe_unit}"

    def _read_fixes(self, output_dir: str) -> dict:
        import json
        fixes: dict = {}
        fixes_dir = Path(output_dir) / "fixes"
        if not fixes_dir.is_dir():
            return fixes
        for fp in fixes_dir.glob("*.json"):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                key = self._violation_key(
                    data["metric_id"], data["file_path"], data["unit_name"]
                )
                fixes[key] = data
            except (Exception,):
                pass
        return fixes

    def _extract_severe(self, output_files: list) -> list:
        import json
        violations = []
        for f in output_files:
            doc = json.loads(f.read_text())
            principle = doc.get("principle", doc.get("agent", ""))
            for file_obj in doc.get("files", []):
                file_path = file_obj.get("file_path", "?")
                for unit in file_obj.get("units", []):
                    unit_name = unit.get("unit_name", "?")
                    for finding in unit.get("findings", []):
                        if finding.get("severity") == "SEVERE":
                            mid = finding.get("metric_id", "")
                            band = finding.get("band_matched", "")
                            metrics = finding.get("metrics", {})
                            desc = self._describe_finding(band, metrics)
                            violations.append({
                                "principle": principle,
                                "metric_id": mid,
                                "file_path": file_path,
                                "unit_name": unit_name,
                                "issue": f"{mid}: {file_path}, unit {unit_name} — {desc}",
                                "fix": f"Call mcp__docs__load_fix_for_violation({mid}) for guidance.",
                            })
        return violations

    def _describe_finding(self, band: str, metrics: dict) -> str:
        """Generate a human-readable description from the band condition and actual metric values."""
        if not band:
            return "SEVERE violation detected"
        if metrics:
            measured = ", ".join(f"{k}={v}" for k, v in metrics.items())
            return f"{band} (measured: {measured})"
        return f"band triggered: {band}"


class ResponseParsing(Protocol):
    def parse_response(self, raw: Optional[str], path: str) -> Optional[list]: ...


class ResponseParser:
    """Parses the LLM's raw text response into a violations list."""

    def __init__(self, parser: ViolationParsing, logger: Logging) -> None:
        self._parser = parser
        self._logger = logger

    def parse_response(self, raw: Optional[str], path: str) -> Optional[list]:
        if not raw:
            self._logger.log(f"HEALTH_ERR {Path(path).name}: bare session returned no result")
            raise RuntimeError(f"claude -p returned no result for {Path(path).name}")
        violations = self._parser.parse(raw)
        if violations is None:
            self._logger.log(
                f"HEALTH_ERR {Path(path).name}: parse_failed: raw[:100]={raw[:100]!r}"
            )
        return violations


class OutputHandling(Protocol):
    def handle(self, raw: Optional[str], path: str, output_dir: Optional[str]) -> Optional[list]: ...


class FileBasedOutputHandler:
    """Output handler that reads violations from submit_batch_findings output files."""

    def __init__(self, output_reader: OutputReading) -> None:
        self._output_reader = output_reader

    def handle(self, raw: Optional[str], path: str, output_dir: Optional[str]) -> list:
        if output_dir is None:
            raise ValueError("FileBasedOutputHandler requires output_dir")
        return self._output_reader.read_violations(output_dir, path)


class TextBasedOutputHandler:
    """Output handler that parses violations from the LLM's raw text response."""

    def __init__(self, response_parser: ResponseParsing) -> None:
        self._response_parser = response_parser

    def handle(self, raw: Optional[str], path: str, output_dir: Optional[str]) -> Optional[list]:
        return self._response_parser.parse_response(raw, path)


# ── LLM review ────────────────────────────────────────────────────────────────

class LLMReviewing(Protocol):
    def review(self, prompt: str, path: str, output_dir: Optional[str] = None) -> Optional[list]: ...


class LLMReviewer:
    """Coordination facade: protocol-typed executor + output_handler.

    Facade: all dependencies are protocol-typed and injected — no internal construction.
    """

    def __init__(self, executor: LLMExecuting, output_handler: OutputHandling) -> None:
        self._executor = executor
        self._output_handler = output_handler

    def review(self, prompt: str, path: str, output_dir: Optional[str] = None) -> Optional[list]:
        raw = self._executor.execute(prompt, path)
        return self._output_handler.handle(raw, path, output_dir)


# ── Health check facade ─────────────────────────────────────────────

class HealthChecking(Protocol):
    def check(
        self,
        content: str,
        path: str,
        language: str,
        parent_session_id: str,
    ) -> Optional[list]: ...


class LLMHealthChecker:
    """Facade coordinating principle loading, prompt building, and LLM review."""

    def __init__(
        self,
        loader: PrinciplesLoading,
        builder: PromptBuilding,
        reviewer: LLMReviewing,
    ) -> None:
        self._loader = loader
        self._builder = builder
        self._reviewer = reviewer

    def check(
        self,
        content: str,
        path: str,
        language: str,
        parent_session_id: str,
    ) -> Optional[list]:
        principles = self._loader.load(content, path)
        if principles is None:
            return None
        if not principles:
            return []
        output_dir = str(Path.home() / ".solid-coder" / "gate" / parent_session_id)
        prompt = self._builder.build(principles, content, path, parent_session_id, output_dir)
        return self._reviewer.review(prompt, path, output_dir=output_dir)
