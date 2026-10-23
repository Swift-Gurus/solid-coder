"""Validates live DRY scenario wiring without launching models."""

import unittest
from unittest.mock import patch

import test_dry_validation_live as live_cases
from review.prepare_review_input import PrepareReviewInput

"""
solid-name: TestDRYLiveScenarios
solid-category: unit-test
solid-spec: [SPEC-040, SPEC-060]
solid-description: Verifies that live DRY cases use the shared review workflow, isolated source project, and normalized file input.
"""


class TestDRYLiveScenarios(unittest.TestCase):
    def setUp(self) -> None:
        self.case = live_cases.TestCodexDRYValidationLive(
            "test_workflow_satisfies_its_live_contract"
        )
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)

    def test_default_scenario_uses_shared_review_preparation(self) -> None:
        scenario = self.case.scenario

        self.assertEqual(scenario.workflow_id, "solid-review")
        self.assertIsInstance(scenario.parameters, PrepareReviewInput)
        self.assertEqual(
            scenario.parameters.target.path, self.case._source_project.review_target
        )
        self.assertEqual(
            self.case.execution_project_root, self.case._source_project.root
        )
        self.assertEqual(
            list(self.case.execution_project_root.rglob("*.swift")),
            [scenario.parameters.target.path],
        )

    def test_identical_wrappers_use_shared_runner_with_duplicate_expectations(
        self,
    ) -> None:
        with (
            patch.object(self.case, "_run_scenario") as run,
            patch.object(self.case, "assert_workflow") as validate,
        ):
            self.case.test_identical_wrappers_are_duplicate_sites()

        scenario = run.call_args.args[0]
        self.assertEqual(scenario.workflow_id, "solid-review")
        self.assertIsInstance(scenario.parameters, PrepareReviewInput)
        self.assertEqual(
            scenario.parameters.target.path, self.case._source_project.review_target
        )
        self.assertEqual(scenario.artifact_scope.scenario, "dry-extracted-helper")
        source = self.case.FIXTURE.read_text(encoding="utf-8")
        self.assertEqual(self.case.FIXTURE.name, "fixture-2.swift")
        self.assertEqual(
            self.case._source_project.review_target.read_text(encoding="utf-8"), source
        )
        self.assertIn(source, scenario.model_context)
        self.assertEqual(self.case.EXPECTED_VALUES, [0, 0, 2])
        self.assertEqual(
            self.case.EXPECTED_METRIC_SEVERITIES, ["COMPLIANT", "COMPLIANT", "SEVERE"]
        )
        self.assertEqual(self.case.EXPECTED_FINAL_SEVERITY, "SEVERE")
        validate.assert_called_once_with(run.return_value)

    def test_protocol_scenario_uses_the_same_root_and_review_contract(self) -> None:
        with (
            patch.object(self.case, "_run_scenario") as run,
            patch.object(self.case, "assert_rule_workflow"),
            patch.object(self.case, "_assert_candidate_classification"),
        ):
            self.case.test_existing_protocol_with_different_names_is_an_exact_reuse_miss()

        scenario = run.call_args.args[0]
        self.assertEqual(scenario.workflow_id, "solid-review")
        self.assertIsInstance(scenario.parameters, PrepareReviewInput)
        self.assertEqual(
            scenario.parameters.target.path, self.case._source_project.review_target
        )
        self.assertEqual(
            self.case.execution_project_root, self.case._source_project.root
        )
        self.assertEqual(
            {path.name for path in self.case.execution_project_root.rglob("*.swift")},
            {"ReviewTarget.swift", "RemoteContentLoading.swift"},
        )
