"""
solid-name: IsolatedRunPathResolver
solid-category: service
solid-spec: [SPEC-031]
solid-description: Decides which directory a run provisions into and which directory its step execution treats as the base, based on whether the run is isolated.
"""

from __future__ import annotations

from pathlib import Path

from harness.isolated_run_path_resolving import IsolatedRunPathResolving
from harness.isolated_run_paths import ISOLATED_RUNS_DIRNAME
from harness.startup_context import StartupContext


"""
solid-name: IsolatedRunPathResolver
solid-category: service
solid-spec: [SPEC-031, SPEC-047]
solid-description: Resolves the run collection used to provision normal and isolated workflows.
"""
class IsolatedRunPathResolver(IsolatedRunPathResolving):

    def provisioning_base_dir(self, startup: StartupContext, isolated: bool) -> Path:
        return (startup.base_dir / ISOLATED_RUNS_DIRNAME) if isolated else startup.base_dir
