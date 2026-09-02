"""Writes project policy fixtures from the currently packaged review-rule set."""

from pathlib import Path


"""
solid-name: BundledReviewRulePolicyWriter
solid-category: test-support
solid-spec: [SPEC-036, SPEC-039]
solid-description: Selects one packaged review rule for main-chain integration tests without duplicating the bundled rule inventory.
"""
class BundledReviewRulePolicyWriter:

    def __init__(self, plugin_root: Path, project_root: Path) -> None:
        self._rules_root = plugin_root / "workflows" / "review" / "rules"
        self._project_root = project_root

    def write_only(self, selected_rule_id: str) -> Path:
        rule_ids = [
            entrypoint.parent.name
            for entrypoint in sorted(self._rules_root.glob("*/workflow.yaml"))
        ]
        if selected_rule_id not in rule_ids:
            raise ValueError(
                f"Packaged review rule '{selected_rule_id}' was not discovered"
            )

        policy_path = (
            self._project_root / ".solid-coder" / "policies" / "review.yaml"
        )
        policy_path.parent.mkdir(parents=True, exist_ok=True)
        disabled_rules = [
            rule_id for rule_id in rule_ids if rule_id != selected_rule_id
        ]
        overrides = "\n".join(
            "  - workflow_id: "
            + rule_id
            + "\n    enabled: false"
            + "\n    reason: Isolated validation selects one packaged rule."
            for rule_id in disabled_rules
        )
        policy_path.write_text(
            "version: 1\nrules:\n" + overrides + "\n",
            encoding="utf-8",
        )
        return policy_path
