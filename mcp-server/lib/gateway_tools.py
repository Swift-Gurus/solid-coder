"""Builds the fully configured model-facing gateway."""

from pathlib import Path
from typing import Optional

from findings.batch_submission_decorating import BatchSubmissionDecorating
from findings.batch_submission_handling import BatchSubmissionHandling
from findings.batch_submission_coordinator import BatchSubmissionCoordinator
from findings.batch_submission_preparer import BatchSubmissionPreparer
from findings.batch_unit_coverage_validator import BatchUnitCoverageValidator
from findings.fix_completeness_validator import FixCompletenessValidator
from findings.fix_persister import FixPersister
from findings.fix_submitter import FixSubmitter
from findings.gateway_handler import GatewayHandler, GatewayHandling
from findings.hook_context_ownership_validator import HookContextOwnershipValidator
from findings.hook_context_path_resolver import HookContextPathResolver
from findings.json_additional_info_decoder import JsonAdditionalInfoDecoder
from findings.json_file_writer import JsonFileWriter
from findings.json_hook_context_parser import JsonHookContextParser
from findings.json_partial_review_output_renderer import (
    JsonPartialReviewOutputRenderer,
)
from findings.mapping_principle_coverage_scope_input_parser import (
    MappingPrincipleCoverageScopeInputParser,
)
from findings.mcp_batch_submission_builder import McpBatchSubmissionBuilder
from findings.mcp_batch_submission_handler import McpBatchSubmissionHandler
from findings.mcp_batch_submission_parser import McpBatchSubmissionParser
from findings.mcp_batch_submission_payload_validator import (
    McpBatchSubmissionPayloadValidator,
)
from findings.mcp_batch_submission_response_formatter import (
    McpBatchSubmissionResponseFormatter,
)
from findings.ordered_batch_submission_persister import (
    OrderedBatchSubmissionPersister,
)
from findings.partial_output_validator import PartialOutputValidator
from findings.partial_review_output_persister import PartialReviewOutputPersister
from findings.principle_coverage_scope_factory import PrincipleCoverageScopeFactory
from findings.principle_coverage_scope_input_factory import (
    PrincipleCoverageScopeInputFactory,
)
from findings.principle_coverage_scope_parser import PrincipleCoverageScopeParser
from findings.principle_coverage_scopes_factory import PrincipleCoverageScopesFactory
from findings.principle_submission_submitter import PrincipleSubmissionSubmitter
from findings.requested_hook_context_loader import RequestedHookContextLoader
from findings.severity_summariser import SeveritySummariser
from findings.submission_context_applier import SubmissionContextApplier
from findings.submit_orchestrator import SubmitOrchestrator
from findings.unit_coverage_validator import load_applies_to
from findings.violation_reader import ViolationReader
from findings.violation_response_formatting import ViolationResponseFormatter
from findings.review_unit_kind_parser import ReviewUnitKindParser
from findings.review_unit_kinds_parser import ReviewUnitKindsParser
from findings.findings_submitter import FindingsSubmitter
from findings.utf8_text_file_writer import Utf8TextFileWriter
from harness.path_builder import PathBuilder
from health.llama.json_deserializer import JsonDeserializer
from json_serializer import JsonSerializer
from rules.detection_rules_loader import DetectionRulesLoader
from rules.fix_instructions_loader import FixInstructionsLoader
from rules.principle_content_builder import PrincipleContentBuilder
from rules.principle_registry import PrincipleRegistry
from rules.rules_handler import RulesHandler
from scoring.files_scoring_handler import FilesScoringHandler
from scoring.principle_scorer import PrincipleScorerProvider
from scoring.principle_submission_scorer import PrincipleSubmissionScorer
from scoring.review_unit_scorer import ReviewUnitScorer
from scoring.scoring_handler import ScoringHandler
from utils.prompt_builder import PlainTextFileReader


"""
solid-name: GatewayHandlerFactory
solid-category: factory
solid-description: Builds the production gateway and its scoring, submission, rule, and fix capabilities.
"""
class GatewayHandlerFactory:
    def __init__(
        self,
        batch_decorator: Optional[BatchSubmissionDecorating] = None,
    ) -> None:
        self._batch_decorator = batch_decorator

    def make(self, refs_root: Path) -> GatewayHandler:
        path_builder = PathBuilder()
        json_deserializer = JsonDeserializer()
        json_serializer = JsonSerializer()
        registry = PrincipleRegistry(refs_root)
        principle_scorers = PrincipleScorerProvider(refs_root)
        scoring = ScoringHandler(
            scorer_provider=principle_scorers,
            files_scorer=FilesScoringHandler(),
        )
        partial_output_validator = PartialOutputValidator(refs_root)
        submit_orchestrator = SubmitOrchestrator(
            scoring=scoring,
            validator=partial_output_validator,
            submitter=FindingsSubmitter(JsonFileWriter(json_serializer)),
            summariser=SeveritySummariser(),
        )
        scope_parser = PrincipleCoverageScopeParser(
            input_parser=MappingPrincipleCoverageScopeInputParser(
                PrincipleCoverageScopeInputFactory()
            ),
            scopes_factory=PrincipleCoverageScopesFactory(
                unit_kinds_parser=ReviewUnitKindsParser(ReviewUnitKindParser()),
                scope_factory=PrincipleCoverageScopeFactory(),
            ),
        )
        context_loader = RequestedHookContextLoader(
            path_resolver=HookContextPathResolver(path_builder),
            reader=PlainTextFileReader(),
            parser=JsonHookContextParser(json_deserializer),
            ownership_validator=HookContextOwnershipValidator(path_builder),
        )
        preparer = BatchSubmissionPreparer(
            context_loader=context_loader,
            context_applier=SubmissionContextApplier(),
            coverage_validator=BatchUnitCoverageValidator(
                scope_parser.parse(load_applies_to(refs_root))
            ),
        )
        persister = OrderedBatchSubmissionPersister(
            submission_submitter=PrincipleSubmissionSubmitter(
                scoring=PrincipleSubmissionScorer(
                    ReviewUnitScorer(principle_scorers)
                ),
                persisting=PartialReviewOutputPersister(
                    renderer=JsonPartialReviewOutputRenderer(
                        serializer=json_serializer,
                        additional_info_decoder=JsonAdditionalInfoDecoder(
                            json_deserializer
                        ),
                    ),
                    writer=Utf8TextFileWriter(),
                ),
            ),
            path_builder=path_builder,
        )
        response_formatter = McpBatchSubmissionResponseFormatter(
            violation_reader=ViolationReader(),
            violation_formatter=ViolationResponseFormatter(),
        )
        batch_coordinator = BatchSubmissionCoordinator(
            preparer=preparer,
            persister=persister,
            response_formatter=response_formatter,
        )
        batch_handler: BatchSubmissionHandling = batch_coordinator
        if self._batch_decorator is not None:
            batch_handler = self._batch_decorator.make_submission(batch_coordinator)
        batch_submission = McpBatchSubmissionHandler(
            parser=McpBatchSubmissionParser(
                payload_validator=McpBatchSubmissionPayloadValidator(),
                output_validator=partial_output_validator,
                builder=McpBatchSubmissionBuilder(json_serializer),
            ),
            handler=batch_handler,
        )
        return GatewayHandler(
            scoring=scoring,
            submit_orchestrator=submit_orchestrator,
            rules=RulesHandler(
                detection=DetectionRulesLoader(
                    all_principles=registry,
                    refs_root=refs_root,
                    content_builder=PrincipleContentBuilder(),
                ),
                fix_instructions=FixInstructionsLoader(registry),
            ),
            fix_submitter=FixSubmitter(
                persister=FixPersister(),
                completeness=FixCompletenessValidator(ViolationReader()),
            ),
            batch_submission=batch_submission,
        )


def make_gateway_handler(
    refs_root: Path,
    batch_decorator: Optional[BatchSubmissionDecorating] = None,
) -> GatewayHandler:
    """Build a gateway with production collaborators."""
    return GatewayHandlerFactory(batch_decorator).make(refs_root)
