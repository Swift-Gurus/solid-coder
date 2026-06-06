#!/usr/bin/env python3
"""solid-coder pipeline MCP server.

Architecture:
  ApplicationBootstrapper — SRP Facade, protocol-typed deps, pure delegation.
  make_bootstrapper()     — Factory that produces the bootstrapper with production defaults.
  main()                  — Entry point; calls the factory and runs.
"""

import importlib
import json
import sys
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
from lib.skill_runner import SkillRunning, ResultFormatting, SkillRunner, SkillResultFormatter
from lib.tool_registry import ToolRegistering, ToolRegistry
from pipeline.handlers import ReviewResultsCollecting, ReviewResultsCollector
from lib.gateway_tools import make_gateway_handler as _make_gw_pipeline
from lib.unit_kind_filter import filter_by_unit_kind as _filter_by_kind

_LARGE_OUTPUT = {"anthropic/maxResultSizeChars": 200_000}


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

    def run(self) -> None:
        self._register_all_tools()
        self._server.run()

    def _register_all_tools(self) -> None:
        reg = self._registry
        runner, fmt = self._runner, self._fmt

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

        def _split_plan(plan_path, output_dir, arch_path=None):
            args = [plan_path, "--output-dir", output_dir]
            if arch_path:
                args += ["--arch", arch_path]
            ok, out, err = runner.execute("synthesize-implementation", "split-plan.py", args)
            chunks = sorted(Path(output_dir).glob("*.json")) if ok else []
            return fmt.format(ok, err, success=ok, chunks=[str(c) for c in chunks], count=len(chunks))

        def _generate_report(data_dir, report_dir=None):
            report_dir = report_dir or data_dir
            ok, out, err = runner.execute("generate-report", "generate-report.py", [data_dir, report_dir])
            md = str(Path(report_dir) / "report.md") if ok else None
            html = str(Path(report_dir) / "report.html") if ok else None
            return fmt.format(ok, err, success=ok, md_path=md, html_path=html)

        def _validate_arch(arch_path):
            schema = str(SKILLS_ROOT / "plan" / "arch.schema.json")
            ok, out, err = runner.execute("plan", "validate-arch.py", [arch_path, "--schema", schema])
            return fmt.format(ok, err, valid=ok, output=out, errors=err if not ok else None)

        def _validate_findings(output_root):
            ok, out, err = runner.execute("validate-findings", "validate-findings.py",
                                          [output_root, str(PLUGIN_ROOT)])
            return fmt.format(ok, err, success=ok, output=out)

        def _search(sources_dir=None, plan_path=None, tags=None, spec_numbers=None, min_matches=3):
            return self._search.search(
                sources_dir=sources_dir, plan_path=plan_path, tags=tags,
                spec_numbers=spec_numbers, min_matches=min_matches,
            )

        reg.register("collect_review_results",
                     "Collect and summarise all review outputs. Returns verdict (ALL_COMPLIANT|MINOR_ONLY|HAS_SEVERE), summary table, and minor_findings.",
                     {"type": "object", "properties": {"output_root": {"type": "string"}}, "required": ["output_root"]},
                     self._collector.collect, meta=_LARGE_OUTPUT)

        reg.register("check_severity",
                     "Check review findings for SEVERE violations. Returns structured verdict.",
                     {"type": "object", "properties": {"output_root": {"type": "string"}}, "required": ["output_root"]},
                     self._check_sev.check_severity)

        reg.register("validate_findings",
                     "Filter findings to changed line ranges and reorganize by file. Writes by-file/*.output.json.",
                     {"type": "object", "properties": {"output_root": {"type": "string"}}, "required": ["output_root"]},
                     _validate_findings)

        reg.register("load_synthesis_context",
                     "Load all validated findings for synthesis. Returns per-principle summaries and severity counts.",
                     {"type": "object", "properties": {"output_root": {"type": "string"}}, "required": ["output_root"]},
                     self._ctx.load_context, meta=_LARGE_OUTPUT)

        reg.register("generate_report",
                     "Generate MD + HTML reports from validated findings and synthesized fix plans.",
                     {"type": "object", "properties": {
                         "data_dir": {"type": "string"},
                         "report_dir": {"type": "string"},
                     }, "required": ["data_dir"]},
                     _generate_report)

        reg.register("validate_architecture",
                     "Validate arch.json structure and semantic SOLID constraints.",
                     {"type": "object", "properties": {"arch_path": {"type": "string"}}, "required": ["arch_path"]},
                     _validate_arch)

        reg.register("split_implementation_plan",
                     "Split implementation-plan.json into semantically grouped chunks.",
                     {"type": "object", "properties": {
                         "plan_path": {"type": "string"},
                         "output_dir": {"type": "string"},
                         "arch_path": {"type": "string"},
                     }, "required": ["plan_path", "output_dir"]},
                     _split_plan)

        reg.register("search_codebase",
                     "Search the codebase for reusable types and existing implementations by solid-frontmatter tags.",
                     {"type": "object", "properties": {
                         "sources_dir": {"type": "string"},
                         "plan_path": {"type": "string"},
                         "tags": {"type": "array", "items": {"type": "string"}},
                         "spec_numbers": {"type": "array", "items": {"type": "string"}},
                         "min_matches": {"type": "integer"},
                     }, "required": []},
                     _search, meta=_LARGE_OUTPUT)

        reg.register("prepare_review_input",
                     "Prepare git changes (staged, unstaged, untracked) into structured review-input.json.",
                     {"type": "object", "properties": {
                         "candidate_tags": {"type": "array", "items": {"type": "string"}},
                     }},
                     _prepare_input)

        reg.register("submit_findings",
                     "Score a partial review output for one principle via severity-bands in rule.md and write review-output.json. LLM provides metrics; server fills scoring and findings.",
                     {"type": "object", "properties": {
                         "partial_output": {"type": "object"},
                         "output_path": {"type": "string"},
                     }, "required": ["partial_output", "output_path"]},
                     self._gw.submit_findings)

        reg.register("submit_batch_findings",
                     "Submit health-check findings for all reviewed principles in one call. Keyed by label; output at {output_dir}/{label}/review-output.json.",
                     {"type": "object", "properties": {
                         "output_dir": {"type": "string"},
                         "submissions": {"type": "object", "additionalProperties": {"type": "object"}},
                     }, "required": ["output_dir", "submissions"]},
                     self._gw.submit_batch_findings)

        reg.register("submit_fix",
                     "Submit concrete fixes for ALL SEVERE violations in one call. "
                     "Returns {complete, violations_with_fixes} on success, {error} if any fix is missing or malformed.",
                     {"type": "object", "properties": {
                         "output_dir": {"type": "string"},
                         "fixes": {
                             "type": "array",
                             "description": "One entry per SEVERE violation — must cover all violations from submit_batch_findings.",
                             "items": {
                                 "type": "object",
                                 "properties": {
                                     "metric_id": {"type": "string"},
                                     "file_path": {"type": "string"},
                                     "unit_name": {"type": "string"},
                                     "suggested_fix": {"type": "string"},
                                 },
                                 "required": ["metric_id", "file_path", "unit_name", "suggested_fix"],
                             },
                         },
                     }, "required": ["output_dir", "fixes"]},
                     self._gw.submit_fix)

        reg.register("validate_phase_output",
                     "Validate a JSON file against a JSON schema.",
                     {"type": "object", "properties": {
                         "json_path": {"type": "string"},
                         "schema_path": {"type": "string"},
                     }, "required": ["json_path", "schema_path"]},
                     self._validate.validate_json)


# ── Factory and entry point ───────────────────────────────────────────────────

def make_bootstrapper() -> ApplicationBootstrapper:
    """Factory: construct concrete implementations and return a ready-to-run bootstrapper."""
    mcp = MCPServer("solid-coder-pipeline", "1.0.0")
    return ApplicationBootstrapper(
        server=mcp,
        registry=ToolRegistry(mcp),
        skill_runner=SkillRunner(SKILLS_ROOT),
        result_fmt=SkillResultFormatter(),
        collector=ReviewResultsCollector(),
        gateway=_make_gw_pipeline(PLUGIN_ROOT / "references"),
        check_severity=importlib.import_module("check-severity"),
        load_context=importlib.import_module("load-context"),
        validate_output=importlib.import_module("validate-output"),
        search=importlib.import_module("lib.codebase_searcher"),
    )



def get_pipeline_tools() -> dict:
    """Factory: returns pipeline tool callables keyed by name, for CLI/script access."""
    import importlib as _il
    from lib.skill_runner import SkillRunner as _SR, SkillResultFormatter as _SRF
    from pipeline.handlers import ReviewResultsCollector as _RRC
    from lib.gateway_tools import make_gateway_handler as _mgw

    runner = _SR(SKILLS_ROOT)
    fmt = _SRF()
    collector = _RRC()
    gw = _mgw(PLUGIN_ROOT / 'references')
    chk = _il.import_module('check-severity')
    ctx = _il.import_module('load-context')
    vo = _il.import_module('validate-output')
    search = _il.import_module('lib.codebase_searcher')

    def _validate_findings(output_root):
        ok, out, err = runner.execute('validate-findings', 'validate-findings.py', [output_root, str(PLUGIN_ROOT)])
        return fmt.format(ok, err, success=ok, output=out)

    def _generate_report(data_dir, report_dir=None):
        rd = report_dir or data_dir
        ok, out, err = runner.execute('generate-report', 'generate-report.py', [data_dir, rd])
        md = str(PLUGIN_ROOT / rd / 'report.md') if ok else None
        html = str(PLUGIN_ROOT / rd / 'report.html') if ok else None
        return fmt.format(ok, err, success=ok, md_path=md, html_path=html)

    def _validate_arch(arch_path):
        schema = str(SKILLS_ROOT / 'plan' / 'arch.schema.json')
        ok, out, err = runner.execute('plan', 'validate-arch.py', [arch_path, '--schema', schema])
        return fmt.format(ok, err, valid=ok, output=out, errors=err if not ok else None)

    def _split_plan(plan_path, output_dir, arch_path=None):
        import pathlib as _pl
        args = [plan_path, '--output-dir', output_dir]
        if arch_path:
            args += ['--arch', arch_path]
        ok, out, err = runner.execute('synthesize-implementation', 'split-plan.py', args)
        chunks = sorted(_pl.Path(output_dir).glob('*.json')) if ok else []
        return fmt.format(ok, err, success=ok, chunks=[str(c) for c in chunks], count=len(chunks))

    def _prepare_input(candidate_tags=None):
        import json as _json
        ok, out, err = runner.execute('prepare-review-input', 'prepare-changes.py', [])
        if not ok:
            return {'error': err}
        try:
            data = _json.loads(out)
            data['candidate_tags'] = candidate_tags or []
            return data
        except _json.JSONDecodeError:
            return {'error': f'Could not parse script output: {out}'}

    def _search(sources_dir=None, plan_path=None, tags=None, spec_numbers=None, min_matches=3):
        return search.search(sources_dir=sources_dir, plan_path=plan_path, tags=tags, spec_numbers=spec_numbers, min_matches=min_matches)

    return {
        'check_severity': chk.check_severity,
        'load_synthesis_context': ctx.load_context,
        'validate_phase_output': vo.validate_json,
        'validate_findings': _validate_findings,
        'generate_report': _generate_report,
        'validate_architecture': _validate_arch,
        'split_implementation_plan': _split_plan,
        'search_codebase': _search,
        'prepare_review_input': _prepare_input,
        'submit_findings': gw.submit_findings,
        'submit_batch_findings': gw.submit_batch_findings,
        'submit_fix': gw.submit_fix,
    }

def main() -> None:
    make_bootstrapper().run()


if __name__ == "__main__":
    main()
