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
from typing import Callable, Protocol, runtime_checkable

_SAFE_ROOT = Path.home() / ".solid-coder"


@runtime_checkable
class DebugModeReading(Protocol):
    def is_debug(self) -> bool: ...


class HcConfigDebugReader:
    """Reads debug mode from hc_config.load_config().llm.debug."""

    def is_debug(self) -> bool:
        import hc_config  # noqa: PLC0415
        return hc_config.load_config().llm.debug


def _extract_output_root(content) -> str:
    """Extract output_root value from a tool_result content field."""
    text = ""
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                text = block.get("text", "")
                break
    try:
        data = json.loads(text)
        if isinstance(data, dict):
            return data.get("output_root", "")
    except (json.JSONDecodeError, ValueError, TypeError):
        pass
    return ""


def _parse_output_roots(transcript_path: str) -> list:
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
                        root = _extract_output_root(block.get("content", ""))
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


class PipelineOutputCleaner:
    """StopHandler — deletes pipeline output directories after each turn."""

    def __init__(self, debug_reader: DebugModeReading | None = None) -> None:
        self._debug_reader = debug_reader if debug_reader is not None else HcConfigDebugReader()

    def should_handle(self, event: dict) -> bool:
        return bool(event.get("transcript_path", ""))

    def handle(self, event: dict) -> None:
        if self._debug_reader.is_debug():
            return
        for root in _parse_output_roots(event.get("transcript_path", "")):
            if _is_safe_path(root):
                shutil.rmtree(root, ignore_errors=True)
            else:
                sys.stderr.write(
                    f"cleanup_pipeline_output: skipping unsafe path {root!r}\n"
                )
