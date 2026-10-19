"""Configured path exclusions retain every glob segment."""

import unittest

from hook_utils import path_matches_pattern


class TestPathPatternMatcher(unittest.TestCase):
    def test_recursive_pattern_preserves_extension(self):
        self.assertTrue(path_matches_pattern("/repo/Vendor/Lib/A.swift", "Vendor/**/*.swift"))
        self.assertFalse(path_matches_pattern("/repo/Vendor/Lib/A.json", "Vendor/**/*.swift"))

    def test_recursive_segment_can_match_zero_directories(self):
        self.assertTrue(path_matches_pattern("/repo/Vendor/A.swift", "Vendor/**/*.swift"))

    def test_recursive_suffix_remains_required(self):
        self.assertTrue(path_matches_pattern("/repo/Sources/A/Generated/B.swift", "Sources/**/Generated/*.swift"))
        self.assertFalse(path_matches_pattern("/repo/Sources/A/B.swift", "Sources/**/Generated/*.swift"))

    def test_single_star_does_not_cross_directory_boundary(self):
        self.assertTrue(path_matches_pattern("/repo/Sources/A.swift", "Sources/*.swift"))
        self.assertFalse(path_matches_pattern("/repo/Sources/Nested/A.swift", "Sources/*.swift"))

    def test_existing_directory_and_basename_patterns(self):
        self.assertTrue(path_matches_pattern("/repo/tests/fixtures/A.swift", "tests/**"))
        self.assertFalse(path_matches_pattern("/repo/contest/A.swift", "tests/**"))
        self.assertTrue(path_matches_pattern("/repo/Sources/A.generated.swift", "*.generated.swift"))

    def test_absolute_pattern_does_not_match_sibling_root(self):
        self.assertTrue(path_matches_pattern("/repo/Vendor/A.swift", "/repo/Vendor/**"))
        self.assertFalse(path_matches_pattern("/other/repo/Vendor/A.swift", "/repo/Vendor/**"))

    def test_path_separator_normalization(self):
        self.assertTrue(path_matches_pattern("C:\\repo\\tests\\A.swift", "tests/**"))
