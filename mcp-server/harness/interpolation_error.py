""" 
solid-description: Exception raised when a template expression cannot be resolved against the run context.
solid-category: model
"""

from __future__ import annotations


class InterpolationError(Exception):
    """
    solid-description: Raised when a template expression cannot be resolved against the run context.
    solid-category: model
    """

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message
