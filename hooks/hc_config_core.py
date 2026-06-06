"""
solid-description: Provides configuration access with type-safe conversion.
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
# Anchor to the project root (hooks/ parent) so the config is found regardless of cwd.
_PROJECT_ROOT = _HOOKS_DIR.parent
T = TypeVar("T")


class TomlLoader(Protocol):
    def __call__(self, path: Path) -> dict: ...


def find_config(_cwd: Optional[Path] = None) -> Optional[Path]:
    """Return the project-level config path, or None if it does not exist.

    Searches _cwd when provided, otherwise uses _PROJECT_ROOT (the parent of the
    hooks/ directory) so the config is always found regardless of the process's
    working directory at hook invocation time.
    """
    base = _cwd if _cwd is not None else _PROJECT_ROOT
    path = base / ".claude" / _FILENAME
    return path if path.exists() else None


def read_section(
    section: str,
    _loader: TomlLoader = load_toml,
    _cwd: Optional[Path] = None,
) -> dict:
    path = find_config(_cwd=_cwd)
    return _loader(path).get(section, {}) if path else {}


def read_llm_section(
    _loader: TomlLoader = load_toml,
    _env: Optional[dict] = None,
    _cwd: Optional[Path] = None,
) -> dict:
    env = _env if _env is not None else os.environ
    override = env.get("SOLID_CODER_TEST_MODEL_PROFILE")
    if override:
        return _loader(Path(override)).get("llm", {})
    return read_section("llm", _loader=_loader, _cwd=_cwd)


def safe_convert(value: Any, default: T, converter: Callable[[Any], T]) -> T:
    """Apply converter to value, returning default on None input or conversion failure."""
    try:
        return converter(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def llm_value(
    key: str,
    default: T,
    converter: Callable[[Any], T],
    _loader: TomlLoader = load_toml,
    _env: Optional[dict] = None,
    _cwd: Optional[Path] = None,
) -> T:
    """Read a typed value from the [llm] section of the project config."""
    return safe_convert(
        read_llm_section(_loader=_loader, _env=_env, _cwd=_cwd).get(key),
        default,
        converter,
    )