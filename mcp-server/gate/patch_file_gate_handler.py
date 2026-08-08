"""Reviews one simulated patch file through the existing write-gate coordinator."""

from coordinator_making import CoordinatorMaking
from decision_gate_creating import DecisionGateCreating
from hook_decision import HookDecision
from hook_decision_creating import HookDecisionCreating
from logging_protocol import Logging
from patch_file_simulation import PatchFileSimulation


"""
solid-name: PatchFileGateHandler
solid-category: service
solid-description: Evaluates one simulated file change and returns its isolated authorization decision.
solid-tags: [hook]
"""
class PatchFileGateHandler:
    def __init__(
        self,
        simulation: PatchFileSimulation,
        language: str,
        coordinator_maker: CoordinatorMaking,
        gate_factory: DecisionGateCreating,
        decision_factory: HookDecisionCreating,
        logger: Logging,
    ) -> None:
        self._simulation = simulation
        self._language = language
        self._coordinator_maker = coordinator_maker
        self._gate_factory = gate_factory
        self._decision_factory = decision_factory
        self._logger = logger

    def should_handle(self, event: dict) -> bool:
        return True

    def handle(self, event: dict) -> HookDecision:
        gate = self._gate_factory.create(self._logger)
        self._coordinator_maker.make_coordinator(gate).run(
            tool_name="Write",
            tool_input={
                "file_path": self._simulation.file_path,
                "content": self._simulation.content,
            },
            file_path=self._simulation.file_path,
            language=self._language,
            session_id=event.get("session_id", ""),
            cwd=event.get("cwd", ""),
        )
        decision = gate.decision
        if decision.allow or not decision.reason:
            return decision
        return self._decision_factory.create(
            allow=False,
            reason=f"{self._simulation.file_path}:\n{decision.reason}",
            additional_context=decision.additional_context,
        )
