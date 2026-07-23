#!/usr/bin/env python3
"""solid-coder pipeline MCP server.

Architecture:
  ApplicationBootstrapper — SRP Facade, protocol-typed deps, pure delegation.
  make_bootstrapper()     — Composition root: wires production defaults, all deps injectable.
  main()                  — Entry point; calls the factory and runs.
"""

import dataclasses
import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Protocol

SERVER_DIR = Path(__file__).resolve().parent
MCP_DIR = SERVER_DIR.parent
PLUGIN_ROOT = MCP_DIR.parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"

sys.path.insert(0, str(MCP_DIR))
sys.path.insert(0, str(SKILLS_ROOT / "validate-findings" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "synthesize-fixes" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "prepare-review-input" / "scripts"))

from protocol import MCPServer
from pipeline.skill_runner import SkillRunning, ResultFormatting, SkillRunner, SkillResultFormatter
from pipeline.tool_registry import ToolRegistering, ToolRegistry
from pipeline.handlers import ReviewResultsCollector, make_review_results_collector
from pipeline.interfaces import ReviewResultsCollecting
from lib.gateway_tools import make_gateway_handler as _make_gw_pipeline
from common.mcp_meta import LARGE_OUTPUT
from harness.flow_run_orchestrating import FlowRunOrchestrating
from pipeline.output_path_factory import OutputPathFactory


# ── Service protocols ─────────────────────────────────────────────────────────

class CheckSeverityRunning(Protocol):
    def check_severity(self, output_root: str) -> dict: ...


class ContextLoading(Protocol):
    def load_context(self, output_root: str) -> dict: ...


class OutputValidating(Protocol):
    def validate_json(self, json_path: str, schema_path: str) -> dict: ...


class CodebaseSearching(Protocol):
    def search(
        self,
        sources_dir: Optional[str] = None,
        plan_path: Optional[str] = None,
        tags: Optional[list] = None,
        spec_numbers: Optional[list] = None,
        min_matches: int = 3,
    ) -> Any: ...


class GatewayHandling(Protocol):
    def submit_findings(self, partial_output: dict, output_path: str) -> dict: ...
    def submit_batch_findings(self, output_dir: str, submissions: dict) -> dict: ...
    def submit_fix(self, output_dir: str, fixes: list) -> dict: ...


class MCPServerRunning(Protocol):
    def run(self) -> None: ...


# ── Path provider ─────────────────────────────────────────────────────────────

def get_output_path(operation: str, spec_number: str = "") -> dict:
    """Compute the standardized home-dir output path for a solid-coder operation.

    Reads CLAUDE_PROJECT_DIR from the environment (set by Claude Code) and
    derives a Claude-style slug by replacing '/' with '-'. Returns the
    absolute output_root the caller should use as OUTPUT_ROOT.

    Args:
        operation:   "review" | "refactor" | "implement" | "validate-spec" | "health"
        spec_number: For implement only — e.g. "SPEC-042". Omit for other ops.
    """
    return OutputPathFactory().compute(operation, spec_number)


# ── Shared tool callables ─────────────────────────────────────────────────────

def _build_tool_callables(
    runner: SkillRunning,
    fmt: ResultFormatting,
    search: CodebaseSearching,
    check_sev: CheckSeverityRunning,
    ctx: ContextLoading,
    validate: OutputValidating,
    gw: GatewayHandling,
    collector: ReviewResultsCollecting,
) -> dict:
    """Build the complete pipeline tool callable dict.

    Single source of truth for tool implementations. Used by both
    ApplicationBootstrapper (MCP registration) and get_pipeline_tools (CLI access).
    """

    def _prepare_input(candidate_tags=None):
        ok, out, err = runner.execute("prepare-review-input", "prepare-changes.py", [])
        if not ok:
            return {"error": err}
        try:
            data = json.loads(out)
            data["candidate_tags"] = candidate_tags or []
            return data
        except json.JSONDecodeError:
            return {"error": f"Could not parse script output: {out}"}

    def _run_and_format(skill: str, script: str, args: list, build_extra) -> dict:
        """Runs a skill script and formats the result, delegating tool-specific
        extra fields to build_extra(ok, out, err)."""
        ok, out, err = runner.execute(skill, script, args)
        extra = build_extra(ok, out, err)
        return fmt.format(ok, err, **extra)

    def _split_plan(plan_path, output_dir, arch_path=None):
        args = [plan_path, "--output-dir", output_dir]
        if arch_path:
            args += ["--arch", arch_path]

        def _extra(ok, out, err):
            chunks = sorted(Path(output_dir).glob("*.json")) if ok else []
            return {"success": ok, "chunks": [str(c) for c in chunks], "count": len(chunks)}

        return _run_and_format("synthesize-implementation", "split-plan.py", args, _extra)

    def _generate_report(data_dir, report_dir=None):
        report_dir = report_dir or data_dir

        def _extra(ok, out, err):
            md = str(Path(report_dir) / "report.md") if ok else None
            html = str(Path(report_dir) / "report.html") if ok else None
            return {"success": ok, "md_path": md, "html_path": html}

        return _run_and_format("generate-report", "generate-report.py", [data_dir, report_dir], _extra)

    def _validate_arch(arch_path):
        schema = str(SKILLS_ROOT / "plan" / "arch.schema.json")
        return _run_and_format(
            "plan", "validate-arch.py", [arch_path, "--schema", schema],
            lambda ok, out, err: {"valid": ok, "output": out, "errors": err if not ok else None},
        )

    def _validate_findings(output_root):
        return _run_and_format(
            "validate-findings", "validate-findings.py", [output_root, str(PLUGIN_ROOT)],
            lambda ok, out, err: {"success": ok, "output": out},
        )

    def _search_fn(sources_dir=None, plan_path=None, tags=None, spec_numbers=None, min_matches=3):
        return search.search(
            sources_dir=sources_dir, plan_path=plan_path, tags=tags,
            spec_numbers=spec_numbers, min_matches=min_matches,
        )

    return {
        "collect_review_results": collector.collect,
        "check_severity": check_sev.check_severity,
        "validate_findings": _validate_findings,
        "load_synthesis_context": ctx.load_context,
        "generate_report": _generate_report,
        "validate_architecture": _validate_arch,
        "split_implementation_plan": _split_plan,
        "search_codebase": _search_fn,
        "prepare_review_input": _prepare_input,
        "validate_phase_output": validate.validate_json,
        "submit_findings": gw.submit_findings,
        "submit_batch_findings": gw.submit_batch_findings,
        "submit_fix": gw.submit_fix,
        "get_output_path": get_output_path,
    }


def _build_flow_callables(flow_run: FlowRunOrchestrating) -> dict:
    """Build flow tool callables that delegate to FlowRunOrchestrating."""

    def _flow_start(flow: str, params: Optional[dict] = None) -> dict:
        return dataclasses.asdict(flow_run.flow_start(flow, params))

    def _flow_next(outputs: Optional[dict] = None) -> dict:
        return dataclasses.asdict(flow_run.flow_next(outputs))

    def _flow_status() -> dict:
        return dataclasses.asdict(flow_run.flow_status())

    return {
        "flow_start": _flow_start,
        "flow_next": _flow_next,
        "flow_status": _flow_status,
    }


# ── Application facade ────────────────────────────────────────────────────────

class ApplicationBootstrapper:
    """Wires pipeline services into MCP tools and runs the server.

    Facade: all dependencies are protocol-typed and injected. No internal
    construction — satisfies SRP Facade exception (pure coordination).
    Use make_bootstrapper() for production defaults.
    """

    def __init__(
        self,
        server: MCPServerRunning,
        registry: ToolRegistering,
        skill_runner: SkillRunning,
        result_fmt: ResultFormatting,
        collector: ReviewResultsCollecting,
        gateway: GatewayHandling,
        check_severity: CheckSeverityRunning,
        load_context: ContextLoading,
        validate_output: OutputValidating,
        search: CodebaseSearching,
        flow_run: Optional[FlowRunOrchestrating] = None,
    ) -> None:
        self._server = server
        self._registry = registry
        self._runner = skill_runner
        self._fmt = result_fmt
        self._collector = collector
        self._gw = gateway
        self._check_sev = check_severity
        self._ctx = load_context
        self._validate = validate_output
        self._search = search
        self._flow_run = flow_run

    def run(self) -> None:
        self._register_all_tools()
        self._server.run()

    def _register_all_tools(self) -> None:
        reg = self._registry
        tools = _build_tool_callables(
            self._runner, self._fmt, self._search,
            self._check_sev, self._ctx, self._validate,
            self._gw, self._collector,
        )

        reg.register("collect_review_results",
                     "Collect and summarise all review outputs. Returns verdict (ALL_COMPLIANT|MINOR_ONLY|HAS_SEVERE), summary table, and minor_findings.",
                     {"type": "object", "properties": {"output_root": {"type": "string"}}, "required": ["output_root"]},
                     tools["collect_review_results"], meta=LARGE_OUTPUT)

        reg.register("check_severity",
                     "Check review findings for SEVERE violations. Returns structured verdict.",
                     {"type": "object", "properties": {"output_root": {"type": "string"}}, "required": ["output_root"]},
                     tools["check_severity"])

        reg.register("validate_findings",
                     "Filter findings to changed line ranges and reorganize by file. Writes by-file/*.output.json.",
                     {"type": "object", "properties": {"output_root": {"type": "string"}}, "required": ["output_root"]},
                     tools["validate_findings"])

        reg.register("load_synthesis_context",
                     "Load all validated findings for synthesis. Returns per-principle summaries and severity counts.",
                     {"type": "object", "properties": {"output_root": {"type": "string"}}, "required": ["output_root"]},
                     tools["load_synthesis_context"], meta=LARGE_OUTPUT)

        reg.register("generate_report",
                     "Generate MD + HTML reports from validated findings and synthesized fix plans.",
                     {"type": "object", "properties": {
                         "data_dir": {"type": "string"},
                         "report_dir": {"type": "string"},
                     }, "required": ["data_dir"]},
                     tools["generate_report"])

        reg.register("validate_architecture",
                     "Validate arch.json structure and semantic SOLID constraints.",
                     {"type": "object", "properties": {"arch_path": {"type": "string"}}, "required": ["arch_path"]},
                     tools["validate_architecture"])

        reg.register("split_implementation_plan",
                     "Split implementation-plan.json into semantically grouped chunks.",
                     {"type": "object", "properties": {
                         "plan_path": {"type": "string"},
                         "output_dir": {"type": "string"},
                         "arch_path": {"type": "string"},
                     }, "required": ["plan_path", "output_dir"]},
                     tools["split_implementation_plan"])

        reg.register("search_codebase",
                     "Search the codebase for reusable types and existing implementations by solid-frontmatter tags.",
                     {"type": "object", "properties": {
                         "sources_dir": {"type": "string"},
                         "plan_path": {"type": "string"},
                         "tags": {"type": "array", "items": {"type": "string"}},
                         "spec_numbers": {"type": "array", "items": {"type": "string"}},
                         "min_matches": {"type": "integer"},
                     }, "required": []},
                     tools["search_codebase"], meta=LARGE_OUTPUT)

        reg.register("prepare_review_input",
                     "Prepare git changes (staged, unstaged, untracked) into structured review-input.json.",
                     {"type": "object", "properties": {
                         "candidate_tags": {"type": "array", "items": {"type": "string"}},
                     }},
                     tools["prepare_review_input"])

        reg.register("submit_findings",
                     "Score a partial review output for one principle via severity-bands in rule.md and write review-output.json. LLM provides metrics; server fills scoring and findings.",
                     {"type": "object", "properties": {
                         "partial_output": {"type": "object"},
                         "output_path": {"type": "string"},
                     }, "required": ["partial_output", "output_path"]},
                     tools["submit_findings"])

        _unit_schema = {
            "type": "object",
            "required": ["unit_name", "unit_kind", "metrics"],
            "properties": {
                "unit_name": {"type": "string"},
                "unit_kind": {"type": "string", "enum": ["class", "struct", "enum", "protocol", "extension", "actor", "function"]},
                "line_start": {"type": "integer"},
                "line_end": {"type": "integer"},
                "metrics": {
                    "type": "object",
                    "description": "Keys are principle names (e.g. 'SRP'). Each value is an object of metric_var: {value: N}.",
                    "additionalProperties": {"type": "object"},
                },
            },
        }
        _submission_schema = {
            "type": "object",
            "required": ["timestamp", "files"],
            "properties": {
                "timestamp": {"type": "string", "format": "date-time"},
                "files": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["units"],
                        "properties": {
                            "units": {"type": "array", "items": _unit_schema},
                        },
                    },
                },
            },
        }
        reg.register("submit_batch_findings",
                     "Submit findings for all reviewed principles in one unified payload. Discovers principle keys from metrics, scores each, writes output_dir/{principle}/review-output.json.",
                     {"type": "object", "properties": {
                         "output_dir": {"type": "string"},
                         "submissions": {
                             "type": "object",
                             "description": "Map of principle_name to review-output payload (references/review-output.schema.json). E.g. {'SRP': {timestamp, files:[{units:[{unit_name, unit_kind, metrics:{SRP:{verb_count:{value:3}}}}]}]}}",
                             "additionalProperties": _submission_schema,
                         },
                     }, "required": ["output_dir", "submissions"]},
                     tools["submit_batch_findings"])

        reg.register("submit_fix",
                     "Submit concrete fixes for ALL SEVERE violations in one call.",
                     {"type": "object", "properties": {
                         "output_dir": {"type": "string"},
                         "fixes": {
                             "type": "array",
                             "items": {
                                 "type": "object",
                                 "required": ["rule_id", "file_path", "unit_name", "suggested_fix"],
                             },
                         },
                     }, "required": ["output_dir", "fixes"]},
                     tools["submit_fix"])

        reg.register("validate_phase_output",
                     "Validate a JSON file against a JSON schema.",
                     {"type": "object", "properties": {
                         "json_path": {"type": "string"},
                         "schema_path": {"type": "string"},
                     }, "required": ["json_path", "schema_path"]},
                     self._validate.validate_json)

        reg.register("get_output_path",
                     "Compute the standardized home-dir output path for a solid-coder operation. "
                     "Reads CLAUDE_PROJECT_DIR from env, derives Claude-style project slug, returns timestamped output_root.",
                     {"type": "object", "properties": {
                         "operation": {"type": "string", "enum": ["review", "refactor", "implement", "validate-spec"]},
                         "spec_number": {"type": "string"},
                     }, "required": ["operation"]},
                     tools["get_output_path"])

        if self._flow_run is not None:
            self._register_flow_tools(self._flow_run)

    def _register_flow_tools(self, flow_run: FlowRunOrchestrating) -> None:
        flow_tools = _build_flow_callables(flow_run)
        reg = self._registry

        reg.register(
            "flow_start",
            "Start the DAG state machine for a flow: creates a new run, writes active.json, and returns the "
            "first ready step(s) with their prompts. Call flow_next after each step to advance the machine "
            "through its states until status is 'done' or 'timed_out'. Only one run can be active at a time.",
            {
                "type": "object",
                "properties": {
                    "flow": {
                        "type": "string",
                        "description": (
                            "Flow name — matches the YAML file's name, e.g. 'code_review' means "
                            "'code_review.yaml'. Resolved against '<project>/.solid-coder/harness/flows/"
                            "<name>.yaml' first, then the plugin's bundled harness/flows/<name>.yaml. "
                            "A direct path to a flow YAML file also works if no name match is found."
                        ),
                    },
                    "params": {
                        "type": "object",
                        "description": (
                            "Optional key/value inputs for this run, available to step prompts via '{{params.<key>}}'."
                        ),
                    },
                },
                "required": ["flow"],
            },
            flow_tools["flow_start"],
        )

        reg.register(
            "flow_next",
            "Submit the outputs for the step(s) you were just given and get the next ready step(s). The steps "
            "are deterministic — fixed by the flow's YAML file, not decided by you — so always follow the "
            "returned prompt(s) exactly rather than improvising or skipping ahead. Operates on the single "
            "active run (no run id needed) — call this in a loop, once per completed step, until status is "
            "'done' or 'timed_out'.",
            {
                "type": "object",
                "properties": {
                    "outputs": {
                        "type": "object",
                        "description": (
                            "Map of instance_id (from the 'steps[].instance_id' you were given by flow_start/"
                            "flow_next) to that step's output values, keyed by output name as declared in the "
                            "step's 'outputs:' spec in the flow YAML. Omit a step's key, or pass '{}', if it "
                            "declares no outputs."
                        ),
                    },
                },
            },
            flow_tools["flow_next"],
        )

        reg.register(
            "flow_status",
            "Read the state of the currently active flow run without side effects — no arguments. Returns the flow "
            "name, run id, status ('in_progress'/'done'/'timed_out'/'no_active_run'), completed/running/pending "
            "step ids, and turn counts.",
            {
                "type": "object",
                "properties": {},
            },
            flow_tools["flow_status"],
        )


# ── Composition root and entry point ─────────────────────────────────────────

def make_bootstrapper(
    server: Optional[MCPServerRunning] = None,
    registry: Optional[ToolRegistering] = None,
    skill_runner: Optional[SkillRunning] = None,
    result_fmt: Optional[ResultFormatting] = None,
    collector: Optional[ReviewResultsCollecting] = None,
    gateway: Optional[GatewayHandling] = None,
    check_severity: Optional[CheckSeverityRunning] = None,
    load_context: Optional[ContextLoading] = None,
    validate_output: Optional[OutputValidating] = None,
    search: Optional[CodebaseSearching] = None,
    refs_root: Path = PLUGIN_ROOT / "references",
    flow_run: Optional[FlowRunOrchestrating] = None,
) -> ApplicationBootstrapper:
    """Composition root: all dependencies injectable; production defaults applied when omitted."""
    if flow_run is None:
        from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
        from harness.runs_base_dir_resolver import RunsBaseDirResolver

        flow_run = FlowRunOrchestratorFactory(base_dir_resolver=RunsBaseDirResolver()).build()

    mcp = server or MCPServer("solid-coder-pipeline", "1.0.0")
    return ApplicationBootstrapper(
        server=mcp,
        registry=registry or ToolRegistry(mcp),
        skill_runner=skill_runner or SkillRunner(SKILLS_ROOT),
        result_fmt=result_fmt or SkillResultFormatter(),
        collector=collector or make_review_results_collector(),
        gateway=gateway or _make_gw_pipeline(refs_root),
        check_severity=check_severity or importlib.import_module("check-severity"),
        load_context=load_context or importlib.import_module("load-context"),
        validate_output=validate_output or importlib.import_module("validate-output"),
        search=search or importlib.import_module("search.codebase_searcher"),
        flow_run=flow_run,
    )


def get_pipeline_tools() -> dict:
    """Return pipeline tool callables keyed by name, for CLI/script access.

    Delegates to make_bootstrapper to avoid duplicating construction logic.
    """
    b = make_bootstrapper()
    return _build_tool_callables(
        b._runner, b._fmt, b._search,
        b._check_sev, b._ctx, b._validate,
        b._gw, b._collector,
    )


def main() -> None:
    make_bootstrapper().run()


if __name__ == "__main__":
    main()
