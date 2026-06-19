"""
solid-description: Utility for writing output to a file based on language.
solid-category: utility
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = _HEALTH_DIR.parents[1] / 'hooks'
for _d in (_HOOKS_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from typing import Protocol


class HealthCheckContextWriting(Protocol):
    def write(self, output_dir: str, file_path: str, language: str) -> None: ...
