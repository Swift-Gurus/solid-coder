"""
solid-name: ParallelHookDispatcher
solid-category: service
solid-description: Executes hooks for an event and combines their decisions into a unified result.
solid-tags: [hook]
"""

from handler_executing import HandlerExecuting
from hook_decision import HookDecision
from hook_decision_aggregating import DecisionAggregating
from hook_decision_aggregator import HookDecisionAggregator


class ParallelHookDispatcher:
    def __init__(
        self,
        executor: HandlerExecuting,
        aggregator: DecisionAggregating = HookDecisionAggregator(),
    ) -> None:
        self._executor = executor
        self._aggregator = aggregator

    def dispatch(self, event: dict) -> HookDecision:
        decisions = self._executor.run(event)
        return self._aggregator.aggregate(decisions)