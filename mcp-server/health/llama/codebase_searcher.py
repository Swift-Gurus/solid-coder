"""
solid-description: Provides unified access to codebase search operations.
solid-category: service
solid-tags: [hook, llm]
"""

from typing import Callable, Protocol


class CodebaseSearching(Protocol):
    def search(self, query: str) -> str: ...
    def grep(self, name: str) -> str: ...
    def glob(self, pattern: str) -> str: ...
    def read(self, file_path: str) -> str: ...


class CodebaseSearcher:
    """Adapts four injected callables to the CodebaseSearching protocol."""

    def __init__(
        self,
        search_fn: Callable[[str], str],
        grep_fn: Callable[[str], str],
        glob_fn: Callable[[str], str],
        read_fn: Callable[[str], str],
    ) -> None:
        self._search_fn = search_fn
        self._grep_fn = grep_fn
        self._glob_fn = glob_fn
        self._read_fn = read_fn

    def search(self, query: str) -> str:
        return self._search_fn(query)

    def grep(self, name: str) -> str:
        return self._grep_fn(name)

    def glob(self, pattern: str) -> str:
        return self._glob_fn(pattern)

    def read(self, file_path: str) -> str:
        return self._read_fn(file_path)
