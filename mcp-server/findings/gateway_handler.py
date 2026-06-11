"""
solid-description: Provides severity scoring, findings and fix submission, and access to detection rules and fix instructions.
solid-category: service
solid-tags: [utility, service]
"""

import json
from pathlib import Path
from typing import Any, Optional, Protocol

from findings.fix_submitter import FixSubmitting
from findings.submit_orchestrator import ResolveAndScoring, SubmitOrchestrating
from rules.rules_handler import RulesLoading


class ScoringSeverity(Protocol):
    def score_severity(self, partial_outputs: list) -> dict: ...


class GatewayHandling(ScoringSeverity, RulesLoading, Protocol):
    """Composed protocol for all gateway tool operations."""


class GatewayHandler:
    """Pure Facade delegating to ScoringSeverity, SubmitOrchestrating, RulesLoading, and FixSubmitting."""

    def __init__(
        self,
        scoring: ScoringSeverity,
        submit_orchestrator: SubmitOrchestrating,
        rules: RulesLoading,
        fix_submitter: FixSubmitting,
    ) -> None:
        self._scoring = scoring
        self._submit_orchestrator = submit_orchestrator
        self._rules = rules
        self._fix_submitter = fix_submitter

    def score_severity(self, partial_outputs: list) -> dict[str, Any]:
        return self._scoring.score_severity(partial_outputs)

    def submit_findings(self, partial_output: dict, output_path: str) -> dict[str, Any]:
        return self._submit_orchestrator.orchestrate(partial_output, output_path)

    def submit_batch_findings(self, output_dir: str, submissions: dict) -> dict[str, Any]:
        for label, partial_output in submissions.items():
            output_path = str(Path(output_dir) / label / "review-output.json")
            result = self._submit_orchestrator.orchestrate(partial_output, output_path)
            if "error" in result:
                return {"error": result["error"], "failed_at": label}
        violations = self._read_severe_violations(output_dir)
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

    def submit_fix(self, output_dir: str, fixes: list) -> dict[str, Any]:
        return self._fix_submitter.submit_fix(output_dir, fixes)

    def load_detection_rules(
        self, principle: Optional[str] = None, matched_tags: Optional[list] = None,
    ) -> dict[str, Any]:
        return self._rules.load_detection_rules(principle, matched_tags)

    def load_fix_instructions(self, metric_id: str) -> str:
        return self._rules.load_fix_instructions(metric_id)

    def _read_severe_violations(self, output_dir: str) -> list:
        violations = []
        for scored_file in sorted(Path(output_dir).glob("*/review-output.json")):
            try:
                doc = json.loads(scored_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            for file_obj in doc.get("files", []):
                file_path = file_obj.get("file_path", "?")
                for unit in file_obj.get("units", []):
                    unit_name = unit.get("unit_name", "?")
                    unit_metrics = unit.get("metrics", {})
                    for violation in unit.get("violations", []):
                        if violation.get("severity") != "SEVERE":
                            continue
                        rule_id = violation.get("rule_id", "")
                        principle = rule_id.split("-")[0] if "-" in rule_id else rule_id
                        principle_metrics = unit_metrics.get(principle, {})
                        measured = ", ".join(
                            f"{var}={m['value']}"
                            for var, m in principle_metrics.items()
                            if isinstance(m, dict) and "value" in m
                        )
                        violations.append({
                            "rule_id": rule_id,
                            "file_path": file_path,
                            "unit_name": unit_name,
                            "issue": f"{rule_id}: {file_path}, unit {unit_name} — {measured or 'SEVERE violation detected'}",
                            "fix": f"Call mcp__docs__load_fix_for_violation({rule_id}) for specific guidance.",
                        })
        return violations
