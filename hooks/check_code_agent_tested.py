#!/usr/bin/env python3
"""SubagentStop hook — blocks code-agent from finishing if Phase 5 was skipped.

Reads the subagent transcript and checks whether the build/test MCP tools
were called. If the agent completed without running tests, blocks the stop
so the agent resumes and must complete Phase 5 before finishing.

Fires only on exit_reason == "completed" — errors and cancellations pass through.
"""

import json
import sys
from pathlib import Path

# Any tool name that contains these substrings counts as a test run.
# Covers mcp__plugin_solid-coder_apple-build__test, xcodebuild test,
# swift test, pytest, etc.
_TEST_PATTERNS = ("__test", "xcodebuild", "swift test", "pytest", "unittest")

REMINDER = (
    "Phase 5 (Build & Test) was not completed. "
    "You MUST complete all of the following before finishing:\n"
    "  - Build the project and fix all errors and warnings\n"
    "  - Run the linter and fix all violations\n"
    "  - Run unit tests (component, then full suite) — all must be green\n"
    "  - Run UI tests if they exist — all must be green\n"
    "Return to Phase 5 and complete every step before outputting Phase 6."
)


def _test_was_run(called: set, bash_commands: list) -> bool:
    """Return True if any test invocation is detected."""
    for name in called:
        if any(p in name.lower() for p in _TEST_PATTERNS):
            return True
    for cmd in bash_commands:
        if any(p in cmd.lower() for p in _TEST_PATTERNS):
            return True
    return False


def _parse_transcript(transcript_path: str) -> tuple:
    """Return (tool_names: set, bash_commands: list) from the transcript."""
    tool_names: set = set()
    bash_commands: list = []
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    if obj.get("type") == "assistant":
                        for block in obj.get("message", {}).get("content", []):
                            if block.get("type") == "tool_use":
                                name = block.get("name", "")
                                tool_names.add(name)
                                if name == "Bash":
                                    cmd = block.get("input", {}).get("command", "")
                                    if cmd:
                                        bash_commands.append(cmd)
                except (json.JSONDecodeError, ValueError):
                    pass
    except OSError:
        pass
    return tool_names, bash_commands


def main() -> None:
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if event.get("exit_reason") != "completed":
        sys.exit(0)

    transcript_path = event.get("transcript_path", "")
    if not transcript_path:
        sys.exit(0)

    tool_names, bash_commands = _parse_transcript(transcript_path)

    if _test_was_run(tool_names, bash_commands):
        sys.exit(0)

    sys.stdout.write(json.dumps({"decision": "block", "reason": REMINDER}))
    sys.stdout.flush()
    sys.exit(0)


if __name__ == "__main__":
    main()
