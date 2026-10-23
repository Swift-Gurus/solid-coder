"""Ensures hook test helpers cannot turn unexpected failures into passing allow checks."""

import sys
from unittest.mock import Mock

import pytest
import test_utils


@pytest.mark.parametrize(
    "error", [RuntimeError("hook defect"), ValueError("bad hook state")]
)
def test_unexpected_hook_failure_reaches_pytest_and_restores_streams(
    error: Exception,
) -> None:
    original_stdin, original_stdout = sys.stdin, sys.stdout

    with pytest.raises(type(error)) as raised:
        test_utils.call_main({}, Mock(side_effect=error))

    assert raised.value is error
    assert sys.stdin is original_stdin
    assert sys.stdout is original_stdout


@pytest.mark.parametrize("exit_code", [None, 0, 1, 2])
def test_expected_hook_exit_is_still_captured(exit_code: int | None) -> None:
    code, output = test_utils.call_main({}, Mock(side_effect=SystemExit(exit_code)))

    assert code == (exit_code or 0)
    assert output == ""


def test_successful_hook_keeps_stdin_and_output_capture() -> None:
    def main() -> None:
        print(sys.stdin.read())

    assert test_utils.call_main({"tool_name": "Read"}, main) == (
        0,
        '{"tool_name": "Read"}\n',
    )
