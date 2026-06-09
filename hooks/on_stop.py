#!/usr/bin/env python3
"""
solid-description: Dispatches Claude Code Stop events to registered handlers.
solid-category: hook
"""

import json
import sys
from pathlib import Path
from typing import List, Optional, Protocol, runtime_checkable

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import ensure_on_path  # noqa: E402


@runtime_checkable
class StopHandler(Protocol):
    """Structural protocol for all Stop event handlers."""

    def should_handle(self, event: dict) -> bool: ...
    def handle(self, event: dict) -> None: ...


class StopEventReading(Protocol):
    """Narrow read protocol for the Stop event source."""

    def read(self) -> dict: ...


class StopDispatching(Protocol):
    """Narrow dispatch protocol for a stop event gate."""

    def run(self, event: dict) -> None: ...


class EventSource(Protocol):
    """Protocol for reading raw event text."""

    def read(self) -> str: ...


class HookEventReader:
    """Reads and parses a Claude Code Stop event from an injectable source."""

    def __init__(self, source: Optional[EventSource] = None) -> None:
        self._source = source  # None means use sys.stdin at call time

    def read(self) -> dict:
        try:
            raw = (self._source.read() if self._source is not None else sys.stdin.read())
            return json.loads(raw) if raw.strip() else {}
        except Exception as exc:
            sys.stderr.write(f"on_stop: failed to parse Stop event: {exc}\n")
            return {}


class OnStopGate:
    """Dispatches a Stop event to every registered handler that opts in."""

    def __init__(self, handlers: List[StopHandler]) -> None:
        self._handlers = handlers

    def run(self, event: dict) -> None:
        for handler in self._handlers:
            if handler.should_handle(event):
                handler.handle(event)


def main(reader: StopEventReading, gate: StopDispatching) -> None:
    """Dispatch a Stop event via the injected reader and gate, then exit 0."""
    event = reader.read()
    gate.run(event)
    sys.exit(0)


if __name__ == "__main__":
    ensure_on_path(Path(__file__).resolve().parent)
    from slack_notify import SlackStopNotifier  # noqa: PLC0415

    main(
        reader=HookEventReader(),
        gate=OnStopGate(handlers=[SlackStopNotifier()]),
    )
