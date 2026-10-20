from pathlib import Path

from code_smells_validation_e2e_live_base import CodeSmellsValidationE2ELiveBase


"""
solid-name: CodeSmellsBoundaryE2ELiveBase
solid-category: test-support
solid-spec: [SPEC-066]
solid-description: Reuses the live rule contract for cohesive contracts, direct and extension conformance, and a file-private supporting helper.
"""
class CodeSmellsBoundaryE2ELiveBase(CodeSmellsValidationE2ELiveBase):
    ARTIFACT_SCENARIO = "code-smells-cohesive-boundary"
    FIXTURE = Path(__file__).resolve().parents[3] / "tests/principles/code-smells/fixtures/fixture-2.swift"
    EXPECTED_VALUES = [0, 1, 0]
    EXPECTED_METRIC_SEVERITIES = ["COMPLIANT", "COMPLIANT", "COMPLIANT"]
    EXPECTED_FINAL_SEVERITY = "COMPLIANT"
