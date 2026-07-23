"""
solid-name: flow_engine_doubles
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Shared test doubles (spies/stubs) reused across flow-engine unit tests to avoid redefining identical collaborators per test file.
"""


class SpyEventAppender:
    def __init__(self) -> None:
        self.events: list[tuple] = []

    def append(self, path, event_type, payload) -> None:
        self.events.append((path, event_type, payload))


class SpyCompletionChecker:
    def __init__(self, result=None) -> None:
        self._result = result
        self.calls: list[tuple] = []

    def check(self, base_dir, run_id, events_path, flow_def, run_state):
        self.calls.append((base_dir, run_id, events_path, flow_def, run_state))
        return self._result


class StubRunSnapshotResolver:
    def __init__(self, snapshot=None, error=None) -> None:
        self._snapshot = snapshot
        self._error = error
        self.calls: list[tuple] = []

    def resolve(self, events_path, flow_def, params):
        self.calls.append((events_path, flow_def, params))
        if self._error is not None:
            raise self._error
        return self._snapshot
