#!/usr/bin/env python3
"""
solid-description: Removes temporary pipeline output directories.
solid-category: hook

Parses the session transcript for get_output_path MCP tool results and
deletes each returned output_root directory, unless debug_mode() is true.
Only paths under ~/.solid-coder/ are eligible for deletion.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from flow_transition_handler import FlowStopApplicabilityChecking
from harness.structured_model_decoding import StructuredModelDecoding
from hc_config import SolidCoderConfigLoader
from hc_config_debug_reader import HcConfigDebugReader
from pipeline_cleanup.pipeline_cleanup_applicability_checker import PipelineCleanupApplicabilityChecker
from pipeline_cleanup.pipeline_cleanup_handler import PipelineCleanupHandler, PipelineCleanupHandling
from pipeline_cleanup.pipeline_output_cleanup import PipelineOutputCleanup
from transcript_content.tool_result_output_root_decoder import ToolResultOutputRootDecoder

_SAFE_ROOT = Path.home() / ".solid-coder"


def _parse_output_roots(
    transcript_path: str,
    output_decoder: StructuredModelDecoding[str] = ToolResultOutputRootDecoder(),
) -> list[str]:
    """Return deduplicated output_root paths from get_output_path results in the transcript."""
    seen: set = set()
    roots: list = []
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    if obj.get("type") != "user":
                        continue
                    for block in obj.get("message", {}).get("content", []):
                        if block.get("type") != "tool_result":
                            continue
                        root = output_decoder.decode(block.get("content", ""), "transcript tool result")
                        if root and root not in seen:
                            seen.add(root)
                            roots.append(root)
                except (json.JSONDecodeError, ValueError):
                    pass
    except OSError:
        pass
    return roots


def _is_safe_path(path: str) -> bool:
    """Return True only if path is under ~/.solid-coder/."""
    try:
        return Path(path).is_relative_to(_SAFE_ROOT)
    except (ValueError, TypeError):
        return False


"""
solid-name: PipelineOutputCleaner
solid-category: service
solid-description: Coordinates pipeline-output cleanup for eligible host stop events.
"""
class PipelineOutputCleaner:
    """StopHandler — deletes pipeline output directories after each turn."""

    def __init__(
        self,
        applicability: FlowStopApplicabilityChecking = PipelineCleanupApplicabilityChecker(),
        handler: PipelineCleanupHandling = PipelineCleanupHandler(
            cleanup=PipelineOutputCleanup(
                debug_reader=HcConfigDebugReader(SolidCoderConfigLoader()),
                roots_reader=_parse_output_roots,
                path_safety=_is_safe_path,
                remover=shutil.rmtree,
                diagnostics=sys.stderr,
            ),
        ),
    ) -> None:
        self._applicability = applicability
        self._handler = handler

    def should_handle(self, event: dict) -> bool:
        return self._applicability.applies(event)

    def handle(self, event: dict) -> None:
        return self._handler.handle(event)
