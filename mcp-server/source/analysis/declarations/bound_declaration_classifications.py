from pydantic import BaseModel, ConfigDict

from source.analysis.declarations.bound_declaration_classification import BoundDeclarationClassification


"""
solid-name: BoundDeclarationClassifications
solid-category: model
solid-spec: [SPEC-066]
solid-description: Publishes source-ordered validated declaration classifications for authored workflow filters and deterministic reducers.
"""
class BoundDeclarationClassifications(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    declarations: list[BoundDeclarationClassification]
