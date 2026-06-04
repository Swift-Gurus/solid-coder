#!/usr/bin/env python3
"""PreToolUse hook — auto-corrects solid-frontmatter quality in source files.

Supported: .swift and .py files that contain a solid-description field.

Phase 1 (script): fast exits — unsupported file type, no solid-description present.
Phase 2 (claude -p --bare): receives the entire content being written, identifies
  the language-appropriate comment boundaries, and fixes only solid-description.
  Returns allow + updatedInput so the write proceeds with clean frontmatter.

Fails open on any infrastructure problem.
"""

import sys
from pathlib import Path
from typing import Optional

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import (  # noqa: E402
    HookResponder,
    parse_hook_event,
    parse_json_field,
    run_claude_bare,
)

_SUPPORTED_EXTENSIONS = {".swift", ".py"}

CORRECTION_PROMPT = """\
You are a solid-frontmatter quality checker.

The content below is a source code file. Locate every solid-frontmatter block \
in the file and fix any `solid-description` field that violates the quality rules. \
Use the code that follows each block as context — the description should capture \
behavior and purpose, not implementation detail.

Solid-frontmatter is a structured comment block embedded in the file using \
the comment syntax of whatever language the file is written in. Different languages \
use different boundary markers — for example, Swift uses `/** ... */` doc-comment \
blocks placed before each type declaration, while Python uses a module-level \
triple-quoted string at the top of the file. Identify the correct comment boundaries \
for the language you see, then look for solid-frontmatter fields inside them.

A solid-frontmatter block contains these fields:
- solid-name        — name of the type or module  (DO NOT modify)
- solid-category    — category/role, e.g. service, utility, abstraction, model, \
viewmodel, screen, view-component, unit-test  (DO NOT modify)
- solid-spec        — spec number(s), e.g. [SPEC-014]  (optional; DO NOT modify)
- solid-stack       — frameworks/technologies, e.g. [swiftui, combine]  (optional; DO NOT modify)
- solid-description — one-sentence capability description  (fix ONLY this field)

Rules for solid-description:
Describe the CAPABILITY — what the type or module does at the interface level, \
not how it does it. Ask: "would this sentence still be true if the implementation \
changed entirely?" If not, it is describing implementation, not capability.

- One concise sentence at the capability/role level
- Must NOT name any concrete thing inside the implementation: types, variables, \
APIs, values, colors, layout details, composition steps, wiring to other \
components — anything that could change without changing the public contract
- Must NOT be vague: "A view", "A service", "Handles data" with no substance
- For abstraction category: MUST start with "Contract for..." or \
"Contract that defines..."

When fixing:
- Preserve solid-name, solid-category, solid-spec, solid-stack exactly
- Only correct solid-description — touch nothing else
- Do not modify any code or the comment boundary markers

Your entire response MUST be a single raw JSON object and nothing else. \
No markdown fences. No explanation. No commentary. The response starts \
with `{{` and ends with `}}` and contains only valid JSON.

{{"corrected_content": "<full file content corrected or unchanged>"}}

File content:
{content}
"""


def fix(content: str, parent_session_id: str = "") -> Optional[str]:
    header = f"# spawned-by: {parent_session_id}\n\n" if parent_session_id else ""
    prompt = header + CORRECTION_PROMPT.format(content=content)
    raw = run_claude_bare(prompt, timeout=300)
    if not raw:
        return None
    v = parse_json_field(raw, "corrected_content", str)
    return v if isinstance(v, str) else None


def main() -> None:
    responder = HookResponder()
    parsed = parse_hook_event(sys.stdin.read())
    if parsed is None:
        responder.allow()
        return

    tool_name, tool_input, file_path, session_id = parsed

    ext = Path(file_path).suffix.lower()
    if ext not in _SUPPORTED_EXTENSIONS:
        responder.allow()
        return

    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
    else:
        responder.allow()
        return

    if "solid-description:" not in content:
        responder.allow()
        return

    corrected = fix(content, parent_session_id=session_id)

    if corrected is None or corrected == content:
        responder.allow()
        return

    input_key = "content" if tool_name == "Write" else "new_string"
    updated = dict(tool_input)
    updated[input_key] = corrected
    responder.allow_with_update(updated)


if __name__ == "__main__":
    main()
