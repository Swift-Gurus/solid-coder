"""Provides the write-gate construction facade."""

from coordinator_making import CoordinatorMaking
from coordinator_running import CoordinatorRunning
from gate_handling import GateHandling
from gate_orchestrator import GateOrchestrator
from gate_orchestrator_factory import GateOrchestratorFactory


"""
solid-name: DefaultCoordinatorFactory
solid-category: facade
solid-description: Coordinates creation of write-gate coordinator and orchestrator products.
solid-tags: [hook]
"""
class DefaultCoordinatorFactory:
    def __init__(
        self,
        coordinator_factory: CoordinatorMaking,
        orchestrator_factory: GateOrchestratorFactory,
    ) -> None:
        self._coordinator_factory = coordinator_factory
        self._orchestrator_factory = orchestrator_factory

    def make_coordinator(self, gate: GateHandling) -> CoordinatorRunning:
        return self._coordinator_factory.make_coordinator(gate)

    def make_orchestrator(self, gate: GateHandling) -> GateOrchestrator:
        return self._orchestrator_factory.create(gate, self)
