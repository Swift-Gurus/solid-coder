"""solid-description: Creates the appropriate language model runner based on configuration.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path

_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hc_checker import ClaudeRunner, ClaudeRunning
from hc_llama_runner import make_llama_server_runner  # noqa: F401 — must be module-level for test patching
from hc_config import llm_backend, llm_host, llm_model, bare_session_timeout, codex_home
from hook_utils import run_claude_bare

_MODEL_PLACEHOLDERS = {"", "claude", "local", "codex"}


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
    backend = llm_backend().lower()
    raw_model = llm_model()
    model = raw_model if raw_model not in _MODEL_PLACEHOLDERS else ""

    if backend == "local":
        from hc_llama_runner import make_llama_server_runner

        return make_llama_server_runner(
            host=llm_host(), model=raw_model,
            session_id=session_id, file_path=file_path,
        )

    if backend == "codex":
        from hc_codex_runner import make_codex_runner

        if raw_model.startswith("claude-"):
            raise ValueError(
                f"Model '{raw_model}' is a Claude model and cannot be used with backend='codex'. "
                f"Set an OpenAI-compatible model (e.g. 'gpt-4o', 'o3') or leave model unset "
                f"to use Codex's default."
            )
        return make_codex_runner(
            model=model,
            timeout=bare_session_timeout(),
            codex_home=codex_home(),
        )

    return ClaudeRunner(mcp_config=mcp_config, allowed_tools=allowed_tools, fn=run_claude_bare, model=model)
