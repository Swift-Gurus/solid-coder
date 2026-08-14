"""Defines normalization of compact MCP findings payloads."""

from typing import Protocol


"""
solid-name: BatchSubmissionNormalizing
solid-category: abstraction
solid-description: Contract for normalizing compact MCP findings payloads into the typed submission shape.
"""
class BatchSubmissionNormalizing(Protocol):
    def normalize(self, payload: object) -> object: ...
