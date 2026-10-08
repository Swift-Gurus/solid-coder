from findings.review_unit_kind import ReviewUnitKind
from source.analysis.relationships.source_declaration_reference import SourceDeclarationReference
from source.analysis.relationships.source_declaration_relationship import SourceDeclarationRelationship
from source.analysis.relationships.source_reference_candidate_resolving import SourceReferenceCandidateResolving
from source.analysis.relationships.source_relationship_status import SourceRelationshipStatus
from source.source_analysis import SourceAnalysis
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: SourceReferenceCandidateResolver
solid-category: service
solid-spec: [SPEC-057]
solid-description: Identifies bounded declaration candidates while preserving missing sources, name ambiguity, and unevaluated constraints.
"""
class SourceReferenceCandidateResolver(SourceReferenceCandidateResolving):
    def resolve(
        self,
        reference: SourceDeclarationReference,
        analyses: list[SourceAnalysis],
    ) -> SourceDeclarationRelationship:
        if len(reference.target.tokens) != 1:
            return SourceDeclarationRelationship(
                reference=reference,
                status=SourceRelationshipStatus.UNRESOLVED,
                reason="Qualified or compound type references require semantic resolution.",
            )
        candidates: list[SourceUnitIdentity] = []
        requires_semantics = bool(reference.generic_parameters or reference.constraints)
        for analysis in analyses:
            for unit in analysis.units:
                if unit.kind in {ReviewUnitKind.EXTENSION, ReviewUnitKind.FUNCTION, ReviewUnitKind.DOCUMENT}:
                    continue
                signature = unit.signature
                if signature.kind != "declaration" or signature.name.tokens != reference.target.tokens:
                    continue
                identity = SourceUnitIdentity(source_identity=analysis.source_identity, unit_identity=unit.identity)
                if identity == reference.owner:
                    continue
                candidates.append(identity)
                requires_semantics = requires_semantics or bool(signature.generic_parameters or signature.constraints)
        if not candidates:
            status = SourceRelationshipStatus.UNRESOLVED
            reason = "No eligible declaration was found in the supplied source analyses; repository absence is not established."
        elif len(candidates) > 1:
            status = SourceRelationshipStatus.AMBIGUOUS
            reason = "Multiple declarations match the reference; module ownership is not verified."
        elif requires_semantics:
            status = SourceRelationshipStatus.UNRESOLVED
            reason = "A possible declaration was found, but generic or conditional applicability requires semantic analysis."
        else:
            status = SourceRelationshipStatus.CANDIDATE
            reason = "One declaration-name candidate exists in the supplied sources; module ownership and conformance are not verified."
        return SourceDeclarationRelationship(
            reference=reference, status=status, candidates=candidates, reason=reason,
        )
