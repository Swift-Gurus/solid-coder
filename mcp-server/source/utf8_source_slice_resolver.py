"""Resolves exact source slices from UTF-8 parser offsets."""


"""
solid-name: UTF8SourceSliceResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Extracts immutable source text using the UTF-8 byte offsets returned by source parsers.
"""
class UTF8SourceSliceResolver:
    def resolve(self, source: str, start_offset: int, end_offset: int) -> str:
        encoded = source.encode("utf-8")
        return encoded[start_offset:end_offset + 1].decode("utf-8")
