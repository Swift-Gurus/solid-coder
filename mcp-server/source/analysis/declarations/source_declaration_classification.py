from typing import Annotated, TypeAlias

from pydantic import Field

from source.analysis.declarations.associated_declaration_classification import AssociatedDeclarationClassification
from source.analysis.declarations.independent_declaration_classification import IndependentDeclarationClassification


SourceDeclarationClassification: TypeAlias = Annotated[
    IndependentDeclarationClassification | AssociatedDeclarationClassification,
    Field(discriminator="kind"),
]
