"""Defines the outcome of persisting one principle submission."""

from dataclasses import dataclass

"""
solid-name: PrincipleSubmissionResult
solid-category: model
solid-description: Reports whether one principle review submission completed or failed with a message.
"""


@dataclass(frozen=True)
class PrincipleSubmissionResult:
    error_message: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error_message is None
