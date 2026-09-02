"""Tests project-policy filtering at the explicit rules-all boundary."""

import sys
import unittest
from pathlib import Path

_MCP_SERVER = Path(__file__).resolve().parents[4] / "mcp-server"
if str(_MCP_SERVER) not in sys.path:
    sys.path.insert(0, str(_MCP_SERVER))

from harness.policy_rule_set_members_resolver import (  # noqa: E402
    PolicyRuleSetMembersResolver,
)
from harness.project_review_policy_audit import ProjectReviewPolicyAudit  # noqa: E402
from harness.project_review_policy_resolution import (  # noqa: E402
    ProjectReviewPolicyResolution,
)
from harness.review_policy import ReviewPolicy  # noqa: E402
from harness.review_policy_rule_override import ReviewPolicyRuleOverride  # noqa: E402
from harness.rule_enablement_resolver import RuleEnablementResolver  # noqa: E402
from harness.rule_set_member_include import RuleSetMemberInclude  # noqa: E402
from harness.workflow_include_runtime import WorkflowIncludeRuntime  # noqa: E402


class StubRuleSetMembersResolver:
    def __init__(self, members: list[RuleSetMemberInclude]) -> None:
        self._members = members

    def resolve(
        self,
        search_paths: list[str],
        runtime: WorkflowIncludeRuntime,
    ) -> list[RuleSetMemberInclude]:
        return self._members


class StubReviewPolicyLoader:
    def __init__(self, resolution: ProjectReviewPolicyResolution) -> None:
        self._resolution = resolution

    def load(self) -> ProjectReviewPolicyResolution:
        return self._resolution


"""
solid-name: TestPolicyRuleSetMembersResolver
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Proves rules-all excludes project-disabled rules before child workflow materialization.
"""
class TestPolicyRuleSetMembersResolver(unittest.TestCase):

    def test_excludes_project_disabled_members(self) -> None:
        runtime = WorkflowIncludeRuntime()
        members = [
            RuleSetMemberInclude("ocp", "ocp", runtime),
            RuleSetMemberInclude("srp", "srp", runtime),
        ]
        policy_content = (
            "version: 1\nrules:\n"
            "  - workflow_id: ocp\n"
            "    enabled: false\n"
        )
        resolution = ProjectReviewPolicyResolution(
            policy=ReviewPolicy(
                version=1,
                rules=[
                    ReviewPolicyRuleOverride(
                        workflow_id="ocp",
                        enabled=False,
                    )
                ],
            ),
            audit=ProjectReviewPolicyAudit(
                source_path=Path("/project/.solid-coder/policies/review.yaml"),
                content_hash="policy-hash",
            ),
            authored_content=policy_content,
        )
        resolver = PolicyRuleSetMembersResolver(
            members=StubRuleSetMembersResolver(members),
            policy_loader=StubReviewPolicyLoader(resolution),
            enablement=RuleEnablementResolver(),
        )

        selected = resolver.resolve(["/workflows"], runtime)

        self.assertEqual([member.workflow_id for member in selected], ["srp"])


if __name__ == "__main__":
    unittest.main()
