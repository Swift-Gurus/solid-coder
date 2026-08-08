"""Defines the outcome of ordered findings-batch persistence."""

from dataclasses import dataclass
from typing import Optional


"""
solid-name: BatchPersistenceResult
solid-category: model
solid-description: Reports completion or the first labelled failure while persisting an ordered findings batch.
"""
@dataclass(frozen=True)
class BatchPersistenceResult:
    failed_principle_label: Optional[str] = None
    error_message: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error_message is None
