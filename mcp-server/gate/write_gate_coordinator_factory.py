"""Constructs write-gate coordinators."""

from apply_patch_content_simulator_factory import ApplyPatchContentSimulatorFactory
from code_health_check_adapter import CodeHealthCheckAdapter
from content_simulator import ContentSimulator
from coordinator_running import CoordinatorRunning
from diff_chunker import DiffChunker
from edit_classifier import EditClassifier
from edit_content_simulator import EditContentSimulator
from frontmatter_adapter import FrontmatterAdapter
from gate_handling import GateHandling
from path_file_system_reader import PathFileSystemReader
from write_content_simulator import WriteContentSimulator
from write_gate_coordinator import WriteGateCoordinator


"""
solid-name: WriteGateCoordinatorFactory
solid-category: factory
solid-description: Prepares write operations for health and metadata validation.
solid-tags: [hook]
"""
class WriteGateCoordinatorFactory:
    def __init__(
        self,
        patch_simulator_factory: ApplyPatchContentSimulatorFactory,
    ) -> None:
        self._patch_simulator_factory = patch_simulator_factory

    def make_coordinator(self, gate: GateHandling) -> CoordinatorRunning:
        import code_health_check as health
        import validate_swift_frontmatter as frontmatter
        from hc_violation_parser import ViolationParser
        from safe_frontmatter_fixer import SafeFrontmatterFixer
        from safe_health_checker import SafeHealthChecker
        from tool_input_updater import ToolInputUpdater

        classifier = EditClassifier()
        reader = PathFileSystemReader()
        simulator = ContentSimulator(handlers={
            "Write": WriteContentSimulator(
                file_reader=reader,
                classifier=classifier,
                chunker=DiffChunker(),
            ),
            "Edit": EditContentSimulator(
                file_reader=reader,
                classifier=classifier,
            ),
            "apply_patch": self._patch_simulator_factory.create(),
        })
        return WriteGateCoordinator(
            health_gate=SafeHealthChecker(
                checker=CodeHealthCheckAdapter(check_fn=health._check),
                formatter=ViolationParser(),
            ),
            frontmatter_gate=SafeFrontmatterFixer(
                fixer=FrontmatterAdapter(fix_fn=frontmatter.fix),
            ),
            simulator=simulator,
            gate=gate,
            input_updater=ToolInputUpdater(),
        )
