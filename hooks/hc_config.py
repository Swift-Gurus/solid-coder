"""
solid-description: Provides project-scoped solid-coder runtime configuration values to hooks.
solid-category: utility
solid-tags: [hook]
"""

import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, TypeVar

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import load_toml  # noqa: E402

_FILENAME = "solid-coder-local.toml"
T = TypeVar("T")


class TomlLoader(Protocol):
    def __call__(self, path: Path) -> dict: ...


def _find_config(_cwd: Optional[Path] = None) -> Optional[Path]:
    """Return the project-level config path, or None if it does not exist."""
    base = _cwd if _cwd is not None else Path.cwd()
    path = base / ".claude" / _FILENAME
    return path if path.exists() else None


def _read_section(
    section: str,
    _loader: TomlLoader = load_toml,
    _cwd: Optional[Path] = None,
) -> dict:
    path = _find_config(_cwd=_cwd)
    return _loader(path).get(section, {}) if path else {}


def _read_config_file(
    _loader: TomlLoader = load_toml,
    _env: Optional[dict] = None,
    _cwd: Optional[Path] = None,
) -> dict:
    env = _env if _env is not None else os.environ
    override = env.get("SOLID_CODER_TEST_MODEL_PROFILE")
    if override:
        return _loader(Path(override)).get("llm", {})
    return _read_section("llm", _loader=_loader, _cwd=_cwd)


def _get_typed(key: str, default: T, converter: Callable[[Any], T]) -> T:
    """Generic typed accessor: read key from [llm] config, convert, fall back to default."""
    raw = _read_config_file().get(key, None)
    try:
        return converter(raw) if raw is not None else default
    except (TypeError, ValueError):
        return default


def _get(key: str, default: str) -> str:
    return _get_typed(key, default, str) or default


def _get_int(key: str, default: int) -> int:
    return _get_typed(key, default, int)


# ── LLM backend ─────────────────────────────────────────────────────────────────────────────

def llm_backend() -> str:
    return _get("backend", "claude")


def llm_host() -> str:
    return _get("host", "http://localhost:8080")


def llm_model() -> str:
    return _get("model", "local")


def llm_timeout() -> int:
    return _get_int("timeout", 300)


# ── Bare subprocess settings (shared by health check and frontmatter) ─────────

def bare_session_timeout() -> int:
    """Timeout for claude -p bare subprocess calls (health check + frontmatter).

    Configure via [llm] bare_session_timeout in solid-coder-local.toml.
    Default: 300 seconds (5 minutes).
    """
    return _get_int("bare_session_timeout", 300)


def bare_session_model() -> str:
    """Model for claude -p bare subprocess calls (health check + frontmatter).

    Configure via [llm] bare_session_model in solid-coder-local.toml.
    Empty string (default) defers to the CLI default model.
    Set to e.g. 'claude-sonnet-4-5' to pin both subprocesses to the same model
    and prevent divergence caused by context inheritance differences.
    """
    return _get("bare_session_model", "")


# ── Hook exclusions ──────────────────────────────────────────────────────────────────────────────

def hook_exclude_patterns(hook: str) -> list:
    """Return the exclude glob patterns for a named hook.

    Reads [hooks.<hook>].exclude from the project config, e.g.:

        [hooks.pre_write_gate]
        exclude = ["tests/fixtures/**"]

    Returns an empty list when the section or key is absent.
    """
    return list(_read_section("hooks").get(hook, {}).get("exclude", []))


# ── Inference ──────────────────────────────────────────────────────────────────────────────────

def _inference_get(cfg: dict, key: str, default: Any, converter: Callable) -> Any:
    try:
        return converter(cfg.get(key, default))
    except (TypeError, ValueError):
        return converter(default)


def inference_params() -> dict:
    """Return [inference] section defaults for per-request generation params."""
    cfg = _read_section("inference")
    get = _inference_get
    return {
        "temperature":    get(cfg, "temperature",    0,     float),
        "top_k":          get(cfg, "top_k",          20,    int),
        "top_p":          get(cfg, "top_p",          0.95,  float),
        "min_p":          get(cfg, "min_p",          0.05,  float),
        "repeat_penalty": get(cfg, "repeat_penalty", 1.1,   float),
        "max_tokens":     get(cfg, "max_tokens",     4096,  int),
    }
