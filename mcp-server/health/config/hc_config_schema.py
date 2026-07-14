"""
solid-description: Loads, merges, and validates configuration from multiple sources.
solid-category: service
solid-tags: [hook, config]
"""

import sys
from pathlib import Path
from typing import Optional

_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from pydantic import ValidationError

from hc_config_core import read_llm_section, read_section
from solid_coder_config import SolidCoderConfig
from solid_coder_config_error import SolidCoderConfigError


def load_config(cwd: Optional[Path] = None) -> SolidCoderConfig:
    """Load, merge, and validate config.toml + config.local.toml.

    Raises SolidCoderConfigError with a field-level message on any unknown
    key or type mismatch — mistakes surface immediately instead of silently
    falling back to a default.
    """
    raw = {
        "llm": read_llm_section(_cwd=cwd),
        "hooks": read_section("hooks", _cwd=cwd),
        "inference": read_section("inference", _cwd=cwd),
        "server": read_section("server", _cwd=cwd),
    }
    try:
        return SolidCoderConfig.model_validate(raw)
    except ValidationError as exc:
        raise SolidCoderConfigError(str(exc)) from exc