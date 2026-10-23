"""
solid-description: Constructs fully-configured instances ready for immediate use.
solid-category: service
solid-tags: [hook]
"""

from pathlib import Path

from gate.hook_context_buffer import HookContextBuffer
from gate_logger import GateLogger
from gateway_output_writing import GatewayOutputWriting
from hook_gate import HookGate
from hook_responder import HookResponder
from hook_utils import solid_coder_project_dir
from stdout_writer import StdoutWriter
from utils.debug_logger import DebugLogger

"""
solid-name: HookGateFactory
solid-category: service
solid-description: Constructs production-ready hook execution gates.
"""


class HookGateFactory:
    """Factory: constructs HookGate with production defaults.

    Constructing, holding, and wiring concrete dependencies is inherently
    this class's job (OCP factory exception).
    """

    def __init__(
        self,
        log_path: Path | None = None,
        output: GatewayOutputWriting | None = None,
    ) -> None:
        self._log_path = log_path
        self._output = output

    def build(self) -> HookGate:
        path = self._log_path or (solid_coder_project_dir() / "gate.log")
        return HookGate(
            context=HookContextBuffer(),
            logger=GateLogger(
                DebugLogger(project_dir_fn=lambda: path.parent, filename=path.name)
            ),
            responder=HookResponder(
                output=self._output if self._output is not None else StdoutWriter(),
            ),
        )
