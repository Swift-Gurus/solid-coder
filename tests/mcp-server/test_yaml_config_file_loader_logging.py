"""Checks YAML/JSON load failures are observable while preserving optional-content results."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from harness.json_loading import JsonLoader
from scoring.yaml_config_file_loader import YamlConfigFileLoader
from scoring.yaml_loader import PyYamlLoader, YamlLoading


@pytest.mark.parametrize(
    "parser, content, error_name",
    [
        (PyYamlLoader(), "value: [", "ParserError"),
        (JsonLoader(), "not json", "JSONDecodeError"),
    ],
)
def test_malformed_configuration_logs_path_and_parser_failure(
    tmp_path: Path,
    parser: YamlLoading,
    content: str,
    error_name: str,
) -> None:
    path = tmp_path / "broken.config"
    path.write_text(content)
    logger = Mock()

    assert YamlConfigFileLoader(loader=parser, logger=logger).load(path) is None

    logger.log.assert_called_once()
    message = logger.log.call_args.args[0]
    assert str(path) in message
    assert error_name in message


def test_unexpected_parser_failure_is_logged_and_keeps_unavailable_result(
    tmp_path: Path,
) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("value: 1")
    parser, logger = Mock(), Mock()
    parser.safe_load.side_effect = RuntimeError("parser failed")

    assert YamlConfigFileLoader(loader=parser, logger=logger).load(path) is None

    logger.log.assert_called_once_with(
        f"Configuration loading failed: path={path}; RuntimeError: parser failed"
    )


def test_read_failure_logs_and_does_not_invoke_parser(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "config.yaml"
    path.touch()
    monkeypatch.setattr(Path, "read_text", Mock(side_effect=OSError("read denied")))
    parser, logger = Mock(), Mock()

    assert YamlConfigFileLoader(loader=parser, logger=logger).load(path) is None

    parser.safe_load.assert_not_called()
    logger.log.assert_called_once_with(
        f"Configuration loading failed: path={path}; OSError: read denied"
    )


def test_encoding_failure_logs_before_parsing(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_bytes(b"\xff")
    parser, logger = Mock(), Mock()

    assert YamlConfigFileLoader(loader=parser, logger=logger).load(path) is None

    parser.safe_load.assert_not_called()
    logger.log.assert_called_once()
    assert str(path) in logger.log.call_args.args[0]
    assert "UnicodeDecodeError" in logger.log.call_args.args[0]


def test_absent_optional_file_does_not_log_or_parse(tmp_path: Path) -> None:
    parser, logger = Mock(), Mock()

    assert (
        YamlConfigFileLoader(loader=parser, logger=logger).load(
            tmp_path / "missing.yaml"
        )
        is None
    )

    parser.safe_load.assert_not_called()
    logger.log.assert_not_called()


@pytest.mark.parametrize("parser", [PyYamlLoader(), JsonLoader()])
def test_non_mapping_content_keeps_unavailable_result_without_error_log(
    tmp_path: Path, parser: YamlLoading
) -> None:
    path = tmp_path / "config"
    path.write_text('["value"]')
    logger = Mock()

    assert YamlConfigFileLoader(loader=parser, logger=logger).load(path) is None
    logger.log.assert_not_called()


@pytest.mark.parametrize("parser", [PyYamlLoader(), JsonLoader()])
def test_valid_mapping_is_returned_without_error_log(
    tmp_path: Path, parser: YamlLoading
) -> None:
    path = tmp_path / "config"
    path.write_text('{"value": 1}')
    logger = Mock()

    assert YamlConfigFileLoader(loader=parser, logger=logger).load(path) == {"value": 1}
    logger.log.assert_not_called()
