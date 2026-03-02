#!/usr/bin/env python3
"""
Generate a self-contained HTML report from validated per-file findings.

Usage:
    python3 generate-report.py <output-root> [template-path]

Input:
    <output-root>/by-file/*.output.json

Output:
    <output-root>/report.html
"""

import json
import os
import re
import sys
from html import escape
from pathlib import Path
from datetime import datetime, timezone


SEVERITY_ORDER = {
    "COMPLIANT": 0, "MINOR": 1, "MODERATE": 2,
    "IMPORTANT": 3, "SEVERE": 4, "CRITICAL": 5,
}


def badge_class(severity):
    s = severity.lower()
    if s == "important":
        return "badge-severe"
    return f"badge-{s}"


def worst_severity(severities):
    if not severities:
        return "COMPLIANT"
    return max(severities, key=lambda s: SEVERITY_ORDER.get(s, 0))


def render_code_blocks(text):
    """Convert markdown code fences to HTML code blocks, with surrounding text as paragraphs."""
    parts = re.split(r"```\w*\n?", text)
    html = []
    for i, part in enumerate(parts):
        content = part.strip()
        if not content:
            continue
        if i % 2 == 1:
            # inside a code fence
            html.append(f'<div class="code-block">{escape(content)}</div>')
        else:
            # text between fences
            for line in content.split("\n\n"):
                line = line.strip()
                if line:
                    html.append(f"<p>{escape(line)}</p>")
    return "\n".join(html)


def render_verification(verification):
    if not verification:
        return ""

    items = []
    orig = verification.get("original_class", {})
    if orig:
        sev = orig.get("expected_severity", "")
        items.append(f'<span class="verification-item">Original &rarr; {escape(sev)}</span>')

    for key in ("extracted_types", "refactored_types"):
        for t in verification.get(key, []):
            name = t.get("name", "")
            sev = t.get("expected_severity", "")
            items.append(f'<span class="verification-item">{escape(name)} &rarr; {escape(sev)}</span>')

    if not items:
        return ""

    return f"""<div class="verification">
      <p class="label">Verification (predicted post-refactoring):</p>
      <div class="verification-row">
        {"".join(items)}
      </div>
    </div>"""


def render_finding(f):
    sev = f.get("severity", "")
    sev_lower = sev.lower()
    card_class = f"severity-{sev_lower}"
    if sev_lower == "important":
        card_class = "severity-important"

    lines_html = ""
    if f.get("line_start") and f.get("line_end"):
        lines_html = f'<p><span class="label">Lines:</span> <span class="line-range">{f["line_start"]}&ndash;{f["line_end"]}</span></p>'

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


def render_suggestion(s):
    sev = s.get("severity", "")
    addresses = " ".join(f'<code>{escape(a)}</code>' for a in s.get("addresses", []))

    pattern_html = ""
    if s.get("pattern"):
        pattern_html = f'<span class="pattern-tag">{escape(s["pattern"])}</span>'

    code_html = render_code_blocks(s.get("suggested_fix", ""))

    todo_html = ""
    todo_items = s.get("todo_items", [])
    if todo_items:
        items = "".join(f"<li>{escape(t)}</li>" for t in todo_items)
        todo_html = f"""<details open>
      <summary>Action Items</summary>
      <ul class="todo-list">
        {items}
      </ul>
    </details>"""

    verification_html = render_verification(s.get("verification"))

    return f"""<div class="fix-card">
      <div class="fix-header">
        <span class="fix-id">{escape(s.get("id", ""))}</span>
        <span class="badge {badge_class(sev)}">{escape(sev)}</span>
        {pattern_html}
        <span class="fix-title">{escape(s.get("title", ""))}</span>
      </div>
      <p class="addresses">Addresses: {addresses}</p>
      <details open>
        <summary>Suggested Fix</summary>
        {code_html}
      </details>
      {todo_html}
      {verification_html}
    </div>"""


def render_principle(p):
    sev = p.get("severity", "COMPLIANT")
    name = p.get("principle", "")

    html = f"""<div class="principle-label">
      {escape(name)}
      <span class="badge {badge_class(sev)}">{escape(sev)}</span>
    </div>
    <h3 class="section-heading">Findings</h3>"""

    findings = p.get("findings", [])
    if not findings:
        html += '\n    <p class="no-findings">No violations found. Code is compliant.</p>'
    else:
        for f in findings:
            html += "\n" + render_finding(f)

    suggestions = p.get("suggestions", [])
    html += '\n    <h3 class="section-heading">Fix Suggestions</h3>'
    if not suggestions:
        html += '\n    <p class="no-findings">No fix suggestions available.</p>'
    else:
        for s in suggestions:
            html += "\n" + render_suggestion(s)

    return html


def main():
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} <output-root> [template-path]", file=sys.stderr)
        sys.exit(1)

    output_root = Path(sys.argv[1])
    script_dir = Path(__file__).parent
    template_path = Path(sys.argv[2]) if len(sys.argv) > 2 else script_dir / "template.html"

    by_file_dir = output_root / "by-file"
    if not by_file_dir.exists():
        print(f"Error: {by_file_dir} not found", file=sys.stderr)
        sys.exit(1)

    # Read template
    with open(template_path, "r") as f:
        template = f.read()

    # Extract CSS from template (everything between <style> and </style>)
    css_match = re.search(r"<style>(.*?)</style>", template, re.DOTALL)
    css = css_match.group(1) if css_match else ""

    # Load all .output.json files
    file_data = []
    for p in sorted(by_file_dir.glob("*.output.json")):
        with open(p, "r") as f:
            file_data.append(json.load(f))

    if not file_data:
        print(f"Error: No .output.json files found in {by_file_dir}", file=sys.stderr)
        sys.exit(1)

    timestamp = file_data[0].get("timestamp", datetime.now(timezone.utc).isoformat())

    # Build summary rows
    summary_rows = []
    for fd in file_data:
        file_path = fd.get("file", "")
        filename = os.path.basename(file_path)
        principles = fd.get("principles", [])

        all_severities = [p.get("severity", "COMPLIANT") for p in principles]
        ws = worst_severity(all_severities)

        total_findings = sum(len(p.get("findings", [])) for p in principles)
        total_suggestions = sum(len(p.get("suggestions", [])) for p in principles)

        summary_rows.append(
            f'<tr>'
            f'<td title="{escape(file_path)}">{escape(filename)}</td>'
            f'<td><span class="badge {badge_class(ws)}">{escape(ws)}</span></td>'
            f'<td>{total_findings}</td>'
            f'<td>{total_suggestions}</td>'
            f'</tr>'
        )

    # Build file sections
    file_sections = []
    for fd in file_data:
        file_path = fd.get("file", "")
        filename = os.path.basename(file_path)
        principles = fd.get("principles", [])

        all_severities = [p.get("severity", "COMPLIANT") for p in principles]
        ws = worst_severity(all_severities)

        principles_html = ""
        for p in principles:
            principles_html += render_principle(p)

        file_sections.append(
            f'<section class="file-section">'
            f'<div class="file-header">'
            f'<h2 title="{escape(file_path)}">{escape(filename)}</h2>'
            f'<span class="badge {badge_class(ws)}">{escape(ws)}</span>'
            f'</div>'
            f'{principles_html}'
            f'</section>'
        )

    # Assemble final HTML
    html = f"""<!DOCTYPE html>
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
        <tr>
          <th>File</th>
          <th>Severity</th>
          <th>Findings</th>
          <th>Suggestions</th>
        </tr>
      </thead>
      <tbody>
        {"".join(summary_rows)}
      </tbody>
    </table>
  </section>

  {"".join(file_sections)}

</body>
</html>"""

    report_path = output_root / "report.html"
    with open(report_path, "w") as f:
        f.write(html)

    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
