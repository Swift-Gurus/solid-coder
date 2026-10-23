"""Defines the backend-neutral live Unit Testing expectations."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from rule_validation_e2e_live_base import RuleValidationE2ELiveBase

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = (
    _PROJECT_ROOT
    / "tests"
    / "testing"
    / "unit"
    / "swift"
    / "fixtures"
    / "fixture-1.swift"
)


"""
solid-name: UnitTestingValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039, SPEC-055]
solid-description: Supplies the file-scoped Unit Testing fixture and locked MCP-scored observations to the shared live rule contract.
"""


class UnitTestingValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "unit-testing"
    ARTIFACT_SCENARIO = "unit-testing"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS: ClassVar[list[str]] = [
        "isolation_violations",
        "structure_violations",
        "naming_violations",
        "test_double_violations",
        "setup_violations",
        "framework_violations",
    ]
    EXPECTED_METRIC_IDS: ClassVar[list[str]] = [
        "TEST-1",
        "TEST-2",
        "TEST-3",
        "TEST-4",
        "TEST-5",
        "TEST-6",
    ]
    EXPECTED_VALUES: ClassVar[list[int]] = [1, 2, 3, 1, 1, 1]
    EXPECTED_METRIC_SEVERITIES = ["SEVERE"] * 6
    EXPECTED_FINAL_SEVERITY = "SEVERE"
    ALLOW_AUXILIARY_STEPS = True
