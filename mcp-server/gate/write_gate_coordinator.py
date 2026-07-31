"""
solid-description: Validates file health and corrects frontmatter before allowing write operations.
solid-category: service
solid-tags: [hook]
"""

import re
from pathlib import Path

from gate_protocols import ContentSimulating, FrontmatterGateApplying, HealthGateChecking
from hook_utils import GateHandling
from tool_input_updating import ToolInputUpdating


class WriteGateCoordinator:
    """Facade: coordinates health check and frontmatter correction via injected protocol-typed subsystems."""

    _FM_KEY = "solid-" + "description:"

    def __init__(
        self,
        health_gate: HealthGateChecking,
        frontmatter_gate: FrontmatterGateApplying,
        simulator: ContentSimulating,
        gate: GateHandling,
        input_updater: ToolInputUpdating,
    ) -> None:
        self._health_gate = health_gate
        self._frontmatter_gate = frontmatter_gate
        self._simulator = simulator
        self._gate = gate
        self._input_updater = input_updater

    def run(self, tool_name: str, tool_input: dict, file_path: str, language: str, session_id: str, cwd: str = "") -> None:
        content, existing, low_risk = self._simulator.simulate(tool_name, tool_input)
        file_name = Path(file_path).name
        run_health = not low_risk
        run_frontmatter = bool(re.search(r'^\s*' + self._FM_KEY + r'\s*\S', content, re.MULTILINE))
        if not run_health and not run_frontmatter:
            self._gate.allow()
            return
        self._gate.log(f"INVOKE {file_name}: health={run_health} frontmatter={run_frontmatter}")
        if run_health and not self._health_gate.check(content, file_path, language, session_id, self._gate, file_name, cwd):
            return
        if run_frontmatter:
            corrected = self._frontmatter_gate.apply(content, session_id, file_path, self._gate, file_name)
            if corrected is not None and corrected != content:
                self._gate.log(f"CORRECTED {file_name}: frontmatter updated")
                if tool_name in ("Write", "Edit"):
                    updated_input = self._input_updater.build(tool_name, tool_input, corrected, existing)
                    self._gate.allow(updated_input=updated_input)
                else:
                    self._gate.allow()
            else:
                self._gate.log(f"CLEAN {file_name}")
                self._gate.allow()
        else:
            self._gate.log(f"CLEAN {file_name}")
            self._gate.allow()