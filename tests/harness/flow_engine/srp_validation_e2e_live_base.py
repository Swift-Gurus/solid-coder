"""Defines the backend-neutral live SRP workflow assertions."""

from __future__ import annotations

from pathlib import Path

from rule_validation_e2e_live_base import RuleValidationE2ELiveBase


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = _PROJECT_ROOT / "tests" / "principles" / "SRP" / "fixtures" / "fixture-1.swift"


"""
solid-name: SRPValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-034, SPEC-039]
solid-description: Supplies the SRP scenario and exact rule-result assertions to the shared live workflow E2E contract.
"""
class SRPValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "srp"
    ARTIFACT_SCENARIO = "srp"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS = [
        "verb_count",
        "cohesion_groups",
        "stakeholder_count",
    ]
    EXPECTED_METRIC_IDS = ["SRP-1", "SRP-2", "SRP-3"]
    EXPECTED_VALUES = [6, 2, 2]
    EXPECTED_METRIC_SEVERITIES = ["SEVERE", "SEVERE", "SEVERE"]
    EXPECTED_FINAL_SEVERITY = "SEVERE"
