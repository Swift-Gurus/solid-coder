#!/usr/bin/env python3
"""
solid-description: Evaluates code units against design principles and reports violations with fix guidance.
solid-category: service
solid-tags: [utility, service]
"""

import copy
import html
import json
import re
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

try:
    import jsonschema as _jsonschema
    _JSONSCHEMA_AVAILABLE = True
except ImportError:
    _jsonschema = None  # type: ignore[assignment]
    _JSONSCHEMA_AVAILABLE = False

from lib.principal_folder_resolver import resolve as _resolve_folder_fn
from lib.severity_scorer import SeverityScorer
from lib.xml_block_parser import parse as parse_xml_blocks
from lib.fix_file_lookup import resolve_single_fix, list_available_fix_metric_ids
from lib.principle_registry import PrincipleRegistry
from lib.load_reference import strip_frontmatter
from lib.unit_kind_filter import filter_by_unit_kind as _filter_by_kind
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


class PrincipleScorerProviding(Protocol):
    def scorer_for(self, agent: str) -> tuple: ...


class PrincipleScorerProvider:
    """Resolves a principle folder and constructs a scorer for it."""

    def __init__(
        self,
        refs_root: Path,
        scorer_factory: Optional[Callable[[Path], UnitScoring]] = None,
        folder_resolver: Optional[Callable[[str, Path], Path]] = None,
    ) -> None:
        self._refs_root = refs_root
        self._scorer_factory = scorer_factory or SeverityScorer.from_folder
        self._folder_resolver = folder_resolver or _resolve_folder_fn

    def scorer_for(self, agent: str) -> tuple:
        try:
            folder = self._folder_resolver(agent, self._refs_root)
        except (ValueError, FileNotFoundError) as exc:
            return None, {"error": str(exc)}, None
        return self._scorer_factory(folder), None, folder


class FilesScoringCapable(Protocol):
    def score_files(self, scorer: UnitScoring, files: list) -> tuple: ...


_CONDITION_VAR_RE = re.compile(r'\b([a-z][a-z0-9_]*)\b')
_CONDITION_EXTRACT_RE = re.compile(r'<condition>(.*?)</condition>', re.DOTALL)
_PYTHON_KEYWORDS = frozenset({"and", "or", "not", "in", "is", "True", "False", "None"})


def _condition_var_names(bands_xml: str) -> set[str]:
    """Extract identifier names used in severity-band condition expressions."""
    names: set[str] = set()
    for cond in _CONDITION_EXTRACT_RE.findall(bands_xml):
        for m in _CONDITION_VAR_RE.finditer(html.unescape(cond)):
            name = m.group(1)
            if name not in _PYTHON_KEYWORDS:
                names.add(name)
    return names


def _lookup_metric_var(var_name: str, metrics: dict) -> Any:
    """Resolve a condition variable name to a scalar value from the LLM's nested metrics dict.

    Lookup order:
      1. Exact key (e.g. cohesion_groups → metrics["cohesion_groups"]["count"])
      2. Strip _count suffix then try base key and pluralised key
         (e.g. verb_count → "verb" → "verbs" → metrics["verbs"]["count"])
    """
    def _extract(val: Any) -> Any:
        return val["count"] if isinstance(val, dict) and "count" in val else val

    if var_name in metrics:
        return _extract(metrics[var_name])
    if var_name.endswith("_count"):
        stem = var_name[:-6]
        for candidate in (stem, stem + "s"):
            if candidate in metrics:
                return _extract(metrics[candidate])
    return None


def _resolve_bands(metrics: dict, scorer: Any) -> dict[str, dict]:
    """Build a flat variable namespace per severity-band metric_id.

    The LLM fills metrics using the principle's output schema (semantic keys like
    'verbs': {'count': 6}). Severity-band conditions reference variable names like
    'verb_count'. This function bridges the two representations so SeverityScorer
    receives the flat dict it expects without schema changes.
    """
    band_blocks = scorer._blocks.get("severity-bands", {})
    resolved: dict[str, dict] = {}
    for metric_id, bands_xml in band_blocks.items():
        flat: dict[str, Any] = {}
        for var in _condition_var_names(bands_xml):
            val = _lookup_metric_var(var, metrics)
            if val is not None:
                flat[var] = val
        resolved[metric_id] = flat
    return resolved


class FilesScoringHandler:
    """Scores units in a list of files using a provided scorer."""

    def score_files(self, scorer: UnitScoring, files: list) -> tuple:
        # Accept any non-string iterable; reject non-iterables and strings
        # (strings have __iter__ but are not valid file lists)
        if not hasattr(files, "__iter__") or hasattr(files, "lower"):
            return [], {"error": "'files' must be a list of file objects"}
        scored_files = []
        for file_obj in files:
            scored_units = []
            for unit in file_obj.get("units", []):
                metrics = unit.get("metrics", {})
                unit_scores: list = []
                unit_findings: list = []

                _file_path = file_obj.get("file_path", "?")
                _unit_name = unit.get("unit_name", "?")
                for metric_id, flat_vars in _resolve_bands(metrics, scorer).items():
                    r = scorer.score_unit(flat_vars, metric_id)
                    if "error" in r:
                        return scored_files, {
                            "error": (
                                f"{_file_path}, unit {_unit_name}: metric variable missing "
                                f"during {metric_id} evaluation. Ensure all required fields "
                                f"are present per the <submission-metrics-example>. "
                                f"({r['error']})"
                            )
                        }
                    unit_scores.append(r)
                    if r["final_severity"] != "COMPLIANT":
                        unit_findings.append({
                            "metric_id": metric_id,
                            "severity": r["final_severity"],
                            "band_matched": r.get("band_matched"),
                            "metrics": flat_vars,
                        })

                scored_unit = dict(unit)
                scored_unit["scoring"] = unit_scores
                scored_unit["findings"] = unit_findings
                scored_units.append(scored_unit)

            scored_file = dict(file_obj)
            scored_file["units"] = scored_units
            scored_files.append(scored_file)

        return scored_files, None


class ScoringHandler:
    """Facade coordinating principle resolution, unit scoring, and batch severity evaluation."""

    def __init__(
        self,
        scorer_provider: PrincipleScorerProviding,
        files_scorer: FilesScoringCapable,
    ) -> None:
        self._scorer_provider = scorer_provider
        self._files_scorer = files_scorer

    def resolve_and_score(
        self, agent: str, files: list,
    ) -> tuple[list, Optional[dict], Optional[Path]]:
        if not files:
            return [], None, None
        scorer, error, folder = self._scorer_provider.scorer_for(agent)
        if error:
            return [], error, None
        scored_files, err = self._files_scorer.score_files(scorer, files)
        return scored_files, err, folder

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


class PartialOutputValidating(Protocol):
    def validate_output(self, partial_output: dict, folder: Optional[Path]) -> Optional[dict]: ...


class PartialOutputValidator:
    """Validates a partial_output dict against the principle's review/output.schema.json.

    Strips 'scoring' and 'findings' from the unit-level required list before validating
    because those fields are server-filled — the LLM only provides metrics.
    No-ops when jsonschema is unavailable or no schema file exists for the principle.
    """

    def validate_output(self, partial_output: dict, folder: Optional[Path]) -> Optional[dict]:
        if not _JSONSCHEMA_AVAILABLE or folder is None:
            return None
        schema_path = folder / "review" / "output.schema.json"
        if not schema_path.exists():
            return None
        principle = partial_output.get("principle", str(folder.name))
        schema = copy.deepcopy(json.loads(schema_path.read_text(encoding="utf-8")))
        try:
            unit_items = (
                schema["properties"]["files"]["items"]
                ["properties"]["units"]["items"]
            )
            server_filled = {"scoring", "findings"}
            unit_items["required"] = [
                f for f in unit_items.get("required", []) if f not in server_filled
            ]
        except (KeyError, TypeError):
            pass
        try:
            _jsonschema.validate(partial_output, schema)
        except _jsonschema.ValidationError as exc:
            # Extract file/unit location from the validation path
            vpath = list(exc.absolute_path)
            file_path = "?"
            unit_name = "?"
            if len(vpath) >= 2 and vpath[0] == "files":
                try:
                    fidx = vpath[1]
                    files_list = partial_output.get("files", [])
                    file_path = files_list[fidx].get("file_path", "?")
                    if len(vpath) >= 4 and vpath[2] == "units":
                        uidx = vpath[3]
                        unit_name = files_list[fidx].get("units", [])[uidx].get("unit_name", "?")
                except (IndexError, AttributeError):
                    pass
            return {
                "error": (
                    f"{file_path}, unit {unit_name}: {exc.message}. "
                    f"Use the <submission-metrics-example> format from load_detection_rules output."
                )
            }
        return None


class SubmitOrchestrator:
    """Orchestrates the score → validate → submit → summarise flow for submit_findings."""

    def __init__(
        self,
        scoring: ResolveAndScoring,
        validator: PartialOutputValidating,
        submitter: FindingsSubmitting,
        summariser: SeveritySummarising,
    ) -> None:
        self._scoring = scoring
        self._validator = validator
        self._submitter = submitter
        self._summariser = summariser

    def orchestrate(self, partial_output: dict, output_path: str) -> dict[str, Any]:
        agent = partial_output.get("agent", "")
        principle = partial_output.get("principle", "")
        timestamp = partial_output.get("timestamp", "")
        scored_files, scoring_error, folder = self._scoring.resolve_and_score(
            agent, partial_output.get("files") or []
        )
        # Run schema validation whenever we have the folder — even when scoring already
        # failed. Schema errors are clearer to the LLM than Python evaluation errors
        # (NameError / TypeError from severity-band conditions), so prefer them.
        if folder:
            validation_error = self._validator.validate_output(partial_output, folder)
            if validation_error:
                return validation_error
        if scoring_error:
            return scoring_error
        err = self._submitter.submit(agent, principle, timestamp, scored_files, output_path, folder)
        if err:
            return err
        counts = self._summariser.summarise(scored_files)
        return {
            "principle": principle,
            **counts,
            "notice": (
                "<system-reminder>Scoring is complete and server-authoritative. "
                "The server applied deterministic severity bands from rule.md. "
                "Do NOT resubmit with different metrics to change the severity verdict. "
                "Accept this result and proceed to the next step.</system-reminder>"
            ),
        }


def _minimal_value_for_schema(prop_schema: dict):
    """Generate a minimal representative value for a JSON schema property.

    For string+enum properties returns the first valid enum member so generated
    examples are always schema-valid (never the generic placeholder "example").
    """
    t = prop_schema.get("type", "string")
    if t == "integer":
        return 0
    if t == "string":
        enum = prop_schema.get("enum")
        return enum[0] if enum else "example"
    if t == "boolean":
        return False
    if t == "array":
        items = prop_schema.get("items", {})
        item_props = items.get("properties", {})
        if item_props:
            return [{k: _minimal_value_for_schema(v) for k, v in item_props.items()}]
        return []
    if t == "object":
        props = prop_schema.get("properties", {})
        if props:
            return {k: _minimal_value_for_schema(v) for k, v in props.items()}
        return {}
    return "example"


def _parse_principle_schema(schema_path) -> Optional[dict]:
    """Parse a principle's review/output.schema.json.

    Returns:
        {
            "agent": str,
            "principle_name": str,
            "metrics_example": dict,
            "findings_required": bool,   — True when LLM must populate findings (e.g. DRY)
            "findings_example": dict,    — minimal example finding object, or None
        }
    or None when schema or metrics definition is absent.
    """
    p = Path(str(schema_path))
    if not p.exists():
        return None
    try:
        schema = json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None
    agent = schema.get("properties", {}).get("agent", {}).get("const", "")
    principle_name = schema.get("properties", {}).get("principle", {}).get("const", "")
    try:
        unit_items = (
            schema["properties"]["files"]["items"]
            ["properties"]["units"]["items"]
        )
    except (KeyError, TypeError):
        return None
    try:
        metrics_props = unit_items["properties"]["metrics"]["properties"]
    except (KeyError, TypeError):
        return None
    if not metrics_props:
        return None

    findings_required = "findings" in unit_items.get("required", [])
    findings_example = None
    if findings_required:
        try:
            finding_props = unit_items["properties"]["findings"]["items"]["properties"]
            findings_example = {k: _minimal_value_for_schema(v) for k, v in finding_props.items()}
        except (KeyError, TypeError):
            pass

    return {
        "agent": agent,
        "principle_name": principle_name,
        "metrics_example": {k: _minimal_value_for_schema(v) for k, v in metrics_props.items()},
        "findings_required": findings_required,
        "findings_example": findings_example,
    }


def _metrics_example_from_schema(schema_path) -> Optional[str]:
    """Return a <submission-metrics-example> XML block, or None if schema absent."""
    parsed = _parse_principle_schema(schema_path)
    if not parsed:
        return None
    return (
        "<submission-metrics-example>\n"
        + json.dumps(parsed["metrics_example"], separators=(",", ":"))
        + "\n</submission-metrics-example>"
    )


class PrincipleContentBuilding(Protocol):
    def build(self, p_entry: dict) -> dict: ...


class PrincipleContentBuilder:
    """Reads a principle's rule.md and assembles its detection-rules output dict."""

    def build(self, p_entry: dict) -> dict:
        raw = Path(p_entry["rule_path"]).read_text(encoding="utf-8")
        blocks = parse_xml_blocks(raw)
        name = p_entry["name"]
        if not (blocks["detection"] or blocks["definition"] or blocks["severity-bands"]):
            return {"name": name, "content": strip_frontmatter(raw)}
        sections = [f"## {name.upper()}"]
        for mid, text in blocks["definition"].items():
            sections.append(f'<definition id="{mid}">\n{text}\n</definition>')
        for mid, text in blocks["detection"].items():
            sections.append(f'<detection id="{mid}">\n{text}\n</detection>')
        # Severity bands omitted — server scores via submit_findings, LLM does not need them.
        if blocks["exceptions"]:
            sections.append(f'<exceptions principle="{name.upper()}">\n{blocks["exceptions"]}\n</exceptions>')
        schema_path = Path(p_entry["folder"]) / "review" / "output.schema.json"
        parsed_schema = _parse_principle_schema(schema_path)
        if parsed_schema:
            sections.append(
                "<submission-metrics-example>\n"
                + json.dumps(parsed_schema["metrics_example"], separators=(",", ":"))
                + "\n</submission-metrics-example>"
            )
        return {
            "name": name,
            "content": "\n\n".join(sections),
            "detection": blocks["detection"],
            "definition": blocks["definition"],
            "severity_bands": blocks["severity-bands"],
            "exceptions": blocks["exceptions"],
            "principle_name": parsed_schema["principle_name"] if parsed_schema else name.upper(),
            "metrics_example": parsed_schema["metrics_example"] if parsed_schema else {},
        }


class DetectionRulesLoader:
    """Discovers active principles and delegates content assembly to PrincipleContentBuilding."""

    def __init__(
        self,
        all_principles: AllPrinciplesProviding,
        refs_root: Path,
        discover_fn: Optional[Callable] = None,
        content_builder: Optional[PrincipleContentBuilding] = None,
    ) -> None:
        self._all_principles = all_principles
        self._refs_root = refs_root
        self._discover_fn = discover_fn or _dp.discover_and_filter
        self._content_builder = content_builder or PrincipleContentBuilder()

    def load_detection_rules(
        self,
        principle: Optional[str] = None,
        matched_tags: Optional[list] = None,
    ) -> dict[str, Any]:
        all_p = self._all_principles.all_principles()

        if principle:
            m = next((p for p in all_p if p["name"].lower() == principle.lower()), None)
            if not m:
                available = ", ".join(p["name"] for p in all_p)
                return {"error": f"Principle '{principle}' not found. Available: {available}"}
            return {"principles": [self._content_builder.build(m)]}

        if matched_tags is None:
            active = all_p
        else:
            # Normalize: empty string or empty list → [] (only always-on).
            # Single string (e.g. "unit-test" from CLI) → single-item list.
            if matched_tags == "" or matched_tags == []:
                tags: list = []
            elif isinstance(matched_tags, list):
                tags = matched_tags
            else:
                tags = [matched_tags]
            active = self._discover_fn(str(self._refs_root), matched_tags=tags)["active_principles"]
        return {"principles": [self._content_builder.build(p) for p in active]}


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


# ── Fix submission ────────────────────────────────────────────────────────────

def _violation_key(metric_id: str, file_path: str, unit_name: str) -> str:
    """Stable identifier for a (metric_id, file, unit) triple used to match fixes to violations."""
    safe_path = re.sub(r'[^\w.-]', '_', file_path)
    safe_unit = re.sub(r'[^\w.-]', '_', unit_name)
    return f"{metric_id}__{safe_path}__{safe_unit}"


class ViolationReading(Protocol):
    def read_violations(self, output_dir: str) -> list: ...


class ViolationReader:
    """Reads SEVERE violations from scored output files in an output directory."""

    def read_violations(self, output_dir: str) -> list:
        violations = []
        for scored_file in sorted(Path(output_dir).glob("*/review-output.json")):
            try:
                doc = json.loads(scored_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            for file_obj in doc.get("files", []):
                file_path = file_obj.get("file_path", "?")
                for unit in file_obj.get("units", []):
                    unit_name = unit.get("unit_name", "?")
                    for finding in unit.get("findings", []):
                        if finding.get("severity") == "SEVERE":
                            violations.append({
                                "metric_id": finding.get("metric_id", ""),
                                "file_path": file_path,
                                "unit_name": unit_name,
                            })
        return violations


class FixSubmitting(Protocol):
    def submit_fix(self, output_dir: str, fixes: list) -> dict: ...


class FixSubmitter:
    """Persists fix suggestions and delegates completeness validation to an injected reader.

    Single responsibility: fix file persistence. Violation reading is a separate concern
    owned by the injected ViolationReading dependency.
    """

    def __init__(self, reader: ViolationReading) -> None:
        self._reader = reader

    def submit_fix(self, output_dir: str, fixes: list) -> dict:
        if not isinstance(fixes, list):
            return {"error": "'fixes' must be a list of {metric_id, file_path, unit_name, suggested_fix} objects"}

        fixes_dir = Path(output_dir) / "fixes"
        fixes_dir.mkdir(parents=True, exist_ok=True)

        for fix in fixes:
            try:
                key = _violation_key(fix["metric_id"], fix["file_path"], fix["unit_name"])
            except KeyError as exc:
                return {"error": f"Fix entry missing required field: {exc}. Required: metric_id, file_path, unit_name, suggested_fix"}
            (fixes_dir / f"{key}.json").write_text(
                json.dumps(fix), encoding="utf-8",
            )

        all_violations = self._reader.read_violations(output_dir)
        violation_keys = {
            _violation_key(v["metric_id"], v["file_path"], v["unit_name"])
            for v in all_violations
        }
        fix_keys = {p.stem for p in fixes_dir.glob("*.json")}
        missing_keys = violation_keys - fix_keys

        if missing_keys:
            missing_ids = [
                v["metric_id"] for v in all_violations
                if _violation_key(v["metric_id"], v["file_path"], v["unit_name"]) in missing_keys
            ]
            return {
                "error": (
                    f"Missing fixes for {len(missing_keys)} violation(s): {missing_ids}. "
                    "Include an entry for every violation in the fixes array."
                ),
            }

        fixes_by_key: dict = {}
        for fp in fixes_dir.glob("*.json"):
            try:
                data = json.loads(fp.read_text(encoding="utf-8"))
                fkey = _violation_key(data["metric_id"], data["file_path"], data["unit_name"])
                fixes_by_key[fkey] = data
            except (json.JSONDecodeError, OSError, KeyError):
                pass

        violations_with_fixes = [
            {**v, "suggested_fix": fixes_by_key.get(
                _violation_key(v["metric_id"], v["file_path"], v["unit_name"]), {}
            ).get("suggested_fix", "")}
            for v in all_violations
        ]
        return {"complete": True, "violations_with_fixes": violations_with_fixes}


class GatewayHandler:
    """Pure Facade delegating to ScoringSeverity, SubmitOrchestrating, RulesLoading, and FixSubmitting.

    All dependencies are protocol-typed and injected via __init__. No internal
    construction — use make_gateway_handler() for production wiring.
    """

    def __init__(
        self,
        scoring: ScoringSeverity,
        submit_orchestrator: SubmitOrchestrating,
        rules: RulesLoading,
        fix_submitter: FixSubmitting,
    ) -> None:
        self._scoring = scoring
        self._submit_orchestrator = submit_orchestrator
        self._rules = rules
        self._fix_submitter = fix_submitter

    def score_severity(self, partial_outputs: list) -> dict[str, Any]:
        return self._scoring.score_severity(partial_outputs)

    def submit_findings(self, partial_output: dict, output_path: str) -> dict[str, Any]:
        return self._submit_orchestrator.orchestrate(partial_output, output_path)

    def submit_batch_findings(self, output_dir: str, submissions: dict) -> dict[str, Any]:
        """Submit findings for multiple principles in one call.

        Scores each principle's metrics, writes output files, and returns violations.
        When SEVERE violations exist, the response includes instructions for the LLM
        to call load_fix_for_violation and submit_fix for each one.

        Fails fast on the first validation or scoring error.
        """
        for label, partial_output in submissions.items():
            output_path = str(Path(output_dir) / label / "review-output.json")
            result = self._submit_orchestrator.orchestrate(
                _filter_by_kind(partial_output), output_path
            )
            if "error" in result:
                return {"error": result["error"], "failed_at": label}
        violations = self._read_severe_violations(output_dir)
        response: dict = {"violations": violations}
        if violations:
            response["output_dir"] = output_dir
            response["message"] = (
                f"Found {len(violations)} SEVERE violation(s). Complete these steps:\n"
                f"1. Call mcp__docs__load_fix_for_violation ONCE with metric_ids=["
                + ", ".join(f"'{v['metric_id']}'" for v in violations)
                + f"] to get all fix strategies in one call.\n"
                f"2. For each violation, prepare a concrete code-specific fix using the guidance.\n"
                f"3. Call mcp__pipeline__submit_fix ONCE with output_dir='{output_dir}' and "
                f"fixes=[{{metric_id, file_path, unit_name, suggested_fix}}, ...] for all violations."
            )
        return response

    def submit_fix(self, output_dir: str, fixes: list) -> dict[str, Any]:
        return self._fix_submitter.submit_fix(output_dir, fixes)

    def _read_severe_violations(self, output_dir: str) -> list:
        """Read SEVERE violations from all scored output files in output_dir."""
        violations = []
        for scored_file in sorted(Path(output_dir).glob("*/review-output.json")):
            try:
                doc = json.loads(scored_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            principle = doc.get("principle", doc.get("agent", ""))
            for file_obj in doc.get("files", []):
                file_path = file_obj.get("file_path", "?")
                for unit in file_obj.get("units", []):
                    unit_name = unit.get("unit_name", "?")
                    for finding in unit.get("findings", []):
                        if finding.get("severity") != "SEVERE":
                            continue
                        mid = finding.get("metric_id", "")
                        band = finding.get("band_matched", "")
                        metrics = finding.get("metrics", {})
                        if band and metrics:
                            measured = ", ".join(f"{k}={v}" for k, v in metrics.items())
                            desc = f"{band} (measured: {measured})"
                        else:
                            desc = band or "SEVERE violation detected"
                        violations.append({
                            "principle": principle,
                            "metric_id": mid,
                            "file_path": file_path,
                            "unit_name": unit_name,
                            "issue": f"{mid}: {file_path}, unit {unit_name} — {desc}",
                            "fix": (
                                f"Call mcp__docs__load_fix_for_violation({mid}) "
                                "for specific guidance."
                            ),
                        })
        return violations

    def load_detection_rules(
        self, principle: Optional[str] = None, matched_tags: Optional[list] = None,
    ) -> dict[str, Any]:
        return self._rules.load_detection_rules(principle, matched_tags)

    def load_fix_instructions(self, metric_id: str) -> str:
        return self._rules.load_fix_instructions(metric_id)


def make_gateway_handler(refs_root: Path) -> GatewayHandler:
    """Wire production defaults and return a ready-to-use GatewayHandler."""
    registry = PrincipleRegistry(refs_root)
    scoring = ScoringHandler(
        scorer_provider=PrincipleScorerProvider(refs_root),
        files_scorer=FilesScoringHandler(),
    )
    return GatewayHandler(
        scoring=scoring,
        submit_orchestrator=SubmitOrchestrator(
            scoring=scoring,
            validator=PartialOutputValidator(),
            submitter=FindingsSubmitter(),
            summariser=SeveritySummariser(),
        ),
        rules=RulesHandler(
            detection=DetectionRulesLoader(registry, refs_root=refs_root),
            fix_instructions=FixInstructionsLoader(registry),
        ),
        fix_submitter=FixSubmitter(ViolationReader()),
    )
