"""
solid-description: Contract for creating a coordinator from a gate.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Optional, Protocol

from hook_utils import GateHandling
from coordinator_running import CoordinatorRunning
from patch_review_context import PatchReviewContext


"""
solid-name: CoordinatorMaking
solid-description: Contract for constructing a write coordinator with its prospective review context.
solid-category: abstraction
solid-tags: [hook]
"""
class CoordinatorMaking(Protocol):
    def make_coordinator(
        self,
        gate: GateHandling,
        patch_context: Optional[PatchReviewContext] = None,
    ) -> CoordinatorRunning: ...
