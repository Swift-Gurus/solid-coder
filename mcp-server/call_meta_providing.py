"""
solid-name: CallMetaProviding
solid-category: abstraction
solid-description: Contract for accessing metadata of the currently handled call.
"""

from typing import Protocol


class CallMetaProviding(Protocol):
    def get_current_call_meta(self) -> dict: ...
