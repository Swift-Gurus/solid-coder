"""
solid-description: Creates the appropriate language model runner based on configuration.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hc_checker import ClaudeRunner, ClaudeRunning
from hc_llama_runner import make_llama_server_runner  # noqa: F401 — must be module-level for test patching
from hc_config import llm_backend, llm_host, llm_model
from hook_utils import run_claude_bare


def make_llm_runner(
    mcp_config: str,
    allowed_tools: str,
    session_id: str = "",
    file_path: str = "",
) -> ClaudeRunning:
    """Return the configured LLM runner for a bare claude -p session.

    Backend and model read from {cwd}/.claude/solid-coder-local.toml [llm].
    Both health check and frontmatter use this factory — the only caller
    difference is the mcp_config and allowed_tools they pass.
    """
    if llm_backend().lower() == "local":
        from hc_llama_runner import make_llama_server_runner

        return make_llama_server_runner(
            host=llm_host(), model=llm_model(),
            session_id=session_id, file_path=file_path,
        )

    # Use model only when explicitly set to a real model id, not a generic placeholder.
    _PLACEHOLDERS = {"", "claude", "local"}
    _model = llm_model()
    model = _model if _model not in _PLACEHOLDERS else ""
    return ClaudeRunner(mcp_config=mcp_config, allowed_tools=allowed_tools, fn=run_claude_bare, model=model)