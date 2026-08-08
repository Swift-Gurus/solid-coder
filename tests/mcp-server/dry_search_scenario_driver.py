"""Executes a DRY-search enforcement integration scenario."""

from pathlib import Path

from findings.batch_submission import BatchSubmission
from findings.batch_submission_parse_result import BatchSubmissionParseResult
from dry_search_scenario import DrySearchScenario
from dry_search_scenario_outcome import DrySearchScenarioOutcome


"""
solid-name: DrySearchScenarioDriver
solid-category: test-support
solid-description: Executes the ordered calls in a DRY-search enforcement scenario.
"""
class DrySearchScenarioDriver:
    def run(
        self,
        scenario: DrySearchScenario,
        output_dir: Path,
    ) -> DrySearchScenarioOutcome:
        output_path = str(output_dir)
        parse_result = BatchSubmissionParseResult(BatchSubmission(()))
        initial = scenario.submission.submit_batch(output_path, parse_result)
        malformed = scenario.search.search(
            tags=["Batch handler routing"],
            output_dir=output_path,
        )
        still_blocked = scenario.submission.submit_batch(
            output_path,
            parse_result,
        )
        zero_match = scenario.search.search(
            query="Batch handler routing",
            output_dir=output_path,
        )
        accepted = scenario.submission.submit_batch(
            output_path,
            parse_result,
        )
        return DrySearchScenarioOutcome(
            initial_error=initial["error"],
            malformed_search=malformed,
            blocked_error=still_blocked["error"],
            zero_match_search=zero_match,
            accepted_violations=accepted["violations"],
            submission_call_count=scenario.submission_backend.submit_batch.call_count,
        )
