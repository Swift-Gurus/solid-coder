"""
solid-name: IntegrationTestBase
solid-category: utility
solid-description: Base class for principle review integration tests. Discovers all
principles with fixture tests, runs apply and health flows via the test harness, and
tolerates expectation mismatches — only infrastructure failures (exceptions, timeouts,
missing files) cause test failure.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from typing import ClassVar

_INTEGRATION_DIR = Path(__file__).resolve().parent
_HARNESS_DIR = _INTEGRATION_DIR.parent
_PROJECT_ROOT = _HARNESS_DIR.parents[1]

for _d in (str(_HARNESS_DIR), str(_HARNESS_DIR / "tests")):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from harness_factory import HarnessFactory  # noqa: E402


class IntegrationTestBase(unittest.TestCase):
    """Base class for end-to-end principle review integration tests.

    Not collected directly by pytest — subclasses are the concrete test targets.

    NOTE: Expectation mismatches are expected and acceptable at this stage.
    These tests verify the harness runs end-to-end without infrastructure
    failures, not that the LLM matches specific fixture expectations.
    Update expectations once the harness is stable and LLM outputs are
    consistent.

    Subclasses must set MODEL_PROFILE to a filename stem in models/
    (e.g. "haiku", "opus", "local"). TIMEOUT controls per-fixture seconds
    and defaults to 300 — override in subclasses that need more headroom.
    """

    __test__ = False  # prevent pytest from collecting the base class directly

    MODEL_PROFILE: ClassVar[str]
    TIMEOUT: ClassVar[int] = 300

    # ── Helpers ────────────────────────────────────────────────────────────────

    @classmethod
    def _models_dir(cls) -> Path:
        return _INTEGRATION_DIR / "models"

    @classmethod
    def _principles(cls) -> list[Path]:
        """Return all principle folders that have a fixtures/ subdirectory."""
        principles_root = _PROJECT_ROOT / "tests" / "principles"
        if not principles_root.is_dir():
            return []
        return sorted(
            p for p in principles_root.iterdir()
            if p.is_dir() and (p / "fixtures").is_dir()
        )

    def _run_principle(self, principle_folder: Path, flow: str) -> None:
        """Run one principle+flow. Fails on infrastructure errors; tolerates expectation mismatches."""
        print(
            f"\n  [{self.MODEL_PROFILE}] {principle_folder.name} / {flow} "
            f"(timeout={self.TIMEOUT}s) ...",
            flush=True,
        )
        factory = HarnessFactory()
        runner = factory.build(
            project_root=_PROJECT_ROOT,
            principle_folder=_PROJECT_ROOT / "references" / "principles" / principle_folder.name,
            profile_dir=self._models_dir(),
        )
        # runner.run() returns False on expectation mismatches — that is OK here.
        # Infrastructure failures raise RuntimeError and propagate as a test failure.
        passed = runner.run(
            principle_path=f"references/principles/{principle_folder.name}",
            flow=flow,
            fixture_filter=None,
            model_name=self.MODEL_PROFILE,
            timeout=self.TIMEOUT,
        )
        status = "PASS" if passed else "MISMATCH (ok)"
        print(f"  [{self.MODEL_PROFILE}] {principle_folder.name} / {flow} → {status}", flush=True)

    # ── Test methods ───────────────────────────────────────────────────────────

    def test_apply_flow(self) -> None:
        """Run apply flow for every principle with fixtures.

        NOTE: Expectation mismatches are OK — this is a harness smoke test.
        """
        principles = self._principles()
        if not principles:
            self.skipTest("No principles with fixtures found under tests/principles/")
        for principle in principles:
            with self.subTest(principle=principle.name):
                self._run_principle(principle, "apply")

    def test_health_flow(self) -> None:
        """Run health flow for every principle with fixtures.

        NOTE: Expectation mismatches are OK — this is a harness smoke test.
        """
        principles = self._principles()
        if not principles:
            self.skipTest("No principles with fixtures found under tests/principles/")
        for principle in principles:
            with self.subTest(principle=principle.name):
                self._run_principle(principle, "health")
