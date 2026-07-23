"""
solid-description: Reconstructs execution state from event logs.
solid-category: service
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Protocol

from harness.models import RunState
from harness.run_state_reconstructing import RunStateReconstructing


class EventParsing(Protocol):
    """
    solid-description: Contract for parsing raw event input into structured events.
    solid-category: abstraction
    """

    def parse(self, lines: list[str]) -> list[dict]: ...


class EventParser:
    """
    solid-description: Parses event input with automatic error recovery.
    solid-category: service
    """

    def parse(self, lines: list[str]) -> list[dict]:
        result: list[dict] = []
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            try:
                result.append(json.loads(line))
            except json.JSONDecodeError:
                sys.stderr.write(f"event_log: skipping corrupt line: {line[:80]}\n")
        return result


class EventReplayer:
    """
    solid-description: Reconstructs execution state from recorded events.
    solid-category: service
    """

    def __init__(self, parser: EventParsing, reconstructor: RunStateReconstructing) -> None:
        self._parser = parser
        self._reconstructor = reconstructor

    def replay(self, path: str) -> RunState:
        p = Path(path)
        if not p.exists():
            return RunState(completed={}, running=[], turn_count=0, status="not_started")
        events = self._parser.parse(p.read_text().splitlines())
        return self._reconstructor.reconstruct(events)
