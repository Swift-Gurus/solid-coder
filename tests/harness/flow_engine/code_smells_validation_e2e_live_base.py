"""Defines the backend-neutral live Code Smells expectations."""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from rule_validation_e2e_live_base import RuleValidationE2ELiveBase

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = (
    _PROJECT_ROOT
    / "tests"
    / "principles"
    / "code-smells"
    / "fixtures"
    / "fixture-1.swift"
)


"""
solid-name: CodeSmellsValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039, SPEC-055]
solid-description: Supplies the file-scoped Code Smells fixture and locked MCP-scored observations to the shared live rule contract.
"""


class CodeSmellsValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "code-smells"
    REVIEW_WORKFLOW_ID = "solid-file-review-aggregate"
    ARTIFACT_SCENARIO = "code-smells"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS: ClassVar[list[str]] = [
        "static_logic_count",
        "class_struct_count",
        "inline_type_count",
    ]
    EXPECTED_METRIC_IDS: ClassVar[list[str]] = ["CS-1", "CS-2", "CS-3"]
    EXPECTED_VALUES: ClassVar[list[int]] = [1, 2, 1]
    EXPECTED_METRIC_SEVERITIES: ClassVar[list[str]] = ["SEVERE", "SEVERE", "SEVERE"]
    EXPECTED_FINAL_SEVERITY = "SEVERE"
    EXPECTED_ANALYSIS_STEP_IDS: ClassVar[list[str]] = [
        "analyze_source",
        "select_declarations",
        "classify_declarations",
        "bind_classifications",
    ]
    EXCEPTION_STEP_IDS: ClassVar[list[str]] = []
