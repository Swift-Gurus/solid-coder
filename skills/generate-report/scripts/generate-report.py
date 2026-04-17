#!/usr/bin/env python3
"""
Generate MD + HTML reports from validated per-file findings and synthesized fix plans.

Usage:
    python3 generate-report.py <root> [<report-dir>] [--template <path>]

Arguments:
    <root>        Refactor/review root. Aggregates data across ALL iteration
                  subdirectories (1/, 2/, ...). Also accepts a single-iteration
                  directory (with `by-file/` at its root) for backward compat.
    <report-dir>  Where report.md and report.html are written. Defaults to <root>.

Input:
    <root>/<N>/by-file/*.output.json       (per-iteration validated findings)
    <root>/<N>/synthesized/*.plan.json     (optional per-iteration fix plans)

Output:
    <report-dir>/report.md
    <report-dir>/report.html

Deduplication:
    Findings are keyed by (file_path, principle, finding_id) — later iterations
    overwrite earlier ones (later state is the residual state after fixes).
    Actions are keyed by (file_path, suggestion_id) — union across iterations.
"""

import json
import os
import re
import sys
from html import escape
from pathlib import Path
from datetime import datetime, timezone


SEVERITY_ORDER = {"COMPLIANT": 0, "MINOR": 1, "SEVERE": 2}


def load_json(path):
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error parsing {path}: {e}", file=sys.stderr)
        sys.exit(1)


def badge_class(severity):
    return f"badge-{severity.lower()}"


def worst_severity(severities):
    if not severities:
        return "COMPLIANT"
    return max(severities, key=lambda s: SEVERITY_ORDER.get(s, 0))


def plan_key(file_path):
    return os.path.basename(file_path)


def iteration_dirs(root):
    """Return ordered list of iteration subdirs (numeric names). Fallback: root itself."""
    if not root.is_dir():
        return []
    numeric = sorted(
        (p for p in root.iterdir() if p.is_dir() and p.name.isdigit()),
        key=lambda p: int(p.name),
    )
    if numeric:
        return numeric
    # Backward compat: single-iteration layout (by-file/ directly under root)
    if (root / "by-file").exists():
        return [root]
    return []


def aggregate_data(root):
    """Aggregate findings + plans across all iteration subdirs of root.

    Returns:
        file_data: list of per-file dicts (dedup by file_path, merged principles/findings)
        plans:     dict[basename(file_path)] -> merged plan dict
        timestamp: ISO timestamp (latest seen)
    """
    iter_dirs = iteration_dirs(root)
    if not iter_dirs:
        return [], {}, None

    # (file_path, principle) -> principle_entry with dedup'd findings
    principle_entries = {}
    file_order = []   # preserve first-seen order
    latest_timestamp = None

    for it_dir in iter_dirs:
        by_file_dir = it_dir / "by-file"
        if not by_file_dir.exists():
            continue
        for p in sorted(by_file_dir.glob("*.output.json")):
            fd = load_json(p)
            fp = fd.get("file_path", "")
            if not fp:
                continue
            ts = fd.get("timestamp")
            if ts and (latest_timestamp is None or ts > latest_timestamp):
                latest_timestamp = ts
            if fp not in file_order:
                file_order.append(fp)
            for pr in fd.get("principles", []):
                key = (fp, pr.get("principle", ""))
                existing = principle_entries.get(key)
                if existing is None:
                    principle_entries[key] = {
                        **pr,
                        "findings": {f["id"]: f for f in pr.get("findings", []) if f.get("id")},
                    }
                else:
                    existing["severity"] = pr.get("severity", existing.get("severity"))
                    for f in pr.get("findings", []):
                        if f.get("id"):
                            existing["findings"][f["id"]] = f

    # Flatten into file_data list
    file_data = []
    for fp in file_order:
        principles = []
        for (fp_key, _), entry in principle_entries.items():
            if fp_key != fp:
                continue
            flat = {**entry, "findings": list(entry["findings"].values())}
            principles.append(flat)
        file_data.append({
            "file_path": fp,
            "timestamp": latest_timestamp or datetime.now(timezone.utc).isoformat(),
            "principles": principles,
        })

    # Aggregate plans: dedup actions by suggestion_id, merge unresolved + conflicts
    plans_by_file = {}
    for it_dir in iter_dirs:
        synth_dir = it_dir / "synthesized"
        if not synth_dir.exists():
            continue
        for p in sorted(synth_dir.glob("*.plan.json")):
            plan = load_json(p)
            fp = plan.get("file_path", "")
            if not fp:
                continue
            key = plan_key(fp)
            merged = plans_by_file.setdefault(key, {
                "file_path": fp,
                "actions": {},     # keyed by suggestion_id
                "unresolved": {},  # keyed by finding_id
                "conflicts_detected": [],
            })
            for a in plan.get("actions", []):
                sid = a.get("suggestion_id")
                if sid:
                    merged["actions"][sid] = a  # later iteration overwrites
            for u in plan.get("unresolved", []):
                fid = u.get("finding_id")
                if fid:
                    merged["unresolved"][fid] = u
            merged["conflicts_detected"].extend(plan.get("conflicts_detected", []))

    # Flatten plans
    plans = {}
    for key, merged in plans_by_file.items():
        plans[key] = {
            "file_path": merged["file_path"],
            "actions": list(merged["actions"].values()),
            "unresolved": list(merged["unresolved"].values()),
            "conflicts_detected": merged["conflicts_detected"],
        }

    return file_data, plans, latest_timestamp


# ────────────────────────────── Markdown ──────────────────────────────


def md_finding(f):
    sev = f.get("severity", "")
    lines = []
    lines.append(f"- **`{f.get('id','')}`** · **{sev}** · _{f.get('metric','')}_ — {f.get('title','')}")
    if f.get("issue"):
        lines.append(f"  - Issue: {f['issue']}")
    if f.get("impact"):
        lines.append(f"  - Impact: {f['impact']}")
    if f.get("line_start") and f.get("line_end"):
        lines.append(f"  - Lines: {f['line_start']}–{f['line_end']}")
    return "\n".join(lines)


def md_action(a):
    lines = []
    resolves = ", ".join(f"`{r}`" for r in a.get("resolves", []))
    lines.append(f"#### `{a.get('suggestion_id','')}` · {a.get('principle','')} — resolves {resolves or '_(none)_'}")
    if a.get("note"):
        lines.append(f"\n> {a['note']}")
    todos = a.get("todo_items", [])
    if todos:
        lines.append("\n**Steps:**")
        for t in todos:
            lines.append(f"- [ ] {t}")
    fix = a.get("suggested_fix", "").strip()
    if fix:
        lines.append("\n**Suggested fix:**\n")
        lines.append(fix if "```" in fix else f"```swift\n{fix}\n```")
    depends = a.get("depends_on", [])
    if depends:
        lines.append(f"\n_Depends on: {', '.join(f'`{d}`' for d in depends)}_")
    checks = a.get("cross_check_results", [])
    if checks:
        check_line = ", ".join(
            f"{c.get('principle','')}={'✓' if c.get('passed') else '✗'}" for c in checks
        )
        lines.append(f"\n_Cross-checks: {check_line}_")
    return "\n".join(lines)


def md_file_section(fd, plan):
    file_path = fd.get("file_path", "")
    filename = os.path.basename(file_path)
    principles = fd.get("principles", [])
    ws = worst_severity([p.get("severity", "COMPLIANT") for p in principles])

    out = [f"## {filename}  \n**Severity: {ws}**  \n`{file_path}`\n"]

    for p in principles:
        out.append(f"### {p.get('principle','')} — {p.get('severity','')}")
        findings = p.get("findings", [])
        if not findings:
            out.append("_No violations._\n")
        else:
            for f in findings:
                out.append(md_finding(f))
            out.append("")

    if plan:
        actions = plan.get("actions", [])
        if actions:
            out.append("### Synthesized Fix Plan\n")
            for a in actions:
                out.append(md_action(a))
                out.append("")
        unresolved = plan.get("unresolved", [])
        if unresolved:
            out.append("### Unresolved\n")
            for u in unresolved:
                out.append(f"- `{u.get('finding_id','')}` — {u.get('reason','')}")
            out.append("")
        conflicts = plan.get("conflicts_detected", [])
        if conflicts:
            out.append("### Conflicts Detected\n")
            for c in conflicts:
                claimed = ", ".join(c.get("claimed_by", []))
                out.append(f"- `{c.get('finding','')}` claimed by {claimed} → {c.get('resolution','')}")
            out.append("")

    return "\n".join(out)


def render_markdown(file_data, plans, output_root, timestamp):
    lines = [
        "# SOLID Code Review Report",
        "",
        f"**Generated:** {timestamp}  ",
        f"**Source:** `{output_root}`",
        "",
        "## Summary",
        "",
        "| File | Severity | Findings | Planned Actions |",
        "|------|----------|----------|-----------------|",
    ]
    for fd in file_data:
        file_path = fd.get("file_path", "")
        filename = os.path.basename(file_path)
        principles = fd.get("principles", [])
        ws = worst_severity([p.get("severity", "COMPLIANT") for p in principles])
        total_findings = sum(len(p.get("findings", [])) for p in principles)
        plan = plans.get(plan_key(file_path))
        total_actions = len(plan.get("actions", [])) if plan else 0
        lines.append(f"| `{filename}` | **{ws}** | {total_findings} | {total_actions} |")

    lines.append("")
    for fd in file_data:
        plan = plans.get(plan_key(fd.get("file_path", "")))
        lines.append(md_file_section(fd, plan))

    return "\n".join(lines) + "\n"


# ──────────────────────────────── HTML ────────────────────────────────


CODE_MARKER_RE = re.compile(
    r"(?:\b(?:func|class|struct|protocol|enum|extension|import|let|var|guard|return|async|await)\b|[{};]|@\w+|^\s{2,})",
    re.MULTILINE,
)


def _looks_like_code(block: str) -> bool:
    """Heuristic: block looks like source code rather than prose."""
    if not block.strip():
        return False
    return bool(CODE_MARKER_RE.search(block))


def render_code_blocks(text):
    """Render text with optional ``` fences as HTML.

    - Fenced blocks → <pre class="code-block"><code>…</code></pre>, indentation preserved.
    - Unfenced content → split on blank lines; paragraphs that look like source code
      are rendered as code blocks (preserving whitespace), prose paragraphs become <p>
      with single newlines preserved as <br>.
    """
    parts = re.split(r"```[^\n]*\n?", text)
    html = []
    for i, part in enumerate(parts):
        if i % 2 == 1:
            code = part.strip("\n")
            if not code:
                continue
            html.append(f'<pre class="code-block"><code>{escape(code)}</code></pre>')
            continue

        # Unfenced chunk — split on blank lines; classify each paragraph
        trimmed = part.strip("\n")
        if not trimmed.strip():
            continue
        for paragraph in re.split(r"\n\s*\n", trimmed):
            body = paragraph.strip("\n")
            if not body.strip():
                continue
            if _looks_like_code(body):
                html.append(f'<pre class="code-block"><code>{escape(body)}</code></pre>')
            else:
                lines = [escape(ln) for ln in body.split("\n")]
                html.append(f"<p>{'<br>'.join(lines)}</p>")
    return "\n".join(html)


def render_finding(f):
    sev = f.get("severity", "")
    card_class = f"severity-{sev.lower()}"
    lines_html = ""
    if f.get("line_start") and f.get("line_end"):
        lines_html = (
            f'<p><span class="label">Lines:</span> '
            f'<span class="line-range">{f["line_start"]}&ndash;{f["line_end"]}</span></p>'
        )
    impact_html = ""
    if f.get("impact"):
        impact_html = f'<p><span class="label">Impact:</span> {escape(f["impact"])}</p>'
    return f"""<div class="finding-card {card_class}">
      <div class="finding-header">
        <span class="finding-id">{escape(f.get("id", ""))}</span>
        <span class="badge {badge_class(sev)}">{escape(sev)}</span>
        <span class="metric-tag">{escape(f.get("metric", ""))}</span>
        <span class="finding-title">{escape(f.get("title", ""))}</span>
      </div>
      <div class="finding-body">
        <p><span class="label">Issue:</span> {escape(f.get("issue", ""))}</p>
        {impact_html}
        {lines_html}
      </div>
    </div>"""


def render_action(a):
    resolves = " ".join(f'<code>{escape(r)}</code>' for r in a.get("resolves", []))
    code_html = render_code_blocks(a.get("suggested_fix", ""))
    todos = a.get("todo_items", [])
    todo_html = ""
    if todos:
        items = "".join(f"<li>{escape(t)}</li>" for t in todos)
        todo_html = f"<details open><summary>Steps</summary><ul class=\"todo-list\">{items}</ul></details>"
    note_html = ""
    if a.get("note"):
        note_html = f'<p class="addresses">{escape(a["note"])}</p>'
    checks = a.get("cross_check_results", [])
    checks_html = ""
    if checks:
        items = "".join(
            f'<span class="verification-item">{escape(c.get("principle",""))} '
            f'&rarr; {"✓" if c.get("passed") else "✗"}</span>'
            for c in checks
        )
        checks_html = (
            '<div class="verification"><p class="label">Cross-checks:</p>'
            f'<div class="verification-row">{items}</div></div>'
        )
    return f"""<div class="fix-card">
      <div class="fix-header">
        <span class="fix-id">{escape(a.get("suggestion_id", ""))}</span>
        <span class="pattern-tag">{escape(a.get("principle", ""))}</span>
        <span class="fix-title">Resolves: {resolves or '<em>(none)</em>'}</span>
      </div>
      {note_html}
      <details open><summary>Suggested Fix</summary>{code_html}</details>
      {todo_html}
      {checks_html}
    </div>"""


def render_principle(p):
    sev = p.get("severity", "COMPLIANT")
    name = p.get("principle", "")
    html = f"""<div class="principle-label">
      {escape(name)}
      <span class="badge {badge_class(sev)}">{escape(sev)}</span>
    </div>"""
    findings = p.get("findings", [])
    html += '<h3 class="section-heading">Findings</h3>'
    if not findings:
        html += '<p class="no-findings">No violations found.</p>'
    else:
        for f in findings:
            html += render_finding(f)
    return html


def render_file_section(fd, plan):
    file_path = fd.get("file_path", "")
    filename = os.path.basename(file_path)
    principles = fd.get("principles", [])
    ws = worst_severity([p.get("severity", "COMPLIANT") for p in principles])

    principles_html = "".join(render_principle(p) for p in principles)

    plan_html = ""
    if plan and plan.get("actions"):
        actions_html = "".join(render_action(a) for a in plan["actions"])
        plan_html = (
            '<h3 class="section-heading">Synthesized Fix Plan</h3>' + actions_html
        )
        unresolved = plan.get("unresolved", [])
        if unresolved:
            items = "".join(
                f'<li><code>{escape(u.get("finding_id",""))}</code> — {escape(u.get("reason",""))}</li>'
                for u in unresolved
            )
            plan_html += f'<h3 class="section-heading">Unresolved</h3><ul class="todo-list">{items}</ul>'

    return f"""<section class="file-section">
      <div class="file-header">
        <h2 title="{escape(file_path)}">{escape(filename)}</h2>
        <span class="badge {badge_class(ws)}">{escape(ws)}</span>
      </div>
      {principles_html}
      {plan_html}
    </section>"""


def render_html(file_data, plans, output_root, timestamp, css):
    summary_rows = []
    for fd in file_data:
        file_path = fd.get("file_path", "")
        filename = os.path.basename(file_path)
        principles = fd.get("principles", [])
        ws = worst_severity([p.get("severity", "COMPLIANT") for p in principles])
        total_findings = sum(len(p.get("findings", [])) for p in principles)
        plan = plans.get(plan_key(file_path))
        total_actions = len(plan.get("actions", [])) if plan else 0
        summary_rows.append(
            f'<tr><td title="{escape(file_path)}">{escape(filename)}</td>'
            f'<td><span class="badge {badge_class(ws)}">{escape(ws)}</span></td>'
            f'<td>{total_findings}</td><td>{total_actions}</td></tr>'
        )

    file_sections = "".join(
        render_file_section(fd, plans.get(plan_key(fd.get("file_path", ""))))
        for fd in file_data
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>SOLID Code Review Report</title>
  <style>{css}</style>
</head>
<body>
  <header>
    <h1>SOLID Code Review Report</h1>
    <p class="meta">Generated: {escape(timestamp)} &bull; Source: {escape(str(output_root))}</p>
  </header>
  <section id="summary">
    <table class="summary-table">
      <thead>
        <tr><th>File</th><th>Severity</th><th>Findings</th><th>Planned Actions</th></tr>
      </thead>
      <tbody>{"".join(summary_rows)}</tbody>
    </table>
  </section>
  {file_sections}
</body>
</html>"""


# ──────────────────────────────── main ────────────────────────────────


def main():
    args = sys.argv[1:]
    template_override = None
    if "--template" in args:
        idx = args.index("--template")
        template_override = Path(args[idx + 1])
        del args[idx : idx + 2]

    if len(args) < 1:
        print(f"Usage: {sys.argv[0]} <root> [<report-dir>] [--template <path>]", file=sys.stderr)
        sys.exit(1)

    root = Path(args[0])
    report_dir = Path(args[1]) if len(args) > 1 else root

    script_dir = Path(__file__).parent
    template_path = template_override or (script_dir / "template.html")

    with open(template_path, "r") as f:
        template = f.read()
    css_match = re.search(r"<style>(.*?)</style>", template, re.DOTALL)
    css = css_match.group(1) if css_match else ""

    file_data, plans, aggregated_ts = aggregate_data(root)
    if not file_data:
        print(f"Error: no iteration data found under {root}", file=sys.stderr)
        sys.exit(1)

    timestamp = aggregated_ts or datetime.now(timezone.utc).isoformat()

    md = render_markdown(file_data, plans, report_dir, timestamp)
    html = render_html(file_data, plans, report_dir, timestamp, css)

    report_dir.mkdir(parents=True, exist_ok=True)
    md_path = report_dir / "report.md"
    html_path = report_dir / "report.html"
    md_path.write_text(md)
    html_path.write_text(html)

    print(f"Markdown: {md_path}")
    print(f"HTML: {html_path}")


if __name__ == "__main__":
    main()
