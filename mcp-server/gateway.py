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

import json
import sys
from pathlib import Path

from pydantic import TypeAdapter

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
from pipeline.application_bootstrapper_factory import ApplicationBootstrapperFactory  # noqa: E402
from pipeline.flow_result_renderer_creator import FlowResultRendererCreator  # noqa: E402
from pipeline.flow_run_creator import FlowRunCreator  # noqa: E402
from pipeline.output_path_factory import OutputPathFactory  # noqa: E402
from pipeline.pipeline_tools_provider import PipelineToolsProvider  # noqa: E402

_pipeline_factory = ApplicationBootstrapperFactory(
    plugin_root=PLUGIN_ROOT,
    skills_root=SKILLS_ROOT,
    flow_run_creator=FlowRunCreator(PLUGIN_ROOT),
    flow_renderer_creator=FlowResultRendererCreator(),
)
_pt = PipelineToolsProvider(_pipeline_factory).get()
get_output_path = OutputPathFactory().compute
check_severity = _pt['check_severity']
load_synthesis_context = _pt['load_synthesis_context']
validate_phase_output = _pt['validate_phase_output']
validate_findings = _pt['validate_findings']
generate_report = _pt['generate_report']
validate_architecture = _pt['validate_architecture']
split_implementation_plan = _pt['split_implementation_plan']
from search.codebase_searcher import search_raw as search_codebase  # noqa: E402 — raw JSON for CLI
prepare_review_input = _pt['prepare_review_input']

# Spec tools — mcp-server/specs/server.py
from specs.server import query_specs  # noqa: E402
from gateway_application import GatewayApplication  # noqa: E402
from gateway_argument_parser import GatewayArgumentParser  # noqa: E402
from gateway_argument_validator import GatewayArgumentValidator  # noqa: E402
from gateway_arguments import GatewayArguments  # noqa: E402
from gateway_tool_runner import GatewayToolRunner  # noqa: E402
from search_gateway_arguments_normalizer import SearchGatewayArgumentsNormalizer  # noqa: E402
from spec_ancestry_retriever import SpecAncestryRetriever  # noqa: E402
from spec_context_loader import SpecContextLoader  # noqa: E402
from spec_context_renderer import SpecContextRenderer  # noqa: E402
from stderr_logger import StderrLogger  # noqa: E402
from stdout_writer import StdoutWriter  # noqa: E402
from subprocess_adapter import SubprocessAdapter  # noqa: E402
from system_process_exit import SystemProcessExit  # noqa: E402

_spec_context = SpecContextLoader(
    retriever=SpecAncestryRetriever(
        script=SKILLS_ROOT / "find-spec" / "scripts" / "find-spec-query.py",
        executable=sys.executable,
        process=SubprocessAdapter(),
        deserializer=json.loads,
    ),
    renderer=SpecContextRenderer(),
)


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
    "load_spec_context": _spec_context.load,
    "prepare_review_input": prepare_review_input,
    "load_fix_instructions_for_findings": load_fix_instructions_for_findings,
    "load_fix_for_violation": load_fix_for_violation,
    "load_detection_rules": load_detection_rules,
    "get_output_path": get_output_path,
}


if __name__ == "__main__":
    process = SystemProcessExit()
    errors = StderrLogger()
    GatewayApplication(
        parser=GatewayArgumentParser(TypeAdapter(GatewayArguments)),
        normalizer=SearchGatewayArgumentsNormalizer(),
        validator=GatewayArgumentValidator(),
        runner=GatewayToolRunner(
            output=StdoutWriter(),
            errors=errors,
            process=process,
        ),
        tools=TOOLS,
        errors=errors,
        process=process,
    ).run(sys.argv)
