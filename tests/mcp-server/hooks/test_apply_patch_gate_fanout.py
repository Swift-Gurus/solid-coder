"""Regression tests for atomic per-file apply_patch health review."""

import threading
import unittest
from pathlib import Path
from unittest.mock import patch

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from _gate_fixtures import HC, call_main
from solid_coder_config import SolidCoderConfig
from test_utils import parse_hook_output


def _patch_event(files: list[tuple[str, str]]) -> dict:
    lines = ["*** Begin Patch"]
    for file_path, content in files:
        lines.append(f"*** Add File: {file_path}")
        lines.extend(f"+{line}" for line in content.splitlines())
    lines.append("*** End Patch")
    return {
        "tool_name": "apply_patch",
        "tool_input": {"command": "\n".join(lines)},
        "session_id": "patch-test",
        "cwd": "/workspace",
    }


class TestApplyPatchGateFanout(unittest.TestCase):
    def setUp(self):
        config = SolidCoderConfig(code_review_on_write_enabled=True)
        patcher = patch("hc_config.load_config", return_value=config)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_later_file_denial_blocks_after_all_files_run_concurrently(self):
        rendezvous = threading.Barrier(2)

        def check(content, file_path, language, session_id, cwd):
            rendezvous.wait(timeout=2)
            if file_path.endswith("Second.py"):
                return [{"principle": "SRP", "issue": "Second concern.", "fix": "Extract it."}]
            return []

        request = _patch_event([
            ("/src/First.py", "class First:\n    pass"),
            ("/src/Second.py", "class Second:\n    pass"),
        ])
        with patch(HC, side_effect=check) as health:
            _, output = call_main(request)

        result = parse_hook_output(output)
        reviewed_paths = {call.args[1] for call in health.call_args_list}
        self.assertEqual(reviewed_paths, {"/src/First.py", "/src/Second.py"})
        self.assertEqual(result["permissionDecision"], "deny")
        self.assertIn("/src/Second.py", result["permissionDecisionReason"])

    def test_multiple_denials_are_aggregated_into_one_response(self):
        def check(content, file_path, language, session_id, cwd):
            name = Path(file_path).name
            return [{"principle": "SRP", "issue": f"{name} concern.", "fix": "Extract it."}]

        request = _patch_event([
            ("/src/First.py", "class First:\n    pass"),
            ("/src/Second.py", "class Second:\n    pass"),
        ])
        with patch(HC, side_effect=check):
            _, output = call_main(request)

        result = parse_hook_output(output)
        reason = result["permissionDecisionReason"]
        self.assertEqual(result["permissionDecision"], "deny")
        self.assertIn("/src/First.py", reason)
        self.assertIn("/src/Second.py", reason)

    def test_unsupported_first_file_does_not_hide_supported_sibling(self):
        request = _patch_event([
            ("/src/README.md", "documentation"),
            ("/src/Second.py", "class Second:\n    pass"),
        ])
        violation = [{"principle": "SRP", "issue": "Second concern.", "fix": "Extract it."}]
        with patch(HC, return_value=violation) as health:
            _, output = call_main(request)

        result = parse_hook_output(output)
        health.assert_called_once()
        self.assertEqual(health.call_args.args[1], "/src/Second.py")
        self.assertEqual(result["permissionDecision"], "deny")

    def test_all_clean_files_allow_after_every_review(self):
        request = _patch_event([
            ("/src/First.py", "class First:\n    pass"),
            ("/src/Second.py", "class Second:\n    pass"),
        ])
        with patch(HC, return_value=[]) as health:
            code, output = call_main(request)

        self.assertEqual(code, 0)
        self.assertEqual(output, "")
        self.assertEqual(health.call_count, 2)


if __name__ == "__main__":
    unittest.main()
