"""Checks injected schema validation and its existing error-result contract."""

import sys
from pathlib import Path
from unittest.mock import Mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.json_schema_validating import JsonSchemaValidator
from jsonschema_error_formatter import format_schema_errors


def test_uses_supplied_formatter_with_original_schema_and_value() -> None:
    formatter = Mock(return_value=["invalid value"])
    schema, value = {"type": "integer"}, "text"

    result = JsonSchemaValidator(format_errors=formatter).validate(schema, value)

    formatter.assert_called_once_with(schema, value)
    assert result.ok is False
    assert result.errors == ["invalid value"]


@pytest.mark.parametrize("value, valid", [(4, True), ("4", False)])
def test_constructing_site_can_supply_real_schema_formatter(
    value: object, valid: bool
) -> None:
    result = JsonSchemaValidator(format_errors=format_schema_errors).validate(
        {"type": "integer"}, value
    )

    assert result.ok is valid
    assert bool(result.errors) is not valid


@pytest.mark.parametrize(
    "error, message",
    [
        (ImportError("missing"), "jsonschema package not installed"),
        (RuntimeError("formatter failed"), "formatter failed"),
    ],
)
def test_preserves_validation_failure_result(error: Exception, message: str) -> None:
    result = JsonSchemaValidator(format_errors=Mock(side_effect=error)).validate({}, {})

    assert result.ok is False
    assert result.errors == [message]
