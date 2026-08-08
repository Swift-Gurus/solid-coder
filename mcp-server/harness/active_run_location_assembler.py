"""
solid-name: ActiveRunLocationAssembler
solid-category: service
solid-spec: [SPEC-031]
solid-description: Assembles location information for a run execution.
"""

from __future__ import annotations

from pathlib import Path

from harness.active_run_location import ActiveRunLocation
from harness.active_run_location_assembling import ActiveRunLocationAssembling


class ActiveRunLocationAssembler(ActiveRunLocationAssembling):

    def assemble(self, run_id: str, base_dir: Path, run_dir: Path) -> ActiveRunLocation:
        return ActiveRunLocation(
            run_id=run_id,
            base_dir=base_dir,
            run_dir=run_dir,
            events_path=str(run_dir / "events.jsonl"),
            workflow_path=str(run_dir / "workflow.yaml"),
        )
