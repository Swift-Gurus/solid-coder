"""Constructs subprocess execution failures."""

from subprocess_error import SubprocessError


"""
solid-name: SubprocessErrorFactory
solid-category: factory
solid-description: Creates failures for unsuccessful subprocess executions.
"""
class SubprocessErrorFactory:
    def create(self, message: str) -> SubprocessError:
        return SubprocessError(message)
