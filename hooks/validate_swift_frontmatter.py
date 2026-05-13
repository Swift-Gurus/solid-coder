#!/usr/bin/env python3
"""PreToolUse hook — auto-corrects solid-frontmatter quality in Swift files.

Phase 1 (script): fast exits — non-Swift file, no solid-description present.
Phase 2 (claude -p --bare): receives the entire content being written so it
  can read the actual Swift implementation for context. The LLM returns a JSON
  object {"corrected_content": "..."} so the result is always unambiguously
  parseable regardless of any surrounding text.
  Script returns allow + updatedInput so the write proceeds with clean frontmatter.

Fails open on any infrastructure problem.
"""

import json
import re
import subprocess
import sys
from typing import Optional

CORRECTION_PROMPT = """\
You are a Swift solid-frontmatter quality checker.

The content below is being written to a Swift file. Inspect every \
`solid-description` field inside `/** ... */` blocks and fix any that violate \
the quality rules. Use the Swift code that follows each block as context — the \
description should capture behavior and purpose, not implementation detail.

Rules for solid-description:
Describe the CAPABILITY — what the type does at the interface level, not how \
it does it. Ask: "would this sentence still be true if the implementation \
changed entirely?" If not, it's describing implementation, not capability.

- One concise sentence at the capability/role level
- Must NOT name any concrete thing that lives inside the implementation: \
types, variables, APIs, values, colors, layout details, composition steps, \
wiring to other components — anything that could change without changing \
the public contract
- Must NOT be vague: "A view", "A service", "Handles data" with no substance
- For abstraction category: MUST start with "Contract for..." or \
"Contract that defines..."

When fixing:
- Preserve solid-name, solid-category, solid-spec, solid-stack exactly
- Only correct solid-description — touch nothing else
- Do not modify any Swift code

Your entire response MUST be a single raw JSON object and nothing else. \
No markdown fences. No explanation. No commentary. The response starts \
with `{{` and ends with `}}` and contains only valid JSON.

{{"corrected_content": "<full file content corrected or unchanged>"}}

File content:
{content}
"""

_JSON_OBJ = re.compile(r'\{.*\}', re.DOTALL)


def _parse_corrected(raw: str) -> Optional[str]:
    """Extract corrected_content from the LLM JSON response.

    Handles optional markdown code fences around the JSON object.
    Returns None if parsing fails.
    """
    # Strip optional ```json / ``` fences
    text = re.sub(r'```[a-zA-Z]*\n?', '', raw).strip()
    # Find the JSON object — could be surrounded by stray text
    m = _JSON_OBJ.search(text)
    if not m:
        return None
    try:
        obj = json.loads(m.group())
        content = obj.get("corrected_content")
        return content if isinstance(content, str) else None
    except (json.JSONDecodeError, ValueError):
        return None


def fix_with_claude(
    content: str,
    parent_session_id: str = "",
    file_path: str = "",
) -> Optional[str]:
    """Run the content through a bare Claude session.

    Returns:
        None  — infrastructure error, caller should fail open.
        str   — full file content (unchanged or corrected); compare with
                original to decide whether to apply updatedInput.
    """
    header = ""
    if parent_session_id:
        header = f"# spawned-by: {parent_session_id}\n\n"

    prompt = header + CORRECTION_PROMPT.format(content=content)
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--output-format", "json", "--bare"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return None

        try:
            events = json.loads(result.stdout)
            if not isinstance(events, list):
                events = [events]
        except (json.JSONDecodeError, ValueError):
            return None

        inner_raw = ""
        for obj in reversed(events):
            if isinstance(obj, dict) and obj.get("type") == "result":
                inner_raw = obj.get("result", "")
                break

        if not inner_raw.strip():
            return None

        return _parse_corrected(inner_raw)
    except Exception:
        return None


def _allow() -> None:
    sys.exit(0)


def _allow_corrected(tool_name: str, tool_input: dict, corrected: str) -> None:
    input_key = "content" if tool_name == "Write" else "new_string"
    updated = dict(tool_input)
    updated[input_key] = corrected
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": updated,
        }
    }))
    sys.stdout.flush()
    sys.exit(0)


def main() -> None:
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        _allow()
        return

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")
    parent_session_id = event.get("session_id", "")

    if not file_path.endswith(".swift"):
        _allow()
        return

    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
    else:
        _allow()
        return

    if "solid-description:" not in content:
        _allow()
        return

    corrected = fix_with_claude(
        content,
        parent_session_id=parent_session_id,
        file_path=file_path,
    )

    if corrected is None or corrected == content:
        _allow()
        return

    _allow_corrected(tool_name, tool_input, corrected)


if __name__ == "__main__":
    main()
