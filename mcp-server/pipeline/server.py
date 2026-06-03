#!/usr/bin/env python3
"""solid-coder pipeline MCP server — review/refactor orchestration tools.

Tools:
  check_severity          — check findings for SEVERE violations, determine stop/continue
  validate_findings       — filter findings to changed ranges, write by-file/*.output.json
  load_synthesis_context  — load all by-file findings for synthesize-fixes
  generate_report         — generate MD + HTML reports from findings and plans
  validate_architecture   — validate arch.json structure and SOLID constraints
  split_implementation_plan — split implementation-plan.json into dependency chunks
  search_codebase         — search for reusable types by solid-frontmatter
  prepare_review_input    — prepare git changes into structured review-input.json

No external dependencies. Python 3.9+.
"""

import json
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
MCP_DIR = SERVER_DIR.parent
PLUGIN_ROOT = MCP_DIR.parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"

sys.path.insert(0, str(MCP_DIR))
sys.path.insert(0, str(SKILLS_ROOT / "validate-findings" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "synthesize-fixes" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "prepare-review-input" / "scripts"))

import importlib
check_severity_mod = importlib.import_module("check-severity")
load_context_mod = importlib.import_module("load-context")
validate_output_mod = importlib.import_module("validate-output")

from protocol import MCPServer
from lib.subprocess_utils import run_cmd
from lib.chunker import Chunker

server = MCPServer("solid-coder-pipeline", "1.0.0")
_chunker = Chunker()


def _run_skill(skill_dir: str, script_name: str, args: list):
    """Build a SKILLS_ROOT-relative script path and invoke it. Returns (ok, stdout, stderr)."""
    path = str(SKILLS_ROOT / skill_dir / "scripts" / script_name)
    return run_cmd([sys.executable, path] + args)


def _skill_result(ok: bool, err: str, **fields) -> dict:
    """Build a uniform skill-invocation result dict. Error is None when ok."""
    return {**fields, "error": err if not ok else None}


# ---------------------------------------------------------------------------
# Tool: collect_review_results
# ---------------------------------------------------------------------------

@server.tool(
    name="collect_review_results",
    description=(
        "Collect and summarise all review outputs after review agents complete. "
        "Reads every rules/*/review-output.json, aggregates per-principle severity and finding counts, "
        "and returns verdict (ALL_COMPLIANT | MINOR_ONLY | HAS_SEVERE), a summary table, "
        "and minor_findings list. Use the verdict to decide: ALL_COMPLIANT/MINOR_ONLY → stop, HAS_SEVERE → continue."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "output_root": {"type": "string", "description": "Iteration output directory, e.g. .solid_coder/refactor-xxx/1"},
        },
        "required": ["output_root"],
    },
)
def collect_review_results(output_root):
    rules_dir = Path(output_root) / "rules"
    if not rules_dir.is_dir():
        return {"error": f"No rules/ directory found in {output_root}. Have reviews completed?"}

    table = []
    minor_findings = []
    all_compliant = True

    for principle_dir in sorted(rules_dir.iterdir()):
        review_path = principle_dir / "review-output.json"
        if not review_path.exists():
            continue
        try:
            data = json.loads(review_path.read_text(encoding="utf-8"))
        except Exception as e:
            table.append({"principle": principle_dir.name, "severity": "ERROR",
                          "findings": 0, "path": str(review_path), "error": str(e)})
            continue

        severe = minor = 0
        for file_entry in data.get("files", []):
            for unit in file_entry.get("units", []):
                for finding in unit.get("findings", []):
                    sev = finding.get("severity", "COMPLIANT")
                    if sev == "SEVERE":
                        severe += 1
                        all_compliant = False
                    elif sev == "MINOR":
                        minor += 1
                        minor_findings.append(finding)
                        all_compliant = False

        worst = "SEVERE" if severe else ("MINOR" if minor else "COMPLIANT")
        table.append({
            "principle": principle_dir.name,
            "severity": worst,
            "findings": severe + minor,
            "severe": severe,
            "minor": minor,
            "path": str(review_path),
        })

    if not table:
        return {"verdict": "ALL_COMPLIANT", "summary": [], "minor_findings": []}

    has_severe = any(r["severity"] == "SEVERE" for r in table)
    verdict = "ALL_COMPLIANT" if all_compliant else ("HAS_SEVERE" if has_severe else "MINOR_ONLY")

    return _chunker.save_json({
        "verdict": verdict,
        "summary": table,
        "minor_findings": minor_findings,
        "total_severe": sum(r.get("severe", 0) for r in table),
        "total_minor": sum(r.get("minor", 0) for r in table),
    }, "review-results")


# ---------------------------------------------------------------------------
# Tool: check_severity  (kept for backward compatibility)
# ---------------------------------------------------------------------------

@server.tool(
    name="check_severity",
    description="Check review findings for SEVERE violations. Returns structured verdict.",
    input_schema={
        "type": "object",
        "properties": {
            "output_root": {"type": "string", "description": "Iteration output directory"},
        },
        "required": ["output_root"],
    },
)
def check_severity(output_root):
    return check_severity_mod.check_severity(output_root)


# ---------------------------------------------------------------------------
# Tool: validate_findings
# ---------------------------------------------------------------------------

@server.tool(
    name="validate_findings",
    description=(
        "Filter findings to changed line ranges and reorganize by file. "
        "Writes by-file/*.output.json. Run after all review agents complete."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "output_root": {"type": "string", "description": "Iteration output directory"},
        },
        "required": ["output_root"],
    },
)
def validate_findings(output_root):
    ok, out, err = _run_skill("validate-findings", "validate-findings.py",
                              [output_root, str(PLUGIN_ROOT)])
    return _skill_result(ok, err, success=ok, output=out)


# ---------------------------------------------------------------------------
# Tool: load_synthesis_context
# ---------------------------------------------------------------------------

@server.tool(
    name="load_synthesis_context",
    description=(
        "Load all validated findings for synthesis. "
        "Returns files with per-principle summaries, active_principles list, and severity counts."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "output_root": {"type": "string", "description": "Iteration output directory"},
        },
        "required": ["output_root"],
    },
)
def load_synthesis_context(output_root):
    return _chunker.save_json(load_context_mod.load_context(output_root), "synthesis-context")


# ---------------------------------------------------------------------------
# Tool: generate_report
# ---------------------------------------------------------------------------

@server.tool(
    name="generate_report",
    description="Generate MD + HTML reports from validated findings and synthesized fix plans.",
    input_schema={
        "type": "object",
        "properties": {
            "data_dir": {"type": "string", "description": "Iteration directory containing by-file/ and optional synthesized/"},
            "report_dir": {"type": "string", "description": "Where to write report.md and report.html. Defaults to data_dir."},
        },
        "required": ["data_dir"],
    },
)
def generate_report(data_dir, report_dir=None):
    report_dir = report_dir or data_dir
    ok, out, err = _run_skill("generate-report", "generate-report.py", [data_dir, report_dir])
    return _skill_result(ok, err,
                         success=ok,
                         md_path=str(Path(report_dir) / "report.md") if ok else None,
                         html_path=str(Path(report_dir) / "report.html") if ok else None)


# ---------------------------------------------------------------------------
# Tool: validate_architecture
# ---------------------------------------------------------------------------

@server.tool(
    name="validate_architecture",
    description="Validate arch.json structure and semantic SOLID constraints.",
    input_schema={
        "type": "object",
        "properties": {
            "arch_path": {"type": "string", "description": "Path to arch.json"},
        },
        "required": ["arch_path"],
    },
)
def validate_architecture(arch_path):
    schema = str(SKILLS_ROOT / "plan" / "arch.schema.json")
    ok, out, err = _run_skill("plan", "validate-arch.py", [arch_path, "--schema", schema])
    return _skill_result(ok, err, valid=ok, output=out, errors=err if not ok else None)


# ---------------------------------------------------------------------------
# Tool: split_implementation_plan
# ---------------------------------------------------------------------------

@server.tool(
    name="split_implementation_plan",
    description=(
        "Split implementation-plan.json into semantically grouped chunks. "
        "When arch_path is provided, items are classified by component category "
        "(model/enum/typealias → foundations, unit tests → tests, UI tests → ui-tests). "
        "Without arch_path, all items are split by dependency level only."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "plan_path": {"type": "string", "description": "Path to implementation-plan.json"},
            "output_dir": {"type": "string", "description": "Directory to write chunk files"},
            "arch_path": {"type": "string", "description": "Optional path to arch.json for component category classification"},
        },
        "required": ["plan_path", "output_dir"],
    },
)
def split_implementation_plan(plan_path, output_dir, arch_path=None):
    args = [plan_path, "--output-dir", output_dir]
    if arch_path:
        args += ["--arch", arch_path]
    ok, out, err = _run_skill("synthesize-implementation", "split-plan.py", args)
    chunks = sorted(Path(output_dir).glob("*.json")) if ok else []
    return _skill_result(ok, err, success=ok, chunks=[str(c) for c in chunks], count=len(chunks))


# ---------------------------------------------------------------------------
# Tool: search_codebase
# ---------------------------------------------------------------------------

@server.tool(
    name="search_codebase",
    description=(
        "Use this every time you need to search the codebase — for reusable types, existing implementations, "
        "or any concept before creating something new. "
        "Describe what you are looking for, then split that description into individual words plus "
        "LLM-generated semantic synonyms (e.g. 'fetch' → ['fetch', 'retrieve', 'load', 'pull', 'get']) and pass them as tags. "
        "Pass plan_path if you have one (arch.json or implementation-plan.json) to auto-extract structural terms "
        "(component names, interfaces, categories, spec numbers) — these merge with your tags. "
        "Pass spec_numbers (or include SPEC-NNN entries inside tags) to match against solid-spec frontmatter; "
        "spec matches always pass regardless of min_matches. "
        "Matches each file against: solid-description words, solid-tags frontmatter, and import statements. "
        "Returns a compact list of file paths with descriptions — read the description to assess relevance, "
        "use the Read tool to inspect the full source."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "sources_dir": {"type": "string", "description": "Root directory to search. Defaults to the current working directory when omitted."},
            "plan_path": {"type": "string", "description": "Path to arch.json or implementation-plan.json. Auto-extracts component names, interfaces, and spec numbers."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Search terms matched against solid-description words, solid-tags frontmatter, and imports. SPEC-NNN entries are automatically routed to spec number matching. Merged with auto-extracted terms from plan_path."},
            "spec_numbers": {"type": "array", "items": {"type": "string"}, "description": "Spec numbers to match against solid-spec frontmatter"},
            "min_matches": {"type": "integer", "description": "Minimum combined hits (description words + tags + imports) required per file (default: 3). Spec matches always pass."},
        },
        "required": [],
    },
)
def search_codebase(sources_dir=None, plan_path=None, tags=None, spec_numbers=None, min_matches=3):
    from lib.codebase_searcher import search as _search
    return _search(sources_dir=sources_dir, plan_path=plan_path, tags=tags,
                   spec_numbers=spec_numbers, min_matches=min_matches)


# ---------------------------------------------------------------------------
# Tool: prepare_review_input
# ---------------------------------------------------------------------------

@server.tool(
    name="prepare_review_input",
    description="Prepare git changes (staged, unstaged, untracked) into structured review-input.json.",
    input_schema={
        "type": "object",
        "properties": {
            "candidate_tags": {"type": "array", "items": {"type": "string"}, "description": "Candidate tags for import-based principle filtering"},
        },
    },
)
def prepare_review_input(candidate_tags=None):
    ok, out, err = _run_skill("prepare-review-input", "prepare-changes.py", [])
    if not ok:
        return {"error": err}
    try:
        data = json.loads(out)
        data["candidate_tags"] = candidate_tags or []
        return data
    except json.JSONDecodeError:
        return {"error": f"Could not parse script output: {out}"}


# ---------------------------------------------------------------------------
# Tool: submit_findings
# ---------------------------------------------------------------------------

from lib.gateway_tools import make_gateway_handler as _make_gw_pipeline

_gw_pipeline = _make_gw_pipeline(PLUGIN_ROOT / "references")


@server.tool(
    name="submit_findings",
    description=(
        "Accept a single partial review output document (one principle), score it deterministically "
        "via severity-bands XML in rule.md, fill scoring + findings, write the completed document to "
        "output_path, and return a compact summary. "
        "Input: partial output with agent, principle, timestamp, and files[].units[].metrics filled "
        "using the principle's review output schema (semantic metric keys like 'verbs', "
        "'cohesion_groups', 'stakeholders' with nested count/detail dicts). "
        "Scoring and findings in the input should be absent or empty — the server fills them. "
        "The server bridges the schema metric keys to severity-band condition variables automatically. "
        "Returns error if output_path is unwritable."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "partial_output": {
                "type": "object",
                "description": "Partial output document with metrics filled, scoring + findings absent.",
            },
            "output_path": {
                "type": "string",
                "description": "Absolute path where the completed review-output.json will be written.",
            },
        },
        "required": ["partial_output", "output_path"],
    },
)
def submit_findings(partial_output, output_path):
    return _gw_pipeline.submit_findings(partial_output, output_path)


# ---------------------------------------------------------------------------
# Tool: validate_phase_output
# ---------------------------------------------------------------------------

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


if __name__ == "__main__":
    server.run()
