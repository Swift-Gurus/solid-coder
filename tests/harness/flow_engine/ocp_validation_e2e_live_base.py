"""Defines the backend-neutral live OCP workflow expectations."""

from __future__ import annotations

from pathlib import Path

from rule_validation_e2e_live_base import RuleValidationE2ELiveBase


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = _PROJECT_ROOT / "tests" / "principles" / "OCP" / "fixtures" / "fixture-1.swift"


"""
solid-name: OCPValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Supplies the OCP scenario and exact observations to the shared live executable-rule contract.
"""
class OCPValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "ocp"
    ARTIFACT_SCENARIO = "ocp"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS = [
        "sealed_variation_points",
        "untestable_dependencies",
        "testable_direct_count",
    ]
    EXPECTED_METRIC_IDS = ["OCP-1", "OCP-2", "OCP-3"]
    EXPECTED_VALUES = [2, 0, 0]
    EXPECTED_METRIC_SEVERITIES = ["SEVERE", "COMPLIANT", "COMPLIANT"]
    EXPECTED_FINAL_SEVERITY = "SEVERE"
