"""Tests source identity attribution without parsing workflow alias strings."""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from review.review_unit_source_identity_resolver import ReviewUnitSourceIdentityResolver


def test_derives_identity_from_the_normalized_review_unit():
    decoder = Mock()
    decoder.decode.return_value.target.source_identity = "/project/Feature.swift"
    decoder.decode.return_value.target.unit_identity = "protocol:Reading"
    inputs = WorkflowContextValues(entries=[WorkflowContextValue(name="review_unit", value="raw-unit")])

    identity = ReviewUnitSourceIdentityResolver(decoder).resolve(inputs)

    assert identity.source_identity == "/project/Feature.swift"
    assert identity.unit_identity == "protocol:Reading"
    decoder.decode.assert_called_once_with("raw-unit", "review unit provenance")


@pytest.mark.parametrize("supplied", [False, True])
def test_absent_or_custom_non_source_input_does_not_claim_a_verified_identity(supplied):
    decoder = Mock()
    decoder.decode.side_effect = FlowValidationError("Not a normalized source unit")
    inputs = WorkflowContextValues(entries=[WorkflowContextValue(name="review_unit", value="custom")] if supplied else [])

    assert ReviewUnitSourceIdentityResolver(decoder).resolve(inputs) is None
    assert decoder.decode.call_count == int(supplied)
