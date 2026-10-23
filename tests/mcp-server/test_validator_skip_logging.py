"""Checks validation infrastructure failures are logged and propagated without acceptance."""

import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from findings import partial_output_validator, unit_coverage_validator
from findings.partial_output_validator import PartialOutputValidator
from findings.submit_orchestrator import SubmitOrchestrator
from findings.unit_coverage_validator import load_applies_to
from jsonschema.exceptions import SchemaError
from lib.gateway_tools import GatewayHandlerFactory


@pytest.mark.parametrize(
    "schema_content, error_type",
    [
        (b"not json", json.JSONDecodeError),
        (b"\xff", UnicodeDecodeError),
        (b'{"type": "invalid"}', SchemaError),
    ],
)
def test_logs_broken_schema_and_propagates_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    schema_content: bytes,
    error_type: type[Exception],
) -> None:
    broken_schema = tmp_path / "srp" / "review" / "output.schema.json"
    broken_schema.parent.mkdir(parents=True)
    broken_schema.write_bytes(schema_content)
    good_schema = tmp_path / "isp" / "review" / "output.schema.json"
    good_schema.parent.mkdir(parents=True)
    good_schema.write_text('{"type": "object", "required": ["required_metric"]}')
    monkeypatch.setattr(
        partial_output_validator, "_resolve_folder_fn", lambda name, root: root / name
    )
    logger = Mock()
    payload = {
        "files": [
            {
                "file_path": "Example.swift",
                "units": [
                    {"unit_name": "Example", "metrics": {"srp": {}, "isp": {}}},
                ],
            }
        ]
    }

    with pytest.raises(error_type):
        PartialOutputValidator(tmp_path, logger=logger).validate_output(payload)
    logger.log.assert_called_once()
    message = logger.log.call_args.args[0]
    for expected in (
        str(broken_schema),
        "principle=srp",
        "Example.swift",
        "unit=Example",
        error_type.__name__,
    ):
        assert expected in message


def test_valid_schema_produces_no_failure_log(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    schema = tmp_path / "srp" / "review" / "output.schema.json"
    schema.parent.mkdir(parents=True)
    schema.write_text('{"type": "object"}')
    monkeypatch.setattr(
        partial_output_validator, "_resolve_folder_fn", lambda name, root: root / name
    )
    logger = Mock()
    payload = {"files": [{"units": [{"metrics": {"srp": {}}}]}]}

    assert (
        PartialOutputValidator(tmp_path, logger=logger).validate_output(payload) is None
    )
    logger.log.assert_not_called()


@pytest.mark.parametrize("failure", ["encoding", "read", "parser"])
def test_logs_broken_applicability_rule_and_propagates_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: str,
) -> None:
    broken_rule = tmp_path / "principles" / "broken" / "rule.md"
    broken_rule.parent.mkdir(parents=True)
    broken_rule.write_bytes(
        b"\xff" if failure == "encoding" else b"---\napplies_to: [class]\n---"
    )
    good_rule = tmp_path / "principles" / "good" / "rule.md"
    good_rule.parent.mkdir(parents=True)
    good_rule.write_text("---\napplies_to: [protocol]\n---")
    if failure == "read":
        original_read = Path.read_text

        def read(path: Path, *args, **kwargs):
            if path == broken_rule:
                raise OSError("rule read failed")
            return original_read(path, *args, **kwargs)

        monkeypatch.setattr(Path, "read_text", read)
    if failure == "parser":
        original_parse = unit_coverage_validator._parse_applies_to

        def parse(content: str, principle: str):
            if principle == "broken":
                raise RuntimeError("rule parser failed")
            return original_parse(content, principle)

        monkeypatch.setattr(unit_coverage_validator, "_parse_applies_to", parse)
    logger = Mock()

    error_type = {
        "encoding": UnicodeDecodeError,
        "read": OSError,
        "parser": RuntimeError,
    }[failure]
    with pytest.raises(error_type):
        load_applies_to(tmp_path, logger=logger)
    logger.log.assert_called_once()
    message = logger.log.call_args.args[0]
    assert str(broken_rule) in message
    assert "principle=broken" in message
    expected = {
        "encoding": "UnicodeDecodeError",
        "read": "OSError: rule read failed",
        "parser": "RuntimeError: rule parser failed",
    }
    assert expected[failure] in message


def test_factory_logs_rule_failure_and_does_not_construct_gateway(
    tmp_path: Path,
) -> None:
    rule = tmp_path / "principles" / "broken" / "rule.md"
    rule.parent.mkdir(parents=True)
    rule.write_bytes(b"\xff")

    with (
        patch("lib.gateway_tools.DebugLogger") as debug_logger,
        pytest.raises(UnicodeDecodeError),
    ):
        GatewayHandlerFactory().make(tmp_path)

    debug_logger.return_value.log.assert_called_once()
    message, event = debug_logger.return_value.log.call_args.args
    assert str(rule) in message
    assert "UnicodeDecodeError" in message
    assert event == ""


def test_schema_failure_preserves_exception_and_prevents_scoring_or_persistence(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = tmp_path / "srp" / "review" / "output.schema.json"
    schema.parent.mkdir(parents=True)
    schema.write_text('{"type": "object"}')
    monkeypatch.setattr(
        partial_output_validator, "_resolve_folder_fn", lambda name, root: root / name
    )
    error = RuntimeError("validator defect")
    monkeypatch.setattr(
        partial_output_validator._jsonschema, "validate", Mock(side_effect=error)
    )
    logger, scoring, submitter, summariser = Mock(), Mock(), Mock(), Mock()
    orchestrator = SubmitOrchestrator(
        scoring=scoring,
        validator=PartialOutputValidator(tmp_path, logger=logger),
        submitter=submitter,
        summariser=summariser,
    )
    payload = {
        "files": [
            {
                "file_path": "Example.swift",
                "units": [
                    {"unit_name": "Example", "metrics": {"srp": {}}},
                ],
            }
        ]
    }

    with pytest.raises(RuntimeError) as caught:
        orchestrator.orchestrate(payload, str(tmp_path / "output.json"))

    assert caught.value is error
    assert "RuntimeError: validator defect" in logger.log.call_args.args[0]
    logger.log.assert_called_once()
    scoring.resolve_and_score.assert_not_called()
    submitter.submit.assert_not_called()
    summariser.summarise.assert_not_called()


def test_invalid_metrics_still_return_structured_rejection_without_failure_log(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = tmp_path / "srp" / "review" / "output.schema.json"
    schema.parent.mkdir(parents=True)
    schema.write_text('{"type": "object", "required": ["required_metric"]}')
    monkeypatch.setattr(
        partial_output_validator, "_resolve_folder_fn", lambda name, root: root / name
    )
    logger = Mock()
    payload = {
        "files": [
            {
                "file_path": "Example.swift",
                "units": [
                    {"unit_name": "Example", "metrics": {"srp": {}}},
                ],
            }
        ]
    }

    result = PartialOutputValidator(tmp_path, logger=logger).validate_output(payload)

    for expected in (
        "Example.swift",
        "unit Example",
        "principle srp",
        "required_metric",
    ):
        assert expected in result["error"]
    logger.log.assert_not_called()


def test_valid_applicability_rules_load_without_failure_log(tmp_path: Path) -> None:
    rule = tmp_path / "principles" / "good" / "rule.md"
    rule.parent.mkdir(parents=True)
    rule.write_text("---\napplies_to: [protocol]\n---")
    logger = Mock()

    assert load_applies_to(tmp_path, logger=logger) == {"good": ["protocol"]}
    logger.log.assert_not_called()
