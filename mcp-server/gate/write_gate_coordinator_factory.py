"""Constructs write-gate coordinators."""

import re
from pathlib import Path
from typing import Optional

from callable_file_name_resolver import CallableFileNameResolver
from callable_frontmatter_description_detector import (
    CallableFrontmatterDescriptionDetector,
)
from code_health_check_adapter import CodeHealthCheckAdapter
from content_simulator import ContentSimulator
from content_simulator_registration import ContentSimulatorRegistration
from coordinator_making import CoordinatorMaking
from coordinator_running import CoordinatorRunning
from diff_chunker_factory import DiffChunkerFactory
from edit_classifier import EditClassifier
from edit_content_simulator import EditContentSimulator
from frontmatter_adapter import FrontmatterAdapter
from gate_handling import GateHandling
from path_file_system_reader import PathFileSystemReader
from patch_review_context import PatchReviewContext
from write_content_simulator import WriteContentSimulator
from write_gate_coordinator import WriteGateCoordinator


"""
solid-name: WriteGateCoordinatorFactory
solid-category: factory
solid-description: Prepares write operations for health and metadata validation.
solid-tags: [hook]
"""
class WriteGateCoordinatorFactory(CoordinatorMaking):
    def make_coordinator(
        self,
        gate: GateHandling,
        patch_context: Optional[PatchReviewContext] = None,
    ) -> CoordinatorRunning:
        import code_health_check as health
        import validate_swift_frontmatter as frontmatter
        from hc_violation_parser import ViolationParser
        from safe_frontmatter_fixer import SafeFrontmatterFixer
        from safe_health_checker import SafeHealthChecker
        from tool_input_updater import ToolInputUpdater

        classifier = EditClassifier()
        reader = PathFileSystemReader()
        simulator = ContentSimulator(registrations=[
            ContentSimulatorRegistration(
                tool_name="Write",
                simulator=WriteContentSimulator(
                    file_reader=reader,
                    classifier=classifier,
                    chunker=DiffChunkerFactory().make(),
                ),
            ),
            ContentSimulatorRegistration(
                tool_name="Edit",
                simulator=EditContentSimulator(
                    file_reader=reader,
                    classifier=classifier,
                ),
            ),
        ])
        return WriteGateCoordinator(
            health_gate=SafeHealthChecker(
                checker=CodeHealthCheckAdapter(
                    check_fn=health._check,
                    patch_context=patch_context,
                ),
                formatter=ViolationParser(),
            ),
            frontmatter_gate=SafeFrontmatterFixer(
                fixer=FrontmatterAdapter(fix_fn=frontmatter.fix),
            ),
            simulator=simulator,
            gate=gate,
            input_updater=ToolInputUpdater(),
            file_name_resolver=CallableFileNameResolver(
                lambda file_path: Path(file_path).name
            ),
            frontmatter_detector=CallableFrontmatterDescriptionDetector(
                lambda content: re.search(
                    r"^\s*solid-description:\s*\S",
                    content,
                    re.MULTILINE,
                ) is not None
            ),
        )
