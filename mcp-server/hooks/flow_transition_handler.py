"""
solid-name: FlowTransitionHandler
solid-category: service
solid-description: Determines whether a flow transition is permitted based on current flow state.
solid-tags: [hook]
"""

import sys
from pathlib import Path
from typing import Protocol

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from hook_decision import HookDecision  # noqa: E402
from hook_handling import HookHandling  # noqa: E402
from flow_transition_evaluating import FlowTransitionGate  # noqa: E402


class FlowStopApplicabilityChecking(Protocol):
    def applies(self, event: dict) -> bool: ...


class FlowStopEvaluating(Protocol):
    def evaluate_stop(self, event: dict) -> HookDecision: ...


class FlowStopApplicabilityChecker(FlowStopApplicabilityChecking):
    """A flow run is only evaluated on a fresh stop attempt, not a re-entrant one."""

    def applies(self, event: dict) -> bool:
        return not event.get("stop_hook_active")


class FlowStopEvaluator(FlowStopEvaluating):
    """Evaluates the current flow run exactly once per call and turns the result into a HookDecision."""

    def __init__(self, gate: FlowTransitionGate) -> None:
        self._gate = gate

    def evaluate_stop(self, event: dict) -> HookDecision:
        result = self._gate.evaluate()
        if not result.get("allow", True):
            return HookDecision(allow=False, reason=result.get("reason", "Flow run left in_progress."))
        return HookDecision(allow=True)


class FlowTransitionHandler(HookHandling):
    """Coordination facade: filters via applicability, then delegates to the evaluator."""

    def __init__(self, evaluator: FlowStopEvaluating, applicability: FlowStopApplicabilityChecking = FlowStopApplicabilityChecker()) -> None:
        self._applicability = applicability
        self._evaluator = evaluator

    def should_handle(self, event: dict) -> bool:
        return self._applicability.applies(event)

    def handle(self, event: dict) -> HookDecision:
        return self._evaluator.evaluate_stop(event)
