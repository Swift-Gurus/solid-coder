"""Composes file and unit source-search target construction."""

from harness.ordered_string_collector import OrderedStringCollector
from source.exact_source_tokens_resolver import ExactSourceTokensResolver
from source.file_source_search_targets_builder import (
    FileSourceSearchTargetsBuilder,
)
from source.search_target_granularity import SearchTargetGranularity
from source.source_search_target_terms_resolver import (
    SourceSearchTargetTermsResolver,
)
from source.source_search_targets_builder import SourceSearchTargetsBuilder
from source.source_search_targets_builder_registration import (
    SourceSearchTargetsBuilderRegistration,
)
from source.source_search_targets_builder_resolver import (
    SourceSearchTargetsBuilderResolver,
)
from source.source_unit_search_target_builder import (
    SourceUnitSearchTargetBuilder,
)
from source.source_unit_tags_resolver import SourceUnitTagsResolver
from source.technology_detection_scope import TechnologyDetectionScope
from source.technology_detection_scope_matcher import (
    TechnologyDetectionScopeMatcher,
)
from source.unit_source_search_targets_builder import (
    UnitSourceSearchTargetsBuilder,
)
from source.utf8_source_slice_resolver import UTF8SourceSliceResolver


"""
solid-name: SourceSearchTargetsBuilderFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Provides registered complete-file and parsed-unit search-target construction capabilities.
"""
class SourceSearchTargetsBuilderFactory:
    def make(self) -> SourceSearchTargetsBuilder:
        terms = SourceSearchTargetTermsResolver(
            tokens=ExactSourceTokensResolver(),
            strings=OrderedStringCollector(),
        )
        return SourceSearchTargetsBuilder(
            builders=SourceSearchTargetsBuilderResolver([
                SourceSearchTargetsBuilderRegistration(
                    granularity=SearchTargetGranularity.FILE,
                    builder=FileSourceSearchTargetsBuilder(terms),
                ),
                SourceSearchTargetsBuilderRegistration(
                    granularity=SearchTargetGranularity.UNIT,
                    builder=UnitSourceSearchTargetsBuilder(
                        SourceUnitSearchTargetBuilder(
                            tags=SourceUnitTagsResolver(
                                inherited_scope=TechnologyDetectionScopeMatcher(
                                    TechnologyDetectionScope.FILE
                                )
                            ),
                            terms=terms,
                            source_slice=UTF8SourceSliceResolver(),
                        )
                    ),
                ),
            ])
        )
