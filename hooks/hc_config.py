"""
solid-description: Provides project-scoped solid-coder runtime configuration values to hooks.
solid-category: utility
solid-tags: [hook]
"""

import os
import sys
from pathlib import Path
from typing import Optional

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from typing import Callable, Protocol

from hook_utils import load_toml

_FILENAME = "solid-coder-local.toml"


class TomlLoader(Protocol):
    def __call__(self, path: Path) -> dict: ...


def _find_config() -> Optional[Path]:
    """Return the project-level config path, or None if it does not exist.

    The hook subprocess runs from the user's project root, so
    {cwd}/.claude/solid-coder-local.toml is always project-scoped.
    Each project opts in explicitly — there is no plugin-level fallback.
    """
    path = Path.cwd() / ".claude" / _FILENAME
    return path if path.exists() else None


def _read_section(section: str, _loader: TomlLoader = load_toml) -> dict:
    path = _find_config()
    return _loader(path).get(section, {}) if path else {}


def _read_config_file(_loader: TomlLoader = load_toml) -> dict:
    override = os.environ.get("SOLID_CODER_TEST_MODEL_PROFILE")
    if override:
        return _loader(Path(override)).get("llm", {})
    return _read_section("llm", _loader=_loader)


def _get(key: str, default: str) -> str:
    return _read_config_file().get(key, "") or default


def llm_backend() -> str:
    return _get("backend", "claude")


def llm_host() -> str:
    return _get("host", "http://localhost:8080")


def llm_model() -> str:
    return _get("model", "local")


def llm_timeout() -> int:
    raw = _read_config_file().get("timeout", None)
    try:
        return int(raw) if raw is not None else 300
    except (TypeError, ValueError):
        return 300


def hook_exclude_patterns(hook: str) -> list:
    """Return the exclude glob patterns configured for a named hook.

    Reads [hooks.<hook>].exclude from the project config, e.g.:

        [hooks.pre_write_gate]
        exclude = ["tests/fixtures/**"]

    Returns an empty list when the section or key is absent.
    """
    return list(_read_section("hooks").get(hook, {}).get("exclude", []))


def inference_params() -> dict:
    """Return [inference] section defaults for per-request generation params."""
    cfg = _read_section("inference")
    return {
        "temperature": float(cfg.get("temperature", 0)),
        "top_k":       int(cfg.get("top_k", 20)),
        "top_p":       float(cfg.get("top_p", 0.95)),
        "min_p":       float(cfg.get("min_p", 0.05)),
        "repeat_penalty": float(cfg.get("repeat_penalty", 1.1)),
        "max_tokens":  int(cfg.get("max_tokens", 4096)),
    }

