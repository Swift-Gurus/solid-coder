"""
solid-description: Sequences the full gate flow — key guard, event parsing, path resolution, extension and exclusion filtering, and coordination — for every PreToolUse write event.
solid-category: service
solid-tags: [hook]
"""

from pathlib import Path
from typing import Callable, Optional, Protocol


class GuardChecking(Protocol):
    def is_available(self) -> bool: ...


class ExclusionChecking(Protocol):
    def is_excluded(self, file_path: str) -> bool: ...


class GateHandling(Protocol):
    def allow(self) -> None: ...
    def block(self, reason: str) -> None: ...
    def log(self, msg: str) -> None: ...
    def allow_with_update(self, updated_input: dict) -> None: ...


class CoordinatorRunning(Protocol):
    def run(self, tool_name: str, tool_input: dict, file_path: str, language: str, session_id: str) -> None: ...


class CoordinatorMaking(Protocol):
    def make_coordinator(self, gate: GateHandling) -> CoordinatorRunning: ...


class GateOrchestrator:
    """Facade: sequences all gate steps by delegating to protocol-typed subsystems."""

    def __init__(
        self,
        gate: GateHandling,
        guard: GuardChecking,
        parse_fn: Callable[[str], Optional[tuple]],
        supported_extensions: dict,
        exclusion_checker: ExclusionChecking,
        patch_path_fn: Callable[[str], str],
        coordinator_maker: CoordinatorMaking,
    ) -> None:
        self._gate = gate
        self._guard = guard
        self._parse = parse_fn
        self._extensions = supported_extensions
        self._exclusion = exclusion_checker
        self._patch_path = patch_path_fn
        self._coordinator_maker = coordinator_maker

    def run(self, raw: str) -> None:
        if not self._guard.is_available():
            self._gate.allow()
            return
        parsed = self._parse(raw)
        if parsed is None:
            self._gate.allow()
            return
        tool_name, tool_input, file_path, session_id = parsed
        if tool_name == "apply_patch":
            file_path = self._patch_path(tool_input.get("command", ""))
        ext = Path(file_path).suffix.lower()
        if ext not in self._extensions:
            self._gate.allow()
            return
        if self._exclusion.is_excluded(file_path):
            self._gate.allow()
            return
        language = self._extensions[ext]
        self._coordinator_maker.make_coordinator(self._gate).run(tool_name, tool_input, file_path, language, session_id)
