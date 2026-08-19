"""Adapts temporary-directory creation to the shared lifecycle contract."""

from contextlib import AbstractContextManager
from typing import Callable

from common.temporary_directory_providing import TemporaryDirectoryProviding


"""
solid-name: CallableTemporaryDirectoryProvider
solid-category: boundary-adapter
solid-spec: [SPEC-040]
solid-description: Provides cleanup-bound temporary-directory contexts.
"""
class CallableTemporaryDirectoryProvider(TemporaryDirectoryProviding):
    def __init__(
        self,
        create: Callable[[], AbstractContextManager[str]],
    ) -> None:
        self._create = create

    def provide(self) -> AbstractContextManager[str]:
        return self._create()
