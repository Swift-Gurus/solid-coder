#!/usr/bin/env python3
"""
solid-description: Tool implementations for score_severity, submit_findings,
load_detection_rules, and load_fix_instructions. Uses a hierarchy of focused
classes and protocols. Use make_gateway_handler() to wire production defaults.
solid-category: service
solid-tags: [utility, service]
"""

import json
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

from lib.principal_folder_resolver import resolve as _resolve_folder_fn
from lib.severity_scorer import SeverityScorer
from lib.xml_block_parser import parse as parse_xml_blocks
from lib.fix_file_lookup import resolve_single_fix, list_available_fix_metric_ids
from lib.principle_registry import PrincipleRegistry
from lib.load_reference import strip_frontmatter
from lib import discover_principles as _dp


class JsonFileWriting(Protocol):
    def write(self, output_path: str, doc: dict) -> None: ...


class SeveritySummarising(Protocol):
    def summarise(self, scored_files: list) -> dict: ...


class UnitScoring(Protocol):
    def score_unit(self, unit_metrics: dict, metric_id: str) -> dict: ...


class ScoringSeverity(Protocol):
    def score_severity(self, partial_outputs: list) -> dict: ...


class ResolveAndScoring(Protocol):
    def resolve_and_score(self, agent: str, files: list) -> tuple: ...


class SeverityScoring(ScoringSeverity, ResolveAndScoring, Protocol):
    """Composed protocol for ScoringHandler: both public and internal methods."""


class FindingsSubmitting(Protocol):
    def submit(
        self,
        agent: str, principle: str, timestamp: str,
        scored_files: list, output_path: str,
        schema_folder: Optional[Path],
    ) -> Optional[dict]: ...


class SubmitOrchestrating(Protocol):
    def orchestrate(self, partial_output: dict, output_path: str) -> dict: ...


class DetectionRulesLoading(Protocol):
    def load_detection_rules(
        self, principle: Optional[str], matched_tags: Optional[list],
    ) -> dict: ...


class FixInstructionsLoading(Protocol):
    def load_fix_instructions(self, metric_id: str) -> str: ...


class RulesLoading(DetectionRulesLoading, FixInstructionsLoading, Protocol):
    """Composed protocol for both rules loading operations."""


class ScoringHandling(Protocol):
    def score_severity(self, partial_outputs: list) -> dict: ...
    def submit_findings(self, partial_output: dict, output_path: str) -> dict: ...


class GatewayHandling(ScoringHandling, RulesLoading, Protocol):
    """Composed protocol for all four gateway tool operations."""


class AllPrinciplesProviding(Protocol):
    def all_principles(self) -> list: ...


class PrincipleFolderResolving(Protocol):
    def resolve(self, agent: str, refs_root: Path) -> Path: ...


class PrincipleFolderResolver:
    def __init__(
        self,
        resolve_fn: Optional[Callable[[str, Path], Path]] = None,
    ) -> None:
        self._resolve_fn = resolve_fn or _resolve_folder_fn

    def resolve(self, agent: str, refs_root: Path) -> Path:
        return self._resolve_fn(agent, refs_root)


class JsonFileWriter:
    def write(self, output_path: str, doc: dict) -> None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        Path(output_path).write_text(json.dumps(doc, indent=2), encoding="utf-8")


class SeveritySummariser:
    """Counts severe, minor, and compliant units in a list of scored files."""

    def summarise(self, scored_files: list) -> dict:
        total_units = severe_count = minor_count = compliant_count = 0
        for scored_file in scored_files:
            for unit in scored_file.get("units", []):
                severities = {s["final_severity"] for s in unit.get("scoring", [])}
                if "SEVERE" in severities:
                    severe_count += 1
                elif "MINOR" in severities:
                    minor_count += 1
                else:
                    compliant_count += 1
                total_units += 1
        status = "SEVERE" if severe_count else ("MINOR" if minor_count else "COMPLIANT")
        return {
            "total_units": total_units,
            "severe_count": severe_count,
            "minor_count": minor_count,
            "compliant_count": compliant_count,
            "status": status,
        }


class FindingsSubmitter:
    """Writes a scored partial output document to disk."""

    def __init__(self, file_writer: Optional[JsonFileWriting] = None) -> None:
        self._file_writer = file_writer or JsonFileWriter()

    def submit(
        self,
        agent: str, principle: str, timestamp: str,
        scored_files: list, output_path: str,
        schema_folder: Optional[Path],
    ) -> Optional[dict]:
        all_compliant = len(scored_files) == 0
        doc = {"agent": agent, "principle": principle, "timestamp": timestamp,
               "files": scored_files, "all_compliant": all_compliant}
        self._file_writer.write(output_path, doc)
        return None


class ScoringHandler:
    """Resolves principles and scores units in partial review outputs."""

    def __init__(
        self,
        refs_root: Path,
        scorer_factory: Optional[Callable[[Path], UnitScoring]] = None,
        folder_resolver: Optional[PrincipleFolderResolving] = None,
    ) -> None:
        self._refs_root = refs_root
        self._scorer_factory = scorer_factory or SeverityScorer.from_folder
        self._folder_resolver = folder_resolver or PrincipleFolderResolver()

    def _score_files(self, scorer: UnitScoring, files: list) -> tuple[list, Optional[dict]]:
        scored_files = []
        for file_obj in files:
            scored_units = []
            for unit in file_obj.get("units", []):
                metrics = unit.get("metrics", {})
                unit_scores: list = []
                unit_findings: list = []

                for metric_id in list(metrics.keys()):
                    r = scorer.score_unit(metrics[metric_id], metric_id)
                    if "error" in r:
                        return scored_files, {"error": r["error"]}
                    unit_scores.append(r)
                    if r["final_severity"] != "COMPLIANT":
                        unit_findings.append({
                            "metric_id": metric_id,
                            "severity": r["final_severity"],
                            "band_matched": r.get("band_matched"),
                        })

                scored_unit = dict(unit)
                scored_unit["scoring"] = unit_scores
                scored_unit["findings"] = unit_findings
                scored_units.append(scored_unit)

            scored_file = dict(file_obj)
            scored_file["units"] = scored_units
            scored_files.append(scored_file)

        return scored_files, None

    def resolve_and_score(
        self, agent: str, files: list,
    ) -> tuple[list, Optional[dict], Optional[Path]]:
        if not files:
            return [], None, None

        try:
            folder = self._folder_resolver.resolve(agent, self._refs_root)
        except (ValueError, FileNotFoundError) as exc:
            return [], {"error": str(exc)}, None

        scorer = self._scorer_factory(folder)
        scored_files, error = self._score_files(scorer, files)
        return scored_files, error, folder

    def score_severity(self, partial_outputs: list) -> dict[str, Any]:
        results = []
        for idx, entry in enumerate(partial_outputs):
            scored_files, error, _ = self.resolve_and_score(
                entry.get("agent", ""), entry.get("files", []),
            )
            if error:
                results.append({**error, "entry_index": idx})
                continue

            scored_entry = dict(entry)
            scored_entry["files"] = scored_files
            results.append(scored_entry)

        return {"results": results}


class SubmitOrchestrator:
    """Orchestrates the score → submit → summarise flow for submit_findings."""

    def __init__(
        self,
        scoring: ResolveAndScoring,
        submitter: FindingsSubmitting,
        summariser: SeveritySummarising,
    ) -> None:
        self._scoring = scoring
        self._submitter = submitter
        self._summariser = summariser

    def orchestrate(self, partial_output: dict, output_path: str) -> dict[str, Any]:
        agent = partial_output.get("agent", "")
        principle = partial_output.get("principle", "")
        timestamp = partial_output.get("timestamp", "")
        scored_files, error, folder = self._scoring.resolve_and_score(agent, partial_output.get("files") or [])
        if error:
            return error
        err = self._submitter.submit(agent, principle, timestamp, scored_files, output_path, folder)
        if err:
            return err
        counts = self._summariser.summarise(scored_files)
        return {"principle": principle, **counts}


class DetectionRulesLoader:
    """Loads per-metric detection rules from principle rule.md XML blocks."""

    def __init__(
        self,
        all_principles: AllPrinciplesProviding,
        discover_fn: Optional[Callable] = None,
    ) -> None:
        self._all_principles = all_principles
        self._discover_fn = discover_fn or _dp.discover_and_filter

    def load_detection_rules(
        self,
        principle: Optional[str] = None,
        matched_tags: Optional[list] = None,
    ) -> dict[str, Any]:
        def _build(p_entry: dict) -> dict:
            raw = Path(p_entry["rule_path"]).read_text(encoding="utf-8")
            blocks = parse_xml_blocks(raw)
            if not (blocks["detection"] or blocks["definition"] or blocks["severity-bands"]):
                return {"name": p_entry["name"], "full_content": strip_frontmatter(raw)}
            return {
                "name": p_entry["name"],
                "detection": blocks["detection"],
                "definition": blocks["definition"],
                "severity_bands": blocks["severity-bands"],
                "exceptions": blocks["exceptions"],
            }

        all_p = self._all_principles.all_principles()

        if principle:
            m = next((p for p in all_p if p["name"].lower() == principle.lower()), None)
            if not m:
                available = ", ".join(p["name"] for p in all_p)
                return {"error": f"Principle '{principle}' not found. Available: {available}"}
            return {"principles": [_build(m)]}

        refs_root = Path(all_p[0]["folder"]).parent if all_p else Path()
        active = self._discover_fn(str(refs_root), matched_tags=matched_tags)["active_principles"] \
            if matched_tags else all_p
        return {"principles": [_build(p) for p in active]}


class FixInstructionsLoader:
    """Loads fix strategy text for a given metric ID."""

    def __init__(self, all_principles: AllPrinciplesProviding) -> None:
        self._all_principles = all_principles

    def load_fix_instructions(self, metric_id: str) -> str:
        norm = metric_id.strip().upper()
        all_p = self._all_principles.all_principles()
        result = resolve_single_fix(norm, all_p)
        if result is None:
            available = list_available_fix_metric_ids(all_p)
            return f"No fix file for metric '{norm}'. Available: {', '.join(available)}"

        content = strip_frontmatter(result["content"]).rstrip()
        return f"# {result['principle']} — {norm} Fix Strategy\n\n{content}\n"


class RulesHandler:
    """Facade composing DetectionRulesLoader and FixInstructionsLoader."""

    def __init__(
        self,
        detection: DetectionRulesLoading,
        fix_instructions: FixInstructionsLoading,
    ) -> None:
        self._detection = detection
        self._fix_instructions = fix_instructions

    def load_detection_rules(
        self, principle: Optional[str] = None, matched_tags: Optional[list] = None,
    ) -> dict[str, Any]:
        return self._detection.load_detection_rules(principle, matched_tags)

    def load_fix_instructions(self, metric_id: str) -> str:
        return self._fix_instructions.load_fix_instructions(metric_id)


class GatewayHandler:
    """Pure Facade delegating to ScoringSeverity, SubmitOrchestrating, and RulesLoading.

    All dependencies are protocol-typed and injected via __init__. No internal
    construction — use make_gateway_handler() for production wiring.
    """

    def __init__(
        self,
        scoring: ScoringSeverity,
        submit_orchestrator: SubmitOrchestrating,
        rules: RulesLoading,
    ) -> None:
        self._scoring = scoring
        self._submit_orchestrator = submit_orchestrator
        self._rules = rules

    def score_severity(self, partial_outputs: list) -> dict[str, Any]:
        return self._scoring.score_severity(partial_outputs)

    def submit_findings(self, partial_output: dict, output_path: str) -> dict[str, Any]:
        return self._submit_orchestrator.orchestrate(partial_output, output_path)

    def load_detection_rules(
        self, principle: Optional[str] = None, matched_tags: Optional[list] = None,
    ) -> dict[str, Any]:
        return self._rules.load_detection_rules(principle, matched_tags)

    def load_fix_instructions(self, metric_id: str) -> str:
        return self._rules.load_fix_instructions(metric_id)


def make_gateway_handler(refs_root: Path) -> GatewayHandler:
    """Wire production defaults and return a ready-to-use GatewayHandler."""
    registry = PrincipleRegistry(refs_root)
    scoring = ScoringHandler(refs_root)
    return GatewayHandler(
        scoring=scoring,
        submit_orchestrator=SubmitOrchestrator(
            scoring=scoring,
            submitter=FindingsSubmitter(),
            summariser=SeveritySummariser(),
        ),
        rules=RulesHandler(
            detection=DetectionRulesLoader(registry),
            fix_instructions=FixInstructionsLoader(registry),
        ),
    )
