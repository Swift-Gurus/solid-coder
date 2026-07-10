"""
solid-name: ExecutionIntentResolving
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for mapping execution intents to execution mode configurations based on environment detection.
"""

from __future__ import annotations

from typing import Protocol


class ExecutionIntentResolving(Protocol):

    def resolve(self, intent: str, detected_env: str) -> dict: ...
