"""
solid-description: Provides runtime LLM configuration settings, allowing environment variables to override project-level defaults.
solid-category: utility
solid-tags: [hook]
"""

import os
import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import PLUGIN_ROOT

_CONFIG_PATH = PLUGIN_ROOT / ".claude" / "solid-coder-local.toml"


def _load_toml(path: Path) -> dict:
    """Parse a TOML file using tomllib (3.11+), tomli backport, or return {} on failure."""
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        return {}


def _read_config_file() -> dict:
    """Return the [llm] section from the config file, or {} if absent/unparseable."""
    if not _CONFIG_PATH.exists():
        return {}
    return _load_toml(_CONFIG_PATH).get("llm", {})


def _resolve(env_var: str, config_key: str, default: str) -> str:
    """Resolve a setting: env var > config file > default."""
    return (
        os.environ.get(env_var)
        or _read_config_file().get(config_key, "")
        or default
    )


def llm_backend() -> str:
    return _resolve("SOLID_CODER_LLM_BACKEND", "backend", "claude")


def llm_host() -> str:
    return _resolve("SOLID_CODER_LLM_HOST", "host", "http://localhost:8080")


def llm_model() -> str:
    return _resolve("SOLID_CODER_LLM_MODEL", "model", "local")
