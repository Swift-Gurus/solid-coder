"""Defines the backend-neutral live Frontmatter expectations."""

from __future__ import annotations

from pathlib import Path

from rule_validation_e2e_live_base import RuleValidationE2ELiveBase


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = (
    _PROJECT_ROOT
    / "tests"
    / "principles"
    / "frontmatter"
    / "fixtures"
    / "fixture-1.swift"
)


"""
solid-name: FrontmatterValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039, SPEC-055]
solid-description: Supplies the file-scoped Frontmatter fixture and locked MCP-scored observations to the shared live rule contract.
"""
class FrontmatterValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "frontmatter"
    ARTIFACT_SCENARIO = "frontmatter"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS = [
        "missing_frontmatter_count",
        "name_mismatch_count",
        "invalid_category_count",
        "incorrect_stack_count",
        "bad_description_count",
    ]
    EXPECTED_METRIC_IDS = ["FM-1", "FM-2", "FM-3", "FM-4", "FM-5"]
    EXPECTED_VALUES = [1, 0, 0, 0, 0]
    EXPECTED_METRIC_SEVERITIES = [
        "SEVERE",
        "COMPLIANT",
        "COMPLIANT",
        "COMPLIANT",
        "COMPLIANT",
    ]
    EXPECTED_FINAL_SEVERITY = "SEVERE"
    ALLOW_AUXILIARY_STEPS = True
