"""Collects unique strings in first-seen order."""

from harness.ordered_string_collecting import OrderedStringCollecting


"""
solid-name: OrderedStringCollector
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Combines string collections while preserving first-seen order.
"""
class OrderedStringCollector(OrderedStringCollecting):

    def collect(self, collections: list[list[str]]) -> list[str]:
        result: list[str] = []
        for collection in collections:
            for value in collection:
                if value not in result:
                    result.append(value)
        return result
