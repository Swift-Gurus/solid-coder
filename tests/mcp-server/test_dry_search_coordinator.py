"""Verifies validation and completion behavior for health-check DRY searches."""

from unittest.mock import MagicMock

from health.dry_search_coordinator import DrySearchCoordinator
from search.regex_search_term_extractor import RegexSearchTermExtractor
from search.search_terms_resolver import SearchTermsResolver


"""
solid-name: TestDrySearchCoordinator
solid-category: unit-test
solid-description: Verifies health-check DRY searches reject malformed input and record only successful completion.
"""
class TestDrySearchCoordinator:
    def setup_method(self) -> None:
        self.search = MagicMock()
        self.completion = MagicMock()
        self.coordinator = DrySearchCoordinator(
            search=self.search,
            terms=SearchTermsResolver(RegexSearchTermExtractor()),
            completion=self.completion,
        )

    def test_query_delegates_as_individual_tags(self) -> None:
        self.search.search.return_value = "one match"

        result = self.coordinator.search(
            query="Batch handler routing",
            output_dir="/health/run",
        )

        assert result == "one match"
        self.search.search.assert_called_once_with(
            sources_dir=None,
            plan_path=None,
            tags=["Batch", "handler", "routing"],
            spec_numbers=None,
            min_matches=3,
        )

    def test_aggregated_query_inside_tags_is_rejected_without_search(self) -> None:
        result = self.coordinator.search(
            tags=["Batch handler routing"],
            output_dir="/health/run",
        )

        assert result.startswith("Error:")
        self.search.search.assert_not_called()
        self.completion.record.assert_not_called()

    def test_zero_match_result_records_successful_completion(self) -> None:
        self.search.search.return_value = "No files matched in /project (12 files scanned)."

        self.coordinator.search(query="Batch handler", output_dir="/health/run")

        self.completion.record.assert_called_once_with("/health/run")

    def test_search_error_does_not_record_completion(self) -> None:
        self.search.search.return_value = "Error: sources_dir not found"

        self.coordinator.search(query="Batch handler", output_dir="/health/run")

        self.completion.record.assert_not_called()

    def test_search_without_output_directory_does_not_record_completion(self) -> None:
        self.search.search.return_value = "one match"

        self.coordinator.search(query="Batch handler")

        self.completion.record.assert_not_called()
