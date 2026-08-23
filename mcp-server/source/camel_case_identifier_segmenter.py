"""Segments source identifiers at deterministic case boundaries."""

from source.identifier_segmenting import IdentifierSegmenting


"""
solid-name: CamelCaseIdentifierSegmenter
solid-category: service
solid-spec: [SPEC-040]
solid-description: Divides CamelCase and acronym-bearing source identifiers into ordered lexical components.
"""
class CamelCaseIdentifierSegmenter(IdentifierSegmenting):
    def segment(self, identifier: str) -> list[str]:
        boundaries = [0]
        for index in range(1, len(identifier)):
            previous = identifier[index - 1]
            current = identifier[index]
            following = identifier[index + 1] if index + 1 < len(identifier) else ""
            starts_word = current.isupper() and (
                previous.islower()
                or previous.isdigit()
                or (previous.isupper() and following.islower())
            )
            if starts_word:
                boundaries.append(index)
        boundaries.append(len(identifier))
        return [
            identifier[boundaries[index]:boundaries[index + 1]]
            for index in range(len(boundaries) - 1)
            if boundaries[index] < boundaries[index + 1]
        ]
