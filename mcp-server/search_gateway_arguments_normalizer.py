"""Normalizes search command arguments for gateway compatibility."""

from gateway_arguments import GatewayArguments
from gateway_arguments_normalizing import GatewayArgumentsNormalizing


"""
solid-name: SearchGatewayArgumentsNormalizer
solid-category: boundary-adapter
solid-description: Applies search-command compatibility rules to parsed gateway arguments.
"""
class SearchGatewayArgumentsNormalizer(GatewayArgumentsNormalizing):
    def normalize(self, arguments: GatewayArguments) -> GatewayArguments:
        if arguments.tool_name != "search_codebase":
            return arguments
        values = arguments.values
        if "synonyms" in values:
            values.setdefault("tags", values.pop("synonyms"))
        for key in ("tags", "spec_numbers"):
            if key in values and isinstance(values[key], str):
                values[key] = [values[key]]
        if "min_matches" in values:
            try:
                values["min_matches"] = int(values["min_matches"])
            except (ValueError, TypeError):
                pass
        if "sources_dir" not in values:
            raise ValueError("--sources-dir is required for search_codebase")
        return arguments
