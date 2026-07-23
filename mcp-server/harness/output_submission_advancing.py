"""
solid-description: Contract for submitting step outputs and determining submission outcomes.
solid-category: abstraction
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.models import FlowDef, StepInstance
from harness.submission_outcome import SubmissionOutcome


class OutputSubmissionAdvancing(Protocol):

    def submit(
        self,
        events_path: str,
        base_dir: Path,
        run_id: str,
        ready: list[StepInstance],
        step_outputs: dict,
        flow_def: FlowDef,
    ) -> SubmissionOutcome: ...
