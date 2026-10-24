"""Makes shared repository test fixtures importable across test groups."""

import sys
from pathlib import Path

import pytest

TEST_ROOT = Path(__file__).resolve().parent
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))


@pytest.fixture
def isolated_configuration_home(tmp_path, monkeypatch):
    home = tmp_path / "isolated-home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.delenv("SOLID_CODER_TEST_MODEL_PROFILE", raising=False)
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    return home
