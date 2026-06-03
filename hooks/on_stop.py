#!/usr/bin/env python3
"""
solid-description: Gate coordinator for Claude Code Stop events. Reads the
Stop event from stdin and dispatches to all registered StopHandler
implementations in order. New Stop behaviours are added by registering a
handler here — no change to hooks.json is needed.
solid-category: hook
"""

import json
import sys
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class StopHandler(Protocol):
    """Structural protocol for all Stop event handlers."""

    def should_handle(self, event: dict) -> bool: ...
    def handle(self, event: dict) -> None: ...


class HookEventReader:
    """Reads and parses the Claude Code Stop event JSON from stdin."""

    def read(self) -> dict:
        try:
            raw = sys.stdin.read()
            return json.loads(raw) if raw.strip() else {}
        except Exception:
            return {}


class OnStopGate:
    """Dispatches a Stop event to every registered handler that opts in."""

    def __init__(self, handlers: list[StopHandler]) -> None:
        self._handlers = handlers

    def run(self, event: dict) -> None:
        for handler in self._handlers:
            if handler.should_handle(event):
                handler.handle(event)


def _load_handlers() -> list[StopHandler]:
    """Resolve sibling modules from the hooks directory regardless of CWD."""
    hooks_dir = str(Path(__file__).resolve().parent)
    if hooks_dir not in sys.path:
        sys.path.insert(0, hooks_dir)

    from slack_notify import SlackStopNotifier  # noqa: PLC0415

    return [SlackStopNotifier()]


def main() -> None:
    event = HookEventReader().read()
    OnStopGate(handlers=_load_handlers()).run(event)
    sys.exit(0)


if __name__ == "__main__":
    main()
