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
    def _make_event(self, tmp_dir, principle):
        session_id = "test-session-review"
        agent_id = "reviewagent001"
        transcript_path = make_subagent_jsonl(
            tmp_dir, session_id, agent_id,
            f"principle: {principle}\nreview-input: /tmp/x.json",
        )
        return {
            "hook_event_name": "SubagentStart",
            "agent_type": "solid-coder:apply-principle-review-agent",
            "agent_id": agent_id,
            "transcript_path": transcript_path,
        }

    def test_returns_hook_json_with_rule_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(self._make_event(tmp, "SRP"))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            self.assertIn("rule.md", ctx)
            self.assertIn("srp", ctx.lower())

    def test_paths_are_absolute_and_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(self._make_event(tmp, "SRP"))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
            self.assertGreater(len(listed), 0, "no file paths found in context")
            for path in listed:
                self.assertTrue(Path(path).is_file(), f"path does not exist: {path}")

    def test_review_mode_includes_review_instructions(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(self._make_event(tmp, "SRP"))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            self.assertIn("review/instructions.md", ctx)

    def test_missing_principle_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            session_id = "test-session-noprinc"
            agent_id = "noprinc001"
            transcript_path = make_subagent_jsonl(
                tmp, session_id, agent_id, "review-input: /tmp/x.json"
            )
            event = {
                "hook_event_name": "SubagentStart",
                "agent_type": "solid-coder:apply-principle-review-agent",
                "agent_id": agent_id,
                "transcript_path": transcript_path,
            }
            r = run(event)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("principle", r.stderr.lower())

    def test_succeeds_when_jsonl_written_after_hook_fires(self):
        """Parallel agents: JSONL may not exist at hook fire time — retry must recover."""
        import threading
        with tempfile.TemporaryDirectory() as tmp:
            session_id = "test-session-delayed"
            agent_id = "delayedagent001"
            subagent_dir = Path(tmp) / session_id / "subagents"
            subagent_dir.mkdir(parents=True)
            jsonl = subagent_dir / f"agent-{agent_id}.jsonl"
            transcript_path = str(Path(tmp) / f"{session_id}.jsonl")

            event = {
                "hook_event_name": "SubagentStart",
                "agent_type": "solid-coder:apply-principle-review-agent",
                "agent_id": agent_id,
                "transcript_path": transcript_path,
            }

            # Write the JSONL 200ms after the hook script starts
            def write_late():
                time.sleep(0.2)
                entry = {"message": {"role": "user", "content": "principle: SRP\nreview-input: /tmp/x.json"}}
                jsonl.write_text(json.dumps(entry) + "\n", encoding="utf-8")

            t = threading.Thread(target=write_late)
            t.start()
            r = run(event)
            t.join()

        self.assertEqual(r.returncode, 0, r.stderr)
        ctx = additional_context(r)
        self.assertIn("srp", ctx.lower())

    def test_instruction_header_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(self._make_event(tmp, "SRP"))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            self.assertIn("Before starting the review", ctx)
            self.assertIn("MUST apply", ctx)

    def test_principle_case_insensitive(self):
        with tempfile.TemporaryDirectory() as tmp:
            r = run(self._make_event(tmp, "srp"))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            self.assertIn("srp", ctx.lower())


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
    def _make_plan(self, tmp_dir, matched_tags, chunked=True):
        plan = {"matched_tags": matched_tags, "plan_items": []}
        plan_dir = Path(tmp_dir) / "implementation-plan"
        plan_dir.mkdir()
        # Write implementation-plan.json next to the directory
        plan_json = Path(tmp_dir) / "implementation-plan.json"
        plan_json.write_text(json.dumps(plan), encoding="utf-8")
        if chunked:
            (plan_dir / "01-plan.json").write_text(json.dumps(plan), encoding="utf-8")
        return plan_dir, plan_json

    def _event_with_plan(self, tmp_dir, plan_dir, session_id="code-plan-session", agent_id="codeplanagent001"):
        subagent_dir = Path(tmp_dir) / session_id / "subagents"
        subagent_dir.mkdir(parents=True)
        jsonl = subagent_dir / f"agent-{agent_id}.jsonl"
        entry = {"message": {"role": "user", "content": f"mode: implement\nplan: {plan_dir}"}}
        jsonl.write_text(json.dumps(entry) + "\n", encoding="utf-8")
        return {
            "hook_event_name": "SubagentStart",
            "agent_type": "solid-coder:code-agent",
            "agent_id": agent_id,
            "transcript_path": str(Path(tmp_dir) / f"{session_id}.jsonl"),
        }

    def test_filters_to_matched_tags_from_plan(self):
        """Hook reads plan's matched_tags and filters code/instructions to matching principles only."""
        with tempfile.TemporaryDirectory() as tmp:
            plan_dir, _ = self._make_plan(tmp, ["srp"])
            event = self._event_with_plan(tmp, plan_dir)
            r = run(event)
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
            # Only SRP should load — no SwiftUI, no UITesting, no StructuredConcurrency
            for path in listed:
                self.assertNotIn("SwiftUI", path, "SwiftUI should not load for srp-only task")
                self.assertNotIn("UITesting", path, "UITesting should not load for srp-only task")
                self.assertNotIn("ui-testing", path)
                self.assertNotIn("StructuredConcurrency", path)

    def test_reads_tags_from_chunked_plan_directory(self):
        """Hook resolves implementation-plan.json next to the chunk directory."""
        with tempfile.TemporaryDirectory() as tmp:
            plan_dir, plan_json = self._make_plan(tmp, ["swiftui"], chunked=True)
            event = self._event_with_plan(tmp, plan_dir)
            r = run(event)
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            # SwiftUI should be included when tag matches
            self.assertIn("SwiftUI", ctx)

    def test_no_plan_falls_back_to_all_principles(self):
        """If prompt has no plan: line, all principles load (existing behavior)."""
        with tempfile.TemporaryDirectory() as tmp:
            subagent_dir = Path(tmp) / "nosession" / "subagents"
            subagent_dir.mkdir(parents=True)
            agent_id = "noplancodeagent"
            jsonl = subagent_dir / f"agent-{agent_id}.jsonl"
            entry = {"message": {"role": "user", "content": "mode: code\nprompt: write a service"}}
            jsonl.write_text(json.dumps(entry) + "\n", encoding="utf-8")
            event = {
                "hook_event_name": "SubagentStart",
                "agent_type": "solid-coder:code-agent",
                "agent_id": agent_id,
                "transcript_path": str(Path(tmp) / "nosession.jsonl"),
            }
            r = run(event)
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
            self.assertGreater(len(listed), 1, "should load multiple files when no plan")


class TestSynthFixesMatchedTagsFromOutputRoot(unittest.TestCase):
    def _make_output_root(self, tmp_dir, matched_tags):
        output_root = Path(tmp_dir) / "refactor-run" / "1"
        (output_root / "prepare").mkdir(parents=True)
        review_input = {"matched_tags": matched_tags, "files": []}
        (output_root / "prepare" / "review-input.json").write_text(
            json.dumps(review_input), encoding="utf-8"
        )
        return output_root

    def _event(self, tmp_dir, output_root, agent_id="synthagent001"):
        session_id = "synth-session"
        subagent_dir = Path(tmp_dir) / session_id / "subagents"
        subagent_dir.mkdir(parents=True)
        jsonl = subagent_dir / f"agent-{agent_id}.jsonl"
        entry = {"message": {"role": "user", "content": f"output-root: {output_root}\nrules-path: /tmp/rules"}}
        jsonl.write_text(json.dumps(entry) + "\n", encoding="utf-8")
        return {
            "hook_event_name": "SubagentStart",
            "agent_type": "solid-coder:synthesize-fixes-agent",
            "agent_id": agent_id,
            "transcript_path": str(Path(tmp_dir) / f"{session_id}.jsonl"),
        }

    def test_filters_by_matched_tags_from_review_input(self):
        """synth-fixes hook reads matched_tags from prepare/review-input.json."""
        with tempfile.TemporaryDirectory() as tmp:
            output_root = self._make_output_root(tmp, ["srp", "ocp"])
            r = run(self._event(tmp, output_root))
            self.assertEqual(r.returncode, 0, r.stderr)
            ctx = additional_context(r)
            listed = [l.strip().lstrip("- ") for l in ctx.splitlines() if l.strip().startswith("- /")]
            for path in listed:
                self.assertNotIn("ui-testing", path, "ui-testing should not load for srp/ocp task")
                self.assertNotIn("UITesting", path)
                self.assertNotIn("StructuredConcurrency", path)
                self.assertNotIn("SwiftUI", path)

    def test_no_review_input_falls_back_to_all_principles(self):
        """If output-root has no review-input.json, all principles load."""
        with tempfile.TemporaryDirectory() as tmp:
            output_root = Path(tmp) / "empty-run"
            output_root.mkdir()
            r = run(self._event(tmp, output_root))
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
