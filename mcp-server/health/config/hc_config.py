"""
solid-description: Centralizes configuration types and utilities.
solid-category: utility
solid-tags: [hook]
"""

import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_config import HookConfig
from inference_config import InferenceConfig
from llm_config import LlmConfig
from server_config import ServerConfig
from solid_coder_config import SolidCoderConfig
from solid_coder_config_error import SolidCoderConfigError
from solid_coder_config_loader import SolidCoderConfigLoader

__all__ = [
    "HookConfig",
    "InferenceConfig",
    "LlmConfig",
    "ServerConfig",
    "SolidCoderConfig",
    "SolidCoderConfigError",
    "SolidCoderConfigLoader",
]
