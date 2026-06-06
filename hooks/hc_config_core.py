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

_FILENAME_LOCAL = "solid-coder-local.toml"   # not committed — secrets, per-user overrides
_FILENAME_REPO  = "solid-coder.toml"          # committed — shared project defaults
# Anchor to the project root (hooks/ parent) so configs are found regardless of cwd.
_PROJECT_ROOT = _HOOKS_DIR.parent
T = TypeVar("T")


class TomlLoader(Protocol):
    def __call__(self, path: Path) -> dict: ...


def find_config(_cwd: Optional[Path] = None) -> Optional[Path]:
    """Return the local (non-committed) config path, or None if absent.

    Uses _PROJECT_ROOT when _cwd is not provided so the file is always located
    regardless of the process working directory at hook invocation time.
    """
    base = _cwd if _cwd is not None else _PROJECT_ROOT
    path = base / ".claude" / _FILENAME_LOCAL
    return path if path.exists() else None


def find_repo_config(_cwd: Optional[Path] = None) -> Optional[Path]:
    """Return the committed project config path, or None if absent."""
    base = _cwd if _cwd is not None else _PROJECT_ROOT
    path = base / ".claude" / _FILENAME_REPO
    return path if path.exists() else None


def read_section(
    section: str,
    _loader: TomlLoader = load_toml,
    _cwd: Optional[Path] = None,
) -> dict:
    """Read a config section, merging repo defaults under local overrides."""
    repo_path = find_repo_config(_cwd=_cwd)
    local_path = find_config(_cwd=_cwd)
    base = _loader(repo_path).get(section, {}) if repo_path else {}
    override = _loader(local_path).get(section, {}) if local_path else {}
    return {**base, **override}


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