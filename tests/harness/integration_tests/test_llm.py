"""
solid-name: TestLlmPrincipleReview
solid-category: integration-test
solid-description: Integration tests for all principles using a local llama.cpp server.
Starts llama-server via scripts/run-local-llm.sh in setUpClass (fails loudly if the
binary or model is absent), runs all fixture-backed principle tests, then tears down
the server in tearDownClass. Expectation mismatches are acceptable at this stage —
only infrastructure failures cause test failure.

Prerequisites:
  - llama-server binary must be in PATH (brew install llama.cpp or build from source)
  - Model configured in .claude/solid-coder-local.toml [server] must exist in
    ~/.cache/huggingface/
  - Port 8080 must be free (or change [server] port in solid-coder-local.toml)

Run:
    python3 -m pytest tests/harness/integration_tests/test_llm.py -v
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from integration_tests.base import IntegrationTestBase  # noqa: E402

_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_LOCAL_TOML = _PROJECT_ROOT / ".claude" / "solid-coder-local.toml"
_LAUNCH_SCRIPT = _PROJECT_ROOT / "scripts" / "run-local-llm.sh"

_STARTUP_TIMEOUT_S = 120
_HEALTH_POLL_INTERVAL_S = 3


def _read_server_config() -> dict:
    """Read [server] section from solid-coder-local.toml."""
    try:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        with open(_LOCAL_TOML, "rb") as f:
            return tomllib.load(f).get("server", {})
    except Exception:
        return {}


def _server_url() -> str:
    cfg = _read_server_config()
    port = cfg.get("port", 8080)
    return f"http://localhost:{port}"


def _wait_for_server(url: str, timeout: int) -> bool:
    """Poll GET {url}/health until 200 or timeout. Returns True if ready."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except (urllib.error.URLError, OSError):
            pass
        time.sleep(_HEALTH_POLL_INTERVAL_S)
    return False


class TestLlmPrincipleReview(IntegrationTestBase):
    """Principle review integration tests using a local llama.cpp server.

    Fails loudly on setup if llama-server is not available or the model
    is missing — the environment must be fully configured before running.
    Higher timeout than Claude tests because local inference is slower.
    """

    __test__ = True
    MODEL_PROFILE = "local"
    TIMEOUT = 600

    def test_apply_flow(self) -> None:
        self.skipTest("apply flow not yet wired to local LLM backend")

    _server_process: subprocess.Popen | None = None

    @classmethod
    def setUpClass(cls) -> None:
        if not shutil.which("llama-server"):
            raise RuntimeError(
                "llama-server not found in PATH.\n"
                "Install llama.cpp (e.g. `brew install llama.cpp`) and ensure "
                "the binary is on your PATH before running these tests."
            )
        if not _LAUNCH_SCRIPT.exists():
            raise RuntimeError(f"Launch script not found: {_LAUNCH_SCRIPT}")

        url = _server_url()

        # If a server is already running on the expected port, reuse it.
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=2) as resp:
                if resp.status == 200:
                    return
        except (urllib.error.URLError, OSError):
            pass

        cls._server_process = subprocess.Popen(
            ["bash", str(_LAUNCH_SCRIPT)],
            cwd=str(_PROJECT_ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        if not _wait_for_server(url, _STARTUP_TIMEOUT_S):
            cls._server_process.terminate()
            cls._server_process = None
            raise RuntimeError(
                f"llama-server did not become healthy at {url}/health "
                f"within {_STARTUP_TIMEOUT_S}s.\n"
                "Check that the model file exists in ~/.cache/huggingface/ "
                "and that port 8080 is free."
            )

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._server_process is not None:
            cls._server_process.terminate()
            try:
                cls._server_process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                cls._server_process.kill()
            cls._server_process = None
