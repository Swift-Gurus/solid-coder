"""
solid-name: TestHealthFlowInvoker
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Unit tests for SupportedExtensionsProvider, CheckResultWriter,
_env_override_context, and HealthFlowInvoker. Covers language lookup, result writing,
env-var save/restore, and the full invoke contract including timeout and error paths.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import unittest
from pathlib import Path
from typing import Callable
from unittest.mock import MagicMock

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"
_HOOKS_DIR = _PROJECT_ROOT / "hooks"

ensure_on_path(_HARNESS_DIR, _HERE, _HOOKS_DIR)

from health_flow_invoker import (  # noqa: E402
    CheckResultWriter,
    HealthFlowInvoker,
    SupportedExtensionsProvider,
    _env_override_context,
)
from test_fixtures import _make_output_paths, _make_profile  # noqa: E402


class TestSupportedExtensionsProvider(unittest.TestCase):
    def setUp(self) -> None:
        self._extensions = {".swift": "Swift", ".py": "Python"}
        self._provider = SupportedExtensionsProvider(self._extensions)

    def test_returns_language_for_known_extension(self):
        self.assertEqual(self._provider.get_language(".swift"), "Swift")

    def test_returns_python_for_py_extension(self):
        self.assertEqual(self._provider.get_language(".py"), "Python")

    def test_returns_empty_string_for_unknown_extension(self):
        self.assertEqual(self._provider.get_language(".rs"), "")

    def test_different_extensions_map_dict_given_at_construction(self):
        provider = SupportedExtensionsProvider({".kt": "Kotlin"})
        self.assertEqual(provider.get_language(".kt"), "Kotlin")
        self.assertEqual(provider.get_language(".py"), "")


class TestCheckResultWriter(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_ctx = tempfile.TemporaryDirectory()
        self._tmp = Path(self._tmp_ctx.name)
        self._output_paths = _make_output_paths(self._tmp)
        self._writer = CheckResultWriter()

    def tearDown(self) -> None:
        self._tmp_ctx.cleanup()

    def test_creates_log_dir_and_writes_json(self):
        result = [{"principle": "SRP", "issue": "violation"}]
        self._writer.write(result, self._output_paths)
        self.assertTrue(self._output_paths.log_dir.exists())
        written = json.loads(self._output_paths.reasoning_path.read_text(encoding="utf-8"))
        self.assertEqual(written, result)

    def test_writes_empty_list_when_no_violations(self):
        self._writer.write([], self._output_paths)
        written = json.loads(self._output_paths.reasoning_path.read_text(encoding="utf-8"))
        self.assertEqual(written, [])


class TestEnvOverrideContext(unittest.TestCase):
    def test_env_var_set_inside_context(self):
        with _env_override_context({"_TEST_VAR_HC": "hello"}):
            self.assertEqual(os.environ.get("_TEST_VAR_HC"), "hello")

    def test_env_var_restored_after_context(self):
        original = os.environ.get("_TEST_VAR_HC")
        with _env_override_context({"_TEST_VAR_HC": "temp"}):
            pass
        self.assertEqual(os.environ.get("_TEST_VAR_HC"), original)

    def test_restores_previous_value_when_var_was_set(self):
        os.environ["_TEST_VAR_HC"] = "original"
        try:
            with _env_override_context({"_TEST_VAR_HC": "override"}):
                self.assertEqual(os.environ["_TEST_VAR_HC"], "override")
            self.assertEqual(os.environ["_TEST_VAR_HC"], "original")
        finally:
            del os.environ["_TEST_VAR_HC"]

    def test_removes_var_after_context_when_it_was_absent(self):
        os.environ.pop("_TEST_VAR_HC_NEW", None)
        with _env_override_context({"_TEST_VAR_HC_NEW": "injected"}):
            pass
        self.assertNotIn("_TEST_VAR_HC_NEW", os.environ)


class TestHealthFlowInvoker(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_ctx = tempfile.TemporaryDirectory()
        self._tmp = Path(self._tmp_ctx.name)
        self._fixture = self._tmp / "Foo.swift"
        self._fixture.write_text("class Foo {}", encoding="utf-8")
        self._output_paths = _make_output_paths(self._tmp)

    def tearDown(self) -> None:
        self._tmp_ctx.cleanup()

    def _make_invoker(self, violations=None, side_effect: Callable | None = None) -> HealthFlowInvoker:
        checker = MagicMock()
        if side_effect is not None:
            checker.check.side_effect = side_effect
        else:
            checker.check.return_value = violations or []
        provider = SupportedExtensionsProvider({".swift": "Swift"})
        return HealthFlowInvoker(
            checker=checker,
            language_provider=provider,
            result_writer=CheckResultWriter(),
        )

    def test_returns_violations_from_checker(self):
        violations = [{"principle": "SRP"}]
        result = self._make_invoker(violations).invoke(
            self._fixture, self._output_paths, _make_profile(), timeout=10
        )
        self.assertEqual(result, violations)

    def test_writes_reasoning_file_with_violations(self):
        violations = [{"principle": "OCP"}]
        self._make_invoker(violations).invoke(
            self._fixture, self._output_paths, _make_profile(), timeout=10
        )
        written = json.loads(self._output_paths.reasoning_path.read_text(encoding="utf-8"))
        self.assertEqual(written, violations)

    def test_injects_model_profile_env_var_when_profile_path_set(self):
        profile_path = self._tmp / "model.toml"
        profile_path.write_text("[llm]\nbackend = 'local'\n", encoding="utf-8")

        captured_env: dict = {}

        def capture_check(content, path, language, parent_session_id):
            captured_env["val"] = os.environ.get("SOLID_CODER_TEST_MODEL_PROFILE")
            return []

        self._make_invoker(side_effect=capture_check).invoke(
            self._fixture, self._output_paths, _make_profile(profile_path), timeout=10
        )
        self.assertEqual(captured_env.get("val"), str(profile_path))

    def test_env_var_not_set_after_invoke_completes(self):
        profile_path = self._tmp / "model.toml"
        profile_path.write_text("[llm]\nbackend = 'local'\n", encoding="utf-8")

        before = os.environ.get("SOLID_CODER_TEST_MODEL_PROFILE")
        self._make_invoker().invoke(
            self._fixture, self._output_paths, _make_profile(profile_path), timeout=10
        )
        self.assertEqual(os.environ.get("SOLID_CODER_TEST_MODEL_PROFILE"), before)

    def test_raises_timeout_error_when_checker_exceeds_timeout(self):
        def slow_check(*_a, **_kw):
            time.sleep(5)
            return []

        invoker = self._make_invoker(side_effect=slow_check)
        with self.assertRaises(TimeoutError):
            invoker.invoke(self._fixture, self._output_paths, _make_profile(), timeout=1)

    def test_raises_runtime_error_when_checker_raises(self):
        def raising_check(*_a, **_kw):
            raise ValueError("bad input")

        invoker = self._make_invoker(side_effect=raising_check)
        with self.assertRaises(RuntimeError):
            invoker.invoke(self._fixture, self._output_paths, _make_profile(), timeout=10)


class TestHealthFlowInvokerPrincipleFilter(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp_ctx = tempfile.TemporaryDirectory()
        self._tmp = Path(self._tmp_ctx.name)
        self._fixture = self._tmp / "Foo.swift"
        self._fixture.write_text("class Foo {}", encoding="utf-8")
        self._output_paths = _make_output_paths(self._tmp)

    def tearDown(self) -> None:
        self._tmp_ctx.cleanup()

    def _make_invoker(self, principle_name: str, violations: list) -> HealthFlowInvoker:
        checker = MagicMock()
        checker.check.return_value = violations
        return HealthFlowInvoker(
            checker=checker,
            language_provider=SupportedExtensionsProvider({".swift": "Swift"}),
            result_writer=CheckResultWriter(),
            principle_name=principle_name,
        )

    def _violations(self):
        return [
            {"metric_id": "DRY-2", "principle": "DRY"},
            {"metric_id": "DRY-3", "principle": "DRY"},
            {"metric_id": "SRP-1", "principle": "SRP"},
            {"metric_id": "OCP-1", "principle": "OCP"},
        ]

    def test_filter_keeps_only_matching_principle(self):
        result = self._make_invoker("DRY", self._violations()).invoke(
            self._fixture, self._output_paths, _make_profile(), timeout=10
        )
        self.assertEqual([v["metric_id"] for v in result], ["DRY-2", "DRY-3"])

    def test_filter_is_case_insensitive_on_principle_name(self):
        result = self._make_invoker("dry", self._violations()).invoke(
            self._fixture, self._output_paths, _make_profile(), timeout=10
        )
        self.assertEqual([v["metric_id"] for v in result], ["DRY-2", "DRY-3"])

    def test_empty_principle_name_passes_all_violations(self):
        result = self._make_invoker("", self._violations()).invoke(
            self._fixture, self._output_paths, _make_profile(), timeout=10
        )
        self.assertEqual(len(result), 4)

    def test_no_matching_violations_returns_empty(self):
        result = self._make_invoker("ISP", self._violations()).invoke(
            self._fixture, self._output_paths, _make_profile(), timeout=10
        )
        self.assertEqual(result, [])


if __name__ == "__main__":
    unittest.main()
