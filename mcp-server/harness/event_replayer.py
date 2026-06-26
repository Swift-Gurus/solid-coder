"""
solid-description: Parses event logs and reconstructs execution state.
solid-category: service
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Protocol

from harness.models import RunState, StepOutputs


class EventParsing(Protocol):
    """
    solid-description: Contract for parsing raw event input into structured events.
    solid-category: abstraction
    """

    def parse(self, lines: list[str]) -> list[dict]: ...


class EventParser:
    """
    solid-description: Parses raw event input, skipping invalid records.
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

    def __init__(self, parser: EventParsing) -> None:
        self._parser = parser

    def replay(self, path: str) -> RunState:
        p = Path(path)
        if not p.exists():
            return RunState(completed={}, running=[], turn_count=0, status="not_started")
        events = self._parser.parse(p.read_text().splitlines())
        return self._reconstruct(events)

    def _reconstruct(self, events: list[dict]) -> RunState:
        completed: dict[str, StepOutputs] = {}
        running: list[str] = []
        turn_count = 0
        status = "in_progress"

        for event in events:
            kind = event.get("event")
            if kind == "step_started":
                step_id = event.get("step_id", event.get("instance_id", ""))
                if step_id and step_id not in running:
                    running.append(step_id)
            elif kind == "step_completed":
                step_id = event.get("step_id", event.get("instance_id", ""))
                completed[step_id] = StepOutputs.from_dict(event.get("outputs") or {})
                if step_id in running:
                    running.remove(step_id)
            elif kind == "turn_counted":
                turn_count = event.get("total", turn_count + 1)
            elif kind == "run_completed":
                status = "done"
            elif kind == "run_timed_out":
                status = "timed_out"

        return RunState(completed=completed, running=running, turn_count=turn_count, status=status)
