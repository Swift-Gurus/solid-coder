"""Resolves direct and plan-derived terms for codebase source search."""

from pathlib import Path
from typing import Optional

from harness.ordered_string_collecting import OrderedStringCollecting
from harness.structured_model_decoding import StructuredModelDecoding
from scoring.yaml_config_file_loader import ConfigFileLoading
from search.codebase_search_terms import CodebaseSearchTerms
from search.codebase_search_terms_resolving import CodebaseSearchTermsResolving
from search.search_plan_document import SearchPlanDocument
from source.source_tokens_resolving import SourceTokensResolving


"""
solid-name: CodebaseSearchTermsResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves normalized source terms and specification identifiers from search arguments and plan metadata.
"""
class CodebaseSearchTermsResolver(CodebaseSearchTermsResolving):

    def __init__(
        self,
        plan_loader: ConfigFileLoading,
        plan_decoder: StructuredModelDecoding[SearchPlanDocument],
        tokens: SourceTokensResolving,
        strings: OrderedStringCollecting,
    ) -> None:
        self._plan_loader = plan_loader
        self._plan_decoder = plan_decoder
        self._tokens = tokens
        self._strings = strings

    def resolve(
        self,
        plan_path: Optional[Path],
        tags: Optional[list[str]],
        spec_numbers: Optional[list[str]],
    ) -> CodebaseSearchTerms:
        terms: list[str] = []
        specifications = list(spec_numbers or [])
        for tag in tags or []:
            if tag.casefold().startswith("spec-") and tag[5:].isdigit():
                specifications.append(tag)
            else:
                terms.append(tag)

        if plan_path is not None:
            raw_document = self._plan_loader.load(plan_path)
            if raw_document is None:
                raise ValueError(f"plan_path could not be loaded: {plan_path}")
            document = self._plan_decoder.decode(raw_document, "search plan")
            for component in document.components:
                for value in [component.name, component.category]:
                    terms.extend(sorted(self._tokens.resolve(value)))
                for values in [
                    component.interfaces,
                    component.dependencies,
                    component.stack,
                ]:
                    for value in values:
                        terms.extend(sorted(self._tokens.resolve(value)))
            for item in document.plan_items:
                terms.extend(sorted(self._tokens.resolve(item.component)))
            if document.spec_number:
                specifications.append(document.spec_number)

        return CodebaseSearchTerms(
            terms=self._strings.collect([terms]),
            specifications=self._strings.collect([specifications]),
        )
