"""
solid-name: BatchSubmissionHandler
solid-category: service
solid-description: Orchestrates batch submission of findings and returns violations as a structured response.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol

from findings.submit_orchestrator import SubmitOrchestrating
from findings.unit_coverage_validator import HookContextLoading, UnitCoverageValidating
from findings.violation_reader import ViolationReading


class BatchSubmissionHandling(Protocol):
    def submit_batch(self, output_dir: str, submissions: dict) -> dict: ...


class ViolationResponseFormating(Protocol):
    def format(self, violations: list, output_dir: str) -> dict: ...


class ViolationResponseFormatter(ViolationResponseFormating):
    """Formats raw SEVERE violations into a model-facing structured response."""

    def format(self, violations: list, output_dir: str) -> dict:
        response: dict = {"violations": violations}
        if violations:
            rule_ids = ", ".join(f"'{v['rule_id']}'" for v in violations)
            response["output_dir"] = output_dir
            response["message"] = (
                f"Found {len(violations)} SEVERE violation(s). Complete these steps:\n"
                f"1. Call mcp__docs__load_fix_for_violation ONCE with metric_ids=[{rule_ids}] "
                f"to get all fix strategies in one call.\n"
                f"2. For each violation, prepare a concrete code-specific fix using the guidance.\n"
                f"3. Call mcp__pipeline__submit_fix ONCE with output_dir='{output_dir}' and "
                f"fixes=[{{rule_id, file_path, unit_name, suggested_fix}}, ...] for all violations."
            )
        return response


class BatchSubmissionHandler(BatchSubmissionHandling):
    """Coordinates the batch-submission lifecycle for a health-check session.

    Facade: all stored properties are protocol-typed; submit_batch delegates to each
    injected collaborator with no internal business logic.
    """

    def __init__(
        self,
        submit_orchestrator: SubmitOrchestrating,
        context_loader: HookContextLoading,
        violation_reader: ViolationReading,
        response_formatter: ViolationResponseFormating,
        coverage_validator: Optional[UnitCoverageValidating] = None,
    ) -> None:
        self._orchestrator = submit_orchestrator
        self._context_loader = context_loader
        self._violation_reader = violation_reader
        self._response_formatter = response_formatter
        self._coverage_validator = coverage_validator

    def submit_batch(self, output_dir: str, submissions: dict) -> dict:
        if self._coverage_validator:
            error = self._coverage_validator.validate(submissions)
            if error:
                return error

        output_dir, submissions = self._resolve_context(output_dir, submissions)

        for label, partial_output in submissions.items():
            output_path = str(Path(output_dir) / label / "review-output.json")
            result = self._orchestrator.orchestrate(partial_output, output_path)
            if "error" in result:
                return {"error": result["error"], "failed_at": label}

        violations = self._violation_reader.read_violations(output_dir)
        return self._response_formatter.format(violations, output_dir)

    def _resolve_context(self, output_dir: str, submissions: dict) -> tuple:
        ctx = self._context_loader.load()
        if not ctx:
            return output_dir, submissions
        output_dir = ctx.get("output_dir", output_dir)
        auth_path = ctx.get("file_path", "")
        if auth_path:
            submissions = {
                label: {
                    **po,
                    "files": [
                        {**f, "file_path": auth_path}
                        for f in po.get("files", [])
                    ],
                }
                for label, po in submissions.items()
            }
        return output_dir, submissions
