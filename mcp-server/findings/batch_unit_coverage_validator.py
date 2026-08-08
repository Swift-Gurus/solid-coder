"""Validates unit coverage for immutable findings batches."""

from typing import Optional

from findings.batch_coverage_failure import BatchCoverageFailure
from findings.batch_coverage_validating import BatchCoverageValidating
from findings.batch_submission import BatchSubmission
from findings.hook_context import HookContext
from findings.principle_coverage_scope import PrincipleCoverageScope
from findings.principle_submission import PrincipleSubmission
from findings.review_unit_kind import ReviewUnitKind


_SOLID_PRINCIPLES = frozenset({"srp", "ocp", "lsp", "isp", "dry"})


"""
solid-name: BatchUnitCoverageValidator
solid-category: validator
solid-description: Detects active SOLID principles that omit every required source unit from an immutable batch review.
"""
class BatchUnitCoverageValidator(BatchCoverageValidating):
    def __init__(self, scopes: tuple[PrincipleCoverageScope, ...]) -> None:
        self._scopes = scopes

    def validate(
        self,
        submission: BatchSubmission,
        context: Optional[HookContext],
    ) -> Optional[BatchCoverageFailure]:
        expected_units = self._expected_units(submission, context)
        if not expected_units:
            return None

        submitted_kinds = self._submitted_kinds(submission)
        skipped = tuple(
            principle.label
            for principle in submission.principles
            if principle.label.lower() in _SOLID_PRINCIPLES
            and self._has_no_units(principle)
            and not self._is_exempt(principle.label, submitted_kinds)
        )
        if not skipped:
            return None

        return BatchCoverageFailure(
            principle_labels=skipped,
            expected_units=expected_units,
        )

    def _expected_units(
        self,
        submission: BatchSubmission,
        context: Optional[HookContext],
    ) -> tuple[str, ...]:
        if context is not None and context.expected_units:
            return context.expected_units
        return tuple(sorted({
            unit.name
            for principle in submission.principles
            if principle.label.lower() in _SOLID_PRINCIPLES
            for reviewed_file in principle.output.files
            for unit in reviewed_file.units
        }))

    def _submitted_kinds(
        self,
        submission: BatchSubmission,
    ) -> frozenset[ReviewUnitKind]:
        return frozenset(
            unit.kind
            for principle in submission.principles
            for reviewed_file in principle.output.files
            for unit in reviewed_file.units
        )

    def _has_no_units(self, submission: PrincipleSubmission) -> bool:
        return not any(reviewed_file.units for reviewed_file in submission.output.files)

    def _is_exempt(
        self,
        principle_label: str,
        submitted_kinds: frozenset[ReviewUnitKind],
    ) -> bool:
        scope = next(
            (
                candidate
                for candidate in self._scopes
                if candidate.principle_label.lower() == principle_label.lower()
            ),
            None,
        )
        return scope is not None and not bool(scope.unit_kinds & submitted_kinds)
