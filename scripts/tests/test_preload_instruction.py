"""Tests for gateway.py preload_instruction.

Contract:
  - Reads SubagentStart hook JSON from stdin (CC format: agent_type, agent_id,
    transcript_path — no prompt field)
  - Maps agent_type → mode
  - For review mode: reads principle from subagent's JSONL via transcript_path + agent_id
  - Calls load_rules to resolve file paths from references/
  - Emits hook JSON: {"hookSpecificOutput": {"hookEventName": "SubagentStart",
                       "additionalContext": "<instruction with file paths>"}}
"""

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
GATEWAY = PROJECT_ROOT / "mcp-server" / "gateway.py"


def run(event, extra_args=()):
    return subprocess.run(
        [sys.executable, str(GATEWAY), "preload_instruction", *extra_args],
        input=json.dumps(event), capture_output=True, text=True,
        cwd=PROJECT_ROOT,
    )


def additional_context(r):
    """Extract additionalContext string from hook JSON stdout."""
    out = json.loads(r.stdout)
    return out["hookSpecificOutput"]["additionalContext"]


def make_subagent_jsonl(tmp_dir, session_id, agent_id, prompt_text):
    """Write a minimal subagent JSONL file matching CC's layout."""
    subagent_dir = Path(tmp_dir) / session_id / "subagents"
    subagent_dir.mkdir(parents=True)
    jsonl = subagent_dir / f"agent-{agent_id}.jsonl"
    entry = {"message": {"role": "user", "content": prompt_text}}
    jsonl.write_text(json.dumps(entry) + "\n", encoding="utf-8")
    transcript_path = str(Path(tmp_dir) / f"{session_id}.jsonl")
    return transcript_path


class TestInvalidStdin(unittest.TestCase):
    def test_malformed_json_is_rejected(self):
        r = subprocess.run(
            [sys.executable, str(GATEWAY), "preload_instruction"],
            input="not json", capture_output=True, text=True,
            cwd=PROJECT_ROOT,
        )
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("hook JSON", r.stderr)


class TestUnknownAgentType(unittest.TestCase):
    def test_unknown_agent_returns_empty(self):
        event = {
            "hook_event_name": "SubagentStart",
            "agent_type": "solid-coder:not-a-known-agent",
            "agent_id": "abc",
            "transcript_path": "/tmp/fake.jsonl",
        }
        r = run(event)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "")


class TestReviewMode(unittest.TestCase):
    """Review agents are excluded from the hook — they load rules via principle-folder in prompt."""

    def _event(self, agent_id="reviewagent001"):
        return {
            "hook_event_name": "SubagentStart",
            "agent_type": "solid-coder:apply-principle-review-agent",
            "agent_id": agent_id,
            "transcript_path": "/tmp/fake.jsonl",
        }

    def test_review_hook_returns_empty(self):
        r = run(self._event())
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), "")

    def test_review_hook_always_returns_empty_regardless_of_cwd(self):
        with tempfile.TemporaryDirectory() as tmp:
            event = {**self._event(), "cwd": tmp}
            r = run(event)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(r.stdout.strip(), "")


class TestCodeMode(unittest.TestCase):
    def _event(self):
        return {
            "hook_event_name": "SubagentStart",
            "agent_type": "solid-coder:code-agent",
            "agent_id": "codeagent001",
            "transcript_path": "/tmp/fake.jsonl",
        }

    def test_returns_paths_for_multiple_principles(self):
        r = run(self._event())
        self.assertEqual(r.returncode, 0, r.stderr)
        ctx = additional_context(r)
        listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
        self.assertGreater(len(listed), 1, "code mode should return multiple file paths")

    def test_all_returned_paths_exist(self):
        r = run(self._event())
        self.assertEqual(r.returncode, 0, r.stderr)
        ctx = additional_context(r)
        listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
        for path in listed:
            self.assertTrue(Path(path).is_file(), f"path does not exist: {path}")

    def test_excludes_review_instructions(self):
        r = run(self._event())
        self.assertEqual(r.returncode, 0, r.stderr)
        ctx = additional_context(r)
        listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
        for path in listed:
            self.assertNotIn("review/instructions.md", path)

    def test_code_mode_includes_pattern_index(self):
        r = run(self._event())
        self.assertEqual(r.returncode, 0, r.stderr)
        ctx = additional_context(r)
        self.assertIn("Design Patterns Index", ctx)
        self.assertIn("design_patterns", ctx)
        self.assertIn("Whenever you need to use a design pattern", ctx)

    def test_code_mode_excludes_pattern_files_from_preload_list(self):
        r = run(self._event())
        self.assertEqual(r.returncode, 0, r.stderr)
        ctx = additional_context(r)
        listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
        for path in listed:
            self.assertNotIn("design_patterns", path, "pattern files should not be pre-loaded")


class TestCodeModeMatchedTagsFromCwd(unittest.TestCase):
    """Hook reads matched_tags from cwd/.solid_coder/ — no JSONL timing dependency."""

    def _event_with_cwd(self, cwd, agent_id="cwdcodeagent001"):
        return {
            "hook_event_name": "SubagentStart",
            "agent_type": "solid-coder:code-agent",
            "agent_id": agent_id,
            "transcript_path": "/tmp/fake.jsonl",  # JSONL won't exist — cwd takes priority
            "cwd": str(cwd),
        }

    def test_reads_matched_tags_from_implementation_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            solid_dir = Path(tmp) / ".solid_coder" / "implement-SPEC-001"
            solid_dir.mkdir(parents=True)
            plan = {"matched_tags": ["srp", "ocp"], "plan_items": []}
            (solid_dir / "implementation-plan.json").write_text(json.dumps(plan))
            r = run(self._event_with_cwd(tmp))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
            for path in listed:
                self.assertNotIn("SwiftUI", path)
                self.assertNotIn("ui-testing", path)

    def test_no_solid_coder_dir_falls_back_to_all(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(self._event_with_cwd(tmp))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
            self.assertGreater(len(listed), 1)


class TestCodeModeMatchedTagsFromPlan(unittest.TestCase):
    """Code mode reads matched_tags from .solid_coder/implement-*/implementation-plan.json via cwd."""

    def _make_cwd_with_plan(self, tmp_dir, matched_tags):
        plan = {"matched_tags": matched_tags, "plan_items": []}
        solid_dir = Path(tmp_dir) / ".solid_coder" / "implement-SPEC-001"
        solid_dir.mkdir(parents=True)
        (solid_dir / "implementation-plan.json").write_text(json.dumps(plan))
        return tmp_dir

    def _event_with_cwd(self, cwd, agent_id="codeplanagent001"):
        return {
            "hook_event_name": "SubagentStart",
            "agent_type": "solid-coder:code-agent",
            "agent_id": agent_id,
            "transcript_path": "/tmp/fake.jsonl",
            "cwd": str(cwd),
        }

    def test_filters_to_matched_tags_from_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._make_cwd_with_plan(tmp, ["srp"])
            r = run(self._event_with_cwd(cwd))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
            for path in listed:
                self.assertNotIn("SwiftUI", path)
                self.assertNotIn("StructuredConcurrency", path)

    def test_reads_tags_from_chunked_plan_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._make_cwd_with_plan(tmp, ["swiftui"])
            r = run(self._event_with_cwd(cwd))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            self.assertIn("SwiftUI", ctx)

    def test_no_plan_falls_back_to_all_principles(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(self._event_with_cwd(tmp))  # no .solid_coder dir
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
            self.assertGreater(len(listed), 1)


class TestSynthFixesMatchedTagsFromOutputRoot(unittest.TestCase):
    """synth-fixes reads matched_tags from .solid_coder/refactor-*/1/prepare/review-input.json via cwd."""

    def _make_cwd_with_review_input(self, tmp_dir, matched_tags):
        run_dir = Path(tmp_dir) / ".solid_coder" / "refactor-run" / "1" / "prepare"
        run_dir.mkdir(parents=True)
        review_input = {"matched_tags": matched_tags, "files": []}
        (run_dir / "review-input.json").write_text(json.dumps(review_input), encoding="utf-8")
        return tmp_dir

    def _event(self, cwd, agent_id="synthagent001"):
        return {
            "hook_event_name": "SubagentStart",
            "agent_type": "solid-coder:synthesize-fixes-agent",
            "agent_id": agent_id,
            "transcript_path": "/tmp/fake.jsonl",
            "cwd": str(cwd),
        }

    def test_filters_by_matched_tags_from_review_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            cwd = self._make_cwd_with_review_input(tmp, ["srp", "ocp"])
            r = run(self._event(cwd))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
            for path in listed:
                self.assertNotIn("StructuredConcurrency", path)
                self.assertNotIn("SwiftUI", path)

    def test_no_review_input_falls_back_to_all_principles(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(self._event(tmp))  # no .solid_coder dir
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
            self.assertGreater(len(listed), 1)


class TestPlannerMode(unittest.TestCase):
    def test_planner_returns_rule_paths(self):
        event = {
            "hook_event_name": "SubagentStart",
            "agent_type": "solid-coder:plan-agent",
            "agent_id": "planagent001",
            "transcript_path": "/tmp/fake.jsonl",
        }
        r = run(event)
        self.assertEqual(r.returncode, 0, r.stderr)
        ctx = additional_context(r)
        listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
        self.assertGreater(len(listed), 0)
        rule_paths = [p for p in listed if p.endswith("rule.md")]
        self.assertGreater(len(rule_paths), 0)


if __name__ == "__main__":
    unittest.main()
