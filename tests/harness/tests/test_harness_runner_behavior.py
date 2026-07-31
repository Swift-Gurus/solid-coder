"""
solid-name: TestHarnessRunnerBehavior
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Unit tests for TestHarnessRunner. Verifies that RuntimeError and
TimeoutError propagate out of run() (infra errors must not be silently swallowed),
that expectation mismatches return False without raising, and that a fully-passing
run returns True.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"

ensure_on_path(_HARNESS_DIR, _HERE)

from llm_config import LlmConfig  # noqa: E402
from models import DiffEntry, Expectation, ExpectedFinding, FixturePair, ModelProfile, OutputPaths  # noqa: E402
from test_harness_runner import TestHarnessRunner  # noqa: E402


def _make_output_paths(tmp: Path) -> OutputPaths:
    log = tmp / "log"
    return OutputPaths(log_dir=log, reasoning_path=log / "r.txt", review_output_path=log / "o.json")


def _make_profile() -> ModelProfile:
    return ModelProfile(output_dir_name="test", profile_path=None, llm={}, inference={})


def _make_pair(tmp: Path) -> FixturePair:
    fixture = tmp / "f.swift"
    fixture.write_text("class Foo {}", encoding="utf-8")
    exp = tmp / "f.json"
    exp.write_text(json.dumps({"findings": []}), encoding="utf-8")
    return FixturePair(fixture_path=fixture, expectation_path=exp, stem="f")


def _make_runner(
    health_invoker: object,
    findings: list[dict] | None = None,
) -> TestHarnessRunner:
    path_resolver = MagicMock()
    fixture_discovery = MagicMock()
    expectation_loader = MagicMock()
    model_profile_loader = MagicMock()
    output_path_builder = MagicMock()
    finding_comparer = MagicMock()
    finding_normalizer = MagicMock()
    result_formatter = MagicMock()
    timestamp_generator = MagicMock()

    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        pair = _make_pair(tmp)
        profile = _make_profile()

        path_resolver.resolve.return_value = tmp
        fixture_discovery.discover.return_value = [pair]
        expectation_loader.load.return_value = Expectation(findings=[])
        model_profile_loader.load.return_value = profile
        output_path_builder.build.return_value = _make_output_paths(tmp)
        finding_normalizer.normalize.return_value = ([], findings or [])
        finding_comparer.compare.return_value = []
        result_formatter.format_status.return_value = "STATUS"
        result_formatter.format_failures.return_value = []
        timestamp_generator.now_str.return_value = "2026-01-01"

    return TestHarnessRunner(
        path_resolver=path_resolver,
        fixture_discovery=fixture_discovery,
        expectation_loader=expectation_loader,
        model_profile_loader=model_profile_loader,
        output_path_builder=output_path_builder,
        finding_comparer=finding_comparer,
        finding_normalizer=finding_normalizer,
        result_formatter=result_formatter,
        apply_invoker=MagicMock(),
        health_invoker=health_invoker,
        timestamp_generator=timestamp_generator,
    )


class TestHarnessRunnerPropagation(unittest.TestCase):
    """Infrastructure errors must propagate — they must never be silently swallowed."""

    def _runner_with_health_error(self, exc: Exception) -> tuple[TestHarnessRunner, Path]:
        tmp_ctx = tempfile.TemporaryDirectory()
        tmp = Path(tmp_ctx.name)
        self.addCleanup(tmp_ctx.cleanup)

        pair = _make_pair(tmp)
        profile = _make_profile()
        out = _make_output_paths(tmp)

        health_invoker = MagicMock()
        health_invoker.invoke.side_effect = exc

        runner = TestHarnessRunner(
            path_resolver=MagicMock(resolve=MagicMock(return_value=tmp)),
            fixture_discovery=MagicMock(discover=MagicMock(return_value=[pair])),
            expectation_loader=MagicMock(load=MagicMock(return_value=Expectation())),
            model_profile_loader=MagicMock(load=MagicMock(return_value=profile)),
            output_path_builder=MagicMock(build=MagicMock(return_value=out)),
            finding_comparer=MagicMock(compare=MagicMock(return_value=[])),
            finding_normalizer=MagicMock(normalize=MagicMock(return_value=([], []))),
            result_formatter=MagicMock(
                format_status=MagicMock(return_value=""),
                format_failures=MagicMock(return_value=[]),
            ),
            apply_invoker=MagicMock(),
            health_invoker=health_invoker,
            timestamp_generator=MagicMock(now_str=MagicMock(return_value="2026-01-01")),
        )
        return runner, tmp

    def test_runtime_error_propagates(self):
        runner, tmp = self._runner_with_health_error(RuntimeError("codex config broken"))
        with self.assertRaises(RuntimeError, msg="RuntimeError must not be swallowed"):
            runner.run(
                principle_path="principles/SRP",
                flow="health",
                fixture_filter=None,
                model_name=None,
                timeout=10,
            )

    def test_timeout_error_propagates(self):
        runner, tmp = self._runner_with_health_error(TimeoutError("took too long"))
        with self.assertRaises(TimeoutError, msg="TimeoutError must not be swallowed"):
            runner.run(
                principle_path="principles/SRP",
                flow="health",
                fixture_filter=None,
                model_name=None,
                timeout=10,
            )

    def test_expectation_mismatch_returns_false_without_raising(self):
        tmp_ctx = tempfile.TemporaryDirectory()
        tmp = Path(tmp_ctx.name)
        self.addCleanup(tmp_ctx.cleanup)

        pair = _make_pair(tmp)
        profile = _make_profile()
        out = _make_output_paths(tmp)

        health_invoker = MagicMock()
        health_invoker.invoke.return_value = [{"metric_id": "SRP-1"}]

        runner = TestHarnessRunner(
            path_resolver=MagicMock(resolve=MagicMock(return_value=tmp)),
            fixture_discovery=MagicMock(discover=MagicMock(return_value=[pair])),
            expectation_loader=MagicMock(load=MagicMock(return_value=Expectation())),
            model_profile_loader=MagicMock(load=MagicMock(return_value=profile)),
            output_path_builder=MagicMock(build=MagicMock(return_value=out)),
            finding_comparer=MagicMock(compare=MagicMock(return_value=[
                DiffEntry(kind="missing", unit_name="Foo", metric_id="SRP-1", severity="major")
            ])),
            finding_normalizer=MagicMock(normalize=MagicMock(return_value=([], []))),
            result_formatter=MagicMock(
                format_status=MagicMock(return_value=""),
                format_failures=MagicMock(return_value=[]),
            ),
            apply_invoker=MagicMock(),
            health_invoker=health_invoker,
            timestamp_generator=MagicMock(now_str=MagicMock(return_value="2026-01-01")),
        )
        result = runner.run(
            principle_path="principles/SRP",
            flow="health",
            fixture_filter=None,
            model_name=None,
            timeout=10,
        )
        self.assertFalse(result)

    def test_all_fixtures_pass_returns_true(self):
        tmp_ctx = tempfile.TemporaryDirectory()
        tmp = Path(tmp_ctx.name)
        self.addCleanup(tmp_ctx.cleanup)

        pair = _make_pair(tmp)
        profile = _make_profile()
        out = _make_output_paths(tmp)

        health_invoker = MagicMock()
        health_invoker.invoke.return_value = []

        runner = TestHarnessRunner(
            path_resolver=MagicMock(resolve=MagicMock(return_value=tmp)),
            fixture_discovery=MagicMock(discover=MagicMock(return_value=[pair])),
            expectation_loader=MagicMock(load=MagicMock(return_value=Expectation())),
            model_profile_loader=MagicMock(load=MagicMock(return_value=profile)),
            output_path_builder=MagicMock(build=MagicMock(return_value=out)),
            finding_comparer=MagicMock(compare=MagicMock(return_value=[])),
            finding_normalizer=MagicMock(normalize=MagicMock(return_value=([], []))),
            result_formatter=MagicMock(
                format_status=MagicMock(return_value=""),
                format_failures=MagicMock(return_value=[]),
            ),
            apply_invoker=MagicMock(),
            health_invoker=health_invoker,
            timestamp_generator=MagicMock(now_str=MagicMock(return_value="2026-01-01")),
        )
        result = runner.run(
            principle_path="principles/SRP",
            flow="health",
            fixture_filter=None,
            model_name=None,
            timeout=10,
        )
        self.assertTrue(result)


class TestHarnessRunnerTimeoutResolution(unittest.TestCase):
    """timeout=None must defer to the model profile's own llm.timeout. ModelProfileLoader
    guarantees llm.timeout is always present (see test_model_profile_loader.py), so
    TestHarnessRunner itself does no further defaulting."""

    def _run_with(self, llm: dict, timeout) -> object:
        tmp_ctx = tempfile.TemporaryDirectory()
        tmp = Path(tmp_ctx.name)
        self.addCleanup(tmp_ctx.cleanup)

        pair = _make_pair(tmp)
        profile = ModelProfile(output_dir_name="test", profile_path=None, llm=llm, inference={})
        out = _make_output_paths(tmp)

        health_invoker = MagicMock()
        health_invoker.invoke.return_value = []

        runner = TestHarnessRunner(
            path_resolver=MagicMock(resolve=MagicMock(return_value=tmp)),
            fixture_discovery=MagicMock(discover=MagicMock(return_value=[pair])),
            expectation_loader=MagicMock(load=MagicMock(return_value=Expectation())),
            model_profile_loader=MagicMock(load=MagicMock(return_value=profile)),
            output_path_builder=MagicMock(build=MagicMock(return_value=out)),
            finding_comparer=MagicMock(compare=MagicMock(return_value=[])),
            finding_normalizer=MagicMock(normalize=MagicMock(return_value=([], []))),
            result_formatter=MagicMock(
                format_status=MagicMock(return_value=""),
                format_failures=MagicMock(return_value=[]),
            ),
            apply_invoker=MagicMock(),
            health_invoker=health_invoker,
            timestamp_generator=MagicMock(now_str=MagicMock(return_value="2026-01-01")),
        )
        runner.run(
            principle_path="principles/SRP",
            flow="health",
            fixture_filter=None,
            model_name=None,
            timeout=timeout,
        )
        return health_invoker.invoke.call_args.args[-1]

    def test_no_explicit_timeout_defers_to_profile_default_timeout(self):
        received = self._run_with(llm={"timeout": LlmConfig().timeout}, timeout=None)
        self.assertEqual(received, LlmConfig().timeout)

    def test_no_explicit_timeout_defers_to_profile_timeout(self):
        received = self._run_with(llm={"timeout": 600}, timeout=None)
        self.assertEqual(received, 600)

    def test_explicit_timeout_overrides_profile_timeout(self):
        received = self._run_with(llm={"timeout": 600}, timeout=42)
        self.assertEqual(received, 42)


if __name__ == "__main__":
    unittest.main()
