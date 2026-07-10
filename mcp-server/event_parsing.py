"""
solid-description: Contract for parsing raw event data into structured events.
solid-category: abstraction
"""

from typing import Optional, Protocol


class ClaudeBareEventParsing(Protocol):
    """Protocol for parsing the JSON event stream from claude -p --bare output.

    Distinct from harness.event_replayer.EventParsing, which parses recorded
    flow-run log lines (list[str] -> list[dict]) — an unrelated log-replay
    concern with a different shape that happens to share the "EventParsing"
    name.
    """

    def parse_events(self, raw: object) -> list: ...
    def parse_event_dict(self, event: object) -> Optional[dict]: ...
