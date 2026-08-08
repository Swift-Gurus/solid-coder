#!/usr/bin/env python3
"""solid-coder pipeline MCP server.

Architecture:
  ApplicationBootstrapper — SRP Facade, protocol-typed deps, pure delegation.
  make_bootstrapper()     — Composition root: wires production defaults, all deps injectable.
  main()                  — Entry point; calls the factory and runs.
"""

import importlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

SERVER_DIR = Path(__file__).resolve().parent
MCP_DIR = SERVER_DIR.parent
PLUGIN_ROOT = MCP_DIR.parent
SKILLS_ROOT = PLUGIN_ROOT / "skills"
HEALTH_CONFIG_DIR = MCP_DIR / "health" / "config"

sys.path.insert(0, str(MCP_DIR))
sys.path.insert(0, str(HEALTH_CONFIG_DIR))
sys.path.insert(0, str(SKILLS_ROOT / "validate-findings" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "synthesize-fixes" / "scripts"))
sys.path.insert(0, str(SKILLS_ROOT / "prepare-review-input" / "scripts"))

from mcp_server_factory import MCPServerFactory
from message_transport_running import MessageTransportRunning
from pipeline.skill_runner import SkillRunning, ResultFormatting, SkillRunner, SkillResultFormatter
from pipeline.tool_registry import ToolRegistering, ToolRegistry
from pipeline.handlers import ReviewResultsCollector, make_review_results_collector
from pipeline.interfaces import ReviewResultsCollecting
from lib.gateway_tools import make_gateway_handler as _make_gw_pipeline
from findings.gateway_handler import GatewayHandling
from common.mcp_meta import LARGE_OUTPUT
from harness.flow_result_json_renderer import FlowResultJsonRenderer
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_result_renderer import FlowResultRenderer
from harness.flow_result_renderer_selector import FlowResultRendererSelector
from harness.flow_run_orchestrating import FlowRunOrchestrating
from health.dry_search_service_factory import DrySearchServiceFactory
from pipeline.check_severity_running import CheckSeverityRunning
from pipeline.context_loading import ContextLoading
from pipeline.flow_tool_callables_assembler import FlowToolCallablesAssembler
from pipeline.output_path_factory import OutputPathFactory
from pipeline.output_validating import OutputValidating
from pipeline.pipeline_tool_callables_assembler import PipelineToolCallablesAssembler
from pipeline.tool_callables_building import ToolCallablesBuilding
from search.tag_codebase_searching import TagCodebaseSearching


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


# ── Application facade ────────────────────────────────────────────────────────

"""
solid-name: ApplicationBootstrapper
solid-category: service
solid-description: Bootstraps and runs the pipeline tool application.
"""
class ApplicationBootstrapper:
    """Wires pipeline services into MCP tools and runs the server.

    Facade: all dependencies are protocol-typed and injected. No internal
    construction — satisfies SRP Facade exception (pure coordination).
    Use make_bootstrapper() for production defaults.
    """

    def __init__(
        self,
        server: MessageTransportRunning,
        registry: ToolRegistering,
        tool_callables: ToolCallablesBuilding,
        flow_callables: Optional[ToolCallablesBuilding] = None,
    ) -> None:
        self._server = server
        self._registry = registry
        self._tool_callables = tool_callables
        self._flow_callables = flow_callables

    def run(self) -> None:
        self._register_all_tools()
        self._server.run()

    def _register_all_tools(self) -> None:
        reg = self._registry
        tools = self._tool_callables.build()

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
                     "Search for reusable implementations and record successful health-check DRY-search completion.",
                     {"type": "object", "properties": {
                         "sources_dir": {"type": "string"},
                         "plan_path": {"type": "string"},
                         "query": {
                             "type": "string",
                             "description": "Space-separated type-name, responsibility, and synonym terms.",
                         },
                         "tags": {
                             "type": "array",
                             "items": {"type": "string"},
                             "description": (
                                 "Each array item MUST be exactly one search term containing no spaces. "
                                 "Never put an aggregated query in tags; use query for space-separated input."
                             ),
                         },
                         "spec_numbers": {"type": "array", "items": {"type": "string"}},
                         "min_matches": {"type": "integer"},
                         "output_dir": {
                             "type": "string",
                             "description": "Required during health checks; use the output_dir from the prompt.",
                         },
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
                     tools["validate_phase_output"])

        reg.register("get_output_path",
                     "Compute the standardized home-dir output path for a solid-coder operation. "
                     "Reads CLAUDE_PROJECT_DIR from env, derives Claude-style project slug, returns timestamped output_root.",
                     {"type": "object", "properties": {
                         "operation": {"type": "string", "enum": ["review", "refactor", "implement", "validate-spec"]},
                         "spec_number": {"type": "string"},
                     }, "required": ["operation"]},
                     tools["get_output_path"])

        if self._flow_callables is not None:
            self._register_flow_tools()

    def _register_flow_tools(self) -> None:
        if self._flow_callables is None:
            return
        flow_tools = self._flow_callables.build()
        reg = self._registry

        reg.register(
            "flow_start",
            "TRIGGER when the user asks to run, start, or execute a workflow or flow by name (e.g. 'run "
            "workflow <name>', 'execute the <name> flow', 'start flow <name>') — this is how such requests are "
            "fulfilled, not by improvising the steps yourself. Start the DAG state machine for a flow: creates "
            "a new run and returns the first ready step(s) as "
            "plain text. Each returned block starts with 'id: <instance_id>' followed by the step's prompt; if "
            "the step declares outputs, the exact JSON Schema each submitted value must match is stated in that "
            "prompt — follow it precisely, since a wrong-shaped submission is rejected and costs a retry "
            "attempt. A block starting with 'Launch a subagent with the following prompt:' means spawn a "
            "subagent to handle it rather than doing it yourself; that prompt will tell you to pass "
            "isolated=true — do so exactly as instructed. Call flow_next after each step to advance until you "
            "see 'Flow complete.' Only one main run can be active at a time; pass isolated=true only when a "
            "step's rendered instruction told you to.",
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
                    "isolated": {
                        "type": "boolean",
                        "description": (
                            "Only pass true when a step's rendered instruction explicitly told you to. Starts "
                            "this run in its own isolated slot instead of the single main-session run, so it "
                            "doesn't collide with a run already in progress. The response will disclose a "
                            "run_id — pass that same run_id to every later flow_next/flow_status call for this run."
                        ),
                    },
                },
                "required": ["flow"],
            },
            flow_tools["flow_start"],
        )

        reg.register(
            "flow_next",
            "Submit your output values for the step(s) you were just instructed to complete, keyed by the "
            "'id: <instance_id>' each one gave you — each value must match the schema stated in that step's "
            "prompt exactly, or the submission is rejected. Get it right the first time; a rejected submission "
            "wastes a turn. The response is plain text: either the next step(s) to work on, a block starting "
            "with 'Rejected:' explaining exactly what was wrong (retry the same step with a corrected value), "
            "or a terminal message ('Flow complete.', or 'Flow failed...'/'Flow timed out...' naming the step, "
            "why it failed, and the run log path). On a terminal failure/timeout: stop — do not retry or start "
            "another attempt, report it to the user verbatim, and wait for their instructions. Operates on the "
            "single main run unless you were given a run_id (see flow_start's "
            "isolated=true response) — call this in a loop, once per completed step.",
            {
                "type": "object",
                "properties": {
                    "outputs": {
                        "type": "object",
                        "description": (
                            "Map of instance_id (the value after 'id: ' on each block you were given by "
                            "flow_start/flow_next) to that step's output values, keyed by output name as stated "
                            "in that step's prompt. Omit a step's key, or pass '{}', if its prompt declares no "
                            "outputs."
                        ),
                    },
                    "run_id": {
                        "type": "string",
                        "description": (
                            "Only needed if flow_start disclosed a run_id (isolated=true was used to start this "
                            "run). Omit entirely for the single main-session run."
                        ),
                    },
                },
            },
            flow_tools["flow_next"],
        )

        reg.register(
            "flow_status",
            "Read the state of a flow run without side effects. Returns the flow name, run id, status "
            "('in_progress'/'done'/'timed_out'/'no_active_run'), completed/running/pending step ids, and turn "
            "counts.",
            {
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": (
                            "Only needed if flow_start disclosed a run_id (isolated=true was used to start this "
                            "run). Omit entirely to read the single main-session run."
                        ),
                    },
                },
            },
            flow_tools["flow_status"],
        )

        reg.register(
            "flow_clear_lock",
            "Clears a stuck run's lock so flow_start can proceed again. This is for the specific case "
            "where flow_status shows a run left behind by a DIFFERENT, no-longer-running session — not "
            "a workaround for a blocked flow_next in your own current run. If flow_next or the Stop hook "
            "is telling you to keep going, do that instead; do not call this to escape a pending step. "
            "Requires the exact run_id from flow_status to confirm you're clearing the run you intend "
            "to. Does not delete the run's event log — only the lock.",
            {
                "type": "object",
                "properties": {
                    "run_id": {
                        "type": "string",
                        "description": "Exact run_id from a prior flow_status call.",
                    },
                },
                "required": ["run_id"],
            },
            flow_tools["flow_clear_lock"],
        )


# ── Composition root and entry point ─────────────────────────────────────────

def make_bootstrapper(
    server: Optional[MessageTransportRunning] = None,
    registry: Optional[ToolRegistering] = None,
    skill_runner: Optional[SkillRunning] = None,
    result_fmt: Optional[ResultFormatting] = None,
    collector: Optional[ReviewResultsCollecting] = None,
    gateway: Optional[GatewayHandling] = None,
    check_severity: Optional[CheckSeverityRunning] = None,
    load_context: Optional[ContextLoading] = None,
    validate_output: Optional[OutputValidating] = None,
    search: Optional[TagCodebaseSearching] = None,
    refs_root: Path = PLUGIN_ROOT / "references",
    flow_run: Optional[FlowRunOrchestrating] = None,
    flow_result_renderer: Optional[FlowResultRendering] = None,
) -> ApplicationBootstrapper:
    """Composition root: all dependencies injectable; production defaults applied when omitted."""
    mcp = server or MCPServerFactory().build("solid-coder-pipeline", "1.0.0")

    if flow_run is None:
        from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
        from harness.mcp_request_context_session_reader import McpRequestContextSessionReader
        from harness.runs_base_dir_resolver import RunsBaseDirResolver

        flow_run = FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(),
            plugin_root=PLUGIN_ROOT,
            session_reader=McpRequestContextSessionReader(call_meta_provider=mcp),
        ).build()

    if flow_result_renderer is None:
        from hc_config_schema import load_config

        selector = FlowResultRendererSelector(
            plain_text_renderer=FlowResultRenderer(),
            json_renderer=FlowResultJsonRenderer(),
        )
        flow_result_renderer = selector.select(load_config().feature_flags.flow_plain_text_response)

    runner_service = skill_runner or SkillRunner(SKILLS_ROOT)
    formatter_service = result_fmt or SkillResultFormatter()
    collector_service = collector or make_review_results_collector()
    gateway_service = gateway or _make_gw_pipeline(
        refs_root,
        DrySearchServiceFactory(),
    )
    check_severity_service = check_severity or importlib.import_module("check-severity")
    context_service = load_context or importlib.import_module("load-context")
    validation_service = validate_output or importlib.import_module("validate-output")
    search_service = search or importlib.import_module("search.codebase_searcher")
    tool_callables = PipelineToolCallablesAssembler(
        runner=runner_service,
        formatter=formatter_service,
        dry_search=DrySearchServiceFactory().make_search(search_service),
        collect_review_results=collector_service.collect,
        check_severity=check_severity_service.check_severity,
        load_context=context_service.load_context,
        validate_json=validation_service.validate_json,
        submit_findings=gateway_service.submit_findings,
        submit_batch_findings=gateway_service.submit_batch_findings,
        submit_fix=gateway_service.submit_fix,
        output_path=OutputPathFactory(),
        skills_root=SKILLS_ROOT,
        plugin_root=PLUGIN_ROOT,
    )

    return ApplicationBootstrapper(
        server=mcp,
        registry=registry or ToolRegistry(mcp),
        tool_callables=tool_callables,
        flow_callables=FlowToolCallablesAssembler(
            flow_run=flow_run,
            result_renderer=flow_result_renderer,
        ),
    )


def get_pipeline_tools() -> dict:
    """Return pipeline tool callables keyed by name, for CLI/script access.

    Delegates to make_bootstrapper to avoid duplicating construction logic.
    """
    bootstrapper = make_bootstrapper()
    return bootstrapper._tool_callables.build()


def main() -> None:
    make_bootstrapper().run()


if __name__ == "__main__":
    main()
