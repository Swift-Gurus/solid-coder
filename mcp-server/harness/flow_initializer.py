"""
solid-name: FlowInitializer
solid-category: service
solid-spec: [SPEC-031]
solid-description: Initializes a flow run with all required setup and metadata.
"""

from __future__ import annotations

from harness.active_run_location_assembling import ActiveRunLocationAssembling
from harness.flow_init import FlowInit
from harness.flow_initializing import FlowInitializing
from harness.flow_loading import FlowLoading
from harness.isolated_run_path_resolving import IsolatedRunPathResolving
from harness.run_provisioning import RunProvisioning
from harness.run_started_event_logging import RunStartedEventLogging
from harness.startup_context_resolving import StartupContextResolving


class FlowInitializer(FlowInitializing):

    def __init__(
        self,
        startup_context: StartupContextResolving,
        flow_loader: FlowLoading,
        run_provisioner: RunProvisioning,
        path_resolver: IsolatedRunPathResolving,
        location_assembler: ActiveRunLocationAssembling,
        event_recorder: RunStartedEventLogging,
    ) -> None:
        self._startup_context = startup_context
        self._flow_loader = flow_loader
        self._run_provisioner = run_provisioner
        self._path_resolver = path_resolver
        self._location_assembler = location_assembler
        self._event_recorder = event_recorder

    def initialize(self, flow: str, params: dict, isolated: bool) -> FlowInit:
        startup = self._startup_context.resolve()
        flow_def = self._flow_loader.load(flow, startup.search_paths)

        base_dir = self._path_resolver.provisioning_base_dir(startup, isolated)
        run_init = self._run_provisioner.provision(base_dir, flow_def, params, self_contained=isolated)
        effective_base_dir = self._path_resolver.effective_base_dir(base_dir, run_init.run_dir, isolated)

        location = self._location_assembler.assemble(run_init.run_id, base_dir, run_init.run_dir)
        self._event_recorder.record(location.events_path, run_init.run_id, flow_def.name)

        return FlowInit(location=location, effective_base_dir=effective_base_dir, flow_def=flow_def)
