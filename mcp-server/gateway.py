#!/usr/bin/env python3
"""solid-coder CLI gateway — exposes pipeline tools as one-shot commands.

Same tools as the MCP server, but called via bash. One call per operation,
structured JSON output to stdout.

Usage:
    python3 gateway.py <tool-name> [--arg value ...]

Examples:
    python3 gateway.py get_candidate_tags
    python3 gateway.py discover_principles
    python3 gateway.py discover_principles --matched-tags swiftui,testing
    python3 gateway.py load_rules --mode review --principle srp
    python3 gateway.py load_rules --mode code --matched-tags swiftui,testing
    python3 gateway.py load_rules --mode planner
    python3 gateway.py load_rules --mode synth-impl
    python3 gateway.py load_rules --mode synth-fixes --principle srp
    python3 gateway.py load_rules --mode planner --output-format hook-json
    python3 gateway.py check_severity --output-root /path/to/output
    python3 gateway.py load_synthesis_context --output-root /path/to/output
    python3 gateway.py validate_phase_output --json-path /p/file.json --schema-path /p/schema.json
    python3 gateway.py validate_findings --output-root /path/to/output
    python3 gateway.py generate_report --data-dir /path/to/iteration --report-dir /path/to/output
    python3 gateway.py validate_architecture --arch-path /path/to/arch.json
    python3 gateway.py split_implementation_plan --plan-path /p/plan.json --output-dir /p/chunks/
    python3 gateway.py search_codebase --sources-dir /path/to/Sources
    python3 gateway.py query_specs --action scan --args type=feature status=ready

Exit codes:
    0 — success (JSON on stdout)
    1 — error (error message on stderr)
"""

import json
import subprocess
import sys
from pathlib import Path

# Import the server module (same directory)
from server import SKILLS_ROOT
from server import (
    get_candidate_tags,
    discover_principles_tool,
    load_rules,
    check_severity,
    load_synthesis_context,
    validate_phase_output,
    validate_findings,
    generate_report,
    validate_architecture,
    split_implementation_plan,
    search_codebase,
    query_specs,
    prepare_review_input,
)


def parse_args(argv):
    """Parse CLI args into tool name + keyword arguments."""
    if len(argv) < 2:
        return None, {}

    tool = argv[1]
    kwargs = {}
    i = 2
    while i < len(argv):
        arg = argv[i]
        if arg.startswith("--"):
            key = arg[2:].replace("-", "_")
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                value = argv[i + 1]
                # Parse comma-separated lists
                if "," in value:
                    value = [v.strip() for v in value.split(",")]
                kwargs[key] = value
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            # Positional args collected in 'args' list
            kwargs.setdefault("args", []).append(arg)
            i += 1
    return tool, kwargs


def _format_md(result):
    """Format load_rules result as readable markdown/text sections."""
    sep = "=" * 72
    sub = "-" * 40
    lines = []
    total = len(result["active_principles"])
    lines.append(f"{sep}")
    lines.append(f"  ACTIVE PRINCIPLES ({total}): {', '.join(p.upper() for p in result['active_principles'])}")
    lines.append(f"{sep}\n")

    for idx, name in enumerate(result["active_principles"], 1):
        r = result["rules"].get(name, {})
        lines.append(f"{sep}")
        lines.append(f"  [{idx}/{total}] {name.upper()}")
        lines.append(f"{sep}")

        if r.get("rule"):
            lines.append(f"\n{sub}")
            lines.append(f"  RULE — {name.upper()}")
            lines.append(f"{sub}\n")
            lines.append(r["rule"].strip())

        if r.get("instructions"):
            lines.append(f"\n{sub}")
            lines.append(f"  INSTRUCTIONS — {name.upper()}")
            lines.append(f"{sub}\n")
            lines.append(r["instructions"].strip())

        if r.get("code_rules"):
            lines.append(f"\n{sub}")
            lines.append(f"  CODE RULES — {name.upper()}")
            lines.append(f"{sub}\n")
            lines.append(r["code_rules"].strip())

        if r.get("examples"):
            lines.append(f"\n{sub}")
            lines.append(f"  EXAMPLES — {name.upper()} ({len(r['examples'])} files)")
            lines.append(f"{sub}\n")
            for i, ex in enumerate(r["examples"], 1):
                lines.append(f"--- Example {i} ---\n")
                lines.append(ex.strip())
                lines.append("")

        if r.get("patterns"):
            lines.append(f"\n{sub}")
            lines.append(f"  DESIGN PATTERNS — {name.upper()}")
            lines.append(f"{sub}\n")
            for p in r["patterns"]:
                lines.append(p.strip())
                lines.append("")

        lines.append("")

    lines.append(f"{sep}")
    lines.append(f"  END OF RULES")
    lines.append(f"{sep}")

    return "\n".join(lines)


def _format_hook_json(result):
    """Format load_rules result as a SubagentStart hook response.

    Wraps the md output in the JSON shape the Claude Code harness expects
    to inject content into a spawned subagent's context:

        {"hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": "<rules>"
        }}
    """
    md = _format_md(result)
    response = {
        "hookSpecificOutput": {
            "hookEventName": "SubagentStart",
            "additionalContext": md,
        }
    }
    return json.dumps(response)


OUTPUT_FORMATTERS = {
    "md": _format_md,
    "hook-json": _format_hook_json,
}


def load_rules_text(profile=None, principle=None, matched_tags=None,
                    exclude=None, mode=None, output_format="md"):
    """Load rules and dispatch to the chosen output formatter.

    output_format:
      - "md"        (default) — readable text sections, for CLI/human reads
      - "hook-json" — SubagentStart hook response JSON for context injection
    """
    if output_format not in OUTPUT_FORMATTERS:
        valid = ", ".join(sorted(OUTPUT_FORMATTERS.keys()))
        print(f"Error: invalid --output-format '{output_format}'. Valid: {valid}",
              file=sys.stderr)
        sys.exit(1)

    result = load_rules(profile=profile, principle=principle,
                        matched_tags=matched_tags, exclude=exclude, mode=mode)

    if result.get("errors"):
        import json as _json
        print(_json.dumps({"errors": result["errors"]}), file=sys.stderr)
        sys.exit(1)

    if not result.get("active_principles"):
        print("No active principles found.", file=sys.stderr)
        sys.exit(1)

    return OUTPUT_FORMATTERS[output_format](result)


def load_spec_ancestors(**kwargs):
    """Load ancestor and blocked-by spec content as readable text."""
    spec_number = kwargs.get("spec")
    blocked = kwargs.get("blocked", False)
    if not spec_number:
        print("Error: --spec is required", file=sys.stderr)
        sys.exit(1)

    # Run find-spec-query.py ancestors
    script = str(SKILLS_ROOT / "find-spec" / "scripts" / "find-spec-query.py")
    cmd = [sys.executable, script, "ancestors", spec_number]
    if blocked:
        cmd.append("--blocked")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(1)

    specs = json.loads(result.stdout)
    if not specs:
        return "No ancestors found."

    sep = "=" * 72
    sub = "-" * 40
    lines = []
    lines.append(sep)
    lines.append(f"  SPEC CONTEXT: {spec_number} ({len(specs)} specs in chain)")
    lines.append(sep)

    for s in specs:
        number = s.get("number", "?")
        feature = s.get("feature", "")
        status = s.get("status", "")
        path = s.get("path", "")

        lines.append(f"\n{sub}")
        lines.append(f"  {number} — {feature} [{status}]")
        lines.append(f"{sub}\n")

        if path:
            try:
                content = Path(path).read_text(encoding="utf-8")
                lines.append(content.strip())
            except Exception as e:
                lines.append(f"(Could not read: {e})")

        lines.append("")

    lines.append(sep)
    lines.append(f"  END OF SPEC CONTEXT")
    lines.append(sep)

    return "\n".join(lines)


TOOLS = {
    "get_candidate_tags": get_candidate_tags,
    "discover_principles": discover_principles_tool,
    "load_rules": load_rules_text,
    "check_severity": check_severity,
    "load_synthesis_context": load_synthesis_context,
    "validate_phase_output": validate_phase_output,
    "validate_findings": validate_findings,
    "generate_report": generate_report,
    "validate_architecture": validate_architecture,
    "split_implementation_plan": split_implementation_plan,
    "search_codebase": search_codebase,
    "query_specs": query_specs,
    "load_spec_context": load_spec_ancestors,
    "prepare_review_input": prepare_review_input,
}


def main():
    tool_name, kwargs = parse_args(sys.argv)

    if tool_name is None or tool_name in ("-h", "--help", "help"):
        print("Usage: python3 gateway.py <tool-name> [--arg value ...]", file=sys.stderr)
        print(f"\nAvailable tools: {', '.join(sorted(TOOLS.keys()))}", file=sys.stderr)
        sys.exit(1 if tool_name is None else 0)

    handler = TOOLS.get(tool_name)
    if not handler:
        print(f"Error: unknown tool '{tool_name}'", file=sys.stderr)
        print(f"Available: {', '.join(sorted(TOOLS.keys()))}", file=sys.stderr)
        sys.exit(1)

    # Validate kwargs against the handler's signature — reject unknown flags loudly.
    import inspect
    try:
        sig = inspect.signature(handler)
        accepted = {p.name for p in sig.parameters.values()
                    if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                  inspect.Parameter.KEYWORD_ONLY)}
        # Allow VAR_KEYWORD handlers to accept anything
        if not any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()):
            unknown = set(kwargs) - accepted
            if unknown:
                valid = ", ".join(sorted(accepted)) or "(none)"
                bad = ", ".join(sorted(unknown))
                print(f"Error: unknown argument(s) for '{tool_name}': {bad}", file=sys.stderr)
                print(f"  Valid arguments: {valid}", file=sys.stderr)
                sys.exit(1)
    except (ValueError, TypeError):
        pass  # signature inspection failed — fall through to runtime check

    try:
        result = handler(**kwargs)
        if isinstance(result, str):
            print(result)
        else:
            json.dump(result, sys.stdout, indent=2, ensure_ascii=False)
            print()
    except TypeError as e:
        print(f"Error: bad arguments for '{tool_name}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
