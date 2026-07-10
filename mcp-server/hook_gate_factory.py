"""
solid-description: Constructs fully-configured instances ready for immediate use.
solid-category: service
solid-tags: [hook]
"""

from pathlib import Path
from typing import Optional

from hook_utils import OutputWriting, solid_coder_project_dir
from utils.debug_logger import DebugLogger
from gate_logger import GateLogger
from hook_gate import HookGate
from hook_responder import HookResponder
from stdout_writer import StdoutWriter


class HookGateFactory:
    """Factory: constructs HookGate with production defaults.

    Constructing, holding, and wiring concrete dependencies is inherently
    this class's job (OCP factory exception).
    """

    def __init__(
        self,
        log_path: Optional[Path] = None,
        output: Optional[OutputWriting] = None,
    ) -> None:
        self._log_path = log_path
        self._output = output

    def build(self) -> HookGate:
        path = self._log_path or (solid_coder_project_dir() / "gate.log")
        return HookGate(
            logger=GateLogger(DebugLogger(project_dir_fn=lambda: path.parent, filename=path.name)),
            responder=HookResponder(
                output=self._output if self._output is not None else StdoutWriter(),
            ),
        )
