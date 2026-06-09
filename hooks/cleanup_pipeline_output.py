#!/usr/bin/env python3
"""
solid-description: Cleans up pipeline output directories after a Stop event.
solid-category: hook

track_output_path.py records each output_root to ~/.solid_coder/.pending_cleanup via
PostToolUse. This module reads that sentinel, deletes each safe path, then clears it,
unless debug_mode() is true.
"""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

_SAFE_ROOT = Path.home() / ".solid_coder"
_SENTINEL = Path.home() / ".solid_coder" / ".pending_cleanup"


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


# ---------------------------------------------------------------------------
# Protocols
# ---------------------------------------------------------------------------

@runtime_checkable
class DebugModeReading(Protocol):
    def is_debug(self) -> bool: ...


@runtime_checkable
class SentinelReading(Protocol):
    def get_pending_roots(self) -> list: ...
    def clear(self) -> None: ...


@runtime_checkable
class PathSafetyValidating(Protocol):
    def is_safe(self, path: str) -> bool: ...


@runtime_checkable
class DirectoryRemoving(Protocol):
    def remove(self, path: str) -> None: ...


@runtime_checkable
class EventFiltering(Protocol):
    def should_handle(self, event: dict) -> bool: ...


@runtime_checkable
class CleanupOrchestrating(Protocol):
    def handle(self, event: dict) -> None: ...


# ---------------------------------------------------------------------------
# Implementations
# ---------------------------------------------------------------------------

class HcConfigDebugReader:
    """Reads debug mode via an injectable callable; defaults to hc_config_llm.debug_mode."""

    def __init__(self, debug_mode_fn: Callable[[], bool] | None = None) -> None:
        if debug_mode_fn is None:
            from hc_config_llm import debug_mode  # noqa: PLC0415
            debug_mode_fn = debug_mode
        self._fn = debug_mode_fn

    def is_debug(self) -> bool:
        return self._fn()


class SentinelFileReader:
    """Reads and clears the pending_cleanup sentinel file."""

    def __init__(self, sentinel: Path = _SENTINEL) -> None:
        self._sentinel = sentinel

    def get_pending_roots(self) -> list:
        try:
            text = self._sentinel.read_text(encoding="utf-8")
            return [p.strip() for p in text.splitlines() if p.strip()]
        except OSError:
            return []

    def clear(self) -> None:
        try:
            self._sentinel.unlink(missing_ok=True)
        except OSError:
            pass


class SafeRootValidator:
    """Validates that a path is under ~/.solid_coder/ before deletion."""

    def __init__(self, safe_root: Path = _SAFE_ROOT) -> None:
        self._root = safe_root

    def is_safe(self, path: str) -> bool:
        try:
            return Path(path).is_relative_to(self._root)
        except (ValueError, TypeError):
            return False


class ShutilDirectoryRemover:
    """Removes a directory tree via shutil.rmtree."""

    def remove(self, path: str) -> None:
        shutil.rmtree(path, ignore_errors=True)


class StopEventFilter:
    """Determines whether a Stop event is eligible for cleanup."""

    def should_handle(self, event: dict) -> bool:
        return True


class PathCleanupOrchestrator:
    """Reads pending roots, validates safety, deletes dirs, clears sentinel."""

    def __init__(
        self,
        debug_reader: DebugModeReading | None = None,
        sentinel_reader: SentinelReading | None = None,
        validator: PathSafetyValidating | None = None,
        remover: DirectoryRemoving | None = None,
    ) -> None:
        self._debug = debug_reader if debug_reader is not None else HcConfigDebugReader()
        self._sentinel = sentinel_reader if sentinel_reader is not None else SentinelFileReader()
        self._validator = validator if validator is not None else SafeRootValidator()
        self._remover = remover if remover is not None else ShutilDirectoryRemover()

    def handle(self, event: dict) -> None:
        if self._debug.is_debug():
            return
        roots = self._sentinel.get_pending_roots()
        for root in roots:
            if self._validator.is_safe(root):
                self._remover.remove(root)
            else:
                sys.stderr.write(
                    f"cleanup_pipeline_output: skipping unsafe path {root!r}\n"
                )
        self._sentinel.clear()


class PipelineOutputCleaner:
    """StopHandler facade — delegates eligibility and cleanup to injected components."""

    def __init__(
        self,
        event_filter: EventFiltering | None = None,
        cleanup_orchestrator: CleanupOrchestrating | None = None,
        debug_reader: DebugModeReading | None = None,
    ) -> None:
        self._filter = event_filter if event_filter is not None else StopEventFilter()
        self._orchestrator = (
            cleanup_orchestrator
            if cleanup_orchestrator is not None
            else PathCleanupOrchestrator(debug_reader=debug_reader)
        )

    def should_handle(self, event: dict) -> bool:
        return self._filter.should_handle(event)

    def handle(self, event: dict) -> None:
        self._orchestrator.handle(event)
