#!/usr/bin/env python3
"""solid-coder pipeline MCP server.

Architecture:
  ApplicationBootstrapper — SRP Facade, protocol-typed deps, pure delegation.
  ApplicationBootstrapperFactory — external composition root for production defaults.
"""

import sys
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

from message_transport_running import MessageTransportRunning
from pipeline.tool_registry import ToolRegistering, ToolRegistry
from common.mcp_meta import LARGE_OUTPUT
from pipeline.flow_tool_callables_assembler import FlowToolCallablesAssembler
from pipeline.tool_callables_building import ToolCallablesBuilding


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
    Production composition is provided by ApplicationBootstrapperFactory.
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

        _measurement_schema = {
            "type": "object",
            "required": ["value", "is_exception", "additional_info"],
            "properties": {
                "value": {"type": ["integer", "number", "string"]},
                "is_exception": {
                    "type": "boolean",
                    "description": "True only when the metric satisfies a documented principle exception.",
                },
                "additional_info": {
                    "type": "object",
                    "required": ["reasoning", "evidence"],
                    "properties": {
                        "reasoning": {
                            "type": "string",
                            "description": "Why the measurement and exception classification are correct.",
                        },
                        "evidence": {
                            "type": "string",
                            "description": "Relevant code excerpt, line reference, or precise source observation.",
                        },
                    },
                },
            },
        }
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
                    "description": "Keys are principle names. Each metric requires value, is_exception, and additional_info with reasoning and evidence.",
                    "additionalProperties": {
                        "type": "object",
                        "additionalProperties": _measurement_schema,
                    },
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
                             "description": "Map of principle_name to review-output payload (references/review-output.schema.json). Every metric must include value, is_exception, and additional_info {reasoning, evidence}.",
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
                            "Stable workflow ID declared by a package workflow.yaml, discovered recursively "
                            "from '<project>/.solid-coder/workflows/' and '<plugin>/workflows/'. Legacy flat "
                            "YAML files remain discoverable by filename-derived ID from each "
                            "'.solid-coder/harness/flows/' compatibility root. IDs must be unique across the "
                            "combined catalog; collisions fail instead of selecting by root order. An explicit "
                            "YAML path bypasses catalog lookup."
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


if __name__ == "__main__":
    from pipeline.application_bootstrapper_factory import ApplicationBootstrapperFactory
    from pipeline.flow_result_renderer_creator import FlowResultRendererCreator
    from pipeline.flow_run_creator import FlowRunCreator

    ApplicationBootstrapperFactory(
        plugin_root=PLUGIN_ROOT,
        skills_root=SKILLS_ROOT,
        flow_run_creator=FlowRunCreator(PLUGIN_ROOT),
        flow_renderer_creator=FlowResultRendererCreator(),
    ).make().run()
