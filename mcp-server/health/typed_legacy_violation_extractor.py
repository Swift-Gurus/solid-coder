"""Adapts unchanged legacy extraction into typed gate violations."""

from pydantic import TypeAdapter

from health_violation import HealthViolation
from legacy_health_violation_payload import LegacyHealthViolationPayload
from violation_extractor import ViolationExtracting


"""
solid-name: TypedLegacyViolationExtractor
solid-category: boundary-adapter
solid-spec: [SPEC-050]
solid-description: Provides typed gate violations from legacy health review findings.
"""
class TypedLegacyViolationExtractor:
    def __init__(
        self,
        legacy: ViolationExtracting,
        adapter: TypeAdapter[list[LegacyHealthViolationPayload]],
    ) -> None:
        self._legacy = legacy
        self._adapter = adapter

    def extract(self, output_dir: str) -> list[HealthViolation]:
        findings = self._adapter.validate_python(
            self._legacy.extract(output_dir)
        )
        return [
            HealthViolation(
                principle=finding.principle,
                metric_id=finding.metric_id,
                issue=finding.issue,
                evidence=(
                    "Legacy output did not preserve evidence for "
                    f"{finding.metric_id}."
                ),
                fix=finding.fix,
            )
            for finding in findings
        ]
