"""
solid-description: Provides factory methods to create production-configured gate components.
solid-category: service
solid-tags: [hook]
"""

import os
from pathlib import Path
from typing import Optional

import sys
_HOOKS_DIR = Path(__file__).resolve().parents[1]
for _d in (_HOOKS_DIR, _HOOKS_DIR / "gate", _HOOKS_DIR / "patch"):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from api_key_guard import ApiKeyGuard
from apply_patch_content_simulator import ApplyPatchContentSimulator
from apply_patch_parser import ApplyPatchParser
from code_health_check_adapter import CodeHealthCheckAdapter
from content_simulator import ContentSimulator
from diff_chunker import DiffChunker
from edit_classifier import EditClassifier
from edit_content_simulator import EditContentSimulator
from frontmatter_adapter import FrontmatterAdapter
from gate_exclusion_checker import GateExclusionChecker
from hunk_applicator import HunkApplicator
from add_content_extractor import AddContentExtractor
from patch_format_parser import PatchFormatParser
from path_file_system_reader import PathFileSystemReader
from write_content_simulator import WriteContentSimulator
from write_gate_coordinator import WriteGateCoordinator


class DefaultCoordinatorFactory:
    """Factory: constructs WriteGateCoordinator with production-wired dependencies.

    OCP Factory exception: constructing, holding, and wiring concrete dependencies
    is inherently this class's job.
    """

    def make_guard(self) -> ApiKeyGuard:
        import hc_config as _hc
        return ApiKeyGuard(
            backend_fn=lambda: _hc.llm_backend(),
            api_key_fn=lambda: os.environ.get("ANTHROPIC_API_KEY", ""),
        )

    def make_exclusion_checker(self) -> GateExclusionChecker:
        import hc_config as _hc
        from hook_utils import path_matches_pattern
        return GateExclusionChecker(
            exclude_patterns_fn=lambda: _hc.hook_exclude_patterns("pre_write_gate"),
            path_matcher_fn=path_matches_pattern,
        )

    def make_patch_simulator(self) -> ApplyPatchContentSimulator:
        parser = ApplyPatchParser(
            format_parser=PatchFormatParser(),
            content_extractor=AddContentExtractor(),
            hunk_applicator=HunkApplicator(),
        )
        return ApplyPatchContentSimulator(parser=parser, file_reader=PathFileSystemReader())

    def make_orchestrator(self, gate) -> "GateOrchestrator":
        from gate_orchestrator import GateOrchestrator
        from dict_extension_lookup import DictExtensionLookup
        import code_health_check as health
        patch_sim = self.make_patch_simulator()
        return GateOrchestrator(
            gate=gate,
            guard=self.make_guard(),
            parse_fn=__import__('hook_utils').parse_hook_event,
            extension_lookup=DictExtensionLookup(health.SUPPORTED_EXTENSIONS),
            exclusion_checker=self.make_exclusion_checker(),
            patch_path_fn=patch_sim.first_file_path,
            coordinator_maker=self,
        )

    def make_coordinator(self, gate) -> WriteGateCoordinator:
        import code_health_check as health
        import validate_swift_frontmatter as frontmatter
        from hc_violation_parser import ViolationParser
        classifier = EditClassifier()
        reader = PathFileSystemReader()
        chunker = DiffChunker()
        simulator = ContentSimulator(handlers={
            "Write": WriteContentSimulator(file_reader=reader, classifier=classifier, chunker=chunker),
            "Edit": EditContentSimulator(file_reader=reader, classifier=classifier),
            "apply_patch": self.make_patch_simulator(),
        })
        from safe_health_checker import SafeHealthChecker
        from safe_frontmatter_fixer import SafeFrontmatterFixer
        violation_parser = ViolationParser()
        return WriteGateCoordinator(
            health_gate=SafeHealthChecker(
                checker=CodeHealthCheckAdapter(check_fn=health._check),
                formatter=violation_parser,
            ),
            frontmatter_gate=SafeFrontmatterFixer(
                fixer=FrontmatterAdapter(fix_fn=frontmatter.fix),
            ),
            simulator=simulator,
            gate=gate,
        )
