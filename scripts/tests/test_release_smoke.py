"""Checks release smoke rejects startup errors and RPC failures despite development state."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SPEC = importlib.util.spec_from_file_location(
    "release_smoke", Path(__file__).resolve().parents[1] / "release-smoke.py"
)
assert SPEC is not None and SPEC.loader is not None
SMOKE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SMOKE)


def test_clean_environment_does_not_inherit_development_python(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("VIRTUAL_ENV", "/developer/.venv")
    monkeypatch.setenv("PYTHONPATH", "/developer/site-packages")
    monkeypatch.setenv("PATH", "/developer/.venv/bin")

    environment = SMOKE.clean_environment(
        tmp_path / "home",
        tmp_path / "host-bin",
        tmp_path / "plugin",
        tmp_path / "project",
    )

    assert "VIRTUAL_ENV" not in environment
    assert "PYTHONPATH" not in environment
    assert environment["PATH"] == f"{tmp_path / 'host-bin'}:/usr/bin:/bin"


@pytest.mark.parametrize(
    "source",
    [
        "import sys; print('missing runtime dependency', file=sys.stderr); raise SystemExit(1)",
        "import json; print(json.dumps({'id': 1, 'error': {'message': 'not initialized'}})); print(json.dumps({'id': 2, 'result': {'tools': []}}))",
    ],
)
def test_mcp_startup_or_rpc_failure_is_not_a_pass(tmp_path: Path, source: str) -> None:
    script = tmp_path / "broken-server.py"
    script.write_text(source)

    with pytest.raises((RuntimeError, ValueError)):
        SMOKE.check_mcp(
            {"command": sys.executable, "args": [str(script)]}, tmp_path, tmp_path, {}
        )


def test_unprovisioned_desktop_python_fails_without_development_dependencies(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    package = tmp_path / "installed package"
    SMOKE.copy_package(Path(__file__).resolve().parents[2], package)
    host = tmp_path / "unprovisioned-host"
    subprocess.run(
        [sys._base_executable, "-I", "-m", "venv", "--without-pip", str(host)],
        check=True,
    )
    monkeypatch.setenv("PYTHONPATH", "/developer/.venv/site-packages")

    failures = SMOKE.smoke(package, host / "bin/python3.12")

    assert failures
    assert "claude/docs" in failures[0]
    assert "No module named 'pydantic'" in failures[0]
