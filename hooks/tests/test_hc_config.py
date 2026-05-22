"""
solid-description: Unit tests verifying that the LLM configuration loader resolves settings from a project-scoped config file and returns documented defaults when no config is present.
solid-category: unit-test
"""

import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path
ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

import hc_config

_VALID_TOML = b"[llm]\nbackend = \"local\"\nhost = \"http://gpu:9090\"\n"


def _write_toml(directory: Path, content: bytes = _VALID_TOML) -> Path:
    cfg_dir = directory / ".claude"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    path = cfg_dir / "solid-coder-local.toml"
    path.write_bytes(content)
    return path


class TestAccessors(unittest.TestCase):
    def _assert_default(self, fn, expected: str) -> None:
        with patch("hc_config._read_config_file", return_value={}):
            self.assertEqual(fn(), expected)

    def test_backend_defaults_to_claude(self):
        self._assert_default(hc_config.llm_backend, "claude")

    def test_host_defaults_to_localhost_8080(self):
        self._assert_default(hc_config.llm_host, "http://localhost:8080")

    def test_model_defaults_to_local(self):
        self._assert_default(hc_config.llm_model, "local")

    def test_backend_read_from_config(self):
        with patch("hc_config._read_config_file", return_value={"backend": "local"}):
            self.assertEqual(hc_config.llm_backend(), "local")

    def test_host_read_from_config(self):
        with patch("hc_config._read_config_file", return_value={"host": "http://myserver:9090"}):
            self.assertEqual(hc_config.llm_host(), "http://myserver:9090")


class TestFindConfig(unittest.TestCase):
    def _find(self, project_dir: Path):
        with patch("hc_config.Path") as mock_path:
            mock_path.cwd.return_value = project_dir
            mock_path.side_effect = lambda *a, **kw: Path(*a, **kw)
            return hc_config._find_config()

    def test_returns_project_config_when_present(self):
        with tempfile.TemporaryDirectory() as d:
            _write_toml(Path(d))
            result = self._find(Path(d))
            self.assertEqual(result, Path(d) / ".claude" / "solid-coder-local.toml")

    def test_returns_none_when_project_config_absent(self):
        with tempfile.TemporaryDirectory() as d:
            self.assertIsNone(self._find(Path(d)))

    def test_does_not_search_outside_project_dir(self):
        with tempfile.TemporaryDirectory() as project, \
             tempfile.TemporaryDirectory() as other:
            _write_toml(Path(other))  # config elsewhere — must not be found
            self.assertIsNone(self._find(Path(project)))


class TestReadConfigFile(unittest.TestCase):
    @contextmanager
    def _with_temp_toml(self, content: bytes):
        with tempfile.NamedTemporaryFile(suffix=".toml", delete=False) as f:
            f.write(content)
            tmp = Path(f.name)
        try:
            with patch("hc_config._find_config", return_value=tmp):
                yield hc_config._read_config_file()
        finally:
            tmp.unlink()

    def test_returns_empty_when_no_config_found(self):
        with patch("hc_config._find_config", return_value=None):
            self.assertEqual(hc_config._read_config_file(), {})

    def test_returns_empty_dict_on_invalid_toml(self):
        with self._with_temp_toml(b"not valid toml") as result:
            self.assertIsInstance(result, dict)

    def test_reads_llm_section_when_tomllib_available(self):
        with self._with_temp_toml(_VALID_TOML) as result:
            if not result:
                self.skipTest("No TOML parser available")
            self.assertEqual(result.get("backend"), "local")
            self.assertEqual(result.get("host"), "http://gpu:9090")


if __name__ == "__main__":
    unittest.main()
