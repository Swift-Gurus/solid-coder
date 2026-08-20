"""Defines the backend-neutral live LSP workflow expectations."""

from __future__ import annotations

from pathlib import Path

from rule_validation_e2e_live_base import RuleValidationE2ELiveBase


_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_FIXTURE = _PROJECT_ROOT / "tests" / "principles" / "LSP" / "fixtures" / "fixture-1.swift"


"""
solid-name: LSPValidationE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Supplies the LSP scenario and exact observations to the shared live executable-rule contract.
"""
class LSPValidationE2ELiveBase(RuleValidationE2ELiveBase):
    WORKFLOW_ID = "lsp"
    ARTIFACT_SCENARIO = "lsp"
    FIXTURE = _FIXTURE
    EXPECTED_STEP_IDS = [
        "type_checks",
        "contract_violations",
        "fatal_error_methods",
        "empty_methods",
    ]
    EXPECTED_METRIC_IDS = [
        "LSP-1",
        "LSP-2",
        "LSP-3",
        "LSP-4",
    ]
    EXPECTED_VALUES = [0, 0, 1, 0]
    EXPECTED_METRIC_SEVERITIES = [
        "COMPLIANT",
        "COMPLIANT",
        "SEVERE",
        "COMPLIANT",
    ]
    EXPECTED_FINAL_SEVERITY = "SEVERE"
