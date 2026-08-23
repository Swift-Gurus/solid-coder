"""Qualifies child-local dependency identities under an owning alias."""

from harness.nested_identity_qualifying import NestedIdentityQualifying


"""
solid-name: LocalNestedIdentityQualifier
solid-category: service
solid-spec: [SPEC-035, SPEC-037]
solid-description: Prefixes identities declared inside a nested workflow and preserves references declared outside it.
"""
class LocalNestedIdentityQualifier(NestedIdentityQualifying):
    def qualify(
        self,
        alias: str,
        identity: str,
        local_dependency_ids: set[str],
    ) -> str:
        return (
            f"{alias}.{identity}"
            if identity in local_dependency_ids
            else identity
        )
