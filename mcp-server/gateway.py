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
    python3 gateway.py search_codebase --sources-dir /path/to/Sources --synonyms json,line,stream --min-matches 3
    python3 gateway.py search_codebase --sources-dir /path/to/Sources --spec-numbers SPEC-026,SPEC-033
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
    build_pattern_index,
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


# -----------------------------------------------------------------------------
# preload_instruction — SubagentStart hook body
# -----------------------------------------------------------------------------
#
# Reads the SubagentStart hook JSON from stdin, infers mode + principles from
# the subagent_type and prompt, calls load_rules to get the file paths, and
# returns the hook response JSON instructing the subagent to read those files.

SUBAGENT_TYPE_TO_MODE = {
    "solid-coder:apply-principle-review-agent": "review",
    "solid-coder:code-agent": "code",
    "solid-coder:plan-agent": "planner",
    "solid-coder:synthesize-fixes-agent": "synth-fixes",
    "solid-coder:synthesize-implementation-agent": "synth-impl",
}

MODE_INSTRUCTION_TEMPLATES = {
    "review": (
        "Before starting the review, read the following file(s). They contain "
        "the full rule, detection instructions, examples, and patterns for "
        "the principle you are reviewing. You MUST apply them verbatim. Do "
        "NOT call load_rules — the rules are already resolved for you."
    ),
    "code": (
        "Before writing or modifying any code, read the following file(s). "
        "They contain the active SOLID rules and code-writing constraints "
        "you MUST satisfy."
    ),
    "planner": (
        "Before producing the architecture plan, read the following file(s). "
        "They contain the rules the plan MUST respect."
    ),
    "synth-fixes": (
        "Before synthesizing fixes, read the following file(s). They contain "
        "the rules and fix patterns you MUST cross-check every action against."
    ),
    "synth-impl": (
        "Before synthesizing the implementation plan, read the following "
        "file(s). They contain the rules the plan MUST respect."
    ),
}


def _parse_principle_from_prompt(prompt):
    """Extract `principle: NAME` from an agent prompt (case-insensitive)."""
    if not prompt:
        return None
    import re
    m = re.search(r"(?im)^\s*principle\s*:\s*([A-Za-z0-9_\-]+)\s*$", prompt)
    return m.group(1).strip() if m else None


def _read_agent_prompt(transcript_path, agent_id, retries=120, delay=0.5):
    """Read the agent's initial prompt from its JSONL file.

    Derives the subagent JSONL path from the parent transcript path and agent_id,
    reads the first user message, and returns its text content.

    Retries with a short delay because parallel agents are spawned simultaneously —
    CC fires SubagentStart before the JSONL file is written for all of them.
    Only retries if the subagents/ directory exists — if no such directory, returns
    immediately to avoid long waits for fake/test paths.
    """
    import time
    if not transcript_path or not agent_id:
        return ""
    p = Path(transcript_path)
    subagent_dir = p.parent / p.stem / "subagents"
    jsonl = subagent_dir / f"agent-{agent_id}.jsonl"
    for attempt in range(retries):
        try:
            if jsonl.is_file():
                first_line = jsonl.read_text(encoding="utf-8").splitlines()[0]
                entry = json.loads(first_line)
                content = entry.get("message", {}).get("content", "")
                if isinstance(content, str) and content.strip():
                    return content
                if isinstance(content, list):
                    text = " ".join(
                        item.get("text", "") for item in content if isinstance(item, dict)
                    )
                    if text.strip():
                        return text
            elif attempt == 0 and not p.parent.exists():
                # Parent session directory doesn't exist — truly invalid path, don't wait
                return ""
        except Exception:
            pass
        time.sleep(delay)
    return ""


def _parse_matched_tags_from_prompt(prompt):
    """Extract `matched-tags: a,b,c` from an agent prompt (case-insensitive)."""
    if not prompt:
        return None
    import re
    m = re.search(r"(?im)^\s*matched[-_]tags\s*:\s*(.+)$", prompt)
    if not m:
        return None
    return [t.strip() for t in m.group(1).split(",") if t.strip()]


def _extract_matched_tags_from_cwd(cwd, mode):
    """Find matched_tags from the most recent pipeline output in {cwd}/.solid_coder/.

    Reads from files written by the previous pipeline phase — no JSONL timing dependency.

    code (implement):   implementation-plan.json      → matched_tags[] field
    code (refactor):    prepare/review-input.json     → matched_tags[] field
    synth-fixes:        prepare/review-input.json     → matched_tags[] field
    synth-impl:         arch.json                     → derive from component category/stack
    """
    solid_dir = Path(cwd) / ".solid_coder"
    if not solid_dir.exists():
        return None

    def _read_tags(files):
        for f in sorted(files, key=lambda x: x.stat().st_mtime, reverse=True)[:3]:
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
                tags = data.get("matched_tags", [])
                if isinstance(tags, list) and tags:
                    return [t.strip() for t in tags if t.strip()]
            except Exception:
                pass
        return None

    if mode == "code":
        # Distinguish implement vs refactor by the most recent run folder name
        run_dirs = sorted(
            [d for d in solid_dir.iterdir() if d.is_dir()],
            key=lambda d: d.stat().st_mtime, reverse=True
        )
        latest = run_dirs[0].name if run_dirs else ""
        if latest.startswith("implement-"):
            return _read_tags(solid_dir.rglob("implementation-plan.json"))
        if latest.startswith("refactor-"):
            return _read_tags(solid_dir.rglob("review-input.json"))
        # Fallback: try both
        return (_read_tags(solid_dir.rglob("implementation-plan.json"))
                or _read_tags(solid_dir.rglob("review-input.json")))

    if mode in ("synth-fixes",):
        return _read_tags(solid_dir.rglob("review-input.json"))

    if mode == "synth-impl":
        # Derive tags from arch.json components (category + stack) and validation.json
        def _tags_from_components(data):
            tags = set()
            for comp in data.get("components", []):
                if comp.get("category"):
                    tags.add(comp["category"].lower())
                for s in comp.get("stack", []):
                    tags.add(s.lower())
            return sorted(tags) if tags else None

        for arch in sorted(solid_dir.rglob("arch.json"),
                           key=lambda f: f.stat().st_mtime, reverse=True)[:3]:
            try:
                tags = _tags_from_components(json.loads(arch.read_text(encoding="utf-8")))
                if tags:
                    return tags
            except Exception:
                pass

        for val in sorted(solid_dir.rglob("validation.json"),
                          key=lambda f: f.stat().st_mtime, reverse=True)[:3]:
            try:
                tags = _tags_from_components(json.loads(val.read_text(encoding="utf-8")))
                if tags:
                    return tags
            except Exception:
                pass
        return None

    return None


def _extract_matched_tags_from_output_root(prompt):
    """Read matched_tags from prepare/review-input.json via `output-root:` in prompt.

    Used for synth-fixes and synth-impl modes whose prompts contain an output-root
    pointing to a refactor/implement iteration directory.
    """
    if not prompt:
        return None
    import re
    m = re.search(r"(?im)^\s*output[-_]root\s*:\s*(.+)$", prompt)
    if not m:
        return None
    output_root = Path(m.group(1).strip())
    candidates = [
        output_root / "prepare" / "review-input.json",
        output_root.parent / "prepare" / "review-input.json",
    ]
    for candidate in candidates:
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            tags = data.get("matched_tags", [])
            if isinstance(tags, list) and tags:
                return [t.strip() for t in tags if t.strip()]
        except Exception:
            pass
    return None


def _extract_matched_tags_from_plan(prompt):
    """Read matched_tags from implementation-plan.json found via `plan:` in prompt.

    The plan: value may be a directory (chunked) — looks for implementation-plan.json
    one level up, or reads the first *.json in the directory.
    Returns list of tags or None if not found / not applicable.
    """
    if not prompt:
        return None
    import re
    m = re.search(r"(?im)^\s*plan\s*:\s*(.+)$", prompt)
    if not m:
        return None
    plan_path = Path(m.group(1).strip())

    candidates = []
    if plan_path.is_dir():
        # chunked layout: implementation-plan.json sits next to the directory
        candidates.append(plan_path.parent / "implementation-plan.json")
        # fallback: first JSON chunk in the directory
        chunks = sorted(plan_path.glob("*.json"))
        if chunks:
            candidates.append(chunks[0])
    elif plan_path.is_file():
        candidates.append(plan_path)

    for candidate in candidates:
        try:
            data = json.loads(candidate.read_text(encoding="utf-8"))
            tags = data.get("matched_tags", [])
            if isinstance(tags, list) and tags:
                return [t.strip() for t in tags if t.strip()]
        except Exception:
            pass
    return None


def _build_additional_context(mode, paths):
    """Render the SubagentStart additionalContext instruction text."""
    header = MODE_INSTRUCTION_TEMPLATES.get(
        mode,
        "Before starting, read the following file(s). You MUST apply their rules."
    )
    file_list = "\n".join(f"- {p}" for p in paths)
    body = (
        f"{header}\n\n"
        f"Files to read (absolute paths):\n{file_list}\n\n"
        f"If any file is missing or unreadable, stop and report the error."
    )
    pattern_index = build_pattern_index()
    if pattern_index:
        body += (
            f"\n\n{pattern_index}\n"
            f"Whenever you need to use a design pattern — whether writing, "
            f"reviewing, planning, or synthesizing — read its file (path listed "
            f"above) before applying or suggesting it."
        )
    return body


def preload_instruction(**_ignored):
    """Emit a SubagentStart hook response instructing the subagent to read rule files.

    Reads the hook event JSON from stdin. Expects at least:
      { "hook_event_name": "SubagentStart",
        "subagent_type": "solid-coder:apply-principle-review-agent",
        "prompt": "principle: SRP\\n..." }
    """
    try:
        raw = sys.stdin.read()
        event = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError as e:
        print(f"Error: invalid hook JSON on stdin: {e}", file=sys.stderr)
        sys.exit(1)

    agent_type = event.get("agent_type") or event.get("subagent_type") or event.get("subagentType") or ""

    mode = SUBAGENT_TYPE_TO_MODE.get(agent_type)
    if not mode:
        return ""

    cwd = event.get("cwd", "")

    if mode == "review":
        return ""  # review agents handle their own rule loading via principle-folder in prompt

    # Resolve matched_tags from files written before spawning — no JSONL dependency.
    # JSONL is only written on the agent's first API call which is AFTER the hook
    # completes, so reading it would deadlock. Use cwd-based resolution instead.
    matched_tags = _extract_matched_tags_from_cwd(cwd, mode) if cwd else None

    result = load_rules(principle=None, matched_tags=matched_tags, mode=mode)

    if result.get("errors"):
        print(json.dumps({"errors": result["errors"]}), file=sys.stderr)
        sys.exit(1)

    paths = result.get("paths_to_load", [])
    if not paths:
        print(f"Error: no files resolved for mode={mode}, principle={principle!r}, "
              f"matched_tags={matched_tags!r}", file=sys.stderr)
        sys.exit(1)

    return {"hookSpecificOutput": {"hookEventName": "SubagentStart",
                                   "additionalContext": _build_additional_context(mode, paths)}}


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
    "preload_instruction": preload_instruction,
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


if __name__ == "__main__":
    main()
