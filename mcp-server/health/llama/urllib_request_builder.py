"""
solid-description: Constructs HTTP requests with specified URL, data, headers, and method.
solid-category: utility
solid-tags: [hook, llm, http]
"""

import urllib.request
from typing import Protocol


class HttpRequestBuilding(Protocol):
    def build(self, url: str, data: bytes, headers: dict, method: str): ...


class UrllibRequestBuilder:
    """Boundary adapter: wraps urllib.request.Request (stdlib C-extension, cannot be subclassed).

    urllib.request.Request is a C-extension type — instantiation here satisfies
    the OCP Boundary Adapter exception. Tests swap the enclosing UrllibSender via
    the HttpRequestBuilding protocol rather than mocking this class directly.
    """

    def build(self, url: str, data: bytes, headers: dict, method: str):
        return urllib.request.Request(url, data=data, headers=headers, method=method)
