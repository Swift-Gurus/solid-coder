"""Defines the backend-neutral live ISP workflow expectations."""

from __future__ import annotations

from pathlib import Path

from rule_validation_e2e_live_base import RuleValidationE2ELiveBase


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = _PROJECT_ROOT / "tests" / "principles" / "ISP" / "fixtures" / "fixture-1.swift"


"""
solid-name: ISPValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Supplies the ISP scenario and exact observations to the shared live executable-rule contract.
"""
class ISPValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "isp"
    ARTIFACT_SCENARIO = "isp"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS = [
        "width",
        "min_coverage",
        "cohesion_groups",
    ]
    EXPECTED_METRIC_IDS = ["ISP-1", "ISP-2", "ISP-3"]
    EXPECTED_VALUES = [10, 50, 2]
    EXPECTED_METRIC_SEVERITIES = ["SEVERE", "SEVERE", "SEVERE"]
    EXPECTED_FINAL_SEVERITY = "SEVERE"
