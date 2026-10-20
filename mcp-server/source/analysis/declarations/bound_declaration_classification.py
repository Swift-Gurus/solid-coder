from typing import Literal

from pydantic import BaseModel, ConfigDict

from findings.metric_additional_info import MetricAdditionalInfo
from source.analysis.declarations.source_scoped_declaration import SourceScopedDeclaration


"""
solid-name: BoundDeclarationClassification
solid-category: model
solid-spec: [SPEC-066]
solid-description: Joins an evidenced declaration judgment to authoritative lexical and bounded implementation facts without calculating rule scores.
"""
class BoundDeclarationClassification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    declaration: SourceScopedDeclaration
    kind: Literal["independent", "implemented_contract", "supporting_helper", "cohesive_contract"]
    has_business_logic: bool
    related_declaration: SourceScopedDeclaration
    declared_implementation: bool
    has_declared_implementation: bool
    related_has_declared_implementation: bool
    additional_info: MetricAdditionalInfo
