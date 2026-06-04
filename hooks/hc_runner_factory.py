"""
solid-description: Resolves and returns the appropriate language model runner for the current deployment environment.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hc_checker import ClaudeRunner, ClaudeRunning
from hc_llama_runner import make_llama_server_runner
from hc_config import llm_backend, llm_host, llm_model


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
        return make_llama_server_runner(
            host=llm_host(), model=llm_model(),
            session_id=session_id, file_path=file_path,
        )

    # Use model only when explicitly set to a real model id, not a generic placeholder.
    _PLACEHOLDERS = {"", "claude", "local"}
    model = llm_model() if llm_model() not in _PLACEHOLDERS else ""
    return ClaudeRunner(mcp_config=mcp_config, allowed_tools=allowed_tools, model=model)
