"""
solid-name: TestLiveRuleContracts
solid-category: unit-test
solid-description: Keeps live rule metrics aligned with their deterministic workflow contracts.
"""

import unittest

import test_lsp_validation_flow as lsp_deterministic
import test_lsp_validation_live as lsp_live
import test_ocp_validation_flow as ocp_deterministic
import test_ocp_validation_live as ocp_live
from rule_validation_e2e_live_base import RuleValidationE2ELiveBase
from rule_validation_scenario import RuleValidationScenario
from rule_metric_result_expectation import RuleMetricResultExpectation


class TestLiveRuleContracts(unittest.TestCase):
    def test_ocp_live_metrics_match_the_deterministic_contract(self) -> None:
        self._assert_metric_contract(
            ocp_deterministic.TestOCPValidationFlow.SCENARIO,
            ocp_live.TestCodexOCPValidationLive(),
        )

    def test_lsp_live_metrics_match_the_deterministic_contract(self) -> None:
        self._assert_metric_contract(
            lsp_deterministic.TestLSPValidationFlow.SCENARIO,
            lsp_live.TestCodexLSPValidationLive(),
        )

    def _assert_metric_contract(
        self,
        scenario: RuleValidationScenario,
        case: RuleValidationE2ELiveBase,
    ) -> None:
        expected = [
            RuleMetricResultExpectation(
                step_id=metric.step_id,
                metric_id=metric.metric_id,
                observation_id=metric.observation_id,
                value=metric.value,
                severity=metric.severity,
            )
            for metric in scenario.metrics
        ]

        self.assertEqual(case._validation_expectation().metrics, expected)
