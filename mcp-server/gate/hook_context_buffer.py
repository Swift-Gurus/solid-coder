from typing import Protocol


"""
solid-name: HookContextBuffering
solid-category: abstraction
solid-description: Contract for retaining hook context until it is inspected or consumed by a final response.
"""
class HookContextBuffering(Protocol):
    def append(self, message: str) -> None: ...
    def render(self, additional_context: str = "") -> str: ...
    def consume(self, additional_context: str = "") -> str: ...


"""
solid-name: HookContextBuffer
solid-category: service
solid-description: Retains ordered hook context and clears it when the final response consumes it.
"""
class HookContextBuffer(HookContextBuffering):
    def __init__(self) -> None:
        self._messages: list[str] = []

    def append(self, message: str) -> None:
        self._messages.append(message)

    def render(self, additional_context: str = "") -> str:
        return "\n\n".join(filter(None, [*self._messages, additional_context]))

    def consume(self, additional_context: str = "") -> str:
        context = self.render(additional_context)
        self._messages.clear()
        return context
