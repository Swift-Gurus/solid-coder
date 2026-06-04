"""
solid-description: Provides LLM inference generation parameters with default values.
solid-category: utility
solid-tags: [hook]
"""

import sys
from pathlib import Path
from typing import Any, Callable

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hc_config_core import read_section, safe_convert  # noqa: E402


def inference_params() -> dict:
    """Return [inference] section defaults for per-request generation params."""
    cfg = read_section("inference")

    def get(key: str, default: Any, converter: Callable) -> Any:
        return safe_convert(cfg.get(key, default), default, converter)

    return {
        "temperature":    get("temperature",    0,     float),
        "top_k":          get("top_k",          20,    int),
        "top_p":          get("top_p",          0.95,  float),
        "min_p":          get("min_p",          0.05,  float),
        "repeat_penalty": get("repeat_penalty", 1.1,   float),
        "max_tokens":     get("max_tokens",     4096,  int),
    }