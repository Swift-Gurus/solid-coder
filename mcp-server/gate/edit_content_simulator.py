"""
solid-description: Simulates the post-edit file content and low-risk classification for Edit tool events.
solid-category: service
solid-tags: [hook]
"""

from simulated_write import SimulatedWrite
from write_content_simulator import EditClassifying, FileReading


"""
solid-name: EditContentSimulator
solid-description: Simulates prospective file content and review risk for a targeted edit request.
solid-category: service
solid-tags: [hook]
"""
class EditContentSimulator:
    """Simulates the resulting file content and low-risk status for an Edit tool event."""

    def __init__(self, file_reader: FileReading, classifier: EditClassifying) -> None:
        self._reader = file_reader
        self._classifier = classifier

    def simulate(self, tool_name: str, tool_input: dict) -> SimulatedWrite:
        file_path = tool_input.get("file_path", "")
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        replace_all = tool_input.get("replace_all", False)
        low_risk = self._classifier.is_low_risk(old_string, new_string)
        existing = ""
        try:
            existing = self._reader.read_text(file_path)
            content = existing.replace(old_string, new_string) if replace_all \
                      else existing.replace(old_string, new_string, 1)
        except OSError:
            content = new_string
        return SimulatedWrite(
            content=content,
            existing_content=existing,
            low_risk=low_risk,
        )
