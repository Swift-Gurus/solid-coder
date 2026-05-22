"""
solid-description: Provides the appropriate LLM runner for the currently configured backend.
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
    """Return the configured LLM runner.

    Backend read from {cwd}/.claude/solid-coder-local.toml [llm] backend.
    Defaults to 'claude' when no project config is present.

    When backend=local, session_id and file_path are used to write
    per-call JSONL logs to ~/.solid-coder/llm-sessions/.
    """
    if llm_backend().lower() == "local":
        return make_llama_server_runner(
            host=llm_host(), model=llm_model(),
            session_id=session_id, file_path=file_path,
        )

    return ClaudeRunner(mcp_config=mcp_config, allowed_tools=allowed_tools)
