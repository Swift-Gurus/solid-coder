"""
solid-name: TestHarnessRunner
solid-category: service
solid-spec: [SPEC-014]
solid-description: Facade/Coordinator orchestrating a principle test harness run. All dependencies
are protocol-typed and injected via init. Resolves paths, discovers fixtures, loads model profile,
generates run timestamp, and for each fixture/flow invokes the appropriate flow invoker, normalizes
findings per flow, compares results, formats and prints status lines. Returns True when all
fixtures pass, False otherwise.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from interfaces import (  # noqa: E402
    ExpectationLoading,
    FindingComparing,
    FindingNormalizing,
    FixtureDiscovering,
    FlowInvoking,
    ModelProfileLoading,
    OutputPathBuilding,
    PathResolving,
    ResultFormatting,
    TestHarnessRunning,
    TimestampGenerating,
)
from models import FixturePair, ModelProfile, OutputPaths  # noqa: E402

_FLOWS = ("apply", "health")


class TestHarnessRunner(TestHarnessRunning):
    def __init__(
        self,
        path_resolver: PathResolving,
        fixture_discovery: FixtureDiscovering,
        expectation_loader: ExpectationLoading,
        model_profile_loader: ModelProfileLoading,
        output_path_builder: OutputPathBuilding,
        finding_comparer: FindingComparing,
        finding_normalizer: FindingNormalizing,
        result_formatter: ResultFormatting,
        apply_invoker: FlowInvoking,
        health_invoker: FlowInvoking,
        timestamp_generator: TimestampGenerating,
    ) -> None:
        self._path_resolver = path_resolver
        self._fixture_discovery = fixture_discovery
        self._expectation_loader = expectation_loader
        self._model_profile_loader = model_profile_loader
        self._output_path_builder = output_path_builder
        self._finding_comparer = finding_comparer
        self._finding_normalizer = finding_normalizer
        self._result_formatter = result_formatter
        self._apply_invoker = apply_invoker
        self._health_invoker = health_invoker
        self._timestamp_generator = timestamp_generator

    def run(
        self,
        principle_path: str,
        flow: str | None,
        fixture_filter: str | None,
        model_name: str | None,
        timeout: int | None,
    ) -> bool:
        tests_path = self._path_resolver.resolve(principle_path)
        pairs = self._fixture_discovery.discover(tests_path)
        model_profile = self._model_profile_loader.load(model_name)
        effective_timeout = timeout if timeout is not None else model_profile.llm["timeout"]
        run_timestamp = self._timestamp_generator.now_str()
        category_path = str(tests_path.relative_to(tests_path.parents[1]))

        selected_pairs = [
            p for p in pairs
            if fixture_filter is None or p.stem == fixture_filter
        ]
        flows_to_run = [flow] if flow else list(_FLOWS)

        all_passed = True
        for pair in selected_pairs:
            expectation = self._expectation_loader.load(pair.expectation_path)
            for flow_name in flows_to_run:
                output_paths = self._output_path_builder.build(
                    run_timestamp=run_timestamp,
                    model_name=model_profile.output_dir_name,
                    category_path=category_path,
                    fixture_stem=pair.stem,
                    flow_name=flow_name,
                )
                actual_findings = self._invoke_flow(
                    flow_name, pair, output_paths, model_profile, effective_timeout
                )
                expected_norm, actual_norm = self._finding_normalizer.normalize(
                    flow_name, expectation.findings, actual_findings
                )
                diffs = self._finding_comparer.compare(expected_norm, actual_norm)
                passed = not diffs
                if not passed:
                    all_passed = False
                print(self._result_formatter.format_status(
                    passed, model_profile.output_dir_name, category_path, pair.stem, flow_name
                ))
                for line in self._result_formatter.format_failures(diffs, output_paths.reasoning_path):
                    print(line)

        return all_passed

    def _invoke_flow(
        self,
        flow_name: str,
        pair: FixturePair,
        output_paths: OutputPaths,
        model_profile: ModelProfile,
        timeout: int,
    ) -> list[dict]:
        invoker = self._apply_invoker if flow_name == "apply" else self._health_invoker
        return invoker.invoke(pair.fixture_path, output_paths, model_profile, timeout)
