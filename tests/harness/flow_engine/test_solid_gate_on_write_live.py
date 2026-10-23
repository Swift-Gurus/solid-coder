"""Run the production gate with either locked live model profile.

python3.12 -m pytest tests/harness/flow_engine/test_solid_gate_on_write_live.py -v -s
Append ::TestCodexSolidGateOnWriteLive or ::TestClaudeSolidGateOnWriteLive
to run one backend. The hook launches the model; tests do not author its prompt.
"""

import sys
from pathlib import Path

_HARNESS = Path(__file__).resolve().parents[1]
if str(_HARNESS) not in sys.path:
    sys.path.insert(0, str(_HARNESS))

from claude_test_base import ClaudeTestBase
from codex_test_base import CodexTestBase
from solid_gate_on_write_e2e_live_base import SolidGateOnWriteE2ELiveBase

"""
solid-name: TestCodexSolidGateOnWriteLive
solid-category: integration-test
solid-spec: [SPEC-036, SPEC-050]
solid-description: Runs the shared real-hook aggregate gate contract using the locked Codex model profile.
"""


class TestCodexSolidGateOnWriteLive(CodexTestBase, SolidGateOnWriteE2ELiveBase):
    __test__ = True


"""
solid-name: TestClaudeSolidGateOnWriteLive
solid-category: integration-test
solid-spec: [SPEC-036, SPEC-050]
solid-description: Runs the shared real-hook aggregate gate contract using the locked Claude model profile.
"""


class TestClaudeSolidGateOnWriteLive(ClaudeTestBase, SolidGateOnWriteE2ELiveBase):
    __test__ = True
