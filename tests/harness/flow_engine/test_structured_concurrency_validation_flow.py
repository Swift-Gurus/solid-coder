"""
solid-name: test_structured_concurrency_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039, SPEC-055]
solid-description: Verifies fact-based concurrency scoring, scoped exceptions, unavailable outcomes, and evidence through the real bundled workflow.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_analysis_expectation import RuleAnalysisExpectation
from rule_metric_expectation import RuleMetricExpectation
from rule_validation_flow_contract import RuleValidationFlowContract
from rule_validation_scenario import RuleValidationScenario


class TestStructuredConcurrencyValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="structured-concurrency",
        rule_path=_PROJECT_ROOT / "references/coding/apple/StructuredConcurrency/rule.md",
        fixture_path=_PROJECT_ROOT / "tests/coding/apple/structured-concurrency/fixtures/fixture-1.swift",
        analysis=[
            RuleAnalysisExpectation(
                step_id="classify_concurrency_models",
                output={
                    "verification": {
                        "status": "VERIFIED",
                        "reasoning": "The complete fixture provides the relevant source.",
                        "evidence": "ProfileSynchronizer in fixture-1.swift."
                    },
                    "models": [
                        {
                            "has_async": True,
                            "has_gcd": True,
                            "has_async_callbacks": False,
                            "legacy_bridge_only": False,
                            "location": "ProfileSynchronizer",
                            "reasoning": "The async type dispatches unrelated GCD work.",
                            "evidence": "async synchronize(); DispatchQueue.main.async"
                        }
                    ]
                },
            ),
            RuleAnalysisExpectation(
                step_id="classify_task_lifecycle",
                output={
                    "verification": {
                        "status": "VERIFIED",
                        "reasoning": "The complete fixture provides the relevant source.",
                        "evidence": "ProfileSynchronizer in fixture-1.swift."
                    },
                    "tasks": [
                        {
                            "kind": "TASK",
                            "has_stored_handle": False,
                            "has_cancellation_path": False,
                            "is_test_code": False,
                            "location": "synchronize Task",
                            "reasoning": "The created task is neither retained nor cancelled.",
                            "evidence": "Task { await refreshCache() }"
                        }
                    ]
                },
            ),
            RuleAnalysisExpectation(
                step_id="classify_safety_bypasses",
                output={
                    "verification": {
                        "status": "VERIFIED",
                        "reasoning": "The complete fixture provides the relevant source.",
                        "evidence": "ProfileSynchronizer in fixture-1.swift."
                    },
                    "bypasses": [
                        {
                            "kind": "UNCHECKED_SENDABLE",
                            "is_synchronization_primitive": False,
                            "location": "ProfileSynchronizer annotation",
                            "reasoning": "The type synchronizes profiles, not OS locking.",
                            "evidence": "ProfileSynchronizer: @unchecked Sendable"
                        }
                    ]
                },
            ),
            RuleAnalysisExpectation(
                step_id="classify_sequential_awaits",
                output={
                    "verification": {
                        "status": "VERIFIED",
                        "reasoning": "The complete fixture provides the relevant source.",
                        "evidence": "ProfileSynchronizer in fixture-1.swift."
                    },
                    "awaits": [
                        {
                            "has_sequential_peer": True,
                            "has_data_dependency": False,
                            "requires_ordering": False,
                            "has_conflicting_effects": False,
                            "location": "synchronize fetchProfile",
                            "reasoning": "The calls have no result dependencies or state effects.",
                            "evidence": "await fetchProfile(); private func fetchProfile() async {}"
                        },
                        {
                            "has_sequential_peer": True,
                            "has_data_dependency": False,
                            "requires_ordering": False,
                            "has_conflicting_effects": False,
                            "location": "synchronize fetchPermissions",
                            "reasoning": "The calls have no result dependencies or state effects.",
                            "evidence": "await fetchPermissions(); private func fetchPermissions() async {}"
                        },
                        {
                            "has_sequential_peer": True,
                            "has_data_dependency": False,
                            "requires_ordering": False,
                            "has_conflicting_effects": False,
                            "location": "synchronize fetchPreferences",
                            "reasoning": "The calls have no result dependencies or state effects.",
                            "evidence": "await fetchPreferences(); private func fetchPreferences() async {}"
                        },
                        {
                            "has_sequential_peer": False,
                            "has_data_dependency": False,
                            "requires_ordering": False,
                            "has_conflicting_effects": False,
                            "location": "Task refreshCache",
                            "reasoning": "This await is alone in its own Task closure.",
                            "evidence": "Task { await refreshCache() }"
                        },
                        {
                            "has_sequential_peer": False,
                            "has_data_dependency": False,
                            "requires_ordering": True,
                            "has_conflicting_effects": False,
                            "location": "synchronize Task.sleep",
                            "reasoning": "The synchronization wait separates this delay from the fetch sequence.",
                            "evidence": "semaphore.wait(); try? await Task.sleep(nanoseconds: 1_000_000_000)"
                        }
                    ]
                },
            ),
            RuleAnalysisExpectation(
                step_id="classify_bridges",
                output={
                    "verification": {
                        "status": "VERIFIED",
                        "reasoning": "The complete fixture provides the relevant source.",
                        "evidence": "ProfileSynchronizer in fixture-1.swift."
                    },
                    "bridges": [
                        {
                            "kind": "BLOCKING_WAIT",
                            "blocks_async_execution": True,
                            "location": "synchronize semaphore.wait",
                            "reasoning": "The synchronous wait blocks the async function.",
                            "evidence": "let semaphore = DispatchSemaphore(value: 0); semaphore.wait()"
                        }
                    ]
                },
            ),
            RuleAnalysisExpectation(
                step_id="classify_durations",
                output={
                    "verification": {
                        "status": "VERIFIED",
                        "reasoning": "The complete fixture provides the relevant source.",
                        "evidence": "ProfileSynchronizer in fixture-1.swift."
                    },
                    "durations": [
                        {
                            "uses_nanosecond_sleep": True,
                            "is_raw_integer_duration": True,
                            "location": "synchronize Task.sleep",
                            "reasoning": "A raw nanosecond sleep is used.",
                            "evidence": "Task.sleep(nanoseconds: 1_000_000_000)"
                        }
                    ]
                },
            ),
        ],
        metrics=[
            RuleMetricExpectation(step_id="model_mixing", metric_id="SC-1", detection_id="SC-1", detection_name="Concurrency Model Mixing", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="orphaned_tasks", metric_id="SC-2", detection_id="SC-2", detection_name="Unstructured Task Lifecycle", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="safety_bypasses", metric_id="SC-3", detection_id="SC-3", detection_name="Concurrency Safety Bypasses", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="independent_sequential_awaits", metric_id="SC-4", detection_id="SC-4", detection_name="Sequential vs Concurrent Await", value=3, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="blocking_bridges", metric_id="SC-5", detection_id="SC-5", detection_name="Sync-to-Async Bridging", value=1, severity="SEVERE", mcp_owned=True),
            RuleMetricExpectation(step_id="raw_duration_count", metric_id="SC-6", detection_id="SC-6", detection_name="Duration API", value=1, severity="SEVERE", mcp_owned=True),
        ],
        final_severity="SEVERE",
        included_file_extensions=[".swift"],
        included_tags=["structured-concurrency"],
        has_authored_exceptions=False,
    )

    def setUp(self) -> None:
        self.SCENARIO = self.SCENARIO.model_copy(deep=True)
        super().setUp()

    def test_exposes_six_independent_fact_classifiers(self) -> None:
        started = self._start()

        self.assertEqual(
            [step.step_id for step in started.steps],
            [analysis.step_id for analysis in self.SCENARIO.analysis],
        )

    def test_uses_canonical_rule_detection_and_exception_instructions(self) -> None:
        checkpoint = self._complete_workflow()
        prompts = "\n".join(checkpoint.prompts)

        for required in [
            "necessary bridge", "framework-managed cancellation",
            "does not inherit", "Test code is exempt from task lifecycle",
            "synchronization primitive", "OSAllocatedUnfairLock<State>",
            "required ordering", "shared-state effects", "exactly once",
            "synchronization and timing order",
            "Task.sleep(nanoseconds:)", "no rule-wide exception",
            "UNABLE_TO_VERIFY",
        ]:
            with self.subTest(required=required):
                self.assertIn(required, prompts)
        self.assertNotIn("Count ", prompts)
        self.assertNotIn("Scoring:", prompts)
        self.assertNotIn("SEVERE", prompts)

    def test_observation_exception_excludes_only_matching_metric(self) -> None:
        self.SCENARIO.analysis[1].output["tasks"][0]["is_test_code"] = True

        completed = self._complete_workflow()
        result = self._rule_result(completed.run_id)

        self.assertEqual([metric.value for metric in result.metrics], [1, 0, 1, 3, 1, 1])
        self.assertEqual(result.severity, "SEVERE")
        self.assertFalse(result.exception.is_exception)

    def test_swiftui_task_does_not_exempt_its_nested_unstructured_task(self) -> None:
        tasks = self.SCENARIO.analysis[1].output["tasks"]
        tasks.insert(0, {
            **tasks[0],
            "kind": "SWIFTUI_TASK",
            "location": "View.body .task",
            "has_cancellation_path": True,
            "evidence": ".task { Task { await refreshCache() } }",
        })

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[1].value, 1)

    def test_synchronization_primitive_exempts_only_unchecked_sendable(self) -> None:
        bypasses = self.SCENARIO.analysis[2].output["bypasses"]
        bypasses[0]["is_synchronization_primitive"] = True
        bypasses.append({
            **bypasses[0],
            "kind": "NONISOLATED_UNSAFE",
            "location": "Lock unsafe member",
            "evidence": "nonisolated(unsafe) var state",
        })

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[2].value, 1)

    def test_lock_owned_state_without_a_bypass_scores_zero_safety_bypasses(self) -> None:
        self.SCENARIO.analysis[2].output["bypasses"] = []

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[2].value, 0)

    def test_necessary_continuation_does_not_exempt_invalid_resumption(self) -> None:
        self.SCENARIO.analysis[4].output["bridges"] = [
            {
                "kind": "CONTINUATION",
                "native_async_available": False,
                "resumes_exactly_once": True,
                "location": "validBridge",
                "reasoning": "A necessary callback bridge resumes once.",
                "evidence": "legacyCallback { continuation.resume(returning: $0) }",
            },
            {
                "kind": "CONTINUATION",
                "native_async_available": False,
                "resumes_exactly_once": False,
                "location": "invalidBridge",
                "reasoning": "One branch never resumes.",
                "evidence": "if failed { return }",
            },
            {
                "kind": "CONTINUATION",
                "native_async_available": True,
                "resumes_exactly_once": True,
                "location": "unnecessaryBridge",
                "reasoning": "A native async alternative is available.",
                "evidence": "API exposes async fetch()",
            },
        ]

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[4].value, 2)

    def test_await_dependency_ordering_and_shared_effects_are_not_independent(self) -> None:
        awaits = self.SCENARIO.analysis[3].output["awaits"]
        awaits[0]["has_data_dependency"] = True
        awaits[1]["requires_ordering"] = True
        awaits[2]["has_conflicting_effects"] = True

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[3].value, 0)

    def test_duplicate_await_observations_do_not_increase_the_measurement(self) -> None:
        awaits = self.SCENARIO.analysis[3].output["awaits"]
        awaits.append({**awaits[0], "reasoning": "The same occurrence was described again."})

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[3].value, 3)

    def test_typed_duration_is_not_raw_and_nanosecond_sleep_counts_once(self) -> None:
        durations = self.SCENARIO.analysis[5].output["durations"]
        durations.append({
            **durations[0],
            "uses_nanosecond_sleep": False,
            "is_raw_integer_duration": False,
            "location": "typed sleep",
            "evidence": "Task.sleep(for: .seconds(2))",
        })

        completed = self._complete_workflow()

        self.assertEqual(self._rule_result(completed.run_id).metrics[5].value, 1)

    def test_unverified_classification_is_unavailable_not_a_compliant_zero(self) -> None:
        self.SCENARIO.analysis[4].output["verification"] = {
            "status": "UNABLE_TO_VERIFY",
            "reasoning": "The wrapped SDK declaration is unavailable.",
            "evidence": "The source imports an unresolved SDK.",
        }
        self.SCENARIO.analysis[4].output["bridges"] = []

        completed = self._complete_workflow()
        result = self._rule_result(completed.run_id)

        self.assertEqual([metric.metric_id for metric in result.unavailable_metrics], ["SC-5"])
        self.assertNotIn("SC-5", [metric.metric_id for metric in result.metrics])
        self.assertTrue(result.unavailable_metrics[0].additional_info.evidence)

    def test_rejects_missing_evidence_before_scoring(self) -> None:
        started = self._start()
        output = self.SCENARIO.analysis[0].output
        del output["models"][0]["evidence"]

        rejected = self.sut.flow_next({started.steps[0].instance_id: output})

        self.assertEqual(rejected.status, "ready")
        self.assertIn("evidence", rejected.steps[0].rejection_reason)

    def test_combined_partial_submission_scores_facts_and_keeps_missing_classifier_pending(self) -> None:
        workflow = self.project_root / "workflow.yaml"
        workflow.write_text(
            "id: concurrency-aggregate-test\n"
            "name: Concurrency Aggregate Test\n"
            "max_turns: 10\n"
            "steps:\n"
            "  - id: targets\n"
            "    prompt: Identify the test target.\n"
            "    outputs:\n"
            "      - name: units\n"
            "        type: data\n"
            "        schema: {type: array, items: {type: object}}\n"
            "  - group: aggregate_reviews\n"
            "    execution: {mode: aggregate}\n"
            "    presentation: {mode: combined}\n"
            "    steps:\n"
            "      - include: {workflow: structured-concurrency}\n"
            "        as: review\n"
            "        depends_on: [targets]\n"
            "        for_each:\n"
            "          source: '{{steps.targets.outputs.units}}'\n"
            "          mode: batch\n"
            "          label: '{{item.target.name}}'\n"
            "        with:\n"
            "          review_unit: '{{item}}'\n",
            encoding="utf-8",
        )
        initial = self.sut.flow_start(str(workflow))
        started = self.sut.flow_next({initial.steps[0].instance_id: {
            "units": [{"target": {"name": self.review_unit_name}}],
        }})
        self.assertIsNone(started.error, started.error)
        self.assertEqual(len(started.steps), 6)
        self.assertTrue(all(step.batch.mode.value == "aggregate" for step in started.steps))
        batch = started.steps[0].batch

        pending = self.sut.flow_next({batch.label: {batch.workflow_alias: {
            item.step_id: item.output for item in self.SCENARIO.analysis[:-1]
        }}})

        self.assertIsNone(pending.error, pending.error)
        self.assertEqual(len(pending.steps), 1)
        self.assertTrue(pending.steps[0].step_id.endswith("classify_durations"))
        last = self.SCENARIO.analysis[-1]
        exception = self.sut.flow_next({batch.label: {batch.workflow_alias: {
            last.step_id: last.output,
        }}})
        self.assertIsNone(exception.error, exception.error)
        self.assertEqual(len(exception.steps), 1)
        self.assertTrue(exception.steps[0].step_id.endswith("classify_exception"))
        completed = self.sut.flow_next({batch.label: {batch.workflow_alias: {
            "classify_exception": self._output_for("classify_exception"),
        }}})

        self.assertEqual(completed.status, "done", completed.error)
        result = self._aggregate_result(initial.run_id).rule_results[0]
        self.assertEqual([metric.value for metric in result.metrics], [1, 1, 1, 3, 1, 1])
        self.assertTrue(all(metric.derivation is not None for metric in result.metrics))
