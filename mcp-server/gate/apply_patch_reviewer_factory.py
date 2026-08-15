"""Constructs apply-patch reviewers."""

from apply_patch_reviewer import ApplyPatchReviewer
from apply_patch_reviewing import ApplyPatchReviewing
from concurrent_handler_executor import ConcurrentHandlerExecutor
from coordinator_making import CoordinatorMaking
from decision_gate_factory import DecisionGateFactory
from exclusion_checking import ExclusionChecking
from extension_lookup import ExtensionLookup
from file_extension_extracting import FileExtensionExtracting
from gate_handling import GateHandling
from parallel_hook_dispatcher import ParallelHookDispatcher
from patch_file_handler_factory import PatchFileHandlerFactory
from patch_files_simulating import PatchFilesSimulating
from patch_handler_planner import PatchHandlerPlanner


"""
solid-name: ApplyPatchReviewerFactory
solid-category: factory
solid-description: Creates reviewers that evaluate all applicable files in a patch.
solid-tags: [hook]
"""
class ApplyPatchReviewerFactory:
    def create(
        self,
        simulator: PatchFilesSimulating,
        extension_lookup: ExtensionLookup,
        extension_extractor: FileExtensionExtracting,
        exclusion_checker: ExclusionChecking,
        coordinator_maker: CoordinatorMaking,
        gate: GateHandling,
    ) -> ApplyPatchReviewing:
        return ApplyPatchReviewer(
            planner=PatchHandlerPlanner(
                simulator=simulator,
                extension_lookup=extension_lookup,
                extension_extractor=extension_extractor,
                exclusion_checker=exclusion_checker,
                handler_factory=PatchFileHandlerFactory(
                    coordinator_maker=coordinator_maker,
                    gate_factory=DecisionGateFactory(),
                    logger=gate,
                ),
            ),
            dispatcher=lambda handlers, event: ParallelHookDispatcher(
                executor=ConcurrentHandlerExecutor(handlers=handlers),
            ).dispatch(event),
        )
