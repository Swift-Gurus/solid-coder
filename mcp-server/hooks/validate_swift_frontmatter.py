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

from hc_config import bare_session_timeout  # noqa: E402
from hc_runner_factory import make_llm_runner  # noqa: E402
from hook_utils import (  # noqa: E402
    PLUGIN_ROOT,
    HookResponder,
    parse_hook_event,
    parse_json_field,
)
from prompt_builder import BasePromptBuilder, PromptReading  # noqa: E402

_SUPPORTED_EXTENSIONS = {".swift", ".py"}
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


def fix(
    content: str,
    parent_session_id: str = "",
    builder: Optional[FrontmatterPromptBuilder] = None,
    cwd: str = "",
) -> Optional[str]:
    prompt = (builder or FrontmatterPromptBuilder()).build(content, parent_session_id)
    runner = make_llm_runner(mcp_config="", allowed_tools="", cwd=cwd)
    raw = runner.run(prompt, timeout=bare_session_timeout())
    from hook_utils import StrValidator
    v = parse_json_field(raw, "corrected_content", StrValidator())
    return v if v is not None else None


def main() -> None:
    responder = HookResponder()
    parsed = parse_hook_event(sys.stdin.read())
    if parsed is None:
        responder.allow()
        return

    tool_name, tool_input, file_path, session_id, cwd = parsed

    ext = Path(file_path).suffix.lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        responder.allow()
        return

    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
    else:
        responder.allow()
        return

    if "solid-description:" not in content:
        responder.allow()
        return

    corrected = fix(content, parent_session_id=session_id, cwd=cwd)

    if corrected is None or corrected == content:
        responder.allow()
        return

    input_key = "content" if tool_name == "Write" else "new_string"
    updated = dict(tool_input)
    updated[input_key] = corrected
    responder.allow_with_update(updated)


if __name__ == "__main__":
    main()
