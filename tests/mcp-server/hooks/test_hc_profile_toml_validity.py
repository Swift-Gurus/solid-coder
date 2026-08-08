"""
solid-name: TestCodexProfileTomlValidity
solid-category: unit-test
solid-description: Validates that a generated TOML configuration profile is syntactically valid and contains correctly-formed hook command definitions.
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from codex_profile_manager import CodexProfileManager  # noqa: E402
from test_utils import TempDirTestBase  # noqa: E402


class _StubConfig:
    def __init__(self, timeout: int) -> None:
        self.llm = type("Llm", (), {"timeout": timeout})()


class TestCodexProfileTomlValidity(TempDirTestBase):
    def _generated_content(self, config_loader=None) -> str:
        kwargs = {"config_loader": config_loader} if config_loader else {}
        CodexProfileManager(codex_home=str(self.output_dir), **kwargs).ensure_profile()
        return (self.output_dir / "solid-coder-health.config.toml").read_text(encoding="utf-8")

    def _load_toml(self, content: str) -> dict:
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib  # type: ignore[no-redef]
        return tomllib.loads(content)

    def test_generated_profile_parses_as_valid_toml(self):
        content = self._generated_content()
        self._load_toml(content)  # raises on invalid TOML

    def test_hook_commands_contain_absolute_python3_path(self):
        content = self._generated_content()
        data = self._load_toml(content)
        for section in ("PreToolUse", "SessionStart", "Stop"):
            hooks = data.get("hooks", {}).get(section, [])
            for entry in hooks:
                for hook in entry.get("hooks", []):
                    cmd = hook.get("command", "")
                    self.assertTrue(
                        cmd.startswith("python3 "),
                        f"{section} hook command should start with 'python3 ': {cmd!r}",
                    )
                    parts = cmd.split(" ", 1)
                    self.assertEqual(len(parts), 2, f"Expected 'python3 <path>', got: {cmd!r}")
                    self.assertTrue(
                        Path(parts[1]).is_absolute(),
                        f"{section} hook script path is not absolute: {parts[1]!r}",
                    )

    def test_hook_timeout_mirrors_configured_llm_timeout(self):
        content = self._generated_content(config_loader=lambda: _StubConfig(timeout=777))
        data = self._load_toml(content)
        for section in ("PreToolUse", "SessionStart", "Stop"):
            hooks = data.get("hooks", {}).get(section, [])
            for entry in hooks:
                for hook in entry.get("hooks", []):
                    self.assertEqual(hook.get("timeout"), 777)

    def test_hook_timeout_changes_when_configured_timeout_changes(self):
        low = self._load_toml(self._generated_content(config_loader=lambda: _StubConfig(timeout=100)))
        high = self._load_toml(self._generated_content(config_loader=lambda: _StubConfig(timeout=900)))
        self.assertEqual(low["hooks"]["Stop"][0]["hooks"][0]["timeout"], 100)
        self.assertEqual(high["hooks"]["Stop"][0]["hooks"][0]["timeout"], 900)

    def test_hook_script_paths_point_at_real_files(self):
        """Regression: hook scripts live under mcp-server/hooks/, not <plugin_root>/hooks/."""
        content = self._generated_content()
        data = self._load_toml(content)
        for section in ("PreToolUse", "SessionStart", "Stop"):
            hooks = data.get("hooks", {}).get(section, [])
            for entry in hooks:
                for hook in entry.get("hooks", []):
                    _, path = hook.get("command", "").split(" ", 1)
                    self.assertTrue(Path(path).is_file(), f"{section} hook script does not exist: {path!r}")

    def test_mcp_server_paths_point_at_real_files(self):
        content = self._generated_content()
        data = self._load_toml(content)
        for name in ("pipeline", "docs"):
            args = data["mcp_servers"][name]["args"]
            self.assertTrue(Path(args[0]).is_file(), f"{name} server script does not exist: {args[0]!r}")


if __name__ == "__main__":
    unittest.main()
