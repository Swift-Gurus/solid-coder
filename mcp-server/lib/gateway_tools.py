"""
solid-description: Provides gateway handlers for submitting code findings with validation and scoring.
solid-category: service
solid-tags: [utility, service]
"""

from pathlib import Path

from findings.gateway_handler import GatewayHandler, GatewayHandling  # noqa: F401
from findings.fix_submitter import FixSubmitting, FixSubmitter  # noqa: F401
from findings.fix_persister import FixPersisting, FixPersister  # noqa: F401
from findings.fix_completeness_validator import FixCompletenessValidating, FixCompletenessValidator  # noqa: F401
from findings.submit_orchestrator import SubmitOrchestrating, SubmitOrchestrator, ResolveAndScoring  # noqa: F401
from findings.partial_output_validator import PartialOutputValidating, PartialOutputValidator  # noqa: F401
from findings.findings_submitter import FindingsSubmitting, FindingsSubmitter  # noqa: F401
from findings.severity_summariser import SeveritySummarising, SeveritySummariser  # noqa: F401
from findings.json_file_writer import JsonFileWriting, JsonFileWriter  # noqa: F401
from findings.violation_reader import ViolationReading, ViolationReader  # noqa: F401
from findings.batch_submission_handler import BatchSubmissionHandler, ViolationResponseFormatter  # noqa: F401
from findings.hook_context_loader import FileSystemHookContextLoader  # noqa: F401
from findings.unit_coverage_validator import UnitCoverageValidator, load_applies_to  # noqa: F401
from scoring.scoring_handler import ScoringHandling, ScoringHandler  # noqa: F401
from scoring.files_scoring_handler import FilesScoringCapable, FilesScoringHandler  # noqa: F401
from scoring.principle_scorer import PrincipleScorerProviding, PrincipleScorerProvider, UnitScoring  # noqa: F401
from rules.rules_handler import RulesLoading, RulesHandler  # noqa: F401
from rules.fix_instructions_loader import FixInstructionsLoading, FixInstructionsLoader  # noqa: F401
from rules.detection_rules_loader import DetectionRulesLoading, DetectionRulesLoader, AllPrinciplesProviding  # noqa: F401
from rules.principle_content_builder import PrincipleContentBuilding, PrincipleContentBuilder  # noqa: F401


class ValidatedGatewayHandler(GatewayHandler):
    """GatewayHandler subclass that routes submit_batch_findings through BatchSubmissionHandler.

    Adds unit-coverage validation and injectable hook-context loading without modifying
    the base class. Factory exception — wiring concrete collaborators is this class's
    sole responsibility.
    """

    def __init__(self, *args, batch_handler: BatchSubmissionHandler, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._batch_handler = batch_handler

    def submit_batch_findings(self, output_dir: str, submissions: dict) -> dict:
        return self._batch_handler.submit_batch(output_dir, submissions)


class GatewayHandlerFactory:
    """Wires production defaults and creates a ready-to-use ValidatedGatewayHandler.

    Factory class — constructing and wiring concrete dependencies is this
    class's sole responsibility (OCP Factory exception).
    """

    def make(self, refs_root: Path) -> ValidatedGatewayHandler:
        from rules.principle_registry import PrincipleRegistry
        registry = PrincipleRegistry(refs_root)
        scoring = ScoringHandler(
            scorer_provider=PrincipleScorerProvider(refs_root),
            files_scorer=FilesScoringHandler(),
        )
        submit_orchestrator = SubmitOrchestrator(
            scoring=scoring,
            validator=PartialOutputValidator(refs_root),
            submitter=FindingsSubmitter(JsonFileWriter()),
            summariser=SeveritySummariser(),
        )
        context_loader = FileSystemHookContextLoader()
        batch_handler = BatchSubmissionHandler(
            submit_orchestrator=submit_orchestrator,
            context_loader=context_loader,
            violation_reader=ViolationReader(),
            response_formatter=ViolationResponseFormatter(),
            coverage_validator=UnitCoverageValidator(
                context_loader=context_loader,
                applies_to=load_applies_to(refs_root),
            ),
        )
        return ValidatedGatewayHandler(
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
            batch_handler=batch_handler,
        )


def make_gateway_handler(refs_root: Path) -> ValidatedGatewayHandler:
    """Backward-compatible shim — delegates to GatewayHandlerFactory."""
    return GatewayHandlerFactory().make(refs_root)
