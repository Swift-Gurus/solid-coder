"""
solid-name: hook_dispatch_doubles
solid-category: unit-test
solid-description: Supplies reusable test doubles for hook-dispatch unit tests.
"""

import time

from hook_decision import HookDecision


class StubHandler:
    """Configurable HookHandling test double: should_handle result, a decision, or an exception to raise from handle()."""

    def __init__(self, applicable: bool = True, decision: HookDecision = None, exc: Exception = None, name: str = "") -> None:
        self.name = name
        self._applicable = applicable
        self._decision = decision
        self._exc = exc

    def should_handle(self, event: dict) -> bool:
        return self._applicable

    def handle(self, event: dict) -> HookDecision:
        if self._exc is not None:
            raise self._exc
        return self._decision

    def __repr__(self) -> str:
        return f"StubHandler({self.name!r})"


class RecordingLogger:
    def __init__(self) -> None:
        self.messages = []

    def log(self, msg: str) -> None:
        self.messages.append(msg)


class SerialPoolRunner:
    """Deterministic stand-in for the real thread pool — records exactly what was submitted."""

    def __init__(self) -> None:
        self.received_items = None

    def map(self, fn, items):
        self.received_items = list(items)
        return [fn(item) for item in items]


class PassthroughSafeRunner:
    def run(self, handler, event):
        return handler.handle(event)


class RecordingSafeRunner:
    def __init__(self) -> None:
        self.calls = []

    def run(self, handler, event):
        self.calls.append(handler.name)
        return HookDecision(allow=True)


class AllowHandler:
    def should_handle(self, event: dict) -> bool:
        return True

    def handle(self, event: dict) -> HookDecision:
        return HookDecision(allow=True)


class DenyHandler:
    def __init__(self, reason: str, additional_context: str = None) -> None:
        self._reason = reason
        self._context = additional_context

    def should_handle(self, event: dict) -> bool:
        return True

    def handle(self, event: dict) -> HookDecision:
        return HookDecision(allow=False, reason=self._reason, additional_context=self._context)


class NotApplicableHandler:
    def should_handle(self, event: dict) -> bool:
        return False

    def handle(self, event: dict) -> HookDecision:
        raise AssertionError("handle() must not be called when should_handle is False")


class RaisingHandler:
    def should_handle(self, event: dict) -> bool:
        return True

    def handle(self, event: dict) -> HookDecision:
        raise RuntimeError("integration is down")


class SleepingHandler:
    def __init__(self, seconds: float) -> None:
        self._seconds = seconds

    def should_handle(self, event: dict) -> bool:
        return True

    def handle(self, event: dict) -> HookDecision:
        time.sleep(self._seconds)
        return HookDecision(allow=True)


class AllowHandlerWithContext:
    def __init__(self, context: str) -> None:
        self._context = context

    def should_handle(self, event: dict) -> bool:
        return True

    def handle(self, event: dict) -> HookDecision:
        return HookDecision(allow=True, additional_context=self._context)
