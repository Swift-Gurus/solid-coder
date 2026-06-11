"""
solid-name: HealthFlowInvoker
solid-category: service
solid-spec: [SPEC-014]
solid-description: Orchestrates the health-check flow for a fixture file, enforcing a configurable timeout and persisting the resulting violations to configured output paths.
"""

from __future__ import annotations

import concurrent.futures
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

_HARNESS_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = _HARNESS_DIR.parents[1] / "hooks"
for _d in (str(_HARNESS_DIR), str(_HOOKS_DIR)):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from hc_checker import HealthChecking  # noqa: E402

from interfaces import CheckResultWriting, FlowInvoking, SupportedExtensionsProviding  # noqa: E402
from models import ModelProfile, OutputPaths  # noqa: E402


@contextmanager
def _env_override_context(env_override: dict[str, str]) -> Iterator[None]:
    old_env = {k: os.environ.get(k) for k in env_override}
    os.environ.update(env_override)
    try:
        yield
    finally:
        for k, v in old_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


class SupportedExtensionsProvider(SupportedExtensionsProviding):
    def __init__(self, extensions: dict[str, str]) -> None:
        self._extensions = extensions

    def get_language(self, suffix: str) -> str:
        return self._extensions.get(suffix, "")


class CheckResultWriter(CheckResultWriting):
    def write(self, result: list[dict], output_paths: OutputPaths) -> None:
        output_paths.log_dir.mkdir(parents=True, exist_ok=True)
        output_paths.reasoning_path.write_text(
            json.dumps(result, indent=2), encoding="utf-8"
        )


class HealthFlowInvoker(FlowInvoking):
    def __init__(
        self,
        checker: HealthChecking,
        language_provider: SupportedExtensionsProviding,
        result_writer: CheckResultWriting,
        principle_name: str = "",
    ) -> None:
        self._checker = checker
        self._language_provider = language_provider
        self._result_writer = result_writer
        self._principle_name = principle_name.upper()

    def invoke(
        self,
        fixture_path: Path,
        output_paths: OutputPaths,
        model_profile: ModelProfile,
        timeout: int,
    ) -> list[dict]:
        content = fixture_path.read_text(encoding="utf-8", errors="replace")
        language = self._language_provider.get_language(fixture_path.suffix)

        env_override: dict[str, str] = {}
        if model_profile.profile_path is not None:
            env_override["SOLID_CODER_TEST_MODEL_PROFILE"] = str(model_profile.profile_path)

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._run_check, content, str(fixture_path), language, env_override)
            try:
                violations = future.result(timeout=timeout)
            except concurrent.futures.TimeoutError as exc:
                raise TimeoutError(
                    f"Health check timed out after {timeout}s for {fixture_path}"
                ) from exc
            except Exception as exc:
                raise RuntimeError(
                    f"Health check failed for {fixture_path}: {exc}"
                ) from exc

        all_violations: list[dict] = violations or []
        result = self._filter_by_principle(all_violations)
        self._result_writer.write(result, output_paths)
        return result

    def _filter_by_principle(self, violations: list[dict]) -> list[dict]:
        """Keep only violations whose metric_id belongs to the principle under test.

        When principle_name is empty, all violations are returned (no filter).
        """
        if not self._principle_name:
            return violations
        prefix = self._principle_name + "-"
        return [v for v in violations if v.get("metric_id", "").upper().startswith(prefix)]

    def _run_check(
        self,
        content: str,
        path: str,
        language: str,
        env_override: dict[str, str],
    ) -> list | None:
        parent_session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
        with _env_override_context(env_override):
            return self._checker.check(content, path, language, parent_session_id)
