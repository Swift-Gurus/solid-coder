"""Checks expected parsing fallbacks and observable boundary failures."""

import json
import runpy
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from gateway_tool_runner import GatewayToolRunner
from handler_store import HandlerStore
from health.llama.json_deserializer import JsonDeserializer
from pipeline.handlers import _default_read
from tool_result_formatter import ToolResultFormatter
from tools_call_handler import ToolsCallHandler


@pytest.mark.parametrize("raw", [b"not json", b"\xff"])
def test_json_deserializer_preserves_malformed_input_fallback(raw: bytes) -> None:
    assert JsonDeserializer().deserialize(raw) is None


def test_json_deserializer_preserves_valid_data() -> None:
    assert JsonDeserializer().deserialize(b'{"ready": true}') == {"ready": True}


def test_json_deserializer_propagates_unexpected_parser_failure() -> None:
    with (
        patch(
            "health.llama.json_deserializer.json.loads",
            side_effect=RuntimeError("parser bug"),
        ),
        pytest.raises(RuntimeError, match="parser bug"),
    ):
        JsonDeserializer().deserialize(b"{}")


@pytest.mark.parametrize("content", [b"not json", b"\xff"])
def test_legacy_review_reader_preserves_malformed_file_fallback(
    tmp_path: Path, content: bytes
) -> None:
    path = tmp_path / "review-output.json"
    path.write_bytes(content)

    assert _default_read(path) is None


def test_legacy_review_reader_preserves_missing_file_fallback(tmp_path: Path) -> None:
    assert _default_read(tmp_path / "missing.json") is None


def test_legacy_review_reader_preserves_valid_data(tmp_path: Path) -> None:
    path = tmp_path / "review-output.json"
    path.write_text('{"files": []}')

    assert _default_read(path) == {"files": []}


def test_legacy_review_reader_propagates_unexpected_parser_failure(
    tmp_path: Path,
) -> None:
    path = tmp_path / "review-output.json"
    path.write_text("{}")

    with (
        patch("pipeline.handlers.json.loads", side_effect=RuntimeError("parser bug")),
        pytest.raises(RuntimeError, match="parser bug"),
    ):
        _default_read(path)


@pytest.fixture
def principle_result_reader():
    script = (
        Path(__file__).resolve().parents[2]
        / "skills/validate-findings/scripts/check-severity.py"
    )
    return runpy.run_path(str(script))["iter_principle_results"]


@pytest.mark.parametrize("content", [b"not json", b"\xff"])
def test_principle_result_reader_preserves_parse_error_reporting(
    tmp_path: Path,
    principle_result_reader,
    content: bytes,
) -> None:
    principle = tmp_path / "rules" / "srp"
    principle.mkdir(parents=True)
    (principle / "review-output.json").write_bytes(content)

    results = list(principle_result_reader(str(tmp_path)))

    assert len(results) == 1
    assert results[0][0] == "srp"
    assert results[0][-1]


def test_principle_result_reader_propagates_unexpected_parser_failure(
    tmp_path: Path,
    principle_result_reader,
) -> None:
    principle = tmp_path / "rules" / "srp"
    principle.mkdir(parents=True)
    (principle / "review-output.json").write_text("{}")

    with (
        patch("json.loads", side_effect=RuntimeError("parser bug")),
        pytest.raises(RuntimeError, match="parser bug"),
    ):
        list(principle_result_reader(str(tmp_path)))


def test_principle_result_reader_preserves_file_read_error_reporting(
    tmp_path: Path,
    principle_result_reader,
) -> None:
    (tmp_path / "rules" / "srp" / "review-output.json").mkdir(parents=True)

    results = list(principle_result_reader(str(tmp_path)))

    assert len(results) == 1
    assert results[0][0] == "srp"
    assert results[0][-1]


@pytest.mark.parametrize("error", [ValueError("bad input"), RuntimeError("tool bug")])
def test_mcp_boundary_preserves_structured_tool_failure(error: Exception) -> None:
    handlers = HandlerStore()
    handlers.add_handler("failing", Mock(side_effect=error))

    result = ToolsCallHandler(handlers, ToolResultFormatter()).handle(
        "failing", {}, None
    )

    assert result["isError"] is True
    assert json.loads(result["content"][0]["text"]) == {"error": str(error)}


@pytest.mark.parametrize("error", [ValueError("bad input"), RuntimeError("tool bug")])
def test_cli_boundary_preserves_failure_exit_and_diagnostic(error: Exception) -> None:
    output, errors, process = Mock(), Mock(), Mock()

    GatewayToolRunner(output, errors, process).run(
        Mock(side_effect=error), "failing", {}
    )

    errors.log.assert_called_once_with(f"Error: {error}")
    process.exit.assert_called_once_with(1)
    output.write_result.assert_not_called()
