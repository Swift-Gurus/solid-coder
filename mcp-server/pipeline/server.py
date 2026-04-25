#!/usr/bin/env python3
"""solid-coder pipeline MCP server — review/refactor orchestration tools.

Tools:
  check_severity          — check findings for SEVERE violations, determine stop/continue
  validate_findings       — filter findings to changed ranges, write by-file/*.output.json
  load_synthesis_context  — load all by-file findings for synthesize-fixes
  generate_report         — generate MD + HTML report from findings and plans
  validate_architecture   — validate arch.json structure and SOLID constraints
  split_implementation_plan — split implementation-plan.json into dependency chunks
  search_codebase         — search for reusable types by solid-frontmatter
  prepare_review_input    — prepare git changes into structured review-input.json

No external dependencies. Python 3.9+.
"""

import json
import re
import subprocess
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent
MCP_DIR = SERVER_DIR.parent
PLUGIN_ROOT = MCP_DIR.parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"

sys.path.insert(0, str(MCP_DIR))
sys.path.insert(0, str(SKILLS_ROOT / "validate-findings" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "synthesize-fixes" / "scripts"))

import importlib
check_severity_mod = importlib.import_module("check-severity")
load_context_mod = importlib.import_module("load-context")

from protocol import MCPServer

server = MCPServer("solid-coder-pipeline", "1.0.0")


_CHUNK_SIZE = 40_000


def _maybe_chunk(content: str, prefix: str) -> str:
    """Save large text content to chunk files; return Read instructions if chunked."""
    if len(content) <= _CHUNK_SIZE:
        return content
    import tempfile, time
    ts = int(time.time())
    chunks = [content[i:i + _CHUNK_SIZE] for i in range(0, len(content), _CHUNK_SIZE)]
    paths = []
    for n, chunk in enumerate(chunks, 1):
        path = Path(tempfile.gettempdir()) / f"solid-coder-{prefix}-{ts}-{n}of{len(chunks)}.md"
        path.write_text(chunk, encoding="utf-8")
        paths.append(str(path))
    lines = [
        f"Content is large ({len(content):,} chars across {len(chunks)} chunks).",
        "Read each file below in order using the Read tool:",
        "",
    ] + [f"- {p}" for p in paths]
    return "\n".join(lines)


def _maybe_save_json(data, prefix: str):
    """Save large JSON data to a file; return path instruction if too large."""
    serialized = json.dumps(data, indent=2)
    if len(serialized) <= _CHUNK_SIZE:
        return data
    import tempfile, time
    ts = int(time.time())
    path = Path(tempfile.gettempdir()) / f"solid-coder-{prefix}-{ts}.json"
    path.write_text(serialized, encoding="utf-8")
    return {
        "large_output": True,
        "chars": len(serialized),
        "file": str(path),
        "instruction": f"Output is large ({len(serialized):,} chars). Read the file at '{path}' using the Read tool.",
    }


def _run_script(cmd: list) -> tuple[bool, str, str]:
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.returncode == 0, result.stdout.strip(), result.stderr.strip()


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

    return _maybe_save_json({
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
    script = str(SKILLS_ROOT / "validate-findings" / "scripts" / "validate-findings.py")
    ok, out, err = _run_script([sys.executable, script, output_root, str(PLUGIN_ROOT)])
    return {"success": ok, "output": out, "error": err if not ok else None}


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
    return _maybe_save_json(load_context_mod.load_context(output_root), "synthesis-context")


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
    script = str(SKILLS_ROOT / "generate-report" / "scripts" / "generate-report.py")
    ok, out, err = _run_script([sys.executable, script, data_dir, report_dir])
    return {
        "success": ok,
        "md_path": str(Path(report_dir) / "report.md") if ok else None,
        "html_path": str(Path(report_dir) / "report.html") if ok else None,
        "error": err if not ok else None,
    }


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
    script = str(SKILLS_ROOT / "plan" / "scripts" / "validate-arch.py")
    schema = str(SKILLS_ROOT / "plan" / "arch.schema.json")
    ok, out, err = _run_script([sys.executable, script, arch_path, "--schema", schema])
    return {"valid": ok, "output": out, "errors": err if not ok else None}


# ---------------------------------------------------------------------------
# Tool: split_implementation_plan
# ---------------------------------------------------------------------------

@server.tool(
    name="split_implementation_plan",
    description="Split implementation-plan.json into dependency-level chunks for parallel code agents.",
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
    ok, out, err = _run_script([sys.executable, script, plan_path, "--output-dir", output_dir])
    chunks = sorted(Path(output_dir).glob("*.json")) if ok else []
    return {
        "success": ok,
        "chunks": [str(c) for c in chunks],
        "count": len(chunks),
        "error": err if not ok else None,
    }


# ---------------------------------------------------------------------------
# Tool: search_codebase
# ---------------------------------------------------------------------------

_SKIP_DIRS = {".git", ".build", "build", "DerivedData", "Pods", "node_modules", ".solid_coder"}
_SPEC_RE = re.compile(r'^SPEC-\d+$', re.IGNORECASE)
_TYPE_DECL = re.compile(r'\b(class|struct|protocol|enum|typealias|actor)\s+(\w+)')
_IMPORT_DECL = re.compile(r'^import\s+(\w+)')
_COMMENT_STRIP = re.compile(r'^[/\*#\s]+')


def _extract_plan_terms(plan_path: Path) -> tuple[list, list]:
    """Extract search terms and spec numbers from arch.json or implementation-plan.json."""
    try:
        data = json.loads(plan_path.read_text(encoding="utf-8"))
    except Exception:
        return [], []
    terms, specs = [], []
    for comp in data.get("components", []):
        for key in ("name", "category"):
            v = comp.get(key, "")
            if v:
                terms.append(v)
        for iface in comp.get("interfaces", []) + comp.get("dependencies", []):
            terms.append(iface)
        terms.extend(comp.get("stack", []))
    for item in data.get("plan_items", []):
        if item.get("component"):
            terms.append(item["component"])
    if data.get("spec_number"):
        specs.append(data["spec_number"])
    return list(dict.fromkeys(t for t in terms if t)), specs


def _frontmatter_fields(lines: list) -> dict:
    """Extract solid-* frontmatter fields from file lines."""
    result = {"description": "", "tags": set(), "specs": set()}
    for line in lines:
        inner = _COMMENT_STRIP.sub("", line).strip()
        low = inner.lower()
        if low.startswith("solid-description:"):
            result["description"] = inner[len("solid-description:"):].strip()
        elif low.startswith("solid-tags:"):
            raw = inner[len("solid-tags:"):].strip().strip("[]")
            result["tags"].update(t.strip().lower() for t in re.split(r"[,\s]+", raw) if t.strip())
        elif low.startswith("solid-spec:"):
            raw = inner[len("solid-spec:"):].strip().strip("[]")
            result["specs"].update(s.strip().upper() for s in re.split(r"[,\s]+", raw) if s.strip())
    return result


def _match_file(filepath: Path, tags_lower: set, spec_numbers: set, min_matches: int):
    try:
        lines = filepath.read_text(encoding="utf-8", errors="replace").splitlines()
    except OSError:
        return None

    fm = _frontmatter_fields(lines)

    # Spec match — always passes regardless of min_matches
    matched_specs = sorted(fm["specs"] & spec_numbers) if spec_numbers else []
    if matched_specs:
        return {"path": str(filepath), "description": fm["description"], "matched_specs": matched_specs}

    if not tags_lower:
        return None

    hits = 0

    # 1. Description words
    if fm["description"]:
        desc_words = {w.lower() for w in re.split(r"\W+", fm["description"]) if w}
        hits += len(desc_words & tags_lower)

    # 2. solid-tags field
    if fm["tags"]:
        hits += len(fm["tags"] & tags_lower)

    # 3. Imports
    for line in lines:
        m = _IMPORT_DECL.match(line.strip())
        if m and m.group(1).lower() in tags_lower:
            hits += 1

    if hits < min_matches:
        return None

    return {"path": str(filepath), "description": fm["description"]}


@server.tool(
    name="search_codebase",
    description=(
        "Search codebase for reusable types before creating new ones. "
        "Pass plan_path to auto-extract structural terms (component names, interfaces, categories, spec numbers). "
        "Pass tags with LLM-generated semantic synonyms from component responsibilities "
        "(e.g. 'fetch' → ['retrieve', 'load', 'pull']). "
        "Matches each file against: solid-description words, solid-tags frontmatter, and import statements. "
        "Returns a compact list of file paths with descriptions — read the description to assess relevance, "
        "use the Read tool to inspect the full source."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "sources_dir": {"type": "string", "description": "Root directory to search"},
            "plan_path": {"type": "string", "description": "Path to arch.json or implementation-plan.json. Auto-extracts component names, interfaces, and spec numbers."},
            "tags": {"type": "array", "items": {"type": "string"}, "description": "Search terms matched against solid-description words, solid-tags frontmatter, and imports. SPEC-NNN entries are automatically routed to spec number matching. Merged with auto-extracted terms from plan_path."},
            "spec_numbers": {"type": "array", "items": {"type": "string"}, "description": "Spec numbers to match against solid-spec frontmatter"},
            "min_matches": {"type": "integer", "description": "Minimum combined hits (description words + tags + imports) required per file (default: 3). Spec matches always pass."},
        },
        "required": ["sources_dir"],
    },
)
def search_codebase(sources_dir, plan_path=None, tags=None, spec_numbers=None, min_matches=3):
    sources = Path(sources_dir)
    if not sources.is_dir():
        return f"Error: sources_dir not found: {sources_dir}"

    auto_terms, auto_specs = [], []
    if plan_path:
        auto_terms, auto_specs = _extract_plan_terms(Path(plan_path))

    # Separate spec numbers from tags — both can be passed in the tags list
    all_tags = set()
    all_specs = set(s.upper() for s in ((spec_numbers or []) + auto_specs) if s)
    for t in (tags or []) + auto_terms:
        if not t:
            continue
        if _SPEC_RE.match(t):
            all_specs.add(t.upper())
        else:
            all_tags.add(t.lower())

    if not all_tags and not all_specs:
        return "Error: provide plan_path, tags, or spec_numbers to search."

    matches = []
    total = 0
    for filepath in sources.rglob("*"):
        if not filepath.is_file():
            continue
        if any(part in _SKIP_DIRS for part in filepath.parts):
            continue
        total += 1
        match = _match_file(filepath, all_tags, all_specs, min_matches)
        if match:
            matches.append(match)

    if not matches:
        return f"No files matched in {sources_dir} ({total} files scanned)."

    lines = [
        f"Codebase files matching your search ({len(matches)} of {total} scanned).",
        "Review descriptions to assess relevance. Use the Read tool to inspect any file in full.",
        "",
    ]
    for m in matches:
        desc = m.get("description", "")
        spec_tag = f"  [{', '.join(m['matched_specs'])}]" if m.get("matched_specs") else ""
        lines.append(f"{m['path']}{spec_tag}" + (f" — {desc}" if desc else ""))

    return _maybe_chunk("\n".join(lines), "search-results")


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
    script = str(SKILLS_ROOT / "prepare-review-input" / "scripts" / "prepare-changes.py")
    ok, out, err = _run_script([sys.executable, script])
    if not ok:
        return {"error": err}
    try:
        data = json.loads(out)
        data["candidate_tags"] = candidate_tags or []
        return data
    except json.JSONDecodeError:
        return {"error": f"Could not parse script output: {out}"}


if __name__ == "__main__":
    server.run()
