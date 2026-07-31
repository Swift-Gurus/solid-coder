"""Tests for bump-plugin-version.py, invoked via subprocess against its real CLI."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parents[1] / "bump-plugin-version.py"


def _write_manifest(path: Path, version: str, extra: dict = None) -> None:
    data = {"name": "solid-coder", "version": version}
    if extra:
        data.update(extra)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _run(args: list, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


class TestBumpPluginVersion(unittest.TestCase):
    def setUp(self):
        self._tmp_ctx = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp_ctx.cleanup)
        self.repo_root = Path(self._tmp_ctx.name)
        self.claude_manifest = self.repo_root / ".claude-plugin" / "plugin.json"
        self.codex_manifest = self.repo_root / ".codex-plugin" / "plugin.json"

    def _patch_manifest_paths(self):
        """The script hardcodes manifest paths relative to its own location under
        .claude/skills/version-bumper/scripts/ — so tests run it from a fake repo
        root with the same 4-levels-up layout, rather than patching constants."""
        script_home = self.repo_root / ".claude" / "skills" / "version-bumper" / "scripts"
        script_home.mkdir(parents=True)
        (script_home / "bump-plugin-version.py").write_text(_SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
        return script_home / "bump-plugin-version.py"

    def _run_in_fake_repo(self, args: list) -> subprocess.CompletedProcess:
        script_copy = self._patch_manifest_paths()
        return subprocess.run(
            [sys.executable, str(script_copy), *args],
            capture_output=True,
            text=True,
        )

    def test_default_patch_bump(self):
        _write_manifest(self.claude_manifest, "1.7.7")
        _write_manifest(self.codex_manifest, "1.7.7")

        result = self._run_in_fake_repo([])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1.7.7 -> 1.7.8", result.stdout)
        self.assertEqual(json.loads(self.claude_manifest.read_text())["version"], "1.7.8")
        self.assertEqual(json.loads(self.codex_manifest.read_text())["version"], "1.7.8")

    def test_minor_bump_resets_patch(self):
        _write_manifest(self.claude_manifest, "1.7.7")
        _write_manifest(self.codex_manifest, "1.7.7")

        result = self._run_in_fake_repo(["--part", "minor"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1.7.7 -> 1.8.0", result.stdout)

    def test_major_bump_resets_minor_and_patch(self):
        _write_manifest(self.claude_manifest, "1.7.7")
        _write_manifest(self.codex_manifest, "1.7.7")

        result = self._run_in_fake_repo(["--part", "major"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1.7.7 -> 2.0.0", result.stdout)

    def test_explicit_set_version(self):
        _write_manifest(self.claude_manifest, "1.7.7")
        _write_manifest(self.codex_manifest, "1.7.7")

        result = self._run_in_fake_repo(["--set", "9.9.9"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("1.7.7 -> 9.9.9", result.stdout)

    def test_version_drift_across_manifests_fails(self):
        _write_manifest(self.claude_manifest, "1.7.7")
        _write_manifest(self.codex_manifest, "1.7.6")

        result = self._run_in_fake_repo([])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("disagree", result.stderr)

    def test_missing_manifest_fails(self):
        _write_manifest(self.claude_manifest, "1.7.7")
        # codex manifest intentionally not written

        result = self._run_in_fake_repo([])

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not found", result.stderr)

    def test_preserves_other_manifest_fields(self):
        _write_manifest(self.claude_manifest, "1.7.7", extra={"description": "hello"})
        _write_manifest(self.codex_manifest, "1.7.7")

        result = self._run_in_fake_repo([])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(self.claude_manifest.read_text())["description"], "hello")


if __name__ == "__main__":
    unittest.main()
