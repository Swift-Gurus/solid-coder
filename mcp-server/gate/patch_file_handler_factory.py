"""Constructs isolated handlers for simulated patch files."""

from coordinator_making import CoordinatorMaking
from decision_gate_creating import DecisionGateCreating
from hook_handling import HookHandling
from logging_protocol import Logging
from patch_file_gate_handler import PatchFileGateHandler
from patch_file_simulation import PatchFileSimulation
from patch_review_context import PatchReviewContext


"""
solid-name: PatchFileHandlerFactory
solid-category: factory
solid-description: Constructs one isolated write-gate handler for each simulated patch file.
solid-tags: [hook]
"""
class PatchFileHandlerFactory:
    def __init__(
        self,
        coordinator_maker: CoordinatorMaking,
        gate_factory: DecisionGateCreating,
        logger: Logging,
    ) -> None:
        self._coordinator_maker = coordinator_maker
        self._gate_factory = gate_factory
        self._logger = logger

    def create(
        self,
        simulation: PatchFileSimulation,
        language: str,
        context: PatchReviewContext,
    ) -> HookHandling:
        return PatchFileGateHandler(
            simulation=simulation,
            language=language,
            context=context,
            coordinator_maker=self._coordinator_maker,
            gate_factory=self._gate_factory,
            logger=self._logger,
        )
