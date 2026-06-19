"""
solid-name: TestCodexProfileTomlValidity
solid-category: unit-test
solid-description: Validates that a generated TOML configuration profile is syntactically valid and contains correctly-formed hook command definitions.
"""

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from codex_profile_manager import CodexProfileManager  # noqa: E402
from test_utils import TempDirTestBase  # noqa: E402


class TestCodexProfileTomlValidity(TempDirTestBase):
    def _generated_content(self) -> str:
        CodexProfileManager(codex_home=str(self.output_dir)).ensure_profile()
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


if __name__ == "__main__":
    unittest.main()
