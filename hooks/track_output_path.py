#!/usr/bin/env python3
"""
solid-description: Tracks pipeline output locations for deferred cleanup.
solid-category: hook

Registered as a PostToolUse hook for mcp__plugin_solid-coder_pipeline__get_output_path.
Appends the returned output_root to ~/.solid_coder/.pending_cleanup so
cleanup_pipeline_output.py can find and delete it on Stop without parsing subagent transcripts.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Protocol, runtime_checkable

from cleanup_pipeline_output import _extract_output_root
from on_stop import HookEventReader, StopEventReading

_SENTINEL = Path.home() / ".solid_coder" / ".pending_cleanup"


@runtime_checkable
class RootRecording(Protocol):
    def record(self, root: str) -> None: ...


class SentinelFileRecorder:
    """Appends an output_root path to the cleanup sentinel file."""

    def __init__(self, sentinel: Path = _SENTINEL) -> None:
        self._sentinel = sentinel

    def record(self, root: str) -> None:
        self._sentinel.parent.mkdir(parents=True, exist_ok=True)
        with open(self._sentinel, "a", encoding="utf-8") as f:
            f.write(root + "\n")


def main(
    reader: StopEventReading | None = None,
    recorder: RootRecording | None = None,
) -> None:
    _reader = reader if reader is not None else HookEventReader()
    _recorder = recorder if recorder is not None else SentinelFileRecorder()

    event = _reader.read()
    root = _extract_output_root(event.get("tool_response", ""))
    if root:
        _recorder.record(root)


if __name__ == "__main__":
    main()
