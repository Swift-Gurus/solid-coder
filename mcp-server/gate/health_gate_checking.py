"""
solid-description: Contract that defines checking content against validation rules.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Optional, Protocol

from hook_utils import GateHandling
from patch_review_context import PatchReviewContext


"""
solid-name: HealthGateChecking
solid-description: Contract for authorizing prospective source health before a write operation proceeds.
solid-category: abstraction
solid-tags: [hook]
"""
class HealthGateChecking(Protocol):
    def check(
        self,
        content: str,
        path: str,
        language: str,
        session_id: str,
        gate: GateHandling,
        file_name: str,
        cwd: str = "",
        patch_context: Optional[PatchReviewContext] = None,
    ) -> bool: ...
