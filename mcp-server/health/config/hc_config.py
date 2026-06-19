"""
solid-description: Provides unified access to hook configuration settings.
solid-category: utility
solid-tags: [hook]
"""

import sys
from pathlib import Path
_HOOKS_DIR = Path(__file__).resolve().parents[3] / 'hooks'
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hc_config_llm import (  # noqa: F401
    bare_session_model,
    bare_session_timeout,
    codex_home,
    debug_mode,
    llm_backend,
    llm_host,
    llm_model,
    llm_timeout,
)
from hc_config_hooks import hook_exclude_patterns  # noqa: F401
from hc_config_inference import inference_params  # noqa: F401
