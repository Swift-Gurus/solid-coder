"""Checks recovered failures are logged without changing fallback results."""

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
from bash_read_gate import BashReadGate
from build.apple import server as apple
from rules.rule_file_collector import collect_files
from violation_extractor import ViolationExtractor


def test_bash_path_resolution_failure_is_logged_and_still_blocks_source_read() -> None:
    logger = Mock()
    resolve = Path.resolve

    def resolve_path(path: Path) -> Path:
        if path == Path("bad.py"):
            raise OSError("unresolvable")
        return resolve(path)

    with patch.object(Path, "resolve", autospec=True, side_effect=resolve_path):
        result = BashReadGate(logger=logger).check("cat bad.py")

    assert result == "cat"
    logger.log.assert_called_once()
    message = logger.log.call_args.args[0]
    assert "path=bad.py" in message
    assert "OSError: unresolvable" in message


@pytest.mark.parametrize(
    "command, expected", [("cat local.py", "cat"), ("cat /outside/repo/file.py", None)]
)
def test_bash_successful_resolution_has_no_error_log(
    command: str, expected: str | None
) -> None:
    logger = Mock()

    assert BashReadGate(logger=logger).check(command) == expected
    logger.log.assert_not_called()


@pytest.mark.parametrize("broken", ["not json", "{}", "[]"])
def test_bad_fix_is_logged_and_other_fixes_still_merge(
    tmp_path: Path, broken: str
) -> None:
    review = tmp_path / "SRP" / "review-output.json"
    review.parent.mkdir()
    review.write_text(
        json.dumps(
            {
                "files": [
                    {
                        "file_path": "Example.swift",
                        "units": [
                            {
                                "unit_name": "Example",
                                "violations": [
                                    {"rule_id": "SRP-1", "severity": "SEVERE"},
                                    {"rule_id": "SRP-2", "severity": "SEVERE"},
                                ],
                            }
                        ],
                    }
                ]
            }
        )
    )
    fixes = tmp_path / "fixes"
    fixes.mkdir()
    (fixes / "good.json").write_text(
        json.dumps(
            {
                "rule_id": "SRP-1",
                "file_path": "Example.swift",
                "unit_name": "Example",
                "suggested_fix": "Keep this fix",
            }
        )
    )
    bad = fixes / "bad.json"
    bad.write_text(broken)
    logger = Mock()

    result = ViolationExtractor(logger=logger).extract(str(tmp_path))

    assert result[0]["fix"] == "Keep this fix"
    assert "load_fix_for_violation(SRP-2)" in result[1]["fix"]
    logger.log.assert_called_once()
    message = logger.log.call_args.args[0]
    assert str(bad) in message
    assert any(
        name in message for name in ("JSONDecodeError", "KeyError", "AttributeError")
    )


def test_pattern_parser_failure_is_logged_and_keeps_collected_files(
    tmp_path: Path,
) -> None:
    logger = Mock()
    parser = Mock()
    parser.parse.side_effect = OSError("cannot read rule")
    rule = str(tmp_path / "rule.md")

    result = collect_files(tmp_path, rule, set(), "code", parser, logger=logger)

    assert result == [rule]
    logger.log.assert_called_once_with(
        f"Stopped collecting required rule patterns: rule={rule}; OSError: cannot read rule"
    )


def test_pattern_iteration_failure_retains_already_collected_pattern(
    tmp_path: Path,
) -> None:
    pattern = tmp_path / "pattern.md"
    pattern.touch()

    def patterns():
        yield str(pattern)
        raise RuntimeError("pattern lookup stopped")

    logger = Mock()
    parser = Mock()
    parser.parse.return_value = {"required_patterns": patterns()}
    rule = str(tmp_path / "rule.md")

    assert collect_files(tmp_path, rule, set(), "code", parser, logger=logger) == [
        rule,
        str(pattern),
    ]
    assert "RuntimeError: pattern lookup stopped" in logger.log.call_args.args[0]


def test_successful_pattern_collection_has_no_error_log(tmp_path: Path) -> None:
    logger = Mock()
    parser = Mock()
    parser.parse.return_value = {}
    rule = str(tmp_path / "rule.md")

    assert collect_files(tmp_path, rule, set(), "code", parser, logger=logger) == [rule]
    logger.log.assert_not_called()


@pytest.mark.parametrize("outside", [True, False])
def test_lint_preserves_paths_and_logs_only_failed_relative_conversion(
    tmp_path: Path, outside: bool
) -> None:
    path = (
        Path("/outside/project/Example.swift")
        if outside
        else tmp_path / "Example.swift"
    )
    raw = json.dumps(
        [
            {
                "file": str(path),
                "line": 2,
                "character": 3,
                "rule_id": "some_rule",
                "severity": "Warning",
                "reason": "message",
            }
        ]
    )
    logger = Mock()
    with (
        patch.object(apple, "_which", return_value=True),
        patch.object(
            apple.subprocess,
            "run",
            return_value=SimpleNamespace(stdout=raw),
        ),
    ):
        result = apple._run_lint(tmp_path, logger=logger)

    expected_path = str(path) if outside else "Example.swift"
    assert result == f"{expected_path}:2:3: some_rule warning: message"
    if outside:
        logger.log.assert_called_once()
        message = logger.log.call_args.args[0]
        for expected in (
            str(path),
            str(tmp_path),
            "ValueError",
            "retaining original path",
        ):
            assert expected in message
    else:
        logger.log.assert_not_called()


def test_output_reader_failure_logs_and_retains_partial_output() -> None:
    def output():
        yield "first line\n"
        raise OSError("pipe closed")

    logger = Mock()
    proc = SimpleNamespace(stdout=output(), pid=42)
    state = {"stdout": [], "last_progress": 0}
    with patch.object(apple.time, "monotonic", return_value=123):
        apple._ProcessOutputReader(proc, state, logger=logger).run()

    assert state == {"stdout": ["first line\n"], "last_progress": 123}
    logger.log.assert_called_once_with(
        "Stopped reading Apple process output: pid=42; OSError: pipe closed"
    )


def test_successful_output_reader_has_no_error_log() -> None:
    logger = Mock()
    proc = SimpleNamespace(stdout=iter(["complete\n"]), pid=42)
    state = {"stdout": [], "last_progress": 0}

    apple._ProcessOutputReader(proc, state, logger=logger).run()

    assert state["stdout"] == ["complete\n"]
    logger.log.assert_not_called()
