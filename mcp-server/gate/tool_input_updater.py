"""
solid-description: Transforms corrected content into the appropriate input format for different tool types.
solid-category: service
solid-tags: [hook]
"""

from tool_input_updating import ToolInputUpdating


class ToolInputUpdater(ToolInputUpdating):
    def build(self, tool_name: str, tool_input: dict, corrected: str, existing: str) -> dict:
        updated = dict(tool_input)
        if tool_name == "Write":
            updated["content"] = corrected
        elif existing:
            updated["old_string"] = existing
            updated["new_string"] = corrected
            updated.pop("replace_all", None)
        else:
            updated["new_string"] = corrected
        return updated
