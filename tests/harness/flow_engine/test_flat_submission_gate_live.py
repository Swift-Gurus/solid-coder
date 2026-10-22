"""Runs the real gate contract with the opt-in flat submission envelope."""

import test_solid_gate_on_write_live as gate_tests


"""
solid-name: TestCodexFlatSubmissionGateLive
solid-category: integration-test
solid-spec: [SPEC-068]
solid-description: Runs the unchanged production gate fixture and assertions with flat Codex submissions.
"""
class TestCodexFlatSubmissionGateLive(gate_tests.TestCodexSolidGateOnWriteLive):
    SUBMISSION_FORMAT = "flat_array"


"""
solid-name: TestClaudeFlatSubmissionGateLive
solid-category: integration-test
solid-spec: [SPEC-068]
solid-description: Runs the unchanged production gate fixture and assertions with flat Claude submissions.
"""
class TestClaudeFlatSubmissionGateLive(gate_tests.TestClaudeSolidGateOnWriteLive):
    SUBMISSION_FORMAT = "flat_array"
