"""Constructs the pre-write gate orchestrator."""

from pathlib import Path

from apply_patch_content_simulator_factory import ApplyPatchContentSimulatorFactory
from apply_patch_request_handler import ApplyPatchRequestHandler
from apply_patch_reviewer_factory import ApplyPatchReviewerFactory
from coordinator_making import CoordinatorMaking
from default_exclusion_checker_factory import DefaultExclusionCheckerFactory
from default_guard_factory import DefaultGuardFactory
from default_hook_event_parser import DefaultHookEventParser
from dict_extension_lookup import DictExtensionLookup
from gate_handling import GateHandling
from gate_orchestrator import GateOrchestrator
from gate_request_router import GateRequestRouter
from pathlib_extractor import PathlibExtractor
from standard_write_request_handler import StandardWriteRequestHandler


"""
solid-name: GateOrchestratorFactory
solid-category: factory
solid-description: Creates pre-write gate orchestrators that route eligible tool operations.
solid-tags: [hook]
"""
class GateOrchestratorFactory:
    def __init__(
        self,
        guard_factory: DefaultGuardFactory,
        exclusion_checker_factory: DefaultExclusionCheckerFactory,
        patch_simulator_factory: ApplyPatchContentSimulatorFactory,
        patch_reviewer_factory: ApplyPatchReviewerFactory,
    ) -> None:
        self._guard_factory = guard_factory
        self._exclusion_checker_factory = exclusion_checker_factory
        self._patch_simulator_factory = patch_simulator_factory
        self._patch_reviewer_factory = patch_reviewer_factory

    def create(
        self,
        gate: GateHandling,
        coordinator_maker: CoordinatorMaking,
    ) -> GateOrchestrator:
        import code_health_check as health
        from hook_utils import parse_hook_event

        extension_lookup = DictExtensionLookup(health.SUPPORTED_EXTENSIONS)
        extension_extractor = PathlibExtractor(lambda path: Path(path).suffix.lower())
        exclusion_checker = self._exclusion_checker_factory.create()
        patch_reviewer = self._patch_reviewer_factory.create(
            simulator=self._patch_simulator_factory.create(),
            extension_lookup=extension_lookup,
            extension_extractor=extension_extractor,
            exclusion_checker=exclusion_checker,
            coordinator_maker=coordinator_maker,
            gate=gate,
        )
        return GateOrchestrator(
            gate=gate,
            guard=self._guard_factory.create(),
            event_parser=DefaultHookEventParser(parse_hook_event),
            request_router=GateRequestRouter(
                handlers={
                    "apply_patch": ApplyPatchRequestHandler(
                        reviewer=patch_reviewer,
                        gate=gate,
                    ),
                },
                fallback=StandardWriteRequestHandler(
                    gate=gate,
                    extension_lookup=extension_lookup,
                    extension_extractor=extension_extractor,
                    exclusion_checker=exclusion_checker,
                    coordinator_maker=coordinator_maker,
                ),
            ),
        )
