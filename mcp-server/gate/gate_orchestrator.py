"""
solid-description: Coordinates authorization decisions by delegating to protocol-typed subsystems.
solid-category: service
solid-tags: [hook]
"""

from pathlib import Path
from typing import Callable, Optional

from gate_protocols import (
    CoordinatorMaking,
    ExclusionChecking,
    ExtensionLookup,
    GateHandling,
    GuardChecking,
)


class GateOrchestrator:
    """Facade: sequences all gate steps by delegating to protocol-typed subsystems."""

    def __init__(
        self,
        gate: GateHandling,
        guard: GuardChecking,
        parse_fn: Callable[[str], Optional[tuple]],
        extension_lookup: ExtensionLookup,
        exclusion_checker: ExclusionChecking,
        patch_path_fn: Callable[[str], str],
        coordinator_maker: CoordinatorMaking,
    ) -> None:
        self._gate = gate
        self._guard = guard
        self._parse = parse_fn
        self._extension_lookup = extension_lookup
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
        tool_name, tool_input, file_path, session_id, cwd = parsed
        if tool_name == "apply_patch":
            file_path = self._patch_path(tool_input.get("command", ""))
        ext = Path(file_path).suffix.lower()
        language = self._extension_lookup.language_for(ext)
        if language is None:
            self._gate.allow()
            return
        if self._exclusion.is_excluded(file_path):
            self._gate.allow()
            return
        self._coordinator_maker.make_coordinator(self._gate).run(tool_name, tool_input, file_path, language, session_id, cwd)
