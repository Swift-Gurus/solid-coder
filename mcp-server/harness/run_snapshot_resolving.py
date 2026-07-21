"""
solid-name: RunSnapshotResolving
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for computing the currently ready step instances of a flow run.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import FlowDef
from harness.run_snapshot import RunSnapshot


class RunSnapshotResolving(Protocol):

    def resolve(self, events_path: str, flow_def: FlowDef, params: dict) -> RunSnapshot: ...