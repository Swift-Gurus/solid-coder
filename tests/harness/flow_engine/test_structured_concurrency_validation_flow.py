"""
solid-name: test_structured_concurrency_validation_flow
solid-category: integration-test
solid-spec: [SPEC-039]
solid-description: Verifies structured-concurrency applicability, canonical instructions, typed observations, scoring, exceptions, and audit behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_PROJECT_ROOT / "mcp-server"))

from rule_analysis_expectation import RuleAnalysisExpectation  # noqa: E402
from rule_metric_expectation import RuleMetricExpectation  # noqa: E402
from rule_validation_flow_contract import RuleValidationFlowContract  # noqa: E402
from rule_validation_scenario import RuleValidationScenario  # noqa: E402


class TestStructuredConcurrencyValidationFlow(RuleValidationFlowContract):
    __test__ = True
    PROJECT_ROOT = _PROJECT_ROOT
    SCENARIO = RuleValidationScenario(
        workflow_id="structured-concurrency",
        rule_path=(
            _PROJECT_ROOT
            / "references"
            / "coding"
            / "apple"
            / "StructuredConcurrency"
            / "rule.md"
        ),
        fixture_path=(
            _PROJECT_ROOT
            / "tests"
            / "coding"
            / "apple"
            / "structured-concurrency"
            / "fixtures"
            / "fixture-1.swift"
        ),
        analysis=[
            RuleAnalysisExpectation(
                step_id="classify_concurrency_observations",
                output={
                    "observations": [
                        {
                            "classification": "MODEL_MIXING",
                            "location": "synchronize",
                            "is_exception": False,
                            "reasoning": "The async method also dispatches with GCD.",
                            "evidence": "DispatchQueue.main.async inside synchronize().",
                        },
                        {
                            "classification": "ORPHANED_OR_LEAKED_TASK",
                            "location": "synchronize Task closure",
                            "is_exception": False,
                            "reasoning": "The task has no stored handle or cancellation path.",
                            "evidence": "Task { await refreshCache() }.",
                        },
                        {
                            "classification": "SAFETY_BYPASS",
                            "location": "ProfileSynchronizer declaration",
                            "is_exception": False,
                            "reasoning": "Unchecked Sendable bypasses compiler checking.",
                            "evidence": "ProfileSynchronizer: @unchecked Sendable.",
                        },
                        *(
                            {
                                "classification": "INDEPENDENT_SEQUENTIAL_AWAIT",
                                "location": f"synchronize {method}",
                                "is_exception": False,
                                "reasoning": "The await is independent of its siblings.",
                                "evidence": f"await {method}()",
                            }
                            for method in (
                                "fetchProfile",
                                "fetchPermissions",
                                "fetchPreferences",
                            )
                        ),
                        {
                            "classification": "BLOCKING_BRIDGE",
                            "location": "synchronize semaphore wait",
                            "is_exception": False,
                            "reasoning": "A semaphore blocks the async method.",
                            "evidence": "DispatchSemaphore followed by wait().",
                        },
                        {
                            "classification": "RAW_DURATION",
                            "location": "synchronize Task.sleep",
                            "is_exception": False,
                            "reasoning": "The sleep uses a raw nanosecond literal.",
                            "evidence": "Task.sleep(nanoseconds: 1_000_000_000).",
                        },
                    ],
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
    )

    def test_observation_exception_excludes_only_matching_metric(self) -> None:
        started = self._start()
        observations = [
            {
                **observation,
                "is_exception": (
                    observation["classification"]
                    == "ORPHANED_OR_LEAKED_TASK"
                ),
            }
            for observation in self.SCENARIO.analysis[0].output["observations"]
        ]

        exception = self.sut.flow_next({
            started.steps[0].instance_id: {"observations": observations},
        })
        completed = self.sut.flow_next({
            exception.steps[0].instance_id: {
                "is_exception": False,
                "additional_info": {
                    "reasoning": "Only the task observation is exempt.",
                    "evidence": "The remaining findings still apply.",
                },
            },
        })

        self.assertEqual(completed.status, "done", completed.error)
        result = self._rule_result(started.run_id)
        task_metric = next(
            metric for metric in result.metrics if metric.metric_id == "SC-2"
        )
        self.assertEqual(task_metric.value, 0)
        self.assertEqual(task_metric.severity, "COMPLIANT")
        self.assertEqual(result.severity, "SEVERE")
