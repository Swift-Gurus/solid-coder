#!/usr/bin/env python3
"""Hook-facing wrapper: regenerate token docs and emit agent-visible warnings.

Invoked by .claude/settings.json PostToolUse hook when a file under references/
is edited. Regenerates token-budget.md and token-cost-by-mode.md, then emits
JSON on stdout formatted as a PostToolUse hook output so the agent sees the
delta and any threshold warnings.

Output format (Claude Code hook contract):
    {"hookSpecificOutput": {"hookEventName": "PostToolUse",
                            "additionalContext": "..."}}

Thresholds (against 200k context budget):
    - warn if any mode's MAX exceeds WARN_PCT of the budget
    - alert if any mode's MAX exceeds ALERT_PCT of the budget
"""

import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = PROJECT_ROOT / ".claude" / "docs"
BUDGET_DOC = DOCS_DIR / "token-budget.md"
COST_DOC = DOCS_DIR / "token-cost-by-mode.md"

CONTEXT_BUDGET = 200_000
WARN_PCT = 0.10   # 20k  — lowered for demo; typical target: 0.25 (50k)
ALERT_PCT = 0.20  # 40k  — lowered for demo; typical target: 0.40 (80k)


def run_regen() -> tuple[bool, str]:
    errors = []
    for script, out in [
        ("scripts/token-budget.py", BUDGET_DOC),
        ("scripts/token-cost-by-mode.py", COST_DOC),
    ]:
        r = subprocess.run(
            ["python3", str(PROJECT_ROOT / script), "--out", str(out)],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
        if r.returncode != 0:
            errors.append(f"{script}: {r.stderr.strip()}")
    return (len(errors) == 0, "; ".join(errors))


def parse_cost_doc() -> dict:
    """Extract MIN/MAX rows from token-cost-by-mode.md."""
    if not COST_DOC.exists():
        return {}
    text = COST_DOC.read_text()
    result = {"modes": [], "min": {}, "max": {}}

    # Header row: | Principle | Activation | code | review | planner | ... |
    header_match = re.search(r"\| Principle \| Activation \|([^\n]+)\|", text)
    if header_match:
        modes = [m.strip() for m in header_match.group(1).split("|") if m.strip()]
        result["modes"] = modes

    for label in ("MIN", "MAX"):
        m = re.search(rf"\| \*\*{label}\*\* \|([^\n]*)\|", text)
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        cells = [c for c in cells if c]  # drop empty cells (incl. the empty note column)
        vals = {}
        for mode, cell in zip(result["modes"], cells):
            num = re.search(r"([\d,]+)", cell)
            if num:
                vals[mode] = int(num.group(1).replace(",", ""))
        result[label.lower()] = vals
    return result


def build_summary(cost: dict) -> tuple[str, str]:
    """Return (severity, message). severity ∈ {ok, warn, alert}."""
    if not cost or "max" not in cost:
        return "ok", "Token docs regenerated."

    warn_thr = int(CONTEXT_BUDGET * WARN_PCT)
    alert_thr = int(CONTEXT_BUDGET * ALERT_PCT)

    flagged_alert = []
    flagged_warn = []
    for mode, val in cost["max"].items():
        if val >= alert_thr:
            flagged_alert.append((mode, val))
        elif val >= warn_thr:
            flagged_warn.append((mode, val))

    lines = []
    lines.append("Token docs refreshed (references/ changed).")
    lines.append("")
    lines.append(f"MAX load per mode (out of {CONTEXT_BUDGET:,} context):")
    for mode in cost["modes"]:
        max_v = cost["max"].get(mode, 0)
        min_v = cost["min"].get(mode, 0)
        pct = 100 * max_v / CONTEXT_BUDGET
        marker = ""
        if max_v >= alert_thr:
            marker = "  🔴 ALERT"
        elif max_v >= warn_thr:
            marker = "  ⚠️ WARN"
        lines.append(f"  {mode:<12} min {min_v:>6,}  max {max_v:>6,}  ({pct:4.1f}%){marker}")

    severity = "alert" if flagged_alert else ("warn" if flagged_warn else "ok")

    if flagged_alert:
        lines.append("")
        lines.append(f"🔴 {len(flagged_alert)} mode(s) exceed {int(ALERT_PCT*100)}% of context budget — consider splitting principles, trimming instructions, or tightening tag filters.")
    elif flagged_warn:
        lines.append("")
        lines.append(f"⚠️ {len(flagged_warn)} mode(s) exceed {int(WARN_PCT*100)}% of context budget. Monitor principle growth.")

    return severity, "\n".join(lines)


def main():
    ok, err = run_regen()
    if not ok:
        payload = {
            "systemMessage": f"❌ Token-doc regeneration failed: {err}",
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": f"Token-doc regeneration failed: {err}",
            },
        }
        print(json.dumps(payload))
        return

    cost = parse_cost_doc()
    severity, message = build_summary(cost)

    # Only surface a user-visible systemMessage when there's something to flag.
    payload = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": message,
        }
    }
    if severity in ("warn", "alert"):
        payload["systemMessage"] = message

    print(json.dumps(payload))


if __name__ == "__main__":
    main()
