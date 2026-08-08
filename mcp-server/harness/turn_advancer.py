"""
solid-name: TurnAdvancer
solid-category: service
solid-spec: [SPEC-031]
solid-description: Advances the turn and returns the updated run state.
"""

from __future__ import annotations

from harness.event_replaying import EventReplaying
from harness.event_appender import EventAppending
from harness.models import RunState
from harness.turn_advancing import TurnAdvancing


class TurnAdvancer(TurnAdvancing):

    def __init__(self, event_replayer: EventReplaying, event_appender: EventAppending) -> None:
        self._event_replayer = event_replayer
        self._event_appender = event_appender

    def advance(self, events_path: str) -> RunState:
        run_state = self._event_replayer.replay(events_path)
        self._event_appender.append(events_path, "turn_counted", {"total": run_state.turn_count + 1})
        return self._event_replayer.replay(events_path)
