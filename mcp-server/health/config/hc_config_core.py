"""
solid-description: Provides access to effective project configuration settings.
solid-category: utility
solid-tags: [hook]
"""

import os
import sys
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol, TypeVar

_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from harness.flow_validation_error import FlowValidationError
from harness.pydantic_model_decoder import PydanticModelDecoder
from harness.structured_model_decoding import StructuredModelDecoding
from scoring.config_merger import ConfigMerger, ConfigMerging
from scoring.parent_chain import parent_chain
from solid_coder_config import SolidCoderConfig
from solid_coder_config_error import SolidCoderConfigError
from solid_coder_paths import CONFIG_DIR, CONFIG_LOCAL_TOML, CONFIG_TOML
from toml_root_values import TomlRootValues
from utils.debug_logger import Observing

# Anchor to the project root (hooks/ parent) so configs are found regardless of cwd.
_PROJECT_ROOT = _MCP_DIR.parent
T = TypeVar("T")


"""
solid-name: TomlLoader
solid-category: abstraction
solid-description: Contract for retrieving configuration values.
"""


class TomlLoader(Protocol):
    def __call__(self, path: Path) -> dict: ...


def _find_config_file(filename: str, _cwd: Path | None = None) -> Path | None:
    base = _cwd if _cwd is not None else _PROJECT_ROOT
    path = base / CONFIG_DIR / filename
    return path if path.exists() else None


def find_config(_cwd: Path | None = None) -> Path | None:
    """Return the local (non-committed) config path, or None if absent."""
    return _find_config_file(CONFIG_LOCAL_TOML, _cwd=_cwd)


def find_repo_config(_cwd: Path | None = None) -> Path | None:
    """Return the committed project config path, or None if absent."""
    preferred = _find_config_file(CONFIG_TOML, _cwd=_cwd)
    base = _cwd if _cwd is not None else _PROJECT_ROOT
    alternate = base / ".config" / "solid.coder" / CONFIG_TOML
    return (
        preferred
        if preferred is not None
        else (alternate if alternate.exists() else None)
    )


def find_user_config(home: Path) -> Path | None:
    for candidate in (
        home / ".config" / "solid-coder" / CONFIG_TOML,
        home / CONFIG_DIR / CONFIG_TOML,
    ):
        if candidate.exists():
            return candidate
    return None


def find_repository_root(cwd: Path) -> Path | None:
    return next(
        (
            directory
            for directory in parent_chain(cwd.resolve())
            if (directory / ".git").exists()
        ),
        None,
    )


def _resolve_project_cwd(_env: dict | None = None, _cwd: Path | None = None) -> Path:
    """Resolve the effective project directory: explicit cwd, else CLAUDE_PROJECT_DIR, else process cwd."""
    if _cwd is not None:
        return _cwd
    env = _env if _env is not None else os.environ
    # Claude Code sets CLAUDE_PROJECT_DIR; Codex hook processes run in cwd
    project_dir = env.get("CLAUDE_PROJECT_DIR", "")
    return Path(project_dir) if project_dir else Path.cwd()


_DEFAULT_MERGER: ConfigMerging = ConfigMerger()
_CONFIG_DECODER: StructuredModelDecoding[SolidCoderConfig] = PydanticModelDecoder(
    SolidCoderConfig
)


def load_selected_toml(
    path: Path,
    decoder: StructuredModelDecoding[SolidCoderConfig] = _CONFIG_DECODER,
) -> dict:
    try:
        with path.open("rb") as stream:
            values = tomllib.load(stream)
        decoder.decode(values, f"configuration '{path}'")
        return values
    except (OSError, ValueError, FlowValidationError) as error:
        raise SolidCoderConfigError(
            f"Invalid configuration '{path}': {error}"
        ) from error


def _read_with_overrides(
    extract: Callable[[dict], dict],
    _loader: TomlLoader = load_selected_toml,
    _cwd: Path | None = None,
    _merger: ConfigMerging = _DEFAULT_MERGER,
) -> dict:
    """Merge root-to-leaf project settings, stopping at the nearest Git boundary."""
    effective_cwd = _resolve_project_cwd(_cwd=_cwd).resolve()
    root = find_repository_root(effective_cwd)
    directories: list[Path] = []
    for directory in parent_chain(effective_cwd):
        directories.append(directory)
        if root is None or directory == root:
            break

    merged: dict = {}
    user_config = find_user_config(Path.home())
    if user_config is not None:
        merged = extract(_loader(user_config))
    for directory in reversed(directories):
        for config_path in (
            find_repo_config(_cwd=directory),
            find_config(_cwd=directory),
        ):
            if config_path is not None:
                merged = _merger.merge(merged, extract(_loader(config_path)))
    return merged


def read_section(
    section: str,
    _loader: TomlLoader = load_selected_toml,
    _cwd: Path | None = None,
) -> dict:
    """Read a config section, merging repo defaults under local overrides."""
    return _read_with_overrides(
        lambda data: data.get(section, {}), _loader=_loader, _cwd=_cwd
    )


def read_root_section(
    _loader: TomlLoader = load_selected_toml,
    _cwd: Path | None = None,
) -> dict:
    """Read top-level scalar keys (not [table] sections), merging repo defaults under local overrides."""
    return _read_with_overrides(
        lambda data: TomlRootValues.model_validate(data).model_dump(),
        _loader=_loader,
        _cwd=_cwd,
    )


@Observing("config.read_llm_section")
def read_llm_section(
    _loader: TomlLoader = load_selected_toml,
    _env: dict | None = None,
    _cwd: Path | None = None,
) -> dict:
    env = _env if _env is not None else os.environ
    override = env.get("SOLID_CODER_TEST_MODEL_PROFILE")
    if override:
        return _loader(Path(override)).get("llm", {})
    return read_section(
        "llm", _loader=_loader, _cwd=_resolve_project_cwd(_env=env, _cwd=_cwd)
    )


def safe_convert(value: Any, default: T, converter: Callable[[Any], T]) -> T:
    """Apply converter to value, returning default on None input or conversion failure."""
    try:
        return converter(value) if value is not None else default
    except (TypeError, ValueError):
        return default


@Observing("config.llm_value")
def llm_value(
    key: str,
    default: T,
    converter: Callable[[Any], T],
    _loader: TomlLoader = load_selected_toml,
    _env: dict | None = None,
    _cwd: Path | None = None,
) -> T:
    """Read a typed value from the [llm] section of the project config."""
    return safe_convert(
        read_llm_section(_loader=_loader, _env=_env, _cwd=_cwd).get(key),
        default,
        converter,
    )
