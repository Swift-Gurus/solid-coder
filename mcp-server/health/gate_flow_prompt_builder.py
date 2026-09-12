"""Builds the child-session prompt for an existing gate workflow run."""


"""
solid-name: GateFlowPromptBuilder
solid-category: service
solid-spec: [SPEC-036]
solid-description: Builds a source-review bootstrap that continues one server-started workflow run.
"""
class GateFlowPromptBuilder:
    def build(
        self,
        content: str,
        path: str,
        parent_session_id: str,
        run_id: str,
        first_step: str,
    ) -> str:
        return (
            f"# spawned-by: {parent_session_id}\n\n"
            "Review the exact prospective source below. It is already in your "
            "context for every workflow instruction; do not rediscover or reread "
            "the target path.\n\n"
            f"Target path: {path}\n"
            "<prospective-source>\n"
            f"{content}\n"
            "</prospective-source>\n\n"
            "The server has already started the isolated review run. Complete "
            "the current instruction set exactly as rendered:\n\n"
            f"{first_step}\n\n"
            "Submit the requested outputs with solid-coder-flow-engine.flow_next "
            f"and run_id=\"{run_id}\". Follow each returned instruction and "
            "continue with flow_next until it reports completion or failure."
        )
