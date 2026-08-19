"""Defines isolated temporary-directory lifecycle provisioning."""

from contextlib import AbstractContextManager
from typing import Protocol


"""
solid-name: TemporaryDirectoryProviding
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for providing a cleanup-bound isolated temporary directory.
"""
class TemporaryDirectoryProviding(Protocol):
    def provide(self) -> AbstractContextManager[str]: ...
