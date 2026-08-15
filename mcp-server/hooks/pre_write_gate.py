#!/usr/bin/env python3
"""
solid-description: Service that validates solid-coder configuration and gates tool operations.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[1]
_MCP_HEALTH = _MCP_DIR / "health"
for _d in (
    _MCP_DIR,
    _MCP_DIR / "gate",
    _MCP_DIR / "patch",
    _MCP_DIR / "output",
    _MCP_DIR / "utils",
    _MCP_DIR / "session",
    _MCP_HEALTH,
    _MCP_HEALTH / "config",
    _MCP_HEALTH / "llm",
    _MCP_HEALTH / "codex",
):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from apply_patch_content_simulator_factory import ApplyPatchContentSimulatorFactory
from apply_patch_reviewer_factory import ApplyPatchReviewerFactory
from default_coordinator_factory import DefaultCoordinatorFactory
from default_exclusion_checker_factory import DefaultExclusionCheckerFactory
from default_guard_factory import DefaultGuardFactory
from gate_orchestrator_factory import GateOrchestratorFactory
from hook_utils import HookGateFactory
from solid_coder_config_error import SolidCoderConfigError
from write_gate_coordinator_factory import WriteGateCoordinatorFactory

_GATE = HookGateFactory().build()
_PATCH_SIMULATOR_FACTORY = ApplyPatchContentSimulatorFactory()
_COORDINATOR_FACTORY = DefaultCoordinatorFactory(
    coordinator_factory=WriteGateCoordinatorFactory(_PATCH_SIMULATOR_FACTORY),
    orchestrator_factory=GateOrchestratorFactory(
        guard_factory=DefaultGuardFactory(),
        exclusion_checker_factory=DefaultExclusionCheckerFactory(),
        patch_simulator_factory=_PATCH_SIMULATOR_FACTORY,
        patch_reviewer_factory=ApplyPatchReviewerFactory(),
    ),
)
_ORCHESTRATOR = _COORDINATOR_FACTORY.make_orchestrator(_GATE)


def main() -> None:
    try:
        _ORCHESTRATOR.run(sys.stdin.read())
    except SolidCoderConfigError as exc:
        _GATE.block(
            "solid-coder config invalid — fix .solid-coder/config.toml or config.local.toml",
            additional_context=str(exc),
        )


if __name__ == "__main__":
    main()
