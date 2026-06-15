"""
solid-description: Opens HTTP requests and returns response bodies.
solid-category: utility
solid-tags: [hook, llm, http]
"""

import urllib.request
from typing import Protocol


class HttpOpening(Protocol):
    def open(self, request, timeout: int) -> bytes: ...


class UrllibOpener:
    """Boundary adapter: wraps urllib.request.urlopen (stdlib, cannot be subclassed)."""

    def open(self, request, timeout: int) -> bytes:
        with urllib.request.urlopen(request, timeout=timeout) as resp:
            return resp.read()
