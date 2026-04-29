#!/usr/bin/env python3
"""PostToolUse hook — auto-split implementation-plan.json into chunks on write.

Fires after Write or Edit. When the written file is implementation-plan.json,
runs split-plan.py to produce chunk files in {parent}/implementation-plan/.
Silent on success. Prints error and exits 1 on failure so the agent sees it.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT", Path(__file__).resolve().parents[1]))
SPLIT_SCRIPT = PLUGIN_ROOT / "skills" / "synthesize-implementation" / "scripts" / "split-plan.py"


def main():
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        sys.exit(0)

    if event.get("tool_name") not in ("Write", "Edit"):
        sys.exit(0)

    file_path_str = event.get("tool_input", {}).get("file_path", "")
    if not file_path_str or not file_path_str.endswith("implementation-plan.json"):
        sys.exit(0)

    plan_path = Path(file_path_str)
    if not plan_path.exists():
        sys.exit(0)

    output_dir = plan_path.parent / "implementation-plan"
    output_dir.mkdir(exist_ok=True)

    cmd = [sys.executable, str(SPLIT_SCRIPT), str(plan_path), "--output-dir", str(output_dir)]
    arch_path = plan_path.parent / "arch.json"
    if arch_path.exists():
        cmd += ["--arch", str(arch_path)]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "userFacingError": f"split-plan failed for {plan_path.name}:\n{result.stderr.strip()}",
            }
        }))
        sys.exit(1)


if __name__ == "__main__":
    main()
