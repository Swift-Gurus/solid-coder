"""
solid-description: Provides access to LLM configuration settings.
solid-category: utility
solid-tags: [hook]
"""

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hc_config_core import llm_value  # noqa: E402


def _str(key: str, default: str) -> str:
    return llm_value(key, default, str) or default


def _int(key: str, default: int) -> int:
    return llm_value(key, default, int)


def llm_backend() -> str:
    return _str("backend", "claude")


def llm_host() -> str:
    return _str("host", "http://localhost:8080")


def llm_model() -> str:
    return _str("model", "local")


def llm_timeout() -> int:
    return _int("timeout", 300)


def bare_session_timeout() -> int:
    """Timeout for claude -p bare subprocess calls (health check + frontmatter).

    Configure via [llm] bare_session_timeout in solid-coder-local.toml.
    Default: 300 seconds (5 minutes).
    """
    return _int("bare_session_timeout", 300)


def debug_mode() -> bool:
    """When True, gate output files are preserved after each run for inspection.

    Scored output lands in {HOME}/.solid-coder/gate/{session_id}/{label}/review-output.json.
    Inspect these files to see exactly what metrics the LLM submitted and how they were scored.

    Configure via [llm] debug = true in solid-coder-local.toml.
    Default: False (files are cleaned up after each run).
    """
    return bool(_int("debug", 0))


def codex_home() -> str:
    """Path to use as CODEX_HOME for the codex backend.

    Relative paths are resolved against the project root at call time.
    Empty string (default) lets the runner derive it from PLUGIN_ROOT.

    Configure via [llm] codex_home in solid-coder-local.toml.
    Default: "" (runner uses .solid-coder/codex/ under PLUGIN_ROOT).
    """
    return _str("codex_home", "")


def bare_session_model() -> str:
    """Model override for claude -p bare subprocess calls.

    Configure via [llm] bare_session_model in solid-coder-local.toml.
    Empty string (default) defers to the CLI default model.
    NOTE: no current callers — llm_model() via make_llm_runner() is the active mechanism.
    """
    return _str("bare_session_model", "")
