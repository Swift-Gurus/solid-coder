"""
solid-description: Provides the public interface for the findings gateway subsystem.
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
from scoring.scoring_handler import ScoringHandling, ScoringHandler  # noqa: F401
from scoring.files_scoring_handler import FilesScoringCapable, FilesScoringHandler  # noqa: F401
from scoring.principle_scorer import PrincipleScorerProviding, PrincipleScorerProvider, UnitScoring  # noqa: F401
from rules.rules_handler import RulesLoading, RulesHandler  # noqa: F401
from rules.fix_instructions_loader import FixInstructionsLoading, FixInstructionsLoader  # noqa: F401
from rules.detection_rules_loader import DetectionRulesLoading, DetectionRulesLoader, AllPrinciplesProviding  # noqa: F401
from rules.principle_content_builder import PrincipleContentBuilding, PrincipleContentBuilder  # noqa: F401


def make_gateway_handler(refs_root: Path) -> GatewayHandler:
    """Wire production defaults and return a ready-to-use GatewayHandler.

    Factory function — constructing and wiring concrete dependencies is this
    function's sole responsibility (OCP Factory exception).
    """
    from rules.principle_registry import PrincipleRegistry
    registry = PrincipleRegistry(refs_root)
    scoring = ScoringHandler(
        scorer_provider=PrincipleScorerProvider(refs_root),
        files_scorer=FilesScoringHandler(),
    )
    return GatewayHandler(
        scoring=scoring,
        submit_orchestrator=SubmitOrchestrator(
            scoring=scoring,
            validator=PartialOutputValidator(refs_root),
            submitter=FindingsSubmitter(JsonFileWriter()),
            summariser=SeveritySummariser(),
        ),
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
    )
