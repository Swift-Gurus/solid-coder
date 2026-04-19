#!/usr/bin/env python3
"""solid-coder MCP server — exposes all pipeline tools.

No external dependencies. Works on Python 3.9+.
Run: python3 mcp-server/server.py
"""

import json
import os
import subprocess
import sys
from pathlib import Path

# Resolve paths
SERVER_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SERVER_DIR.parent
REFS_ROOT = PLUGIN_ROOT / "references"
SKILLS_ROOT = PLUGIN_ROOT / "skills"

# Add script directories to path for imports
sys.path.insert(0, str(SKILLS_ROOT / "discover-principles" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "parse-frontmatter" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "load-reference" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "code" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "validate-findings" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "synthesize-fixes" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "prepare-review-input" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "generate-report" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "synthesize-implementation" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "plan" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "validate-plan" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "build-spec" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "find-spec" / "scripts"))

# Import modules using hyphenated filenames
import importlib
discover_principles = importlib.import_module("discover-principles")
parse_frontmatter = importlib.import_module("parse-frontmatter")
load_reference = importlib.import_module("load-reference")
collect_principle_files = importlib.import_module("collect-principle-files")
check_severity_mod = importlib.import_module("check-severity")
load_context_mod = importlib.import_module("load-context")
validate_output_mod = importlib.import_module("validate-output")

from protocol import MCPServer
import modes as modes_module
import rule_stripper

server = MCPServer("solid-coder", "1.0.0")


# =============================================================================
# Tool: get_candidate_tags
# =============================================================================

@server.tool(
    name="get_candidate_tags",
    description="Get all candidate tags from all principles. No arguments needed — server knows where references/ is.",
    input_schema={
        "type": "object",
        "properties": {},
        "required": [],
    },
)
def get_candidate_tags():
    result = discover_principles.discover_and_filter(str(REFS_ROOT))
    return {"candidate_tags": result["all_candidate_tags"]}


# =============================================================================
# Tool: discover_principles
# =============================================================================

@server.tool(
    name="discover_principles",
    description=(
        "Discover active principles. Returns metadata only (names, folders) — no content loaded. "
        "Use this in orchestrators to get the list of principles to fan out to agents. "
        "Each agent then calls load_rules for its own principle."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "matched_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional tags to filter principles by",
            },
            "profile": {
                "type": "string",
                "description": "Optional profile ('review' or 'code') — filters out principles whose `profile:` list doesn't include it. Principles with no `profile:` field are available everywhere.",
            },
        },
        "required": [],
    },
)
def discover_principles_tool(matched_tags=None, profile=None):
    result = discover_principles.discover_and_filter(
        str(REFS_ROOT), matched_tags=matched_tags, profile=profile,
    )
    return {
        "active_principles": result["active_principles"],
        "skipped_principles": result["skipped_principles"],
        "all_candidate_tags": result["all_candidate_tags"],
    }


# =============================================================================
# Tool: load_rules
# =============================================================================

@server.tool(
    name="load_rules",
    description=(
        "Load principle rules. Preferred: pass `mode` (code|review|planner|synth-impl|synth-fixes) — "
        "the server resolves profile + exclude from mcp-server/modes.py. "
        "Legacy: pass `profile` + `exclude` directly (kept for backward compatibility)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "mode": {
                "type": "string",
                "enum": list(modes_module.MODES.keys()),
                "description": "Pipeline mode — resolves profile + exclude from modes.py. Preferred over profile/exclude.",
            },
            "profile": {
                "type": "string",
                "enum": ["review", "code"],
                "description": "Legacy: explicit profile. Ignored if `mode` is set.",
            },
            "principle": {
                "type": "string",
                "description": "Load rules for ONE principle by name (e.g. 'srp'). Omit to load all active principles.",
            },
            "matched_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional tags to filter principles by (only used when principle is omitted)",
            },
            "exclude": {
                "type": "string",
                "description": "Legacy: comma-separated sections to skip. Ignored if `mode` is set.",
            },
        },
        "required": [],
    },
)
def load_rules(profile=None, principle=None, matched_tags=None, exclude=None, mode=None):
    # Mode wins — derive profile + exclude from the single source of truth.
    strip_review = False
    if mode:
        if mode not in modes_module.MODES:
            return {"errors": [{"principle": "", "file": "", "error":
                f"Invalid --mode '{mode}'. Valid: {', '.join(modes_module.MODES)}"}]}
        cfg = modes_module.resolve(mode)
        profile = cfg["profile"]
        exclude = ",".join(cfg["exclude"]) if cfg["exclude"] else None
        strip_review = cfg.get("strip_review_content", False)
    if not profile:
        return {"errors": [{"principle": "", "file": "", "error": "Either `mode` or `profile` is required"}]}
    if profile not in ("review", "code"):
        valid_modes = ", ".join(modes_module.MODES)
        return {"errors": [{"principle": "", "file": "", "error":
            f"Invalid --profile '{profile}'. Valid: review, code. "
            f"For pipeline modes ({valid_modes}), use --mode instead."}]}
    # Step 1: Discover and filter principles (by matched tags AND the requested profile)
    result = discover_principles.discover_and_filter(
        str(REFS_ROOT), matched_tags=matched_tags, profile=profile,
    )

    active = result["active_principles"]

    # Filter to single principle if requested (agent mode)
    if principle:
        active = [p for p in active if p["name"].lower() == principle.lower()]
        if not active:
            return {"active_principles": [], "rules": {}, "errors": [
                {"principle": principle, "file": "", "error": f"Principle '{principle}' not found or not active"}
            ], "skipped_principles": result["skipped_principles"]}

    # Parse exclude list: comma-separated string or list
    skip = set()
    if exclude:
        if isinstance(exclude, str):
            skip = set(e.strip().lower() for e in exclude.split(","))
        elif isinstance(exclude, list):
            skip = set(e.lower() for e in exclude)

    errors = []
    rules = {}

    for p in active:
        name = p["name"]
        folder = Path(p["folder"])
        rule_path = p["rule_path"]

        entry = {"rule": None, "instructions": None, "examples": [], "patterns": [], "code_rules": None}

        # Load rule.md (always loaded)
        try:
            loaded = load_reference.load([rule_path])
            if loaded:
                content = loaded[0]["content"]
                if strip_review:
                    content = rule_stripper.strip_review_content(
                        content,
                        h2_sections=modes_module.STRIP_H2_SECTIONS,
                        bold_subsections=modes_module.STRIP_BOLD_SUBSECTIONS,
                        h3_sections=modes_module.STRIP_H3_SECTIONS,
                    )
                entry["rule"] = content
        except Exception as e:
            errors.append({"principle": name, "file": "rule.md", "error": str(e)})

        # Load instructions
        if "instructions" not in skip:
            if profile == "review":
                instr_path = folder / "review" / "instructions.md"
            else:
                instr_path = folder / "fix" / "instructions.md"

            if instr_path.is_file():
                try:
                    loaded = load_reference.load([str(instr_path)])
                    if loaded:
                        entry["instructions"] = loaded[0]["content"]
                except Exception as e:
                    errors.append({"principle": name, "file": str(instr_path.name), "error": str(e)})

        # Load examples
        if "examples" not in skip:
            examples_dir = folder / "Examples"
            if examples_dir.is_dir():
                try:
                    loaded = load_reference.load([str(examples_dir)])
                    entry["examples"] = [f["content"] for f in loaded]
                except Exception:
                    pass

        # Load design patterns
        if "patterns" not in skip:
            try:
                parsed = parse_frontmatter.parse(rule_path)
                for pattern_path in parsed.get("required_patterns", []) if isinstance(parsed.get("required_patterns"), list) else []:
                    if Path(pattern_path).is_file():
                        loaded = load_reference.load([pattern_path])
                        if loaded:
                            entry["patterns"].append(loaded[0]["content"])
            except Exception:
                pass

        # Load code/instructions.md (code profile only)
        if "code_rules" not in skip and profile == "code":
            code_rule = folder / "code" / "instructions.md"
            if code_rule.is_file():
                try:
                    loaded = load_reference.load([str(code_rule)])
                    if loaded:
                        entry["code_rules"] = loaded[0]["content"]
                except Exception:
                    pass

        rules[name] = entry

    return {
        "active_principles": [p["name"] for p in active],
        "skipped_principles": result["skipped_principles"],
        "rules": rules,
        "errors": errors,
    }


# =============================================================================
# Tool: check_severity
# =============================================================================

@server.tool(
    name="check_severity",
    description="Check if review findings contain SEVERE violations. Returns structured verdict.",
    input_schema={
        "type": "object",
        "properties": {
            "output_root": {
                "type": "string",
                "description": "Path to the review output directory",
            },
        },
        "required": ["output_root"],
    },
)
def check_severity(output_root):
    return check_severity_mod.check_severity(output_root)


# =============================================================================
# Tool: load_synthesis_context
# =============================================================================

@server.tool(
    name="load_synthesis_context",
    description="Load all by-file findings for synthesis. Returns files, active principles, severity counts.",
    input_schema={
        "type": "object",
        "properties": {
            "output_root": {
                "type": "string",
                "description": "Path to the review output directory",
            },
        },
        "required": ["output_root"],
    },
)
def load_synthesis_context(output_root):
    return load_context_mod.load_context(output_root)


# =============================================================================
# Tool: validate_phase_output
# =============================================================================

@server.tool(
    name="validate_phase_output",
    description="Validate a JSON file against a JSON schema.",
    input_schema={
        "type": "object",
        "properties": {
            "json_path": {"type": "string", "description": "Path to the JSON file"},
            "schema_path": {"type": "string", "description": "Path to the JSON schema file"},
        },
        "required": ["json_path", "schema_path"],
    },
)
def validate_phase_output(json_path, schema_path):
    return validate_output_mod.validate_json(json_path, schema_path)


# =============================================================================
# Tool: validate_findings
# =============================================================================

@server.tool(
    name="validate_findings",
    description="Filter findings by changed ranges and reorganize by file. Writes by-file/*.output.json.",
    input_schema={
        "type": "object",
        "properties": {
            "output_root": {"type": "string", "description": "Path to review output directory"},
        },
        "required": ["output_root"],
    },
)
def validate_findings(output_root):
    # Call via subprocess since validate-findings.py writes files and uses exit codes
    script = str(SKILLS_ROOT / "validate-findings" / "scripts" / "validate-findings.py")
    result = subprocess.run(
        [sys.executable, script, output_root, str(PLUGIN_ROOT)],
        capture_output=True, text=True,
    )
    return {
        "success": result.returncode == 0,
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else None,
    }


# =============================================================================
# Tool: generate_report
# =============================================================================

@server.tool(
    name="generate_report",
    description="Generate MD + HTML reports from validated findings and synthesized fix plans.",
    input_schema={
        "type": "object",
        "properties": {
            "data_dir": {
                "type": "string",
                "description": "Iteration directory containing by-file/ and optional synthesized/",
            },
            "report_dir": {
                "type": "string",
                "description": "Where report.md and report.html are written. Defaults to data_dir.",
            },
            "output_root": {
                "type": "string",
                "description": "Deprecated alias for data_dir — retained for backward compatibility.",
            },
        },
    },
)
def generate_report(data_dir=None, report_dir=None, output_root=None):
    data_dir = data_dir or output_root
    if not data_dir:
        return {"success": False, "error": "data_dir (or legacy output_root) is required"}
    report_dir = report_dir or data_dir

    script = str(SKILLS_ROOT / "generate-report" / "scripts" / "generate-report.py")
    result = subprocess.run(
        [sys.executable, script, data_dir, report_dir],
        capture_output=True, text=True,
    )
    md_path = str(Path(report_dir) / "report.md")
    html_path = str(Path(report_dir) / "report.html")
    return {
        "success": result.returncode == 0,
        "md_path": md_path if result.returncode == 0 else None,
        "html_path": html_path if result.returncode == 0 else None,
        "error": result.stderr.strip() if result.returncode != 0 else None,
    }


# =============================================================================
# Tool: validate_architecture
# =============================================================================

@server.tool(
    name="validate_architecture",
    description="Validate arch.json structure and semantic constraints.",
    input_schema={
        "type": "object",
        "properties": {
            "arch_path": {"type": "string", "description": "Path to arch.json"},
        },
        "required": ["arch_path"],
    },
)
def validate_architecture(arch_path):
    script = str(SKILLS_ROOT / "plan" / "scripts" / "validate-arch.py")
    schema_path = str(SKILLS_ROOT / "plan" / "arch.schema.json")
    result = subprocess.run(
        [sys.executable, script, arch_path, "--schema", schema_path],
        capture_output=True, text=True,
    )
    return {
        "valid": result.returncode == 0,
        "output": result.stdout.strip(),
        "errors": result.stderr.strip() if result.returncode != 0 else None,
    }


# =============================================================================
# Tool: split_implementation_plan
# =============================================================================

@server.tool(
    name="split_implementation_plan",
    description="Split implementation-plan.json into dependency-level chunks.",
    input_schema={
        "type": "object",
        "properties": {
            "plan_path": {"type": "string", "description": "Path to implementation-plan.json"},
            "output_dir": {"type": "string", "description": "Directory to write chunk files"},
        },
        "required": ["plan_path", "output_dir"],
    },
)
def split_implementation_plan(plan_path, output_dir):
    script = str(SKILLS_ROOT / "synthesize-implementation" / "scripts" / "split-plan.py")
    result = subprocess.run(
        [sys.executable, script, plan_path, "--output-dir", output_dir],
        capture_output=True, text=True,
    )
    chunks = sorted(Path(output_dir).glob("*.json")) if result.returncode == 0 else []
    return {
        "success": result.returncode == 0,
        "chunks": [str(c) for c in chunks],
        "count": len(chunks),
        "output": result.stdout.strip(),
        "error": result.stderr.strip() if result.returncode != 0 else None,
    }


# =============================================================================
# Tool: search_codebase
# =============================================================================

@server.tool(
    name="search_codebase",
    description="Search codebase for reusable types/components by solid-frontmatter.",
    input_schema={
        "type": "object",
        "properties": {
            "sources_dir": {"type": "string", "description": "Directory to search"},
            "synonyms": {
                "type": "object",
                "description": "Synonym groups as JSON (key: term, value: [synonyms])",
            },
            "spec_numbers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Spec numbers to search for (e.g. SPEC-001)",
            },
        },
        "required": ["sources_dir"],
    },
)
def search_codebase(sources_dir, synonyms=None, spec_numbers=None):
    script = str(SKILLS_ROOT / "validate-plan" / "scripts" / "search-codebase.py")
    args = [sys.executable, script, "--sources", sources_dir]
    if synonyms:
        args.extend(["--synonyms", json.dumps(synonyms)])
    if spec_numbers:
        for spec in spec_numbers:
            args.extend(["--spec", spec])
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return {"error": result.stderr.strip(), "matches": []}


# =============================================================================
# Tool: query_specs
# =============================================================================

@server.tool(
    name="query_specs",
    description="Query spec hierarchy. Actions: scan, children, ancestors, next-number, types, statuses, resolve-path, update-status.",
    input_schema={
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["scan", "children", "ancestors", "next-number", "types", "statuses", "resolve-path", "update-status"],
                "description": "Which query to run",
            },
            "args": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Arguments for the action",
            },
        },
        "required": ["action"],
    },
)
def query_specs(action, args=None):
    # Route to the right script
    if action in ("scan", "children", "ancestors", "next-number"):
        script = str(SKILLS_ROOT / "find-spec" / "scripts" / "find-spec-query.py")
    else:
        script = str(SKILLS_ROOT / "build-spec" / "scripts" / "build-spec-query.py")

    cmd = [sys.executable, script, action] + (args or [])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            return {"output": result.stdout.strip()}
    return {"error": result.stderr.strip()}


# =============================================================================
# Tool: prepare_review_input
# =============================================================================

@server.tool(
    name="prepare_review_input",
    description="Prepare git changes into structured review-input.json.",
    input_schema={
        "type": "object",
        "properties": {
            "candidate_tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Candidate tags from get_candidate_tags for import matching",
            },
        },
        "required": [],
    },
)
def prepare_review_input(candidate_tags=None):
    script = str(SKILLS_ROOT / "prepare-review-input" / "scripts" / "prepare-changes.py")
    result = subprocess.run(
        [sys.executable, script],
        capture_output=True, text=True,
    )
    if result.returncode == 0:
        data = json.loads(result.stdout)
        # candidate_tags are passed for the prepare-review-input agent to do matching
        # The script extracts imports; tag matching happens in the agent
        data["candidate_tags"] = candidate_tags or []
        return data
    return {"error": result.stderr.strip()}


if __name__ == "__main__":
    server.run()
