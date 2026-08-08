"""Extracts searchable query terms with regular expressions."""

import re


"""
solid-name: RegexSearchTermExtractor
solid-category: boundary-adapter
solid-description: Extracts individual searchable terms from free-form query text.
"""
class RegexSearchTermExtractor:
    def extract(self, query: str) -> list[str]:
        return re.findall(r"\w+", query, flags=re.UNICODE)
