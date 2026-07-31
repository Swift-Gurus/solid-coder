"""
solid-name: stop_handler_doubles
solid-category: unit-test
solid-description: Provides configurable stub and recording test doubles for stop handler testing.
"""


class StubNotifier:
    def __init__(self, should: bool) -> None:
        self._should = should
        self.handled_events = []

    def should_handle(self, event: dict) -> bool:
        return self._should

    def handle(self, event: dict) -> None:
        self.handled_events.append(event)


class StubGate:
    def __init__(self, result: dict) -> None:
        self._result = result
        self.evaluate_calls = 0

    def evaluate(self) -> dict:
        self.evaluate_calls += 1
        return self._result


class StubValidateFn:
    def __init__(self, result: dict) -> None:
        self._result = result
        self.calls = []

    def __call__(self, session_id, transcript_path, cwd):
        self.calls.append((session_id, transcript_path, cwd))
        return self._result


class StubEventSource:
    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> str:
        return self._text


class StubReader:
    def __init__(self, event: dict) -> None:
        self._event = event

    def read(self) -> dict:
        return self._event


class StubDispatcher:
    def __init__(self, decision) -> None:
        self._decision = decision
        self.dispatched_events = []

    def dispatch(self, event: dict):
        self.dispatched_events.append(event)
        return self._decision


class RecordingResponder:
    def __init__(self) -> None:
        self.allow_calls = []
        self.block_calls = []

    def allow(self, additional_context: str = "") -> None:
        self.allow_calls.append(additional_context)

    def block(self, reason: str, additional_context: str = "") -> None:
        self.block_calls.append((reason, additional_context))


class RecordingLogger:
    def __init__(self) -> None:
        self.messages = []

    def log(self, msg: str) -> None:
        self.messages.append(msg)
