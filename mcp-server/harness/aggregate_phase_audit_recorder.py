"""Persists changed aggregate frontiers at the model-response boundary."""

from pathlib import Path
from typing import Protocol

from harness.aggregate_phase_audit import AggregatePhaseAudit, AggregatePhaseAuditEnvelope, AggregatePolicyScope
from harness.event_appender import EventAppending
from harness.event_replayer import EventParsing
from harness.run_snapshot import RunSnapshot
from harness.structured_model_decoding import StructuredModelDecoding
from utils.prompt_builder import TextFileReading


"""
solid-name: AggregatePhaseAuditRecording
solid-category: abstraction
solid-spec: [SPEC-067]
solid-description: Contract for persisting an internal aggregate frontier without modifying execution state.
"""
class AggregatePhaseAuditRecording(Protocol):
    def record(self, events_path: str, snapshot: RunSnapshot) -> None: ...


"""
solid-name: AggregatePhaseAuditRecorder
solid-category: service
solid-spec: [SPEC-067]
solid-description: Appends changed phase diagnostics to the canonical run log and suppresses identical replay-only observations.
"""
class AggregatePhaseAuditRecorder:
    def __init__(
        self,
        reader: TextFileReading,
        parser: EventParsing,
        decoder: StructuredModelDecoding[AggregatePhaseAuditEnvelope],
        appender: EventAppending,
    ) -> None:
        self._reader = reader
        self._parser = parser
        self._decoder = decoder
        self._appender = appender

    def record(self, events_path: str, snapshot: RunSnapshot) -> None:
        if not snapshot.aggregate_phases:
            return
        audit = AggregatePhaseAudit(
            turn_count=snapshot.run_state.turn_count,
            phases=snapshot.aggregate_phases,
            root_execution=snapshot.flow_def.execution,
            root_presentation=snapshot.flow_def.presentation,
            policy_scopes=[AggregatePolicyScope(
                alias=group.alias,
                owner_alias=group.owner_alias,
                execution=group.execution,
                presentation=group.presentation,
                execution_declared=group.execution_declared,
                presentation_declared=group.presentation_declared,
            ) for group in snapshot.flow_def.alias_groups],
        )
        contents = self._reader.read(Path(events_path)) or ""
        for raw in reversed(self._parser.parse(contents.splitlines())):
            previous = self._decoder.decode(raw, "aggregate audit event").audit
            if previous is not None:
                if previous == audit:
                    return
                break
        self._appender.append(
            events_path, "aggregate_phase_planned",
            AggregatePhaseAuditEnvelope(audit=audit).model_dump(mode="json"),
        )
