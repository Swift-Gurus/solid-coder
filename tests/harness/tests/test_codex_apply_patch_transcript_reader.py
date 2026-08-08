"""Verifies apply_patch invocation extraction from Codex rollout transcripts."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from codex_apply_patch_transcript_reader import (  # noqa: E402
    CodexApplyPatchTranscriptReader,
)
from codex_apply_patch_call import CodexApplyPatchCall  # noqa: E402


class TestCodexApplyPatchTranscriptReader(unittest.TestCase):

    def test_reads_one_exec_wrapped_multi_file_patch(self) -> None:
        patch_content = (
            "*** Begin Patch\n"
            "*** Add File: One.swift\n+one\n"
            "*** Add File: Two.swift\n+two\n"
            "*** End Patch"
        )
        tool_input = (
            f"const patch = {json.dumps(patch_content)};\n"
            "const result = await tools.apply_patch(patch);\n"
            "text(result);"
        )

        calls = self._read(tool_input)

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0].patch_content, patch_content)

    def test_counts_each_apply_patch_invocation_inside_one_exec_call(self) -> None:
        patch_content = "*** Begin Patch\n*** Add File: One.swift\n+one\n*** End Patch"
        tool_input = (
            f"const patch = {json.dumps(patch_content)};\n"
            "await tools.apply_patch(patch);\n"
            "await tools.apply_patch(patch);"
        )

        calls = self._read(tool_input)

        self.assertEqual(len(calls), 2)

    def test_ignores_non_apply_patch_exec_calls(self) -> None:
        calls = self._read("const result = await tools.some_other_tool();")

        self.assertEqual(calls, [])

    def _read(self, tool_input: str) -> list[CodexApplyPatchCall]:
        with tempfile.TemporaryDirectory() as directory:
            sessions_root = Path(directory)
            transcript = sessions_root / "rollout.jsonl"
            transcript.write_text(
                json.dumps(
                    {
                        "type": "response_item",
                        "payload": {
                            "type": "custom_tool_call",
                            "name": "exec",
                            "input": tool_input,
                        },
                    }
                ),
                encoding="utf-8",
            )
            return CodexApplyPatchTranscriptReader().read(sessions_root)


if __name__ == "__main__":
    unittest.main()
