"""
solid-description: Evaluates whether the flow run can safely stop based on its state.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path
from typing import Optional

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from flow_transition_evaluating import FlowTransitionGate, build_default_flow_transition_gate  # noqa: E402
from hook_utils import run_stop_hook_gate  # noqa: E402
from simple_hook_responding import SimpleHookResponding  # noqa: E402
from stop_hook_responder import StopHookResponder  # noqa: E402


def main(gate: Optional[FlowTransitionGate] = None, responder: Optional[SimpleHookResponding] = None) -> None:
    active_gate = gate or build_default_flow_transition_gate()
    run_stop_hook_gate(
        sys.stdin.read(),
        evaluate=lambda _event: active_gate.evaluate(),
        responder=responder or StopHookResponder(),
        default_reason="Flow run left in_progress.",
    )


if __name__ == "__main__":
    main()
