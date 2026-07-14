"""
solid-description: Provides canonical protocols for gate operations and feature management.
solid-category: service
solid-tags: [hook, utility]
"""

from hook_utils import GateHandling  # noqa: F401 — re-exported for consumers
from guard_checking import GuardChecking  # noqa: F401 — re-exported for consumers
from exclusion_checking import ExclusionChecking  # noqa: F401 — re-exported for consumers
from extension_lookup import ExtensionLookup  # noqa: F401 — re-exported for consumers
from coordinator_running import CoordinatorRunning  # noqa: F401 — re-exported for consumers
from coordinator_making import CoordinatorMaking  # noqa: F401 — re-exported for consumers
from health.hc_checker import HealthChecking  # noqa: F401 — re-exported for consumers; canonical definition
from health.hc_violation_parser import BlockReasonFormatting as ViolationFormatting  # noqa: F401 — re-exported; canonical definition
from content_simulating import ContentSimulating  # noqa: F401 — re-exported for consumers
from frontmatter_fixing import FrontmatterFixing  # noqa: F401 — re-exported for consumers
from health_gate_checking import HealthGateChecking  # noqa: F401 — re-exported for consumers
from frontmatter_gate_applying import FrontmatterGateApplying  # noqa: F401 — re-exported for consumers
