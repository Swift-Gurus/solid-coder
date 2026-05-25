"""
solid-description: Provides principle loading, prompt building, LLM invocation, and health-check orchestration as isolated, protocol-typed components.
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
        fn: ClaudeCallable = run_claude_bare,
    ) -> None:
        super().__init__(fn)
        self._mcp_config = mcp_config
        self._allowed_tools = allowed_tools

    def run(self, prompt: str, timeout: int) -> Optional[str]:
        return self._fn(
            prompt,
            mcp_config=self._mcp_config,
            allowed_tools=self._allowed_tools,
            timeout=timeout,
        )


# ── Principles loading ────────────────────────────────────────────────────────

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


# ── Prompt building ───────────────────────────────────────────────────────────

class PromptBuilding(Protocol):
    def build(
        self,
        principles: list,
        content: str,
        path: str,
        parent_session_id: str,
    ) -> str: ...


_PROMPTS_DIR = PLUGIN_ROOT / "mcp-server" / "prompts" / "health-check"


class PromptReading(Protocol):
    def read(self, filename: str) -> str: ...


class FilePromptReader:
    """Reads prompt fragments from a directory on disk."""

    def __init__(self, prompts_dir: Path = _PROMPTS_DIR) -> None:
        self._dir = prompts_dir

    def read(self, filename: str) -> str:
        return (self._dir / filename).read_text(encoding="utf-8").rstrip()


class HealthPromptBuilder:
    """Assembles the LLM health-check prompt from detection rules and file content."""

    def __init__(self, reader: Optional[PromptReading] = None) -> None:
        self._reader = reader or FilePromptReader()

    def build(
        self,
        principles: list,
        content: str,
        path: str,
        parent_session_id: str,
    ) -> str:
        header = f"# spawned-by: {parent_session_id}\n\n" if parent_session_id else ""
        detection_instructions = "\n\n---\n\n".join(
            p["content"] for p in principles if p.get("content")
        )
        return header + (
            self._reader.read("preamble.md")
            + "\n\n<detection-instructions>\n"
            + detection_instructions
            + "\n</detection-instructions>"
            + "\n\n<code-to-review>\n"
            + content
            + "\n</code-to-review>"
            + "\n\n"
            + self._reader.read("workflow.md").replace("{file_path}", path)
            + "\n\n"
            + self._reader.read("output-format.md")
        )


# ── LLM review ────────────────────────────────────────────────────────────────

class LLMReviewing(Protocol):
    def review(self, prompt: str, path: str) -> Optional[list]: ...


class LLMReviewer:
    """Invokes the LLM health-check session and parses its response into violations."""

    def __init__(
        self,
        runner: ClaudeRunning,
        logger: Logging,
        parser: ViolationParsing,
        timeout: int = 300,
    ) -> None:
        self._runner = runner
        self._logger = logger
        self._parser = parser
        self._timeout = timeout

    def review(self, prompt: str, path: str) -> Optional[list]:
        try:
            raw = self._runner.run(prompt, timeout=self._timeout)
        except Exception as e:
            self._logger.log(f"HEALTH_ERR {Path(path).name}: exception={type(e).__name__}: {e}")
            return None
        if not raw:
            self._logger.log(f"HEALTH_ERR {Path(path).name}: bare session returned no result")
            return None
        violations = self._parser.parse(raw)
        if violations is None:
            self._logger.log(
                f"HEALTH_ERR {Path(path).name}: parse_failed: raw[:100]={raw[:100]!r}"
            )
        return violations


# ── Health check facade ───────────────────────────────────────────────────────

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
        prompt = self._builder.build(principles, content, path, parent_session_id)
        return self._reviewer.review(prompt, path)
