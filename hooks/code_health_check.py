#!/usr/bin/env python3
"""PreToolUse hook — SOLID health check on source files before writing.

Fires before Write or Edit on any supported source file. Uses the gateway to
discover active principles for the file content, then passes the rule file paths
to a bare Claude session so it can Read them itself — keeping the initial prompt
small and fast. If violations are found, blocks the write with the full list so
the agent can fix everything in one pass before retrying.

Skips: unsupported extensions, test files.
Fails open silently — an infrastructure error never blocks the write.
"""

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
GATEWAY = PLUGIN_ROOT / "mcp-server" / "gateway.py"

# Extend this dict as new languages gain principle coverage.
# Maps file extension → display name used in the prompt.
SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".swift": "Swift",
}


# Import patterns for tag detection, keyed by candidate tag name.
TAG_PATTERNS: dict[str, list[str]] = {
    "swiftui": [r"\bimport\s+SwiftUI\b", r"\bView\b", r"\b@State\b", r"\b@Observable\b"],
    "structured-concurrency": [r"\basync\b", r"\bawait\b", r"\bTask\b", r"\bActor\b"],
    "unit-test": [r"\bimport\s+Testing\b", r"\bXCTestCase\b", r"\b@Test\b"],
    "ui-test": [r"\bXCUIApplication\b", r"\bXCUIElement\b"],
    "xctest": [r"\bimport\s+XCTest\b"],
}

HEALTH_PROMPT = """\
You are a SOLID code quality gate doing a pre-write check.

<exceptions>
The following are exempt from all rules — do not report violations for them:
- `#Preview` blocks and their entire body
- Files whose sole purpose is SwiftUI previews (filename ends with \
"Previews.swift" or "Preview.swift", or the file contains only `#Preview` \
blocks with no production types)
</exceptions>

<review-rules>
{rules}
</review-rules>

<code-to-review>
{content}
</code-to-review>

Before listing violations, run the DRY-1 search procedure from the loaded rules: \
call `mcp__plugin_solid-coder_pipeline__search_codebase` with synonyms for \
each type defined in this file to detect cross-file reuse misses. \
The destination path for this write is `{file_path}`. Do NOT read that path — \
the file does not exist yet or contains stale content. Use the path only as a \
filter: if `search_codebase` returns a match whose path is `{file_path}`, \
discard that match. It is a self-reference, not a reuse miss.

If you find violations, load targeted fix guidance before writing your response:
- For each unique metric_id violation found, call \
`mcp__docs__load_fix_for_violation` with only metric_id (e.g. metric_id="OCP-1") — \
no principle needed, it is resolved automatically. The tool returns fix instructions \
directly in `content`.
- Use those instructions to make the `fix` field in your response concrete and actionable.

List ALL violations (both within-file and cross-file). For each include:
- principle: the rule name (e.g. SRP, OCP, DRY)
- metric_id: the metric identifier (e.g. OCP-1, SRP-2)
- issue: what is wrong
- fix: the specific change needed (informed by the loaded fix instructions)

Your entire response MUST be a single raw JSON object and nothing else. \
No markdown fences. No explanation. No commentary. The response starts \
with `{{` and ends with `}}` and contains only valid JSON.

{{"violations": [{{"principle": "string", "metric_id": "string", "issue": "string", "fix": "string"}}]}}

Empty array if clean: {{"violations": []}}
"""

_JSON_OBJ = re.compile(r"\{.*\}", re.DOTALL)
_LOG = Path.home() / ".claude" / "solid-coder-gate.log"


def _log_error(file_path: str, reason: str) -> None:
    import time
    name = Path(file_path).name
    try:
        with _LOG.open("a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} HEALTH_ERR {name}: {reason}\n")
    except Exception:
        pass


def _parse_violations(raw: str) -> Optional[list]:
    """Extract the violations array from the LLM JSON response.

    Handles optional markdown code fences and surrounding text.
    Returns None if parsing fails entirely.
    Returns [] if the response is valid JSON with no violations.
    """
    text = re.sub(r"```[a-zA-Z]*\n?", "", raw).strip()
    m = _JSON_OBJ.search(text)
    if not m:
        return None
    try:
        obj = json.loads(m.group())
        violations = obj.get("violations")
        if not isinstance(violations, list):
            return None
        return [
            v for v in violations
            if isinstance(v, dict)
            and isinstance(v.get("principle"), str)
            and isinstance(v.get("issue"), str)
            and isinstance(v.get("fix"), str)
        ]
    except (json.JSONDecodeError, ValueError):
        return None


def _format_block_reason(violations: list) -> str:
    lines = [f"{len(violations)} violation(s) found:"]
    for v in violations:
        lines.append(f"  • {v['principle']} — {v['issue']} Fix: {v['fix']}")
    return "\n".join(lines)


def _detect_tags(content: str, candidate_tags: list) -> list:
    matched = []
    for tag in candidate_tags:
        patterns = TAG_PATTERNS.get(tag, [])
        if any(re.search(p, content) for p in patterns):
            matched.append(tag)
    # UI tests and unit tests are mutually exclusive — XCUIApplication is the
    # definitive signal. If present, drop unit-test/xctest so only UITesting
    # rules load; without it, drop ui-test so only Unit Testing rules load.
    if "ui-test" in matched:
        matched = [t for t in matched if t not in ("unit-test", "xctest")]
    else:
        matched = [t for t in matched if t != "ui-test"]
    return matched


def _get_candidate_tags() -> list:
    try:
        result = subprocess.run(
            ["python3", str(GATEWAY), "get_candidate_tags"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return []
        data = json.loads(result.stdout)
        return data.get("candidate_tags", [])
    except Exception:
        return []


_DISPLAY_NAME_RE = re.compile(r"^displayName:\s*(.+)$", re.MULTILINE)


def _principle_display_name(path: Path) -> str:
    """Return the human-readable principle name for a rule file path.

    Reads ``displayName:`` from the sibling ``rule.md`` in the principle
    folder (``path.parent.parent``).  Falls back to the folder name so the
    function never raises.
    """
    rule_md = path.parent.parent / "rule.md"
    try:
        text = rule_md.read_text(encoding="utf-8")
        m = _DISPLAY_NAME_RE.search(text)
        if m:
            return m.group(1).strip()
    except OSError:
        pass
    return path.parents[1].name


def _load_rules(matched_tags: list) -> Optional[str]:
    """Load and return the concatenated content of all active code rule files."""
    cmd = ["python3", str(GATEWAY), "load_rules", "--mode", "code"]
    if matched_tags:
        cmd += ["--matched_tags", ",".join(matched_tags)]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            return None
        data = json.loads(result.stdout)
        paths = data.get("paths_to_load", [])
        parts = []
        for p in paths:
            try:
                text = Path(p).read_text()
                if text.startswith("---"):
                    end = text.find("\n---", 3)
                    if end != -1:
                        text = text[end + 4:].strip()
                principle = _principle_display_name(Path(p))
                parts.append(f"## {principle}\n{text}")
            except OSError:
                continue
        return "\n\n".join(parts) if parts else None
    except Exception:
        return None


def _check(content: str, path: str, language: str, parent_session_id: str) -> Optional[list]:
    """Run the health check. Returns list of violation dicts, [] if clean, None on error."""
    candidate_tags = _get_candidate_tags()
    matched_tags = _detect_tags(content, candidate_tags)
    rules = _load_rules(matched_tags)
    if not rules:
        _log_error(path, "gateway_failed: could not load rules")
        return None

    header = ""
    if parent_session_id:
        header = f"# spawned-by: {parent_session_id}\n\n"

    prompt = header + HEALTH_PROMPT.format(
        language=language,
        rules=rules,
        content=content,
        file_path=path,
    )

    pipeline_server = str(PLUGIN_ROOT / "mcp-server" / "pipeline" / "server.py")
    docs_server = str(PLUGIN_ROOT / "mcp-server" / "server.py")
    mcp_config = json.dumps({
        "mcpServers": {
            "pipeline": {"command": "python3", "args": [pipeline_server]},
            "docs": {"command": "python3", "args": [docs_server]},
        }
    })

    try:
        result = subprocess.run(
            [
                "claude", "-p", prompt,
                "--output-format", "json",
                "--bare",
                "--mcp-config", mcp_config,
                "--allowedTools", (
                    "mcp__pipeline__search_codebase,"
                    "mcp__docs__load_fix_for_violation"
                ),
            ],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            _log_error(path, f"exit={result.returncode} stderr={result.stderr.strip()[:200]}")
            return None

        try:
            events = json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError) as e:
            _log_error(path, f"json_parse_error={e} stdout[:100]={result.stdout[:100]}")
            return None
        if not isinstance(events, list):
            events = [events]

        inner_raw = ""
        for obj in reversed(events):
            if isinstance(obj, dict) and obj.get("type") == "result":
                inner_raw = obj.get("result", "")
                break

        if not inner_raw.strip():
            return None

        return _parse_violations(inner_raw)
    except subprocess.TimeoutExpired:
        _log_error(path, "timeout=300s")
        return None
    except Exception as e:
        _log_error(path, f"exception={type(e).__name__}: {e}")
        return None


def _allow() -> None:
    sys.exit(0)


def _block(violations: list) -> None:
    reason = "[health-check] " + _format_block_reason(violations)
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
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

    ext = Path(file_path).suffix.lower()
    language = SUPPORTED_EXTENSIONS.get(ext)
    if not language:
        _allow()
        return

    name = Path(file_path).name
    if "Tests" in name or "Spec" in name:
        _allow()
        return

    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
    else:
        _allow()
        return

    violations = _check(content, file_path, language, parent_session_id)
    if violations:
        _block(violations)
    else:
        _allow()


if __name__ == "__main__":
    main()
