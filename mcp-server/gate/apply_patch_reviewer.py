"""Reviews every applicable file represented by one apply_patch request."""

from handler_dispatching import HandlerDispatching
from hook_decision import HookDecision
from patch_handler_planning import PatchHandlerPlanning


"""
solid-name: ApplyPatchReviewer
solid-category: service
solid-description: Dispatches planned per-file reviews and returns their single aggregated authorization decision.
solid-tags: [hook]
"""
class ApplyPatchReviewer:
    def __init__(
        self,
        planner: PatchHandlerPlanning,
        dispatcher: HandlerDispatching,
    ) -> None:
        self._planner = planner
        self._dispatcher = dispatcher

    def review(
        self,
        tool_input: dict,
        session_id: str,
        cwd: str,
    ) -> HookDecision:
        return self._dispatcher(
            self._planner.plan(tool_input),
            {"session_id": session_id, "cwd": cwd},
        )
