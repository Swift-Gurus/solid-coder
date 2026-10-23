from typing import Protocol

from harness.template_value_rendering import TemplateValueRendering
from health.hc_violation_parser import BlockReasonFormatting
from health_check_outcome import HealthCheckOutcome
from hook_decision import HookDecision
from unavailable_health_metric import UnavailableHealthMetric

"""
solid-name: HealthOutcomeRendering
solid-category: abstraction
solid-spec: [SPEC-057]
solid-description: Contract for rendering typed health outcomes into write-gate decisions and warnings without exposing private audit evidence.
"""


class HealthOutcomeRendering(Protocol):
    def render(self, outcome: HealthCheckOutcome) -> HookDecision: ...


"""
solid-name: HealthOutcomeRenderer
solid-category: service
solid-spec: [SPEC-057]
solid-description: Combines measured violations and unavailable-evidence decisions into actionable write blocking or verified-new-interface warnings.
"""


class HealthOutcomeRenderer(HealthOutcomeRendering):
    def __init__(
        self,
        violations: BlockReasonFormatting,
        unavailable: TemplateValueRendering[UnavailableHealthMetric],
    ) -> None:
        self._violations = violations
        self._unavailable = unavailable

    def render(self, outcome: HealthCheckOutcome) -> HookDecision:
        reasons: list[str] = []
        if outcome.violations:
            reasons.append(self._violations.format_block_reason(outcome.violations))
        blocking = [
            self._unavailable.render(metric)
            for metric in outcome.unavailable_metrics
            if metric.blocks_write
        ]
        if blocking:
            reasons.append(
                "Unable to verify required review measurements:\n  • "
                + "\n  • ".join(blocking)
                + "\nProvide the missing source or classification evidence, then retry the same write."
            )
        warnings = [
            self._unavailable.render(metric)
            for metric in outcome.unavailable_metrics
            if not metric.blocks_write and not metric.exception.is_exception
        ]
        if reasons:
            reasons.append(
                "The file was NOT written. Resolve the findings or unavailable evidence before continuing."
            )
        return HookDecision(
            allow=not reasons,
            reason="[health-check] " + "\n\n".join(reasons) if reasons else None,
            additional_context=(
                "[health-check] Verified newly introduced interface: these unverified measurements are warning-only, "
                "not compliant results. Other blocking findings still prevent the write:\n  • "
                + "\n  • ".join(warnings)
            )
            if warnings
            else None,
        )
