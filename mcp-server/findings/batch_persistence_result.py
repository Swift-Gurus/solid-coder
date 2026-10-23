"""Defines the outcome of ordered findings-batch persistence."""

from dataclasses import dataclass

"""
solid-name: BatchPersistenceResult
solid-category: model
solid-description: Reports completion or the first labelled failure while persisting an ordered findings batch.
"""


@dataclass(frozen=True)
class BatchPersistenceResult:
    failed_principle_label: str | None = None
    error_message: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.error_message is None
