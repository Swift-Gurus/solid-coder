"""
solid-name: test_flow_initializer
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests coordinating startup resolution, flow loading, provisioning, and start-event recording.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.active_run_location import ActiveRunLocation
from harness.flow_initializer import FlowInitializer
from harness.models import FlowDef
from harness.run_init import RunInit
from harness.startup_context import StartupContext


class StubStartupContext:
    def __init__(self, context: StartupContext) -> None:
        self._context = context

    def resolve(self) -> StartupContext:
        return self._context


class StubFlowLoader:
    def __init__(self, flow_def: FlowDef) -> None:
        self._flow_def = flow_def
        self.calls: list[tuple] = []

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        self.calls.append((path, search_paths))
        return self._flow_def


class StubRunProvisioner:
    def __init__(self, run_init: RunInit) -> None:
        self._run_init = run_init
        self.calls: list[tuple] = []

    def provision(self, base_dir: Path, flow_def: FlowDef, params: dict, self_contained: bool = False) -> RunInit:
        self.calls.append((base_dir, flow_def, params, self_contained))
        return self._run_init


class StubPathResolver:
    def __init__(self, provisioning_base_dir: Path, effective_base_dir: Path) -> None:
        self._provisioning_base_dir = provisioning_base_dir
        self._effective_base_dir = effective_base_dir
        self.provisioning_calls: list[tuple] = []
        self.effective_calls: list[tuple] = []

    def provisioning_base_dir(self, startup: StartupContext, isolated: bool) -> Path:
        self.provisioning_calls.append((startup, isolated))
        return self._provisioning_base_dir

    def effective_base_dir(self, base_dir: Path, run_dir: Path, isolated: bool) -> Path:
        self.effective_calls.append((base_dir, run_dir, isolated))
        return self._effective_base_dir


class SpyLocationAssembler:
    def __init__(self, location: ActiveRunLocation) -> None:
        self._location = location
        self.calls: list[tuple] = []

    def assemble(self, run_id: str, base_dir: Path, run_dir: Path) -> ActiveRunLocation:
        self.calls.append((run_id, base_dir, run_dir))
        return self._location


class SpyEventRecorder:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    def record(self, events_path: str, run_id: str, flow_name: str) -> None:
        self.calls.append((events_path, run_id, flow_name))


class FlowInitializerFactory:
    """Builds a FlowInitializer with sensible stub/spy defaults; tests override only what they vary."""

    def __init__(self) -> None:
        self.startup_context = StubStartupContext(StartupContext(base_dir=Path("/runs"), search_paths=["/flows"]))
        self.flow_loader = StubFlowLoader(FlowDef(name="code_review", max_turns=10, steps=[]))
        self.run_provisioner = StubRunProvisioner(RunInit(run_id="run-1", run_dir=Path("/runs/run-1")))
        self.path_resolver = StubPathResolver(
            provisioning_base_dir=Path("/runs"), effective_base_dir=Path("/runs"),
        )
        self.location = ActiveRunLocation(
            run_id="run-1", base_dir=Path("/runs"), run_dir=Path("/runs/run-1"),
            events_path="/runs/run-1/events.jsonl", workflow_path="/runs/run-1/workflow.yaml",
        )
        self.location_assembler = SpyLocationAssembler(self.location)
        self.event_recorder = SpyEventRecorder()

    def with_flow_loader(self, flow_loader) -> "FlowInitializerFactory":
        self.flow_loader = flow_loader
        return self

    def with_run_provisioner(self, run_provisioner) -> "FlowInitializerFactory":
        self.run_provisioner = run_provisioner
        return self

    def with_path_resolver(self, path_resolver) -> "FlowInitializerFactory":
        self.path_resolver = path_resolver
        return self

    def make_sut(self) -> FlowInitializer:
        return FlowInitializer(
            startup_context=self.startup_context,
            flow_loader=self.flow_loader,
            run_provisioner=self.run_provisioner,
            path_resolver=self.path_resolver,
            location_assembler=self.location_assembler,
            event_recorder=self.event_recorder,
        )


class TestFlowInitializer(unittest.TestCase):

    def test_loads_the_flow_by_name_with_the_startup_search_paths(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        flow_loader = StubFlowLoader(flow_def)
        factory = FlowInitializerFactory().with_flow_loader(flow_loader)

        factory.make_sut().initialize("code_review", {"key": "value"}, isolated=False)

        self.assertEqual(flow_loader.calls, [("code_review", ["/flows"])])

    def test_provisions_the_run_under_the_path_resolvers_provisioning_base_dir(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        provisioner = StubRunProvisioner(RunInit(run_id="run-1", run_dir=Path("/runs/run-1")))
        path_resolver = StubPathResolver(provisioning_base_dir=Path("/runs/subagents"), effective_base_dir=Path("/x"))
        factory = FlowInitializerFactory().with_flow_loader(StubFlowLoader(flow_def)).with_run_provisioner(
            provisioner
        ).with_path_resolver(path_resolver)

        factory.make_sut().initialize("code_review", {"key": "value"}, isolated=True)

        self.assertEqual(provisioner.calls, [(Path("/runs/subagents"), flow_def, {"key": "value"}, True)])

    def test_returns_the_effective_base_dir_from_the_path_resolver(self):
        path_resolver = StubPathResolver(provisioning_base_dir=Path("/runs"), effective_base_dir=Path("/runs/run-1"))
        factory = FlowInitializerFactory().with_path_resolver(path_resolver)

        result = factory.make_sut().initialize("code_review", {}, isolated=True)

        self.assertEqual(result.effective_base_dir, Path("/runs/run-1"))
        self.assertEqual(path_resolver.effective_calls, [(Path("/runs"), Path("/runs/run-1"), True)])

    def test_assembles_the_location_from_the_provisioned_run(self):
        run_init = RunInit(run_id="run-9", run_dir=Path("/runs/run-9"))
        factory = FlowInitializerFactory().with_run_provisioner(StubRunProvisioner(run_init))

        result = factory.make_sut().initialize("code_review", {}, isolated=False)

        self.assertIs(result.location, factory.location)
        self.assertEqual(factory.location_assembler.calls, [("run-9", Path("/runs"), Path("/runs/run-9"))])

    def test_records_the_run_started_event_with_the_assembled_events_path(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        factory = FlowInitializerFactory().with_flow_loader(StubFlowLoader(flow_def))

        factory.make_sut().initialize("code_review", {}, isolated=False)

        self.assertEqual(factory.event_recorder.calls, [
            ("/runs/run-1/events.jsonl", "run-1", "code_review"),
        ])

    def test_returns_the_loaded_flow_def_in_the_result(self):
        flow_def = FlowDef(name="code_review", max_turns=10, steps=[])
        factory = FlowInitializerFactory().with_flow_loader(StubFlowLoader(flow_def))

        result = factory.make_sut().initialize("code_review", {}, isolated=False)

        self.assertIs(result.flow_def, flow_def)


if __name__ == "__main__":
    unittest.main()
