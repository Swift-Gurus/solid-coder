"""
solid-name: test_workflow_catalog_e2e_live
solid-category: integration-test
solid-spec: [SPEC-035]
solid-description: Applies the shared live workflow-catalog contract to Codex and Claude model-profile test bases.

Run one backend explicitly:
    python3 -m pytest tests/harness/flow_engine/test_workflow_catalog_e2e_live.py::TestCodexWorkflowCatalogE2ELive -v -s
    python3 -m pytest tests/harness/flow_engine/test_workflow_catalog_e2e_live.py::TestClaudeWorkflowCatalogE2ELive -v -s
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parents[1]
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from claude_test_base import ClaudeTestBase  # noqa: E402
from codex_test_base import CodexTestBase  # noqa: E402
from workflow_catalog_e2e_live_base import WorkflowCatalogE2ELiveBase  # noqa: E402


class TestCodexWorkflowCatalogE2ELive(CodexTestBase, WorkflowCatalogE2ELiveBase):

    __test__ = True


class TestClaudeWorkflowCatalogE2ELive(ClaudeTestBase, WorkflowCatalogE2ELiveBase):

    __test__ = True
