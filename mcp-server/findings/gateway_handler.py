"""Provides the model-facing gateway for scoring, findings, rules, and fixes."""

from typing import Any, Optional, Protocol

from findings.fix_submitter import FixSubmitting
from findings.mcp_batch_submission_handling import McpBatchSubmissionHandling
from findings.submit_orchestrator import ResolveAndScoring, SubmitOrchestrating
from rules.rules_handler import RulesLoading


"""
solid-name: ScoringSeverity
solid-category: abstraction
solid-description: Contract for producing server-authoritative severity results from review measurements.
"""
class ScoringSeverity(Protocol):
    def score_severity(self, partial_outputs: list) -> dict: ...


"""
solid-name: GatewayHandling
solid-category: abstraction
solid-description: Contract for the model-facing scoring and rule-loading gateway capabilities.
"""
class GatewayHandling(ScoringSeverity, RulesLoading, Protocol):
    """Composed protocol for all gateway tool operations."""

    def submit_findings(self, partial_output: dict, output_path: str) -> dict: ...

    def submit_batch_findings(
        self,
        output_dir: str,
        submissions: object,
    ) -> dict: ...

    def submit_fix(self, output_dir: str, fixes: list) -> dict: ...


"""
solid-name: GatewayHandler
solid-category: service
solid-description: Routes model-facing gateway requests to dedicated application capabilities.
"""
class GatewayHandler:
    """Pure facade over protocol-typed gateway capabilities."""

    def __init__(
        self,
        scoring: ScoringSeverity,
        submit_orchestrator: SubmitOrchestrating,
        rules: RulesLoading,
        fix_submitter: FixSubmitting,
        batch_submission: McpBatchSubmissionHandling,
    ) -> None:
        self._scoring = scoring
        self._submit_orchestrator = submit_orchestrator
        self._rules = rules
        self._fix_submitter = fix_submitter
        self._batch_submission = batch_submission

    def score_severity(self, partial_outputs: list) -> dict[str, Any]:
        return self._scoring.score_severity(partial_outputs)

    def submit_findings(self, partial_output: dict, output_path: str) -> dict[str, Any]:
        return self._submit_orchestrator.orchestrate(partial_output, output_path)

    def submit_batch_findings(
        self,
        output_dir: str,
        submissions: object,
    ) -> dict[str, Any]:
        return self._batch_submission.submit_batch_findings(output_dir, submissions)

    def submit_fix(self, output_dir: str, fixes: list) -> dict[str, Any]:
        return self._fix_submitter.submit_fix(output_dir, fixes)

    def load_detection_rules(
        self, principle: Optional[str] = None, matched_tags: Optional[list] = None,
    ) -> dict[str, Any]:
        return self._rules.load_detection_rules(principle, matched_tags)

    def load_fix_instructions(self, metric_id: str) -> str:
        return self._rules.load_fix_instructions(metric_id)
