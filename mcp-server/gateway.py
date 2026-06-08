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
    python3 gateway.py split_implementation_plan --plan-path /p/plan.json --output-dir /p/chunks/ [--arch-path /p/arch.json]
    python3 gateway.py search_codebase --sources-dir /path/to/Sources --synonyms json,line,stream --min-matches 3
    python3 gateway.py search_codebase --sources-dir /path/to/Sources --spec-numbers SPEC-026,SPEC-033
    python3 gateway.py query_specs --action scan --args type=feature status=ready
    python3 gateway.py load_fix_for_violation --metric_id OCP-1
    python3 gateway.py load_fix_instructions_for_findings --findings_path /path/to/by-file/Foo.swift.output.json
    python3 gateway.py load_detection_rules
    python3 gateway.py load_detection_rules --matched_tags unit-test,swiftui
    python3 gateway.py load_detection_rules --principle SRP
    python3 gateway.py get_output_path --operation review
    python3 gateway.py get_output_path --operation implement --spec_number SPEC-042

Exit codes:
    0 — success (JSON on stdout)
    1 — error (error message on stderr)
"""

import inspect
import json
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

GATEWAY_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = GATEWAY_DIR.parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"

sys.path.insert(0, str(GATEWAY_DIR))

# Documentation tools — mcp-server/docs/server.py
from docs.server import (  # noqa: E402
    get_candidate_tags,
    discover_principles_tool,
    load_rules,
    load_fix_instructions_for_findings,
    load_fix_for_violation,
    load_detection_rules,
)

# Pipeline tools — constructed via factory for gateway CLI access
from pipeline.server import get_pipeline_tools as _get_pipeline_tools, get_output_path  # noqa: E402
_pt = _get_pipeline_tools()
check_severity = _pt['check_severity']
load_synthesis_context = _pt['load_synthesis_context']
validate_phase_output = _pt['validate_phase_output']
validate_findings = _pt['validate_findings']
generate_report = _pt['generate_report']
validate_architecture = _pt['validate_architecture']
split_implementation_plan = _pt['split_implementation_plan']
search_codebase = _pt['search_codebase']
prepare_review_input = _pt['prepare_review_input']

# Spec tools — mcp-server/specs/server.py
from specs.server import query_specs  # noqa: E402


def parse_args(argv: list) -> tuple:
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
                if "," in value:
                    value = [v.strip() for v in value.split(",")]
                kwargs[key] = value
                i += 2
            else:
                kwargs[key] = True
                i += 1
        else:
            kwargs.setdefault("args", []).append(arg)
            i += 1
    return tool, kwargs


def load_spec_ancestors(**kwargs) -> str:
    """Load ancestor and blocked-by spec content as readable text."""
    spec_number = kwargs.get("spec")
    blocked = kwargs.get("blocked", False)
    if not spec_number:
        print("Error: --spec is required", file=sys.stderr)
        sys.exit(1)

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
    lines = [sep, f"  SPEC CONTEXT: {spec_number} ({len(specs)} specs in chain)", sep]
    sub = "-" * 40
    for s in specs:
        lines.append(f"\n{s.get('number', '?')} — {s.get('feature', '?')}")
        lines.append(f"Status: {s.get('status', '?')}")
        if s.get("content"):
            lines.append(sub)
            lines.append(s["content"].strip())
    lines.extend([sep, "  END OF SPEC CONTEXT", sep])
    return "\n".join(lines)


TOOLS = {
    "get_candidate_tags": get_candidate_tags,
    "discover_principles": discover_principles_tool,
    "load_rules": load_rules,
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
    "load_fix_instructions_for_findings": load_fix_instructions_for_findings,
    "load_fix_for_violation": load_fix_for_violation,
    "load_detection_rules": load_detection_rules,
    "get_output_path": get_output_path,
}


class ArgumentValidator:
    """Validates kwargs against a callable's signature. Rejects unknown flags loudly."""

    def validate(self, handler: Callable, tool_name: str, kwargs: dict) -> None:
        """Raise SystemExit(1) if kwargs contains flags the handler does not accept."""
        try:
            sig = inspect.signature(handler)
            params = sig.parameters.values()
            if any(p.kind == inspect.Parameter.VAR_KEYWORD for p in params):
                return  # handler accepts **kwargs — everything is valid
            accepted = {p.name for p in params
                        if p.kind in (inspect.Parameter.POSITIONAL_OR_KEYWORD,
                                      inspect.Parameter.KEYWORD_ONLY)}
            unknown = set(kwargs) - accepted
            if unknown:
                valid = ", ".join(sorted(accepted)) or "(none)"
                bad = ", ".join(sorted(unknown))
                print(f"Error: unknown argument(s) for '{tool_name}': {bad}", file=sys.stderr)
                print(f"  Valid arguments: {valid}", file=sys.stderr)
                sys.exit(1)
        except (ValueError, TypeError):
            pass  # signature inspection failed — fall through to runtime check


class ToolRunner:
    """Executes a resolved tool callable and writes structured output to stdout."""

    def run(self, handler: Callable, tool_name: str, kwargs: dict) -> None:
        try:
            result = handler(**kwargs)
            if isinstance(result, dict) and result.get("errors"):
                for e in result["errors"]:
                    print(f"Error: {e.get('error', 'unknown error')}", file=sys.stderr)
                sys.exit(1)
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


def main(
    validator: Optional[ArgumentValidator] = None,
    runner: Optional[ToolRunner] = None,
) -> None:
    """Coordination facade: parse → validate → run."""
    validator = validator or ArgumentValidator()
    runner = runner or ToolRunner()

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

    validator.validate(handler, tool_name, kwargs)
    runner.run(handler, tool_name, kwargs)


if __name__ == "__main__":
    main()
