"""Composes real cleanup capabilities for hook tests."""

import shutil
import sys

from cleanup_pipeline_output import PipelineOutputCleaner, _is_safe_path, _parse_output_roots
from hc_config_debug_reader import DebugModeReading
from pipeline_cleanup.pipeline_cleanup_handler import PipelineCleanupHandler
from pipeline_cleanup.pipeline_output_cleanup import PipelineOutputCleanup


"""
solid-name: PipelineOutputCleanerTestFactory
solid-category: test-support
solid-description: Provides pipeline cleanup hooks with real transcript and filesystem capabilities and controlled debug policy.
"""
class PipelineOutputCleanerTestFactory:
    def make(self, debug_reader: DebugModeReading) -> PipelineOutputCleaner:
        return PipelineOutputCleaner(handler=PipelineCleanupHandler(cleanup=PipelineOutputCleanup(
            debug_reader=debug_reader,
            roots_reader=_parse_output_roots,
            path_safety=_is_safe_path,
            remover=shutil.rmtree,
            diagnostics=sys.stderr,
        )))
