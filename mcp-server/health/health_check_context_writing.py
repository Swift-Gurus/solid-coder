"""
solid-description: Contract for persisting and clearing health check output.
solid-category: utility
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from typing import Optional, Protocol

from patch_review_context import PatchReviewContext


"""
solid-name: HealthCheckContextWriting
solid-description: Contract for persisting and clearing isolated prospective-review context.
solid-category: abstraction
solid-tags: [hook]
"""
class HealthCheckContextWriting(Protocol):
    def write(
        self,
        output_dir: str,
        file_path: str,
        language: str,
        content: str = "",
        patch_context: Optional[PatchReviewContext] = None,
    ) -> None: ...
    def clear(self) -> None: ...
