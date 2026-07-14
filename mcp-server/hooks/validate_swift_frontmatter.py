#!/usr/bin/env python3
"""PreToolUse hook — auto-corrects solid-frontmatter quality in source files.

Supported: .swift and .py files that contain a solid-description field.

Phase 1 (script): fast exits — unsupported file type, no solid-description present.
Phase 2 (claude -p --bare): receives the entire content being written, identifies
  the language-appropriate comment boundaries, and fixes only solid-description.
  Returns allow + updatedInput so the write proceeds with clean frontmatter.

Fails open on any infrastructure problem.
"""

import sys
from pathlib import Path
from typing import Optional

_MCP_DIR = Path(__file__).resolve().parents[1]
_MCP_HEALTH = _MCP_DIR / "health"
for _d in (
    _MCP_DIR,
    _MCP_DIR / "utils",
    _MCP_HEALTH,
    _MCP_HEALTH / "config",
    _MCP_HEALTH / "llm",
    _MCP_HEALTH / "codex",
):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import hc_config  # noqa: E402
from default_hook_event_parser import DefaultHookEventParser  # noqa: E402
from frontmatter_correction_orchestrator import FrontmatterCorrectionOrchestrator  # noqa: E402
from frontmatter_file_filter import FrontmatterFileFilter  # noqa: E402
from frontmatter_file_policy import FrontmatterFilePolicy  # noqa: E402
from hc_config_timeout_provider import HcConfigTimeoutProvider  # noqa: E402
from hc_runner_factory import make_llm_runner  # noqa: E402
from hook_utils import (  # noqa: E402
    PLUGIN_ROOT,
    HookResponder,
    parse_hook_event,
)
from llm_prompt_correction_service import LlmPromptCorrectionService  # noqa: E402
from llm_session_runner import LlmSessionRunner  # noqa: E402
from pathlib_extractor import PathlibExtractor  # noqa: E402
from prompt_builder import BasePromptBuilder, PromptReading  # noqa: E402
from tool_content_extractor import ToolContentExtractor  # noqa: E402

_FRONTMATTER_PROMPTS_DIR = PLUGIN_ROOT / "mcp-server" / "prompts" / "frontmatter"


class FrontmatterPromptBuilder(BasePromptBuilder):
    """Assembles the LLM frontmatter-correction prompt from files on disk."""

    def __init__(
        self,
        reader: Optional[PromptReading] = None,
        shared_reader: Optional[PromptReading] = None,
    ) -> None:
        super().__init__(reader=reader, shared_reader=shared_reader, prompts_dir=_FRONTMATTER_PROMPTS_DIR)

    def build(self, content: str, parent_session_id: str = "") -> str:
        return self._header(parent_session_id) + (
            self._read("preamble.md")
            + "\n\n"
            + self._read("rules.md")
            + "\n\n"
            + self._read_shared("constraints.md")
            + "\n\n"
            + self._read("output-format.md")
            + "\n\nFile content:\n"
            + content
        )


def _default_correction_service(builder: Optional[FrontmatterPromptBuilder] = None) -> LlmPromptCorrectionService:
    """Composition root: wires the production PromptCorrecting implementation (OCP factory exception)."""
    session_runner = LlmSessionRunner(
        runner_factory=make_llm_runner,
        config_provider=HcConfigTimeoutProvider(hc_config.load_config),
    )
    return LlmPromptCorrectionService(builder=builder or FrontmatterPromptBuilder(), session_runner=session_runner)


def fix(
    content: str,
    parent_session_id: str = "",
    builder: Optional[FrontmatterPromptBuilder] = None,
    cwd: str = "",
) -> Optional[str]:
    """Backward-compatible entry point — delegates to the production PromptCorrecting service."""
    return _default_correction_service(builder=builder).correct(content, parent_session_id=parent_session_id, cwd=cwd)


def _default_file_policy() -> FrontmatterFilePolicy:
    """Composition root: wires the production FileTypePolicy implementation (OCP factory exception)."""
    path_extractor = PathlibExtractor(lambda p: Path(p).suffix.lower())
    return FrontmatterFilePolicy(
        content_extractor=ToolContentExtractor(),
        file_filter=FrontmatterFileFilter(path_extractor=path_extractor),
    )


def main(
    responder: Optional[HookResponder] = None,
    event_parser: Optional[DefaultHookEventParser] = None,
    file_policy: Optional[FrontmatterFilePolicy] = None,
    orchestrator: Optional[FrontmatterCorrectionOrchestrator] = None,
) -> None:
    responder = responder or HookResponder()
    event_parser = event_parser or DefaultHookEventParser(parse_hook_event)
    file_policy = file_policy or _default_file_policy()
    orchestrator = orchestrator or FrontmatterCorrectionOrchestrator(_default_correction_service(), ToolContentExtractor())

    parsed = event_parser.parse(sys.stdin.read())
    if parsed is None:
        responder.allow()
        return

    tool_name, tool_input, file_path, session_id, cwd = parsed

    content = file_policy.content_for(tool_name, tool_input)
    if content is None or not file_policy.should_process(file_path, content):
        responder.allow()
        return

    orchestrator.correct(tool_name, tool_input, content, session_id, cwd, responder)


if __name__ == "__main__":
    main()
