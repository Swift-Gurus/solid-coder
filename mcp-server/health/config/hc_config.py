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

from hc_config_schema import load_config  # noqa: F401
from hook_config import HookConfig  # noqa: F401
from inference_config import InferenceConfig  # noqa: F401
from llm_config import LlmConfig  # noqa: F401
from server_config import ServerConfig  # noqa: F401
from solid_coder_config import SolidCoderConfig  # noqa: F401
from solid_coder_config_error import SolidCoderConfigError  # noqa: F401
