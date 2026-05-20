#!/usr/bin/env python3
"""PreToolUse hook — SOLID health check on source files before writing.

Two-phase implementation:
  Phase 1: Load structured detection instructions via load_detection_rules.
  Phase 2: Claude measures raw metrics and returns partial outputs.
  Phase 3: score_severity scores the metrics against severity-band XML.
  Phase 4: Allow if clean, block if SEVERE/MINOR findings found.

Skips: unsupported extensions, test files.
Fails open silently — an infrastructure error never blocks the write.
"""

import json
import re
import sys
from pathlib import Path
from typing import Optional

HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from hook_utils import (
    make_hook_gate, run_gateway_cmd, run_claude_bare,
    JSON_OBJ_RE, strip_markdown_fences,
)

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
GATEWAY = PLUGIN_ROOT / "mcp-server" / "gateway.py"

SUPPORTED_EXTENSIONS: dict[str, str] = {
    ".swift": "Swift",
    ".py": "Python",
}

TAG_PATTERNS: dict[str, list[str]] = {
    "swiftui": [r"\bimport\s+SwiftUI\b", r"\bView\b", r"\b@State\b", r"\b@Observable\b"],
    "structured-concurrency": [r"\basync\b", r"\bawait\b", r"\bTask\b", r"\bActor\b"],
    "unit-test": [r"\bimport\s+Testing\b", r"\bXCTestCase\b", r"\b@Test\b"],
    "ui-test": [r"\bXCUIApplication\b", r"\bXCUIElement\b"],
    "xctest": [r"\bimport\s+XCTest\b"],
}

MEASUREMENT_PROMPT = """\
You are a SOLID code quality gate measuring raw metrics before a write.

<exceptions>
The following are exempt from all rules:
- `#Preview` blocks and their entire body
- Files whose sole purpose is SwiftUI previews
</exceptions>

<detection-instructions>
{detection_instructions}
</detection-instructions>

<code-to-review>
{content}
</code-to-review>

For EACH type/class/struct/function in the code, measure the raw metric values
defined in the detection instructions above. Output a JSON array of partial output
documents — one per active principle — matching this structure exactly:

[
  {{
    "agent": "<principle_name_lowercase>",
    "principle": "<Principle Display Name>",
    "timestamp": "2026-01-01T00:00:00Z",
    "files": [
      {{
        "file_path": "{file_path}",
        "units": [
          {{
            "unit_name": "<TypeName>",
            "unit_kind": "class|struct|enum|protocol|extension",
            "metrics": {{
              "<MetricID>": {{ "<metric_key>": <value> }}
            }}
          }}
        ]
      }}
    ]
  }}
]

Your entire response MUST be a single raw JSON array and nothing else.
No markdown fences. No explanation. No commentary.
Empty files array if no measurable units: [{{"agent": "srp", "principle": "...", "timestamp": "...", "files": []}}]
"""


def _parse_violations(raw: str) -> Optional[list]:
    """Extract violations array from a legacy LLM JSON response (fallback path)."""
    text = strip_markdown_fences(raw)
    m = JSON_OBJ_RE.search(text)
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
    if "ui-test" in matched:
        matched = [t for t in matched if t not in ("unit-test", "xctest")]
    else:
        matched = [t for t in matched if t != "ui-test"]
    return matched


def _gateway_call(subcommand: str, extra_args: Optional[list] = None,
                  timeout: int = 10, result_key: Optional[str] = None,
                  default=None):
    """Build and run a gateway command, returning a specific key or the raw dict."""
    cmd = ["python3", str(GATEWAY), subcommand] + (extra_args or [])
    data = run_gateway_cmd(cmd, timeout=timeout)
    if data is None:
        return default
    return data.get(result_key, default) if result_key else data


def _get_candidate_tags() -> list:
    return _gateway_call("get_candidate_tags", result_key="candidate_tags", default=[])


def _load_detection_rules(matched_tags: list) -> Optional[dict]:
    extra = ["--matched_tags", ",".join(matched_tags)] if matched_tags else []
    return _gateway_call("load_detection_rules", extra_args=extra)


def _score_via_gateway(partial_outputs: list) -> Optional[list]:
    return _gateway_call(
        "score_severity",
        extra_args=["--partial_outputs", json.dumps(partial_outputs)],
        timeout=30,
        result_key="results",
    )


def _violations_from_scored_results(scored_results: list) -> list:
    violations = []
    for entry in scored_results:
        if "error" in entry:
            continue
        principle = entry.get("principle", entry.get("agent", ""))
        for file_obj in entry.get("files", []):
            for unit in file_obj.get("units", []):
                for finding in unit.get("findings", []):
                    sev = finding.get("severity", "")
                    if sev in ("SEVERE", "MINOR"):
                        violations.append({
                            "principle": principle,
                            "metric_id": finding.get("metric_id", ""),
                            "issue": f"{finding.get('metric_id', '')} {sev} in {unit.get('unit_name', '')}",
                            "fix": f"Review {finding.get('metric_id', '')} metrics and apply fix guidance.",
                        })
    return violations


def _check(content: str, path: str, language: str, parent_session_id: str) -> Optional[list]:
    """Run the health check. Returns list of violation dicts, [] if clean, None on error."""
    candidate_tags = _get_candidate_tags()
    matched_tags = _detect_tags(content, candidate_tags)

    detection_data = _load_detection_rules(matched_tags)
    if not detection_data:
        return None

    principles = detection_data.get("principles", [])
    if not principles:
        return []

    header = f"# spawned-by: {parent_session_id}\n\n" if parent_session_id else ""
    prompt = header + MEASUREMENT_PROMPT.format(
        detection_instructions=json.dumps(principles, indent=2),
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

    inner_raw = run_claude_bare(prompt, mcp_config=mcp_config)
    if not inner_raw:
        return None

    text = strip_markdown_fences(inner_raw)
    try:
        partial_outputs = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return _parse_violations(inner_raw)

    if not isinstance(partial_outputs, list):
        return _parse_violations(inner_raw)

    scored_results = _score_via_gateway(partial_outputs)
    if scored_results is None:
        return _parse_violations(inner_raw)

    return _violations_from_scored_results(scored_results)


def main() -> None:
    gate = make_hook_gate()
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        gate.allow()
        return

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")
    parent_session_id = event.get("session_id", "")

    ext = Path(file_path).suffix.lower()
    language = SUPPORTED_EXTENSIONS.get(ext)
    if not language:
        gate.allow()
        return

    name = Path(file_path).name
    if "Tests" in name or "Spec" in name:
        gate.allow()
        return

    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
    else:
        gate.allow()
        return

    violations = _check(content, file_path, language, parent_session_id)
    if violations:
        gate.block("[health-check] " + _format_block_reason(violations))
    else:
        gate.allow()


if __name__ == "__main__":
    main()
