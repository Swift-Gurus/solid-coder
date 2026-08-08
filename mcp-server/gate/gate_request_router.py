"""Routes parsed gate requests by tool name."""

from gate_request_handling import GateRequestHandling


"""
solid-name: GateRequestRouter
solid-category: service
solid-description: Selects a configured request handler from the parsed tool name and delegates the request.
solid-tags: [hook]
"""
class GateRequestRouter:
    def __init__(
        self,
        handlers: dict[str, GateRequestHandling],
        fallback: GateRequestHandling,
    ) -> None:
        self._handlers = handlers
        self._fallback = fallback

    def route(self, parsed: tuple) -> None:
        tool_name = parsed[0]
        self._handlers.get(tool_name, self._fallback).handle(parsed)
