"""Defines the backend-neutral live UI Testing expectations."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from rule_validation_e2e_live_base import RuleValidationE2ELiveBase

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = (
    _PROJECT_ROOT
    / "tests"
    / "validators"
    / "apple"
    / "ui-testing"
    / "fixtures"
    / "fixture-1.swift"
)


"""
solid-name: UITestingValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039, SPEC-055]
solid-description: Supplies the file-scoped UI Testing fixture and locked MCP-scored observations to the shared live rule contract.
"""


class UITestingValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "ui-testing"
    ARTIFACT_SCENARIO = "ui-testing"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS: ClassVar[list[str]] = [
        "flow_violations",
        "base_class_violations",
        "grouping_violations",
        "sync_violations",
        "identifier_violations",
    ]
    EXPECTED_METRIC_IDS: ClassVar[list[str]] = [
        "UITEST-1",
        "UITEST-2",
        "UITEST-3",
        "UITEST-4",
        "UITEST-5",
    ]
    EXPECTED_VALUES: ClassVar[list[int]] = [2, 1, 1, 9, 8]
    EXPECTED_METRIC_SEVERITIES = ["SEVERE"] * 5
    EXPECTED_FINAL_SEVERITY = "SEVERE"
    ALLOW_AUXILIARY_STEPS = True
