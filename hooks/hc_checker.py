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

from hook_utils import Logging, run_claude_bare
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


HEALTH_PROMPT = """\
You are a SOLID code quality gate doing a pre-write check.

<global-exceptions>
The following are exempt from ALL rules — do not report violations for them:
- `#Preview` blocks and their entire body
- Files whose sole purpose is SwiftUI previews
</global-exceptions>

The detection instructions below define the rules, how to detect violations, \
and the exceptions that apply to each rule. You MUST follow the detection steps \
exactly as written.

Exception handling rules:
- Each `<exceptions principle="X">` block contains exceptions that apply ONLY \
to principle X. Never apply exceptions from one principle to another.
- Before reporting a finding for principle X metric M, check ONLY the \
`<exceptions principle="X">` block. If the code matches an exception condition \
for that metric, skip ONLY that finding — continue reviewing the same unit \
against all other principles and metrics.
- Do NOT use an exception as a reason to stop reviewing a unit entirely. \
An exception exempts a unit from one specific metric of one specific principle, \
nothing more.

<detection-instructions>
{detection_instructions}
</detection-instructions>

<code-to-review>
{content}
</code-to-review>

Before listing violations, run the DRY-1 search procedure from the detection \
instructions using both methods:

1. **Frontmatter search** — call `mcp__pipeline__search_codebase` with synonyms \
for each type defined in this file. Finds code tagged with solid-frontmatter.

2. **Name-based fallback** — always runs, catches code without solid-frontmatter. \
For each code unit: collect search terms (type name, camelCase-split keywords, \
synonyms). Then: use Grep to search file contents by those terms; use Glob to \
search filenames. Also search for `extension <TypeName>` patterns on types used \
in this file — convenience wrappers are commonly missed. Check shared/common \
directories and design system modules for equivalent components. \
Merge any new hits with step 1 results; skip files already found in step 1.

The destination path for this write is `{file_path}`. Do NOT read that path — \
the file does not exist yet or contains stale content. Discard any match whose \
path is `{file_path}` — it is a self-reference.

If you find violations, load targeted fix guidance before writing your response:
- For each unique metric_id found, call \
`mcp__docs__load_fix_for_violation` with only metric_id (e.g. metric_id="OCP-1"). \
Use the returned instructions to make the `fix` field concrete and actionable.

List only SEVERE violations. For each include:
- principle: the rule name (e.g. SRP, OCP, DRY)
- metric_id: the metric identifier (e.g. OCP-1, SRP-2)
- issue: what is wrong
- fix: the specific change needed

Your entire response MUST be a single raw JSON object and nothing else. \
No markdown fences. No explanation. No commentary.

{{"violations": [{{"principle": "string", "metric_id": "string", "issue": "string", "fix": "string"}}]}}

Empty if clean: {{"violations": []}}
"""


class HealthPromptBuilder:
    """Assembles the LLM health-check prompt from detection rules and file content."""

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
        return header + HEALTH_PROMPT.format(
            detection_instructions=detection_instructions,
            content=content,
            file_path=path,
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
    ) -> None:
        self._runner = runner
        self._logger = logger
        self._parser = parser

    def review(self, prompt: str, path: str) -> Optional[list]:
        try:
            raw = self._runner.run(prompt, timeout=300)
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
