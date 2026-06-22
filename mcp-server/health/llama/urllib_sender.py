"""
solid-description: Sends HTTP POST requests and returns the response.
solid-category: service
solid-tags: [hook, llm, http]
"""

from typing import Optional, Protocol

from llama.urllib_opener import HttpOpening, UrllibOpener
from llama.urllib_request_builder import HttpRequestBuilding, UrllibRequestBuilder


class HttpSending(Protocol):
    def send(self, url: str, data: bytes, headers: dict, timeout: int) -> bytes: ...


class UrllibSender:
    """Sends HTTP POST via injected opener and request builder."""

    def __init__(
        self,
        opener: Optional[HttpOpening] = None,
        builder: Optional[HttpRequestBuilding] = None,
    ) -> None:
        self._opener: HttpOpening = opener or UrllibOpener()
        self._builder: HttpRequestBuilding = builder or UrllibRequestBuilder()

    def send(self, url: str, data: bytes, headers: dict, timeout: int) -> bytes:
        req = self._builder.build(url, data, headers, "POST")
        return self._opener.open(req, timeout)
