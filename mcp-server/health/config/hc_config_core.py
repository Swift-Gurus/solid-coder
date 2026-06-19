"""
solid-description: Provides access to project configuration with support for local overrides.
solid-category: utility
solid-tags: [hook]
"""

import os
import sys
from pathlib import Path
from typing import Any, Callable, Optional, Protocol, TypeVar

_HOOKS_DIR = Path(__file__).resolve().parents[3] / 'hooks'
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import load_toml  # noqa: E402
from solid_coder_paths import CONFIG_DIR, CONFIG_TOML, CONFIG_LOCAL_TOML  # noqa: E402

# Anchor to the project root (hooks/ parent) so configs are found regardless of cwd.
_PROJECT_ROOT = _HOOKS_DIR.parent
T = TypeVar("T")


class TomlLoader(Protocol):
    def __call__(self, path: Path) -> dict: ...


def find_config(_cwd: Optional[Path] = None) -> Optional[Path]:
    """Return the local (non-committed) config path, or None if absent."""
    base = _cwd if _cwd is not None else _PROJECT_ROOT
    path = base / CONFIG_DIR / CONFIG_LOCAL_TOML
    return path if path.exists() else None


def find_repo_config(_cwd: Optional[Path] = None) -> Optional[Path]:
    """Return the committed project config path, or None if absent."""
    base = _cwd if _cwd is not None else _PROJECT_ROOT
    path = base / CONFIG_DIR / CONFIG_TOML
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
    effective_cwd = _cwd
    if effective_cwd is None:
        # Claude Code sets CLAUDE_PROJECT_DIR; Codex hook processes run in cwd
        project_dir = env.get("CLAUDE_PROJECT_DIR", "")
        effective_cwd = Path(project_dir) if project_dir else Path.cwd()
    return read_section("llm", _loader=_loader, _cwd=effective_cwd)


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
