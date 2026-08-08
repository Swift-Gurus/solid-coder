"""Builds production health-check context writers."""

from active_health_check_pointer_store import ActiveHealthCheckPointerStore
from code_unit_extractor import CodeUnitExtractor
from dry_search_service_factory import DrySearchServiceFactory
from findings.json_file_writer import JsonFileWriter
from health_check_context_writer import HealthCheckContextWriter
from health_check_input_writer import HealthCheckInputWriter
from hook_utils import solid_coder_project_dir
from json_serializer import JsonSerializer
from llama.directory_creator import PathDirectoryCreator


"""
solid-name: HealthCheckContextWriterFactory
solid-category: factory
solid-description: Builds the production service for health-check context and active-check lifecycle tracking.
"""
class HealthCheckContextWriterFactory:
    def make(self) -> HealthCheckContextWriter:
        return HealthCheckContextWriter(
            project_dir_fn=solid_coder_project_dir,
            input_writer=HealthCheckInputWriter(
                extractor=CodeUnitExtractor(),
                writer=JsonFileWriter(JsonSerializer()),
                dir_creator=PathDirectoryCreator(),
                completion=DrySearchServiceFactory().make_completion_store(),
            ),
            pointer_store=ActiveHealthCheckPointerStore(),
        )
