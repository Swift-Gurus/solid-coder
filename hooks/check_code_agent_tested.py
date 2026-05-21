#!/usr/bin/env python3
"""SubagentStop hook — blocks code-agent from finishing if it wrote tests but never ran them.

Only fires when the agent actually wrote test files this session. If the agent
wrote only production code, this hook passes through — requiring tests in that
case is a different responsibility.

Errors and cancellations always pass through.
"""

import json
import sys
from pathlib import Path


_REMINDER = (
    "Phase 5 (Build & Test) was not completed. "
    "You wrote test files this session but did not run them. "
    "You MUST complete all of the following before finishing:\n"
    "  - Build the project and fix all errors and warnings\n"
    "  - Run the linter and fix all violations\n"
    "  - Run the tests you wrote — all must be green\n"
    "  - Run UI tests if you wrote UI test files — all must be green\n"
    "Return to Phase 5 and complete every step before outputting Phase 6."
)


def _parse_transcript(transcript_path: str) -> tuple:
    """Return (tool_names, bash_commands, mcp_test_calls, written_paths).

    mcp_test_calls: list of input dicts from mcp__...__test tool calls
    written_paths: file paths from Write/Edit tool calls
    """
    tool_names: set = set()
    bash_commands: list = []
    mcp_test_calls: list = []
    written_paths: list = []

    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                try:
                    obj = json.loads(line.strip())
                    if obj.get("type") == "assistant":
                        for block in obj.get("message", {}).get("content", []):
                            if block.get("type") != "tool_use":
                                continue
                            name = block.get("name", "")
                            inp = block.get("input") or {}
                            tool_names.add(name)
                            if name == "Bash":
                                cmd = inp.get("command", "")
                                if cmd:
                                    bash_commands.append(cmd)
                            elif "__test" in name and "build" in name:
                                mcp_test_calls.append(inp)
                            elif name in ("Write", "Edit"):
                                fp = inp.get("file_path", "")
                                if fp:
                                    written_paths.append(fp)
                except (json.JSONDecodeError, ValueError):
                    pass
    except OSError:
        pass
    return tool_names, bash_commands, mcp_test_calls, written_paths


def _unit_test_files_written(written_paths: list) -> bool:
    """Return True if the agent wrote any unit test files this session."""
    for path in written_paths:
        lower = path.lower()
        # Matches FooTests.swift, FooSpec.swift, tests/Foo.swift, etc.
        if (lower.endswith("tests.swift") or lower.endswith("spec.swift")
                or "/tests/" in lower or "/test/" in lower):
            # Exclude UITest files — those are handled separately
            if "uitest" not in lower and "ui_test" not in lower and "ui-test" not in lower:
                return True
    return False


def _ui_test_files_written(written_paths: list) -> bool:
    """Return True if the agent wrote any UI test files this session."""
    for path in written_paths:
        lower = path.lower()
        if "uitest" in lower or "ui_test" in lower or "ui-test" in lower:
            return True
    return False


def _unit_test_was_run(tool_names: set, bash_commands: list,
                       mcp_test_calls: list) -> bool:
    """Return True if unit tests were run."""
    for call in mcp_test_calls:
        if not call.get("skip_unit_tests", False):
            return True
    for cmd in bash_commands:
        lower = cmd.lower()
        if "xcodebuild" in lower and " test" in lower:
            return True
    for name in tool_names:
        if any(p in name.lower() for p in ("swift test", "pytest", "unittest")):
            return True
    for cmd in bash_commands:
        if any(p in cmd.lower() for p in ("swift test", "pytest", "unittest")):
            return True
    return False


def _ui_test_was_run(mcp_test_calls: list, bash_commands: list) -> bool:
    """Return True if UI tests were run."""
    for call in mcp_test_calls:
        if not call.get("skip_ui_tests", False):
            return True
    for cmd in bash_commands:
        lower = cmd.lower()
        if "xcodebuild" in lower and " test" in lower:
            if "--skip-ui-tests" not in lower and "-skipuitests" not in lower:
                return True
    return False


def main() -> None:
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if event.get("exit_reason") in ("error", "cancelled"):
        sys.exit(0)

    transcript_path = event.get("transcript_path", "")
    if not transcript_path:
        sys.exit(0)

    tool_names, bash_commands, mcp_test_calls, written_paths = _parse_transcript(
        transcript_path
    )

    wrote_unit_tests = _unit_test_files_written(written_paths)
    wrote_ui_tests = _ui_test_files_written(written_paths)

    # Only enforce if the agent actually wrote test code this session
    if not wrote_unit_tests and not wrote_ui_tests:
        sys.exit(0)

    needs_block = (
        (wrote_unit_tests and not _unit_test_was_run(tool_names, bash_commands, mcp_test_calls))
        or (wrote_ui_tests and not _ui_test_was_run(mcp_test_calls, bash_commands))
    )

    if needs_block:
        sys.stdout.write(json.dumps({"decision": "block", "reason": _REMINDER}))
        sys.stdout.flush()
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
